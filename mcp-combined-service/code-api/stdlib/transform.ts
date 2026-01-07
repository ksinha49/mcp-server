/**
 * Data Transformation Utilities
 *
 * Functions for filtering, mapping, grouping, and transforming data.
 */

/**
 * Filter array elements by predicate
 */
export function filter<T>(arr: T[], predicate: (item: T) => boolean): T[] {
  return arr.filter(predicate);
}

/**
 * Map array elements using a transformation function
 */
export function map<T, U>(arr: T[], mapper: (item: T) => U): U[] {
  return arr.map(mapper);
}

/**
 * Group array elements by a key function
 */
export function groupBy<T>(arr: T[], keyFn: (item: T) => string): Record<string, T[]> {
  const result: Record<string, T[]> = {};
  for (const item of arr) {
    const key = keyFn(item);
    if (!result[key]) {
      result[key] = [];
    }
    result[key].push(item);
  }
  return result;
}

/**
 * Sort array by a key function
 */
export function sortBy<T>(
  arr: T[],
  keyFn: (item: T) => number | string,
  order: 'asc' | 'desc' = 'asc'
): T[] {
  return [...arr].sort((a, b) => {
    const aKey = keyFn(a);
    const bKey = keyFn(b);
    let cmp: number;

    if (typeof aKey === 'number' && typeof bKey === 'number') {
      cmp = aKey - bKey;
    } else {
      cmp = String(aKey).localeCompare(String(bKey));
    }

    return order === 'asc' ? cmp : -cmp;
  });
}

/**
 * Get unique elements from array
 */
export function unique<T>(arr: T[], keyFn?: (item: T) => unknown): T[] {
  if (keyFn) {
    const seen = new Set<unknown>();
    return arr.filter((item) => {
      const key = keyFn(item);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }
  return [...new Set(arr)];
}

/**
 * Flatten nested arrays
 */
export function flatten<T>(arr: T[][]): T[] {
  return arr.flat();
}

/**
 * Split array into chunks
 */
export function chunk<T>(arr: T[], size: number): T[][] {
  const result: T[][] = [];
  for (let i = 0; i < arr.length; i += size) {
    result.push(arr.slice(i, i + size));
  }
  return result;
}

/**
 * Take first n elements
 */
export function take<T>(arr: T[], n: number): T[] {
  return arr.slice(0, n);
}

/**
 * Skip first n elements
 */
export function skip<T>(arr: T[], n: number): T[] {
  return arr.slice(n);
}

/**
 * Find first element matching predicate
 */
export function find<T>(arr: T[], predicate: (item: T) => boolean): T | undefined {
  return arr.find(predicate);
}

/**
 * Check if any element matches predicate
 */
export function some<T>(arr: T[], predicate: (item: T) => boolean): boolean {
  return arr.some(predicate);
}

/**
 * Check if all elements match predicate
 */
export function every<T>(arr: T[], predicate: (item: T) => boolean): boolean {
  return arr.every(predicate);
}

/**
 * Count elements matching predicate
 */
export function count<T>(arr: T[], predicate?: (item: T) => boolean): number {
  if (!predicate) return arr.length;
  return arr.filter(predicate).length;
}

/**
 * Sum numeric values
 */
export function sum(arr: number[]): number;
export function sum<T>(arr: T[], valueFn: (item: T) => number): number;
export function sum<T>(arr: T[], valueFn?: (item: T) => number): number {
  if (valueFn) {
    return arr.reduce((acc, item) => acc + valueFn(item), 0);
  }
  return (arr as number[]).reduce((acc, val) => acc + val, 0);
}

/**
 * Calculate average of numeric values
 */
export function avg(arr: number[]): number;
export function avg<T>(arr: T[], valueFn: (item: T) => number): number;
export function avg<T>(arr: T[], valueFn?: (item: T) => number): number {
  if (arr.length === 0) return 0;
  const total = valueFn ? sum(arr, valueFn) : sum(arr as number[]);
  return total / arr.length;
}

/**
 * Find minimum value
 */
export function min(arr: number[]): number;
export function min<T>(arr: T[], valueFn: (item: T) => number): number;
export function min<T>(arr: T[], valueFn?: (item: T) => number): number {
  if (arr.length === 0) return 0;
  if (valueFn) {
    return Math.min(...arr.map(valueFn));
  }
  return Math.min(...(arr as number[]));
}

/**
 * Find maximum value
 */
export function max(arr: number[]): number;
export function max<T>(arr: T[], valueFn: (item: T) => number): number;
export function max<T>(arr: T[], valueFn?: (item: T) => number): number {
  if (arr.length === 0) return 0;
  if (valueFn) {
    return Math.max(...arr.map(valueFn));
  }
  return Math.max(...(arr as number[]));
}

/**
 * Pick specific keys from objects
 */
export function pick<T extends object, K extends keyof T>(arr: T[], keys: K[]): Pick<T, K>[] {
  return arr.map((item) => {
    const result = {} as Pick<T, K>;
    for (const key of keys) {
      if (key in item) {
        result[key] = item[key];
      }
    }
    return result;
  });
}

/**
 * Omit specific keys from objects
 */
export function omit<T extends object, K extends keyof T>(arr: T[], keys: K[]): Omit<T, K>[] {
  const keySet = new Set<string>(keys as string[]);
  return arr.map((item) => {
    const result = {} as Omit<T, K>;
    for (const key of Object.keys(item) as (keyof T)[]) {
      if (!keySet.has(key as string)) {
        (result as Record<string, unknown>)[key as string] = item[key];
      }
    }
    return result;
  });
}

/**
 * Pluck a single property from objects
 */
export function pluck<T, K extends keyof T>(arr: T[], key: K): T[K][] {
  return arr.map((item) => item[key]);
}

/**
 * Create a lookup map from array
 */
export function keyBy<T>(arr: T[], keyFn: (item: T) => string): Record<string, T> {
  const result: Record<string, T> = {};
  for (const item of arr) {
    result[keyFn(item)] = item;
  }
  return result;
}

/**
 * Partition array into two groups based on predicate
 */
export function partition<T>(arr: T[], predicate: (item: T) => boolean): [T[], T[]] {
  const pass: T[] = [];
  const fail: T[] = [];
  for (const item of arr) {
    if (predicate(item)) {
      pass.push(item);
    } else {
      fail.push(item);
    }
  }
  return [pass, fail];
}

/**
 * Zip multiple arrays together
 */
export function zip<T, U>(arr1: T[], arr2: U[]): [T, U][] {
  const length = Math.min(arr1.length, arr2.length);
  const result: [T, U][] = [];
  for (let i = 0; i < length; i++) {
    result.push([arr1[i], arr2[i]]);
  }
  return result;
}
