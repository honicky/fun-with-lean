/// Return the index of the median of `slice[a]`, `slice[b]`, `slice[c]`.
fn median_of_three(slice: &[i64], a: usize, b: usize, c: usize) -> usize {
    let (va, vb, vc) = (slice[a], slice[b], slice[c]);
    if (va <= vb && vb <= vc) || (vc <= vb && vb <= va) {
        b
    } else if (vb <= va && va <= vc) || (vc <= va && va <= vb) {
        a
    } else {
        c
    }
}

/// Partition `slice` in-place using median-of-three pivot selection.
/// Returns the final index of the pivot.
fn partition(slice: &mut [i64]) -> usize {
    let len = slice.len();
    // Choose pivot as median of first, middle, last elements.
    let pivot_idx = if len >= 3 {
        median_of_three(slice, 0, len / 2, len - 1)
    } else {
        len - 1
    };
    // Move pivot to end for Lomuto partitioning.
    slice.swap(pivot_idx, len - 1);
    let pivot = slice[len - 1];
    let mut i = 0;
    for j in 0..len - 1 {
        if slice[j] <= pivot {
            slice.swap(i, j);
            i += 1;
        }
    }
    slice.swap(i, len - 1);
    i
}

/// In-place quicksort (Lomuto scheme with median-of-three pivot).
fn quicksort(slice: &mut [i64]) {
    if slice.len() <= 1 {
        return;
    }
    let p = partition(slice);
    quicksort(&mut slice[..p]);
    quicksort(&mut slice[p + 1..]);
}

fn is_sorted(slice: &[i64]) -> bool {
    slice.windows(2).all(|w| w[0] <= w[1])
}

fn main() {
    let mut data = vec![3, 6, 8, 10, 1, 2, 1];
    println!("Before: {:?}", data);
    quicksort(&mut data);
    println!("After:  {:?}", data);
    assert!(is_sorted(&data));
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty() {
        let mut v: Vec<i64> = vec![];
        quicksort(&mut v);
        assert!(is_sorted(&v));
    }

    #[test]
    fn test_single() {
        let mut v = vec![42];
        quicksort(&mut v);
        assert_eq!(v, vec![42]);
    }

    #[test]
    fn test_sorted() {
        let mut v = vec![1, 2, 3, 4, 5];
        quicksort(&mut v);
        assert_eq!(v, vec![1, 2, 3, 4, 5]);
    }

    #[test]
    fn test_reverse() {
        let mut v = vec![5, 4, 3, 2, 1];
        quicksort(&mut v);
        assert_eq!(v, vec![1, 2, 3, 4, 5]);
    }

    #[test]
    fn test_duplicates() {
        let mut v = vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5];
        quicksort(&mut v);
        assert!(is_sorted(&v));
        assert_eq!(v.len(), 11);
    }

    #[test]
    fn test_all_equal() {
        let mut v = vec![7, 7, 7, 7];
        quicksort(&mut v);
        assert_eq!(v, vec![7, 7, 7, 7]);
    }

    #[test]
    fn test_negative() {
        let mut v = vec![-3, -1, -4, -1, -5];
        quicksort(&mut v);
        assert_eq!(v, vec![-5, -4, -3, -1, -1]);
    }

    #[test]
    fn test_large_sorted_input() {
        // Regression: previously caused O(n²) with last-element pivot.
        let mut v: Vec<i64> = (0..10_000).collect();
        quicksort(&mut v);
        assert!(is_sorted(&v));
    }

    #[test]
    fn test_large_all_equal() {
        let mut v = vec![42; 10_000];
        quicksort(&mut v);
        assert!(is_sorted(&v));
    }
}
