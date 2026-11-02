import { getPractice } from './practice-api';
import { TEXT_SIZE_DEFAULT, TEXT_SIZE_MAX, TEXT_SIZE_MIN, type Preferences, type ThemeChoice } from './types';

/**
 * Appearance preferences. The page keeps no browser storage (AGENTS.md rule 4): Python
 * keeps them in the profile's settings (prefs_get / prefs_set).
 */
export const preferences: Preferences = $state({ theme: 'auto', text_size: TEXT_SIZE_DEFAULT });

export function clampTextSize(value: number): number {
  if (!Number.isFinite(value)) return TEXT_SIZE_DEFAULT;
  return Math.min(TEXT_SIZE_MAX, Math.max(TEXT_SIZE_MIN, Math.round(value)));
}

/** Put the preferences on <html>: data-theme (absent = Automatic) and --text-size. */
export function applyPreferences(root: HTMLElement = document.documentElement): void {
  if (preferences.theme === 'auto') root.removeAttribute('data-theme');
  else root.setAttribute('data-theme', preferences.theme === 'night' ? 'night' : 'day');
  root.style.setProperty('--text-size', String(clampTextSize(preferences.text_size)));
}

let loaded = false;

/** Load from the bridge once (again after a profile opens), then keep both in step. */
export async function loadPreferences(force = false): Promise<void> {
  if (loaded && !force) return;
  loaded = true;
  try {
    const { api } = await getPractice();
    const stored = await api.prefs_get();
    preferences.theme = stored.theme;
    preferences.text_size = clampTextSize(stored.text_size);
  } catch {
    // Defaults are fine; the bridge may not be up yet.
  }
  applyPreferences();
}

async function save(): Promise<void> {
  try {
    const { api } = await getPractice();
    await api.prefs_set({ theme: preferences.theme, text_size: preferences.text_size });
  } catch {
    // Not fatal: the choice still applies for this run.
  }
}

export function setTheme(theme: ThemeChoice): void {
  preferences.theme = theme;
  applyPreferences();
  void save();
}

export function setTextSize(size: number): void {
  preferences.text_size = clampTextSize(size);
  applyPreferences();
  void save();
}
