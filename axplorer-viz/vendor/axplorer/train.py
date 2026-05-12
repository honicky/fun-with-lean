import argparse
import json  # [axplorer-viz patch] trajectory logging
import os
import random  # [axplorer-viz patch] seed Python's RNG for reproducible runs
import time
from logging import getLogger

import numpy as np
import torch

from src.datasets import CharDataset, InfiniteDataLoader, load_initial_data, update_datasets
from src.envs import ENVS, build_env
from src.envs.environment import do_stats
from src.evaluator import sample_and_score
from src.models.model import Transformer
from src.trainer import reload_model_optimizer, train
from src.utils import bool_flag, force_release_memory, initialize_exp, log_resources, write_important_metrics

logger = getLogger()

# ---------------------------------------------------------------------------
# [axplorer-viz patch] trajectory logging (--log_trajectory). One JSONL line
# per epoch, written after the Selection phase. The Manim visualization in
# axplorer-viz consumes this; nothing else in Axplorer changes. See
# axplorer-viz/vendor/PATCH_NOTES.md.
# ---------------------------------------------------------------------------
_TRAJECTORY_LOG_CAP = 32  # max objects / samples per JSONL field, keeps logs readable


def _edge_tokens(datapoint, env):
    """Edge tokens for a datapoint (BOS/EOS/PAD/SEP stripped)."""
    itos = env.tokenizer.itos
    # In every tokenizer here the special symbols map to ``str`` in ``itos``;
    # everything else is an edge/coordinate token.
    return [int(t) for t in env.tokenizer.encode(datapoint) if not isinstance(itos[int(t)], str)]


def _n_edge_tokens(env):
    extra = getattr(env.tokenizer, "extra_symbols", None) or getattr(env, "SPECIAL_SYMBOLS", [])
    return len(env.tokenizer.itos) - len(extra)


def _append_trajectory_log(path, epoch, train_set, new_data, raw_token_seqs, env, start_time):
    cap = _TRAJECTORY_LOG_CAP
    valid = lambda d: getattr(d, "score", None) is not None and d.score >= 0
    top_k = sorted((d for d in train_set if valid(d)), key=lambda d: d.score, reverse=True)[:cap]
    after = sorted((d for d in new_data if valid(d)), key=lambda d: d.score, reverse=True)[:cap]
    n_edge = _n_edge_tokens(env)
    strip = lambda seq: [int(t) for t in seq if 0 <= int(t) < n_edge]
    record = {
        "epoch": int(epoch),
        "n_vertices": int(getattr(getattr(env, "tokenizer", None), "N", 0)),  # [axplorer-viz patch] self-describing logs
        "top_k_objects": [_edge_tokens(d, env) for d in top_k],
        "top_k_scores": [float(d.score) for d in top_k],
        "model_samples_raw": [strip(seq) for seq in (raw_token_seqs or [])][:cap],
        "model_samples_after_search": [_edge_tokens(d, env) for d in after],
        "best_score_so_far": float(max((d.score for d in train_set if valid(d)), default=-1.0)),
        "wall_time_seconds": float(time.time() - start_time),
    }
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def get_parser():
    parser = argparse.ArgumentParser("A simple Axplorer loop for different maths problems")

    parser.add_argument("--gensize", type=int, default=100000, help="Number of generate initial values")
    parser.add_argument("--max_epochs", type=int, default=2000, help="Number of epochs")
    parser.add_argument("--max_steps", type=int, default=50000, help="number of training steps.")
    parser.add_argument("--num_samples_from_model", type=int, default=500000, help="sample the specified number from the model in each loop")
    parser.add_argument("--pop_size", type=int, default=200000, help="Total maximum number of examples at each epoch")
    parser.add_argument("--ntest", type=int, default=1000, help="Size of test set")
    parser.add_argument("--env_name", type=str, default="square", help="Math problem to be addressed")
    ENVS[parser.parse_known_args()[0].env_name].register_args(parser)

    parser.add_argument("--process_pool", type=bool_flag, default="true", help="use process_pool to generate and score initial data")
    parser.add_argument("--always_search", type=bool_flag, default="true", help="if True, use local search for all examples generated")
    parser.add_argument("--redeem_only", type=bool_flag, default="false", help="if True, save invalid examples only")
    parser.add_argument("--new_proportion", type=float, default=0.0, help="proportion of new samples in test set")

    parser.add_argument("--num_workers", type=int, default=8, help="number of data workers for both train/test")
    parser.add_argument("--num_eval_steps", type=int, default=500, help="number of step between each evaluation during training.")
    parser.add_argument("--seed", type=int, default=-1, help="seed")
    # sampling
    parser.add_argument("--top_k", type=int, default=-1, help="top-k for sampling, -1 means no top-k")
    # model
    parser.add_argument("--n_layer", type=int, default=4, help="number of layers")
    parser.add_argument("--n_head", type=int, default=8, help="number of heads (in a transformer)")
    parser.add_argument("--n_embd", type=int, default=256, help="number of feature channels in the model")
    parser.add_argument("--no_positional", type=bool_flag, default="false", help="no positional embedding")
    parser.add_argument("--max_len", type=int, default=500, help="Block size, maximum length of sequences")

    # optimization
    parser.add_argument("--batch_size", type=int, default=32, help="batch size during optimization")
    parser.add_argument("--learning_rate", type=float, default=5e-4, help="learning rate")
    parser.add_argument("--weight_decay", type=float, default=0.01, help="weight decay")
    # evaluation against known "good sequences"
    parser.add_argument("--gen_batch_size", type=int, default=1000, help="generation batch size")
    parser.add_argument("--temperature", type=float, default=1.0, help="temperature")
    parser.add_argument("--temp_span", type=int, default=0, help="temperature span")
    parser.add_argument("--inc_temp", type=float, default=0.0, help="temperature")
    parser.add_argument("--keep_only_unique", type=bool_flag, default="true", help="keep only unique data")
    parser.add_argument("--save_best", type=bool_flag, default="false", help="save best model based on test loss")

    # path and ports
    parser.add_argument("--dump_path", type=str, default="checkpoint", help="Experiment dump path")
    parser.add_argument("--exp_name", type=str, default="debug", help="Experiment name")
    parser.add_argument("--exp_id", type=str, default="", help="Experiment ID")
    parser.add_argument("--cpu", type=bool_flag, default="false", help="run on cpu only")
    parser.add_argument("--data_generation_only", type=bool_flag, default="false", help="only generate data and exit")
    # [axplorer-viz patch] write one JSONL line of trajectory data per epoch to this path (empty = off)
    parser.add_argument("--log_trajectory", type=str, default="", help="[axplorer-viz] path to a .jsonl trajectory log (one line per epoch); empty = disabled")

    return parser


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    if args.exp_id == "" and os.environ.get("MODAL_EXP_ID") is None:
        os.environ["MODAL_EXP_ID"] = time.strftime("%Y_%m_%d_%H_%M_%S")
        args.exp_id = os.environ["MODAL_EXP_ID"]

    args.device = "cpu" if args.cpu else ("mps" if torch.backends.mps.is_available() else "cuda")
    if args.device == "cuda":
        torch.cuda.manual_seed_all(args.seed)
    if args.device == "mps":
        torch.mps.manual_seed(args.seed)

    fused = True if args.device in ["cuda", "mps"] else False

    logger = initialize_exp(args)
    if not os.path.exists(args.dump_path):
        os.makedirs(args.dump_path)

    if args.seed < 0:
        args.seed = np.random.randint(1_000_000_000)
    logger.info(f"seed: {args.seed}")
    # [axplorer-viz patch] also seed Python's and numpy's global RNGs (upstream
    # only seeds torch here). With --process_pool false this makes a run
    # reproducible end to end; with the process pool, worker RNG state is not
    # seeded, so reproducibility is best-effort. See vendor/PATCH_NOTES.md.
    random.seed(args.seed)
    np.random.seed(args.seed)
    _traj_start_time = time.time()  # [axplorer-viz patch] for wall_time_seconds in the log

    env = build_env(args)

    classname = env.data_class

    # system inits
    torch.manual_seed(args.seed)

    args.vocab_size = len(env.tokenizer.itos)

    args.block_size = args.max_len + 2
    stoi = env.tokenizer.stoi
    itos = env.tokenizer.itos

    # Initialize transformer
    model = Transformer(args, stoi["PAD"], stoi["EOS"])
    model.to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=args.weight_decay, betas=(0.9, 0.99), eps=1e-8, fused=fused)
    reload_model_optimizer(args, model, optimizer)

    train_set, test_set = load_initial_data(args, classname)
    if args.data_generation_only:
        logger.info("Data generation only mode. Exiting...")
        exit(0)
    train_data_path = os.path.join(args.dump_path, "train_data.pkl")
    test_data_path = os.path.join(args.dump_path, "test_data.pkl")

    # log initial stats
    metrics = do_stats(-1, data=train_set)
    temperature = args.temperature
    # Loop of Axplorer
    best_loss = None
    epoch_file = os.path.join(args.dump_path, "epoch.txt")
    if os.path.isfile(epoch_file):
        with open(epoch_file, "r") as f:
            n_epoch = int(f.read())
    else:
        n_epoch = 0
    temp_file = os.path.join(args.dump_path, "temperature.txt")
    if os.path.isfile(temp_file):
        with open(temp_file, "r") as f:
            temperature = float(f.read())
    else:
        temperature = args.temperature

    metric_file = os.path.join(args.dump_path, "metrics.txt")
    write_important_metrics(metrics, n_epoch, metric_file, command=args.command)

    for epoch in range(n_epoch, args.max_epochs):
        logger.info(f"==== Starting Epoch {n_epoch} =====")
        log_resources(f"Epoch {epoch} START")

        if args.device == "cuda":
            torch.cuda.empty_cache()
        elif args.device == "mps":
            torch.mps.empty_cache()

        # tokenize
        train_words = [env.tokenizer.encode(d) for d in train_set]
        test_words = [env.tokenizer.encode(d) for d in test_set]
        # data loaders
        train_dataset = CharDataset(train_words, args.max_len, stoi)
        test_dataset = CharDataset(test_words, args.max_len, stoi)
        force_release_memory()

        if args.device == "cuda":
            logger.info(
                f"Memory allocated: {torch.cuda.memory_allocated(0)/(1024*1024):.2f}MB, reserved: {torch.cuda.memory_reserved(0)/(1024*1024):.2f}MB"
            )
        elif args.device == "mps":
            logger.info(
                f"Memory allocated: {torch.mps.current_allocated_memory()/(1024*1024):.2f}MB, reserved: {torch.mps.driver_allocated_memory()/(1024*1024):.2f}MB"
            )

        batch_loader = InfiniteDataLoader(train_dataset, batch_size=args.batch_size, pin_memory=args.device == "cuda", num_workers=0)
        try:
            best_loss = train(model, args, batch_loader, optimizer, test_dataset, current_best_loss=best_loss)
        finally:
            batch_loader.close()
            del batch_loader
        log_resources(f"Epoch {epoch} AFTER_TRAIN")
        force_release_memory()

        logger.info(f"Sample with temperature {temperature} to {temperature+0.1*args.temp_span}")
        if args.device == "cuda":
            torch.cuda.empty_cache()
        elif args.device == "mps":
            torch.mps.empty_cache()

        # [axplorer-viz patch] collect a few raw (pre-local-search) samples for the log
        _raw_samples = [] if args.log_trajectory else None
        new_data = sample_and_score(model, args, stoi, itos, env, temperature, args.temp_span, raw_token_out=_raw_samples)
        log_resources(f"Epoch {epoch} AFTER_SAMPLE")

        if args.device == "cuda":
            torch.cuda.empty_cache()
        elif args.device == "mps":
            torch.mps.empty_cache()

        # Possible to add another generation method here and mix it before taking the best
        train_set, test_set, inc_temp = update_datasets(args, new_data, train_set, test_set, train_data_path, test_data_path)
        log_resources(f"Epoch {epoch} AFTER_UPDATE_DATASETS")
        force_release_memory()

        # Possible to add another generation method here and mix it before taking the best
        if inc_temp and args.inc_temp > 0.0:
            temperature += args.inc_temp

        metrics = do_stats(-1, data=train_set)

        n_epoch += 1
        with open(epoch_file, "w") as f:
            f.write(str(n_epoch))
        with open(temp_file, "w") as f:
            f.write(str(temperature))

        write_important_metrics(metrics, n_epoch, metric_file)

        # [axplorer-viz patch] append one JSONL line of trajectory data for this epoch
        if args.log_trajectory:
            _append_trajectory_log(args.log_trajectory, epoch, train_set, new_data, _raw_samples, env, _traj_start_time)
            logger.info(f"[axplorer-viz] appended trajectory log for epoch {epoch} -> {args.log_trajectory}")
