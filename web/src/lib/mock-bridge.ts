import { createMockApi } from './mock-study';

/**
 * In-page stand-in for the Python bridge so the page works in a plain browser
 * (`npm run dev`, Playwright). Enabled only by `?bridge=mock` in the URL; the
 * real app never passes it. It implements the whole BridgeApi with sample problems.
 */
export function installMockBridge(): void {
  window.pywebview = { api: createMockApi() };
  window.dispatchEvent(new CustomEvent('pywebviewready'));
}

export function mockBridgeRequested(search: string = window.location.search): boolean {
  return new URLSearchParams(search).get('bridge') === 'mock';
}
