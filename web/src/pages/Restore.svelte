<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';
  import { getPractice } from '../lib/practice-api';
  import type { BackupEntry, Profile, ProfileState } from '../lib/types';

  // BAK-4: a profile that failed its integrity check (or could not be opened) is restored
  // from a verified backup here. A new profile is never made over it.
  interface Props {
    profile: Profile;
    problem: string | null;
    /** Called with the new profile state after a restore or a successful re-check. */
    onrestored: (state: ProfileState) => void;
  }

  let { profile, problem, onrestored }: Props = $props();
  let backups = $state<BackupEntry[] | null>(null);
  let chosen = $state<BackupEntry | null>(null);
  let error = $state('');
  let busy = $state(false);

  onMount(() => void load());

  function describe(error: unknown): string {
    return userMessage(error) ?? (error instanceof Error ? error.message : String(error));
  }

  async function load(): Promise<void> {
    try {
      const { api } = await getPractice();
      backups = (await api.restore_list()).backups;
    } catch (caught) {
      error = describe(caught);
      backups = [];
    }
  }

  function when(ms: number | null): string {
    return ms === null ? 'never' : new Date(ms).toLocaleString();
  }

  async function act(run: () => Promise<ProfileState>): Promise<void> {
    busy = true;
    error = '';
    try {
      const state = await run();
      if (state.profile !== null) onrestored(state);
      else error = state.error ?? 'The profile still could not be opened.';
    } catch (caught) {
      error = describe(caught);
    } finally {
      busy = false;
      chosen = null;
    }
  }

  async function restore(entry: BackupEntry): Promise<void> {
    const { api } = await getPractice();
    await act(() => api.restore_backup({ id: entry.id }));
  }

  async function recheck(): Promise<void> {
    const { api } = await getPractice();
    await act(() => api.restore_recheck());
  }
</script>

<section class="page" data-testid="page-restore">
  <h1>Restore {profile.name}'s progress</h1>
  {#if problem}<p class="error" role="alert" data-testid="restore-problem">{problem}</p>{/if}
  <p class="muted">
    Choose a backup to restore. The damaged file is kept beside the backups, and nothing is
    deleted.
  </p>
  {#if backups === null}
    <p class="muted">Checking backups…</p>
  {:else if backups.length === 0}
    <p data-testid="restore-none">No verified backup was found for this profile.</p>
  {:else}
    <ol class="list" data-testid="restore-list">
      {#each backups as entry, index (entry.id)}
        <li data-testid="restore-backup">
          <span>
            <strong>{when(entry.created_at)}</strong>
            {#if index === 0}(latest){/if} · {entry.attempts} answers, last on {when(entry.last_attempt_at)}
          </span>
          {#if chosen?.id === entry.id}
            <Button variant="primary" disabled={busy} onclick={() => restore(entry)} data-testid="restore-confirm">
              Restore this backup
            </Button>
            <Button variant="quiet" disabled={busy} onclick={() => (chosen = null)}>Cancel</Button>
          {:else}
            <Button
              variant={index === 0 ? 'primary' : 'secondary'}
              disabled={busy}
              onclick={() => (chosen = entry)}
              data-testid="restore-choose"
            >
              Restore…
            </Button>
          {/if}
        </li>
      {/each}
    </ol>
  {/if}
  <p>
    <Button variant="quiet" disabled={busy} onclick={recheck} data-testid="restore-recheck">Check again</Button>
  </p>
  {#if error}<p class="error" role="alert" data-testid="restore-error">{error}</p>{/if}
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-2);
    max-width: 40rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .list {
    display: grid;
    gap: var(--sp-1);
    padding-left: var(--sp-3);
  }

  .list li {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--sp-1);
  }

  .error {
    color: var(--incorrect);
  }
</style>
