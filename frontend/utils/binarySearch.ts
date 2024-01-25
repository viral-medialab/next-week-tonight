export default function binarySearch<A, B>(
    haystack: ArrayLike<A>,
    needle: B,
    comparator: (a: A, b: B, index?: number, haystack?: A[]) => any,
    // Notes about comparator return value:
    // * when a<b the comparator's returned value should be:
    //   * negative number or a value such that `+value` is a negative number
    //   * examples: `-1` or the string `"-1"`
    // * when a>b the comparator's returned value should be:
    //   * positive number or a value such that `+value` is a positive number
    //   * examples: `1` or the string `"1"`
    // * when a===b
    //    * any value other than the return cases for a<b and a>b
    //    * examples: undefined, NaN, 'abc'
    low = -1,
    high = -1,
    lowerBound = false,
    upperBound = false
): number {
    if (low === -1) low = 0;
    else {
        low = low | 0;
        if (low < 0 || low >= haystack.length)
            throw new RangeError("invalid lower bound");
    }

    if (high === -1) high = haystack.length - 1;
    else {
        high = high | 0;
        if (high < low || high >= haystack.length)
            throw new RangeError("invalid upper bound");
    }

    while (low <= high) {
        // The naive `low + high >>> 1` could fail for array lengths > 2**31
        // because `>>>` converts its operands to int32. `low + (high - low >>> 1)`
        // works for array lengths <= 2**32-1 which is also Javascript's max array
        // length.
        const mid = low + ((high - low) >>> 1);
        const cmp = +comparator(haystack[mid], needle, mid, haystack as []);

        // Too low.
        if (cmp < 0.0) low = mid + 1;
        // Too high.
        else if (cmp > 0.0) high = mid - 1;
        // Key found.
        else return mid;
    }

    // Key not found.
    if (lowerBound)
        return low; // return the index of the first element that is >= needle
    else if (upperBound)
        return high; // return the index of the last element that is <= needle
    else return ~low;
}
