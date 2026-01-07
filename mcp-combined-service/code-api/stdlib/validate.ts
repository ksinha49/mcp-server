/**
 * Validation Utilities
 *
 * Functions for validating data types and formats.
 */

/**
 * Check if string is a valid email address
 */
export function isEmail(str: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(str);
}

/**
 * Check if string is a valid URL
 */
export function isURL(str: string): boolean {
  try {
    new URL(str);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if string is a valid date
 */
export function isDate(str: string): boolean {
  const date = new Date(str);
  return !isNaN(date.getTime());
}

/**
 * Check if string contains only numeric characters
 */
export function isNumeric(str: string): boolean {
  return /^-?\d+(\.\d+)?$/.test(str);
}

/**
 * Check if value is empty (null, undefined, empty string, empty array, empty object)
 */
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return value.trim() === '';
  if (Array.isArray(value)) return value.length === 0;
  if (typeof value === 'object') return Object.keys(value).length === 0;
  return false;
}

/**
 * Check if object has a property
 */
export function hasProperty<T extends object>(obj: T, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

/**
 * Check if value is a plain object
 */
export function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Check if value is an array
 */
export function isArray(value: unknown): value is unknown[] {
  return Array.isArray(value);
}

/**
 * Check if value is a string
 */
export function isString(value: unknown): value is string {
  return typeof value === 'string';
}

/**
 * Check if value is a number
 */
export function isNumber(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value);
}

/**
 * Check if value is a boolean
 */
export function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean';
}

/**
 * Check if value is a function
 */
export function isFunction(value: unknown): value is (...args: unknown[]) => unknown {
  return typeof value === 'function';
}

/**
 * Check if string matches a regex pattern
 */
export function matches(str: string, pattern: RegExp | string): boolean {
  const regex = typeof pattern === 'string' ? new RegExp(pattern) : pattern;
  return regex.test(str);
}

/**
 * Check if string is a valid UUID
 */
export function isUUID(str: string): boolean {
  const uuidRegex =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(str);
}

/**
 * Check if string is a valid ISO date string
 */
export function isISODate(str: string): boolean {
  const isoRegex = /^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d{3})?(Z|[+-]\d{2}:\d{2})?)?$/;
  return isoRegex.test(str) && isDate(str);
}

/**
 * Check if number is within a range
 */
export function inRange(num: number, min: number, max: number): boolean {
  return num >= min && num <= max;
}

/**
 * Check if string length is within bounds
 */
export function lengthBetween(str: string, min: number, max: number): boolean {
  return str.length >= min && str.length <= max;
}

/**
 * Check if array has minimum length
 */
export function minLength<T>(arr: T[], min: number): boolean {
  return arr.length >= min;
}

/**
 * Check if array has maximum length
 */
export function maxLength<T>(arr: T[], max: number): boolean {
  return arr.length <= max;
}

/**
 * Check if all items in array satisfy predicate
 */
export function allMatch<T>(arr: T[], predicate: (item: T) => boolean): boolean {
  return arr.every(predicate);
}

/**
 * Check if any item in array satisfies predicate
 */
export function anyMatch<T>(arr: T[], predicate: (item: T) => boolean): boolean {
  return arr.some(predicate);
}

/**
 * Check if no item in array satisfies predicate
 */
export function noneMatch<T>(arr: T[], predicate: (item: T) => boolean): boolean {
  return !arr.some(predicate);
}

/**
 * Validate required fields exist in object
 */
export function hasRequiredFields<T extends object>(
  obj: T,
  fields: string[]
): { valid: boolean; missing: string[] } {
  const missing = fields.filter((field) => !hasProperty(obj, field) || isEmpty((obj as Record<string, unknown>)[field]));
  return {
    valid: missing.length === 0,
    missing,
  };
}

/**
 * Validate object against a simple schema
 */
export function validateSchema(
  obj: unknown,
  schema: Record<string, 'string' | 'number' | 'boolean' | 'array' | 'object'>
): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!isObject(obj)) {
    return { valid: false, errors: ['Value must be an object'] };
  }

  for (const [key, expectedType] of Object.entries(schema)) {
    const value = obj[key];

    if (value === undefined) {
      errors.push(`Missing required field: ${key}`);
      continue;
    }

    let typeMatches = false;
    switch (expectedType) {
      case 'string':
        typeMatches = isString(value);
        break;
      case 'number':
        typeMatches = isNumber(value);
        break;
      case 'boolean':
        typeMatches = isBoolean(value);
        break;
      case 'array':
        typeMatches = isArray(value);
        break;
      case 'object':
        typeMatches = isObject(value);
        break;
    }

    if (!typeMatches) {
      errors.push(`Field ${key} must be of type ${expectedType}`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
