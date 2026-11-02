/** A tiny hash router (#/study?mode=extra). The page is static files, so hashes need no server. */

/** The sidebar's screens. */
export type NavId = 'home' | 'study' | 'library' | 'browse' | 'stats' | 'settings';

/** Every page: the sidebar's, plus pages opened from one of them (they sit under it). */
export type RouteId = NavId | 'course' | 'skills' | 'model';

export const ROUTES: readonly { id: NavId; label: string }[] = [
  { id: 'home', label: 'Home' },
  { id: 'study', label: 'Study' },
  { id: 'library', label: 'Library' },
  { id: 'browse', label: 'Browse' },
  { id: 'stats', label: 'Stats' },
  { id: 'settings', label: 'Settings' },
];

/** Course setup and Skills open from the Library (per course); the student model from Settings. */
const SUBPAGES: Record<Exclude<RouteId, NavId>, NavId> = {
  course: 'library',
  skills: 'library',
  model: 'settings',
};

function isSubpage(id: string): id is keyof typeof SUBPAGES {
  return Object.hasOwn(SUBPAGES, id);
}

/** The sidebar entry a page sits under. */
export function navFor(route: RouteId): NavId {
  return isSubpage(route) ? SUBPAGES[route] : (route as NavId);
}

export function parseRoute(hash: string): RouteId {
  const id = hash.replace(/^#\/?/, '').split(/[/?]/)[0] ?? '';
  if (isSubpage(id)) return id;
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
