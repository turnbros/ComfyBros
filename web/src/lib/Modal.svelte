<script>
  import { onMount, onDestroy } from 'svelte'
  import { modalOpen, currentIndex, currentMedia, filteredMedia } from './stores.js'
  import { swipe } from './gestures.js'
  import { fade } from 'svelte/transition'
  
  let scrollY = 0
  let isTransitioning = false
  
  function closeModal() {
    modalOpen.set(false)
  }
  
  function navigate(direction) {
    if (isTransitioning) return // Prevent rapid navigation
    
    isTransitioning = true
    const maxIndex = $filteredMedia.length - 1
    let newIndex = $currentIndex + direction
    
    if (newIndex < 0) {
      newIndex = maxIndex
    } else if (newIndex > maxIndex) {
      newIndex = 0
    }
    
    currentIndex.set(newIndex)
    
    // Reset transition flag after animation
    setTimeout(() => {
      isTransitioning = false
    }, 300)
  }
  
  function previousImage() {
    navigate(-1)
  }
  
  function nextImage() {
    navigate(1)
  }
  
  function handleKeydown(event) {
    switch (event.key) {
      case 'Escape':
        closeModal()
        break
      case 'ArrowLeft':
        previousImage()
        break
      case 'ArrowRight':
        nextImage()
        break
    }
  }
  
  function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }
  
  // Prevent body scrolling when modal is open
  onMount(() => {
    scrollY = window.scrollY
    document.body.style.position = 'fixed'
    document.body.style.width = '100%'
    document.body.style.top = `-${scrollY}px`
    document.body.style.overflow = 'hidden'
  })
  
  onDestroy(() => {
    document.body.style.position = ''
    document.body.style.width = ''
    document.body.style.top = ''
    document.body.style.overflow = ''
    window.scrollTo(0, scrollY)
  })
</script>

<svelte:window on:keydown={handleKeydown} />

{#if $currentMedia}
  <div 
    class="modal" 
    style="--bg-image: url({$currentMedia.url})"
    use:swipe={{
      onSwipeLeft: nextImage,
      onSwipeRight: previousImage,
      onSwipeUp: nextImage,
      onSwipeDown: previousImage
    }}
    on:click={closeModal}
    role="dialog"
    aria-modal="true"
  >
    <div class="modal-content" on:click|stopPropagation>
      <button class="modal-close" on:click={closeModal} aria-label="Close">
        ×
      </button>
      
      <div class="modal-media-container">
        {#key $currentIndex}
          <div class="media-wrapper" in:fade={{ duration: 300, delay: 150 }} out:fade={{ duration: 150 }}>
            {#if $currentMedia.type === 'image'}
              <img 
                src={$currentMedia.url} 
                alt={$currentMedia.name}
                class="modal-image"
              />
            {:else}
              <video 
                src={$currentMedia.url}
                class="modal-video"
                controls
                preload="metadata"
              />
            {/if}
          </div>
        {/key}
        
        {#if $filteredMedia.length > 1}
          <div class="modal-nav">
            <button class="nav-btn nav-prev" on:click={previousImage} aria-label="Previous" disabled={isTransitioning}>
              ‹
            </button>
            <button class="nav-btn nav-next" on:click={nextImage} aria-label="Next" disabled={isTransitioning}>
              ›
            </button>
          </div>
        {/if}
      </div>
      
      <div class="modal-info">
        <h3>{$currentMedia.name}</h3>
        <div class="modal-details">
          <span>{$currentMedia.size}</span>
          <span>{formatDate($currentMedia.date)}</span>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 1rem;
  }
  
  .modal::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: var(--bg-image);
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    filter: blur(20px) brightness(0.3);
    transform: scale(1.1);
    z-index: -1;
  }
  
  .modal-content {
    position: relative;
    max-width: 90vw;
    max-height: 90vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .modal-close {
    position: absolute;
    top: -3rem;
    right: 0;
    background: none;
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    z-index: 1001;
    padding: 0.5rem;
    line-height: 1;
  }
  
  .modal-media-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 80vh;
    max-width: 90vw;
    max-height: 80vh;
    overflow: hidden;
  }
  
  .media-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    position: absolute;
    top: 0;
    left: 0;
  }
  
  .modal-image, .modal-video {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    border-radius: 8px;
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .modal-image:hover, .modal-video:hover {
    transform: scale(1.02);
  }
  
  .modal-nav {
    position: absolute;
    top: 50%;
    width: 100%;
    display: flex;
    justify-content: space-between;
    z-index: 1001;
    pointer-events: none;
  }
  
  .nav-btn {
    background-color: rgba(0, 0, 0, 0.7);
    border: none;
    color: white;
    font-size: 2rem;
    padding: 1rem;
    cursor: pointer;
    border-radius: 50%;
    width: 3rem;
    height: 3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: all;
    transition: background-color 0.2s;
    line-height: 1;
  }
  
  .nav-btn:hover:not(:disabled) {
    background-color: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
  }
  
  .nav-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .nav-btn {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .modal-info {
    margin-top: 1rem;
    text-align: center;
    color: white;
  }
  
  .modal-info h3 {
    margin-bottom: 0.5rem;
    color: var(--primary-color);
  }
  
  .modal-details {
    display: flex;
    gap: 2rem;
    justify-content: center;
    font-size: 0.9rem;
    color: var(--text-secondary);
  }
  
  /* Mobile optimizations */
  @media (max-width: 768px) {
    .modal {
      padding: 0;
    }
    
    .modal-content {
      width: 100vw;
      height: 100vh;
      max-width: 100vw;
      max-height: 100vh;
      justify-content: center;
    }
    
    .modal-media-container {
      width: 100vw;
      height: 85vh;
      max-width: 100vw;
      max-height: 85vh;
    }
    
    .modal-info {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(10px);
      padding: 1rem;
      margin: 0;
    }
    
    .modal-close {
      position: fixed;
      top: 1rem;
      right: 1rem;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(10px);
      border-radius: 50%;
      width: 3rem;
      height: 3rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .nav-btn {
      background-color: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(10px);
      font-size: 1.5rem;
      width: 2.5rem;
      height: 2.5rem;
      padding: 0.5rem;
    }
    
    .modal-details {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .modal-image:hover, .modal-video:hover {
      transform: none;
    }
  }
  
  @media (max-width: 480px) {
    .controls {
      gap: 0.5rem;
    }
    
    .btn, .select {
      padding: 0.8rem;
    }
  }
  
  /* Touch-friendly interactions */
  @media (hover: none) and (pointer: coarse) {
    .modal-image:hover, .modal-video:hover {
      transform: none;
    }
    
    .nav-btn:hover {
      transform: none;
      background-color: rgba(0, 0, 0, 0.7);
    }
    
    .nav-btn:active:not(:disabled) {
      transform: scale(0.95);
      background-color: rgba(0, 0, 0, 0.9);
    }
  }
</style>