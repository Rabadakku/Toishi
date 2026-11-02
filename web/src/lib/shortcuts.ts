/**
 * The study screen's keys (spec: Study screen, "Keys"):
 *   Enter submit · Shift+Enter submit unsure · H hint · G give up · Space continue ·
 *   E too easy · 1-5 in the picker · D dispute · R report · Esc or P pause · U undo.
 * Extras: ` switches the answer box between math and plain text, F toggles focus mode.
 *
 * Letters, digits and Space never fire while the student is typing in a field. Enter and
 * Shift+Enter always do. Esc and ` do too, because they type nothing and must work from the
 * answer box, which has focus nearly all the time.
 */

export type ShortcutAction =
  | { type: 'submit'; unsure: boolean }
  | { type: 'hint' }
  | { type: 'give_up' }
  | { type: 'continue' }
  | { type: 'too_easy' }
  | { type: 'pick'; n: number }
  | { type: 'dispute' }
  | { type: 'report' }
  | { type: 'pause' }
  | { type: 'undo' }
  | { type: 'toggle_mode' }
  | { type: 'focus_mode' };

export interface KeyLike {
  key: string;
  shiftKey: boolean;
  ctrlKey: boolean;
  metaKey: boolean;
  altKey: boolean;
}

/** Map a key press to an action. `typing`: the focus is in a text field. */
export function actionForKey(event: KeyLike, typing: boolean): ShortcutAction | null {
  if (event.ctrlKey || event.metaKey || event.altKey) return null;
  switch (event.key) {
    case 'Enter':
      return { type: 'submit', unsure: event.shiftKey };
    case 'Escape':
      return { type: 'pause' };
    case '`':
      return { type: 'toggle_mode' };
  }
  if (typing) return null;
  switch (event.key.toLowerCase()) {
    case 'h':
      return { type: 'hint' };
    case 'g':
      return { type: 'give_up' };
    case ' ':
      return { type: 'continue' };
    case 'e':
      return { type: 'too_easy' };
    case 'd':
      return { type: 'dispute' };
    case 'r':
      return { type: 'report' };
    case 'p':
      return { type: 'pause' };
    case 'u':
      return { type: 'undo' };
    case 'f':
      return { type: 'focus_mode' };
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
      return { type: 'pick', n: Number(event.key) };
  }
  return null;
}

/** True when keys are going into a text field (the math field, an input, a textarea). */
export function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  if (target.localName === 'math-field' || target.isContentEditable) return true;
  if (target instanceof HTMLTextAreaElement || target instanceof HTMLSelectElement) return true;
  if (target instanceof HTMLInputElement) {
    return !['button', 'checkbox', 'radio', 'range', 'submit', 'reset', 'image'].includes(target.type);
  }
  return false;
}

/** Buttons and links already own Enter and Space; leave those two keys to them. */
export function ownsActivationKeys(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return target.closest('button, a[href], summary, [role="button"], [role="radio"], [role="checkbox"]') !== null;
}
