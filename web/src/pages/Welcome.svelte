<script lang="ts">
  import Button from '../components/Button.svelte';
  import { userMessage } from '../lib/bridge';

  interface Props {
    /** Create the profile; resolves with an error message, or null when it worked. */
    oncreate: (name: string) => Promise<string | null>;
    /** Why the last profile could not be opened, if it couldn't. */
    problem?: string | null;
  }

  let { oncreate, problem = null }: Props = $props();
  let name = $state('');
  let error = $state('');
  let busy = $state(false);
  let input: HTMLInputElement | undefined = $state();

  $effect(() => {
    input?.focus();
  });

  async function submit(event: SubmitEvent): Promise<void> {
    event.preventDefault();
    if (!name.trim()) {
      error = 'Type a name first.';
      return;
    }
    busy = true;
    try {
      error = (await oncreate(name.trim())) ?? '';
    } catch (caught) {
      error = userMessage(caught) ?? (caught instanceof Error ? caught.message : String(caught));
    } finally {
      busy = false;
    }
  }
</script>

<section class="page" data-testid="page-welcome">
  <h1>Welcome</h1>
  {#if problem}
    <p class="error" role="alert" data-testid="profile-problem">{problem}</p>
  {/if}
  <p class="muted">Your progress is kept in a profile on this Mac. A profile needs only a name.</p>
  <form onsubmit={submit}>
    <label for="profile-name">Your name</label>
    <div class="row">
      <input
        id="profile-name"
        bind:this={input}
        bind:value={name}
        maxlength="80"
        autocomplete="off"
        spellcheck="false"
        data-testid="profile-name"
      />
      <Button variant="primary" type="submit" disabled={busy} data-testid="profile-create">Create profile</Button>
    </div>
    {#if error}<p class="error" role="alert" data-testid="profile-error">{error}</p>{/if}
  </form>
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-2);
    max-width: 32rem;
    padding: var(--sp-6) var(--sp-5);
  }

  form {
    display: grid;
    gap: var(--sp-1);
  }

  label {
    font-weight: 600;
  }

  .row {
    display: flex;
    gap: var(--sp-1);
  }

  input {
    flex: 1;
    min-height: 40px;
    padding: 0 var(--sp-1);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--surface);
    color: var(--text);
    font: inherit;
  }

  .error {
    color: var(--incorrect);
  }
</style>
