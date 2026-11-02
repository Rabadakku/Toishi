<script lang="ts">
  import type { IconName } from '../lib/icons';
  import { navFor, navigate, ROUTES, router, type NavId } from '../lib/router.svelte';
  import Icon from './Icon.svelte';

  const ICON_FOR: Record<NavId, IconName> = {
    home: 'home',
    study: 'study',
    library: 'library',
    browse: 'browse',
    stats: 'stats',
    settings: 'settings',
  };
</script>

<nav class="sidebar" aria-label="Main">
  <div class="brand">Toishi</div>
  <ul>
    {#each ROUTES as route (route.id)}
      <li>
        <a
          href={`#/${route.id}`}
          aria-current={navFor(router.route) === route.id ? 'page' : undefined}
          data-testid={`nav-${route.id}`}
          onclick={(event) => {
            event.preventDefault();
            navigate(route.id);
          }}
        >
          <Icon name={ICON_FOR[route.id]} />
          <span>{route.label}</span>
        </a>
      </li>
    {/each}
  </ul>
</nav>

<style>
  .sidebar {
    position: sticky;
    top: 0;
    display: flex;
    flex-direction: column;
    gap: var(--sp-3);
    height: 100vh;
    padding: var(--sp-3) var(--sp-2);
    border-inline-end: 1px solid var(--border);
    background: var(--surface);
  }

  .brand {
    padding-inline: var(--sp-1);
    color: var(--text-muted);
    font-size: var(--fs-small);
    font-weight: 600;
    letter-spacing: 0.02em;
  }

  ul {
    display: grid;
    gap: var(--sp-0);
    margin: 0;
    padding: 0;
    list-style: none;
  }

  a {
    display: flex;
    align-items: center;
    gap: var(--sp-1);
    min-height: 40px;
    padding: 0 var(--sp-1);
    border-radius: var(--radius-sm);
    color: var(--text-muted);
    font-weight: 500;
    text-decoration: none;
    transition:
      background-color var(--dur) ease-out,
      color var(--dur) ease-out;
  }

  a:hover {
    background: var(--surface-sunken);
    color: var(--text);
  }

  a[aria-current='page'] {
    background: var(--selection);
    color: var(--text);
  }
</style>
