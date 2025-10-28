<script>
  import { createEventDispatcher } from 'svelte'
  
  export let item
  export let index
  
  const dispatch = createEventDispatcher()
  let imageLoaded = false
  let imageError = false
  
  function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  function handleClick() {
    dispatch('click')
  }
  
  function handleImageLoad() {
    imageLoaded = true
  }
  
  function handleImageError() {
    imageError = true
  }
</script>

<div class="media-item" on:click={handleClick} on:keydown role="button" tabindex="0">
  {#if !imageLoaded && !imageError}
    <div class="loading-placeholder">
      <div class="loading-spinner"></div>
    </div>
  {/if}
  
  <img 
    src={item.thumbnail} 
    alt={item.name}
    class="media-thumbnail"
    class:loaded={imageLoaded}
    class:error={imageError}
    loading="lazy"
    on:load={handleImageLoad}
    on:error={handleImageError}
  />
  
  <div class="media-overlay" class:visible={imageLoaded}>
    <div class="media-name">{item.name}</div>
    <div class="media-details">
      <span>{item.size}</span>
      <span>{formatDate(item.date)}</span>
    </div>
  </div>
  
  {#if item.type === 'video'}
    <div class="video-indicator" class:visible={imageLoaded}>
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
    contain: layout style;
  }
  
  .media-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
  }
  
  .loading-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--bg-medium);
    z-index: 1;
  }
  
  .loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid #333;
    border-top: 2px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .media-thumbnail {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    opacity: 0;
    transition: opacity 0.3s ease;
    will-change: opacity;
  }
  
  .media-thumbnail.loaded {
    opacity: 1;
  }
  
  .media-thumbnail.error {
    opacity: 0.3;
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
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .media-overlay.visible {
    opacity: 1;
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
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .video-indicator.visible {
    opacity: 1;
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