<script lang="ts">
  import { ICONS, type IconName } from '../lib/icons';

  let { name, size = 1.25 }: { name: IconName; size?: number } = $props();
</script>

<svg
  class="icon"
  viewBox="0 0 24 24"
  width={`${size}em`}
  height={`${size}em`}
  fill="none"
  stroke="currentColor"
  stroke-width="1.75"
  stroke-linecap="round"
  stroke-linejoin="round"
  aria-hidden="true"
  focusable="false"
>
  {#each ICONS[name] as d (d)}
    <path {d} />
  {/each}
</svg>

<style>
  .icon {
    flex: none;
    display: block;
  }
</style>
