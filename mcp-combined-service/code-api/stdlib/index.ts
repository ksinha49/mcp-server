/**
 * Standard Library for Code Execution
 *
 * Provides utility functions available in the execution context.
 */

export * from './transform.ts';
export * from './format.ts';
export * from './validate.ts';

import * as transformModule from './transform.ts';
import * as formatModule from './format.ts';
import * as validateModule from './validate.ts';

/**
 * Standard library namespace
 */
export const transform = transformModule;
export const format = formatModule;
export const validate = validateModule;

export default {
  transform,
  format,
  validate,
};
