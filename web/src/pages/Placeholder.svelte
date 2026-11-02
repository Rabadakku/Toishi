<script lang="ts">
  interface Props {
    title: string;
    /** What this screen will be, in the spec's words. */
    summary: string;
    testid: string;
  }

  let { title, summary, testid }: Props = $props();
</script>

<section class="page" data-testid={testid}>
  <h1>{title}</h1>
  <p class="summary">{summary}</p>
  <p class="soon">Not built yet. This screen is a placeholder in the prototype.</p>
</section>

<style>
  .page {
    display: grid;
    gap: var(--sp-2);
    max-width: 40rem;
    padding: var(--sp-6) var(--sp-5);
  }

  .summary {
    font-size: 1.125rem;
  }

  .soon {
    color: var(--text-muted);
    font-size: var(--fs-small);
  }
</style>
