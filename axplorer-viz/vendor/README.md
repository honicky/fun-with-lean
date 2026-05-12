# vendor/axplorer — vendored copy of AxiomMath/axplorer

This is a **vendored copy** (not a git submodule) of
[AxiomMath/axplorer](https://github.com/AxiomMath/axplorer), license
**Apache-2.0** (see `axplorer/LICENSE`), pinned to upstream commit:

    3298b1afcefc04a3404d3d2b24cb3ccd1877c027   ("dataloader default to 0 worker")

We keep the fork **minimal**: the only change is a small trajectory-logging
patch — see `PATCH_NOTES.md` and the git history of this directory
(`git log -p axplorer-viz/vendor/axplorer/`). We did not refactor any of their
code.

`axplorer-viz` is a learning-in-public reproduction and is **not affiliated
with Axiom Math**. All copyright and attribution in `axplorer/LICENSE` and
`axplorer/` is preserved.

To update the vendored copy: re-clone upstream, re-apply the patch described in
`PATCH_NOTES.md`, and bump the commit hash above.
