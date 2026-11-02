import { waitForBridge, type BridgeApi } from './bridge';
import { createMockApi, isMockApi } from './mock-study';

export interface PracticeBinding {
  api: BridgeApi;
  /** True when the in-page sample problems are in use (no Python bridge: a plain browser). */
  mock: boolean;
}

function hasStudy(api: BridgeApi | undefined): api is BridgeApi {
  return typeof api?.study_start === 'function' && typeof api.profile_get === 'function';
}

/** How long to wait for pywebview: it injects its api only after the page has loaded. */
const BRIDGE_WAIT_MS = 5_000;

/**
 * The Python bridge (pywebview in the app, or the `?bridge=mock` stand-in). In a plain
 * browser with neither, the in-page mock with sample problems, so the page still works.
 * In the app the bridge always arrives: pywebview adds it once the page has loaded.
 */
async function bindPracticeApi(): Promise<PracticeBinding> {
  const api = await waitForBridge(BRIDGE_WAIT_MS).catch(() => undefined);
  if (hasStudy(api)) return { api, mock: isMockApi(api) };
  return { api: createMockApi(), mock: true };
}

let shared: Promise<PracticeBinding> | undefined;

/** One binding for the whole page, so the mock keeps one session's state. */
export function getPractice(): Promise<PracticeBinding> {
  shared ??= bindPracticeApi();
  return shared;
}
