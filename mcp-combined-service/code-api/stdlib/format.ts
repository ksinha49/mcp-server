/**
 * Formatting Utilities
 *
 * Functions for formatting data into various output formats.
 */

/**
 * Convert data to JSON string
 */
export function toJSON(data: unknown, pretty = false): string {
  return JSON.stringify(data, null, pretty ? 2 : undefined);
}

/**
 * Convert array of objects to CSV
 */
export function toCSV<T extends Record<string, unknown>>(
  data: T[],
  columns?: string[]
): string {
  if (data.length === 0) return '';

  const cols = columns || Object.keys(data[0]);
  const escapeValue = (value: unknown): string => {
    const str = value === null || value === undefined ? '' : String(value);
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`;
    }
    return str;
  };

  const header = cols.join(',');
  const rows = data.map((row) => cols.map((col) => escapeValue(row[col])).join(','));

  return [header, ...rows].join('\n');
}

/**
 * Convert array of objects to Markdown table
 */
export function toMarkdownTable<T extends Record<string, unknown>>(
  data: T[],
  columns?: string[]
): string {
  if (data.length === 0) return '';

  const cols = columns || Object.keys(data[0]);
  const header = `| ${cols.join(' | ')} |`;
  const separator = `| ${cols.map(() => '---').join(' | ')} |`;
  const rows = data.map(
    (row) => `| ${cols.map((col) => String(row[col] ?? '')).join(' | ')} |`
  );

  return [header, separator, ...rows].join('\n');
}

/**
 * Truncate string to maximum length
 */
export function truncate(str: string, maxLength: number, suffix = '...'): string {
  if (str.length <= maxLength) return str;
  return str.slice(0, maxLength - suffix.length) + suffix;
}

/**
 * Format date to string
 */
export function formatDate(
  date: Date | string,
  format: 'iso' | 'short' | 'long' | 'time' = 'iso'
): string {
  const d = typeof date === 'string' ? new Date(date) : date;

  switch (format) {
    case 'iso':
      return d.toISOString();
    case 'short':
      return d.toLocaleDateString();
    case 'long':
      return d.toLocaleDateString(undefined, {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    case 'time':
      return d.toLocaleTimeString();
    default:
      return d.toISOString();
  }
}

/**
 * Format number with locale options
 */
export function formatNumber(num: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(undefined, options).format(num);
}

/**
 * Format number as currency
 */
export function formatCurrency(
  num: number,
  currency = 'USD',
  locale = 'en-US'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(num);
}

/**
 * Format number as percentage
 */
export function formatPercent(num: number, decimals = 1): string {
  return `${(num * 100).toFixed(decimals)}%`;
}

/**
 * Format bytes to human readable size
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`;
}

/**
 * Format duration in milliseconds to human readable
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
  return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`;
}

/**
 * Pad string to minimum length
 */
export function padStart(str: string, length: number, char = ' '): string {
  return str.padStart(length, char);
}

/**
 * Pad string to minimum length at end
 */
export function padEnd(str: string, length: number, char = ' '): string {
  return str.padEnd(length, char);
}

/**
 * Capitalize first letter
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Convert to title case
 */
export function titleCase(str: string): string {
  return str.replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Convert to camelCase
 */
export function camelCase(str: string): string {
  return str
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, c) => c.toUpperCase())
    .replace(/^./, (c) => c.toLowerCase());
}

/**
 * Convert to snake_case
 */
export function snakeCase(str: string): string {
  return str
    .replace(/([A-Z])/g, '_$1')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .toLowerCase()
    .replace(/^_/, '');
}

/**
 * Convert to kebab-case
 */
export function kebabCase(str: string): string {
  return str
    .replace(/([A-Z])/g, '-$1')
    .replace(/[^a-zA-Z0-9]+/g, '-')
    .toLowerCase()
    .replace(/^-/, '');
}

/**
 * Create a summary of data
 */
export function summarize<T extends Record<string, unknown>>(
  data: T[],
  options?: { maxItems?: number; includeStats?: boolean }
): string {
  const { maxItems = 5, includeStats = true } = options || {};

  const lines: string[] = [];
  lines.push(`Total items: ${data.length}`);

  if (includeStats && data.length > 0) {
    const keys = Object.keys(data[0]);
    lines.push(`Fields: ${keys.join(', ')}`);
  }

  if (data.length > 0) {
    lines.push('');
    lines.push('Sample:');
    const sample = data.slice(0, maxItems);
    for (const item of sample) {
      lines.push(`  ${JSON.stringify(item)}`);
    }
    if (data.length > maxItems) {
      lines.push(`  ... and ${data.length - maxItems} more`);
    }
  }

  return lines.join('\n');
}
