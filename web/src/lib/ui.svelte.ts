import type { AppInfo, BridgeApi, SelfTestReport } from './bridge';

/** Shell state shared by the sidebar, the study screen and Settings. */
export const ui = $state({
  /** Focus mode: the study screen fills the window and the sidebar is hidden. */
  focusMode: true,
});

/** What the page learned from the Python bridge (Settings > Diagnostics shows it). */
export const bridge: {
  api: BridgeApi | undefined;
  info: AppInfo | undefined;
  error: string;
  selfTest: SelfTestReport | undefined;
} = $state({ api: undefined, info: undefined, error: '', selfTest: undefined });
