import type { MathfieldElement } from 'mathlive';

/**
 * MathLive's inline shortcuts, adjusted for answer entry. Its own `log` shortcut inserts
 * `\log_{#?}` (an empty base box), so typing log(x) gave an answer the checker can't read;
 * here `log` is the plain logarithm, like `ln`.
 */
export const SHORTCUT_OVERRIDES: Record<string, string> = {
  log: '\\log',
};

export function applyInlineShortcuts(field: MathfieldElement): void {
  field.inlineShortcuts = { ...field.inlineShortcuts, ...SHORTCUT_OVERRIDES };
}
