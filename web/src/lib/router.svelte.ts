/** A tiny hash router (#/study?mode=extra). The page is static files, so hashes need no server. */

export type RouteId = 'home' | 'study' | 'library' | 'browse' | 'stats' | 'settings';

export const ROUTES: readonly { id: RouteId; label: string }[] = [
  { id: 'home', label: 'Home' },
  { id: 'study', label: 'Study' },
  { id: 'library', label: 'Library' },
  { id: 'browse', label: 'Browse' },
  { id: 'stats', label: 'Stats' },
  { id: 'settings', label: 'Settings' },
];

export function parseRoute(hash: string): RouteId {
  const id = hash.replace(/^#\/?/, '').split(/[/?]/)[0];
  return ROUTES.find((route) => route.id === id)?.id ?? 'home';
}

/** The query part of the hash (#/study?mode=extra -> {mode: 'extra'}). */
export function parseParams(hash: string): Record<string, string> {
  const query = hash.split('?')[1] ?? '';
  return Object.fromEntries(new URLSearchParams(query));
}

export const router = $state({
  route: parseRoute(window.location.hash),
  params: parseParams(window.location.hash),
  /** Bumped on every navigation, so a page can restart for the same route. */
  visit: 0,
});

window.addEventListener('hashchange', () => {
  router.route = parseRoute(window.location.hash);
  router.params = parseParams(window.location.hash);
  router.visit += 1;
});

export function navigate(route: RouteId, params: Record<string, string> = {}): void {
  const query = new URLSearchParams(params).toString();
  window.location.hash = `#/${route}${query ? `?${query}` : ''}`;
}
