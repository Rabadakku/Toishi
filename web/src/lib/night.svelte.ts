import { preferences } from './settings.svelte';

/**
 * True while the page is in its dark theme: Night chosen, or Automatic with a dark system.
 * Imported Anki cards get the `anki-night` class then, which their note type's night-mode
 * CSS (`.nightMode`) was mapped onto (ADR-0015).
 */
const dark = typeof matchMedia === 'function' ? matchMedia('(prefers-color-scheme: dark)') : null;
let systemDark = $state(dark?.matches ?? false);
dark?.addEventListener('change', (event) => {
  systemDark = event.matches;
});

export function isNight(): boolean {
  return preferences.theme === 'night' || (preferences.theme === 'auto' && systemDark);
}
