<script lang="ts">
  import { onMount } from 'svelte';
  import Sidebar from './components/Sidebar.svelte';
  import { waitForBridge } from './lib/bridge';
  import { navigate, router } from './lib/router.svelte';
  import { runSelfTest } from './lib/selftest';
  import { loadPreferences } from './lib/settings.svelte';
  import { bridge, ui } from './lib/ui.svelte';
  import { getPractice } from './lib/practice-api';
  import Home from './pages/Home.svelte';
  import Library from './pages/Library.svelte';
  import Placeholder from './pages/Placeholder.svelte';
  import Restore from './pages/Restore.svelte';
  import Settings from './pages/Settings.svelte';
  import Study from './pages/Study.svelte';
  import Welcome from './pages/Welcome.svelte';
  import type { Profile, ProfileState } from './lib/types';

  // First run: no profile yet, so the page asks for a name before anything else.
  let profile = $state<ProfileState | null>(null);
  let profileReady = $state(false);
  const needsProfile = $derived(profile !== null && profile.profile === null);
  // A profile that exists but could not be opened: restore it, never make a new one (BAK-4).
  let recovery = $state<Profile | null>(null);

  // Focus mode puts the study screen full screen: no sidebar.
  const focus = $derived(router.route === 'study' && ui.focusMode && !needsProfile);

  onMount(() => {
    void loadPreferences();
    void connect();
    void loadProfile();
  });

  async function loadProfile(): Promise<void> {
    try {
      const { api } = await getPractice();
      const state = await api.profile_get();
      if (state.profile === null) {
        // Even if this fails, the bridge refuses a new profile while one needs restoring.
        recovery = await api.restore_list().then(
          (list) => list.profile,
          () => null,
        );
      }
      profile = state;
    } catch {
      profile = null; // no bridge yet: the pages say so themselves
    } finally {
      profileReady = true;
    }
  }

  async function createProfile(name: string): Promise<string | null> {
    const { api } = await getPractice();
    const created = await api.profile_create({ name });
    if (created.profile === null) return created.error ?? 'The profile could not be created.';
    profile = created;
    await loadPreferences(true);
    navigate('home');
    return null;
  }

  async function restored(state: ProfileState): Promise<void> {
    recovery = null;
    profile = state;
    await loadPreferences(true);
    navigate('home');
  }

  async function connect(): Promise<void> {
    try {
      const api = await waitForBridge();
      bridge.api = api;
      bridge.info = await api.app_info();
      const requested = new URLSearchParams(window.location.search).has('selftest');
      if (bridge.info.self_test || requested) {
        bridge.selfTest = await runSelfTest(api);
        if (bridge.info.self_test) await api.report_self_test(bridge.selfTest);
      }
    } catch (error) {
      bridge.error = error instanceof Error ? error.message : String(error);
    }
  }
</script>

<div class="shell" class:focus>
  {#if !focus}
    <Sidebar />
  {/if}
  <main id="main" tabindex="-1">
    {#if !profileReady && router.route !== 'settings'}
      <p class="loading muted" data-testid="app-loading">Loading…</p>
    {:else if recovery}
      <Restore profile={recovery} problem={profile?.error ?? null} onrestored={restored} />
    {:else if needsProfile && router.route !== 'settings'}
      <Welcome oncreate={createProfile} problem={profile?.error ?? null} />
    {:else if router.route === 'home'}
      <Home />
    {:else if router.route === 'study'}
      <Study />
    {:else if router.route === 'library'}
      <Library />
    {:else if router.route === 'browse'}
      <Placeholder
        testid="page-browse"
        title="Browse"
        summary="Search every card, read it, and edit your own."
      />
    {:else if router.route === 'stats'}
      <Placeholder
        testid="page-stats"
        title="Stats"
        summary="Recall, speed and accuracy by course and skill, and how often your error taps were confirmed."
      />
    {:else}
      <Settings />
    {/if}
  </main>
</div>

<style>
  .shell {
    display: grid;
    grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
    min-height: 100vh;
  }

  .shell.focus {
    grid-template-columns: minmax(0, 1fr);
  }

  main {
    min-width: 0;
    outline: none;
  }

  .loading {
    padding: var(--sp-6) var(--sp-5);
  }
</style>
