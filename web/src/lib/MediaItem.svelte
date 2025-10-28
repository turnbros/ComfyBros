<script>
  import { createEventDispatcher } from 'svelte'
  
  export let item
  export let index
  
  const dispatch = createEventDispatcher()
  
  function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  function handleClick() {
    dispatch('click')
  }
</script>

<div class="media-item" on:click={handleClick} on:keydown role="button" tabindex="0">
  <img 
    src={item.thumbnail} 
    alt={item.name}
    class="media-thumbnail"
    loading="lazy"
  />
  
  <div class="media-overlay">
    <div class="media-name">{item.name}</div>
    <div class="media-details">
      <span>{item.size}</span>
      <span>{formatDate(item.date)}</span>
    </div>
  </div>
  
  {#if item.type === 'video'}
    <div class="video-indicator">
      ▶ Video
    </div>
  {/if}
</div>

<style>
  .media-item {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    background-color: var(--bg-medium);
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    aspect-ratio: 1;
  }
  
  .media-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  }
  
  .media-thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }
  
  .media-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
    padding: 0.5rem;
    color: white;
    font-size: 0.8rem;
  }
  
  .media-name {
    font-weight: 500;
    margin-bottom: 0.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  .media-details {
    font-size: 0.7rem;
    color: var(--text-secondary);
    display: flex;
    justify-content: space-between;
  }
  
  .video-indicator {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-size: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.2rem;
  }
  
  /* Touch-friendly interactions */
  @media (hover: none) and (pointer: coarse) {
    .media-item {
      transform: none;
    }
    
    .media-item:active {
      transform: scale(0.98);
    }
  }
</style>