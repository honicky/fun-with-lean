/// Partition `slice` in-place around the pivot (last element).
/// Returns the final index of the pivot.
fn partition(slice: &mut [i64]) -> usize {
    let pivot_idx = slice.len() - 1;
    let pivot = slice[pivot_idx];
    let mut i = 0;
    for j in 0..pivot_idx {
        if slice[j] <= pivot {
            slice.swap(i, j);
            i += 1;
        }
    }
    slice.swap(i, pivot_idx);
    i
}

/// In-place quicksort (Lomuto partition scheme).
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
}
