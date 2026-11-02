<script lang="ts">
  import katex from 'katex';

  interface Props {
    /** Bare LaTeX, no delimiters. */
    latex: string;
    display?: boolean;
  }

  let { latex, display = false }: Props = $props();
  let host: HTMLElement | undefined = $state();

  $effect(() => {
    if (!host) return;
    try {
      katex.render(latex, host, {
        displayMode: display,
        throwOnError: false,
        trust: false,
        strict: 'ignore',
        maxExpand: 1000,
      });
    } catch {
      host.textContent = latex;
    }
  });
</script>

<span class="tex" bind:this={host}></span>
