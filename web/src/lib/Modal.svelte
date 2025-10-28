<script>
  import { onMount, onDestroy } from 'svelte'
  import { modalOpen, currentIndex, currentMedia, filteredMedia, mediaStore } from './stores.js'
  import { swipe } from './gestures.js'
  import { fade } from 'svelte/transition'
  
  let scrollY = 0
  let isTransitioning = false
  let showInfo = true
  let showMenu = false
  let isZoomed = false
  let mediaElement = null
  let isDoubleTabZoomed = false
  let lastTap = 0
  
  function closeModal() {
    modalOpen.set(false)
  }
  
  function navigate(direction) {
    console.log('Navigate called, direction:', direction, 'isTransitioning:', isTransitioning, 'isZoomed:', isZoomed)
    
    if (isTransitioning || isZoomed) {
      console.log('Navigation blocked')
      return // Prevent navigation when zoomed or transitioning
    }
    
    isTransitioning = true
    
    // Reset zoom states when switching media
    isZoomed = false
    isDoubleTabZoomed = false
    isPinching = false
    activeTouches = 0
    
    const maxIndex = $filteredMedia.length - 1
    let newIndex = $currentIndex + direction
    
    if (newIndex < 0) {
      newIndex = maxIndex
    } else if (newIndex > maxIndex) {
      newIndex = 0
    }
    
    console.log('Navigating from', $currentIndex, 'to', newIndex)
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
  
  function toggleInfo() {
    showInfo = !showInfo
  }
  
  function toggleMenu() {
    showMenu = !showMenu
  }
  
  let activeTouches = 0
  let isPinching = false
  
  function handleTouchStart(event) {
    activeTouches = event.touches.length
    
    if (activeTouches === 2) {
      isPinching = true
      isZoomed = true
      console.log('Pinch started - navigation disabled')
    }
  }
  
  function handleTouchMove(event) {
    if (event.touches.length === 2) {
      isPinching = true
      isZoomed = true
    }
  }
  
  function handleTouchEnd(event) {
    activeTouches = event.touches.length
    
    if (activeTouches === 0) {
      // All touches ended - check if we should reset zoom state
      setTimeout(() => {
        if (activeTouches === 0 && !isPinching && !isDoubleTabZoomed) {
          isZoomed = false
          console.log('Navigation re-enabled')
        }
        isPinching = false
      }, 300) // Delay to allow for gesture completion
    }
  }
  
  function handleDoubleTap(event) {
    const currentTime = new Date().getTime()
    const tapLength = currentTime - lastTap
    
    // Only process if it's actually a double tap (between 50ms and 500ms)
    if (tapLength < 500 && tapLength > 50) {
      // This is a double tap
      event.preventDefault()
      event.stopPropagation()
      toggleDoubleTabZoom()
    }
    
    lastTap = currentTime
  }
  
  function toggleDoubleTabZoom() {
    if (!mediaElement) return
    
    isDoubleTabZoomed = !isDoubleTabZoomed
    isZoomed = isDoubleTabZoomed
    
    if (isDoubleTabZoomed) {
      // Zoom in - scale to 2x
      mediaElement.style.transform = 'scale(2)'
      mediaElement.style.cursor = 'grab'
      console.log('Double-tap zoom: IN')
    } else {
      // Zoom out - reset to normal
      mediaElement.style.transform = 'scale(1)'
      mediaElement.style.cursor = 'default'
      console.log('Double-tap zoom: OUT')
    }
  }
  
  function handleMediaLoad(event) {
    mediaElement = event.target
    // Reset zoom state for new media
    isZoomed = false
    isPinching = false
    activeTouches = 0
    isDoubleTabZoomed = false
    
    // Reset any existing transforms
    if (mediaElement) {
      mediaElement.style.transform = 'scale(1)'
      mediaElement.style.cursor = 'default'
      
      // Force autoplay for videos
      if (mediaElement.tagName === 'VIDEO') {
        setTimeout(() => {
          mediaElement.play().catch(e => {
            console.log('Autoplay prevented:', e)
          })
        }, 100)
      }
    }
    
    // Add touch listeners to detect pinch gestures and double taps
    if (mediaElement) {
      mediaElement.addEventListener('touchstart', handleTouchStart, { passive: true })
      mediaElement.addEventListener('touchmove', handleTouchMove, { passive: true })
      mediaElement.addEventListener('touchend', handleTouchEnd, { passive: true })
      mediaElement.addEventListener('click', handleDoubleTap)
    }
  }
  
  async function deleteCurrentMedia() {
    if (!confirm(`Are you sure you want to delete ${$currentMedia.name}?`)) {
      return
    }
    
    try {
      const response = await fetch(`/api/delete/${$currentMedia.path}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        // Remove from current media array
        const currentArray = $filteredMedia
        const currentIdx = $currentIndex
        const newArray = currentArray.filter((_, i) => i !== currentIdx)
        
        // Update stores
        mediaStore.update(allMedia => allMedia.filter(item => item.path !== $currentMedia.path))
        
        // Navigate to next image or close modal if no more images
        if (newArray.length === 0) {
          closeModal()
        } else {
          // Adjust index if we deleted the last item
          const newIndex = currentIdx >= newArray.length ? newArray.length - 1 : currentIdx
          currentIndex.set(newIndex)
        }
        
        showMenu = false
      } else {
        alert('Failed to delete file')
      }
    } catch (error) {
      console.error('Error deleting file:', error)
      alert('Error deleting file')
    }
  }
  
  async function generateNewImage() {
    try {
      showMenu = false
      
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          trigger: 'gallery_request',
          timestamp: Date.now()
        })
      })
      
      if (response.ok) {
        const result = await response.json()
        alert('Image generation started! Check back in a few moments for new images.')
      } else {
        alert('Failed to start image generation')
      }
    } catch (error) {
      console.error('Error starting generation:', error)
      alert('Error starting generation')
    }
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
      case 'i':
      case 'I':
        toggleInfo()
        break
      case 'm':
      case 'M':
        toggleMenu()
        break
      case 'z':
      case 'Z':
        toggleDoubleTabZoom()
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
    
    // Force Safari fullscreen behavior
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    if (isIOS) {
      // Add minimal-ui to hide Safari UI
      const metaViewport = document.querySelector('meta[name=viewport]')
      if (metaViewport) {
        metaViewport.setAttribute('content', 'width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no, minimal-ui')
      }
      
      // Multiple attempts to hide Safari UI
      const hideSafariUI = () => {
        window.scrollTo(0, 1)
        setTimeout(() => window.scrollTo(0, 0), 0)
      }
      
      // Hide immediately and on orientation change
      hideSafariUI()
      setTimeout(hideSafariUI, 100)
      setTimeout(hideSafariUI, 500)
      setTimeout(hideSafariUI, 1000)
      
      // Force minimal UI on touch
      document.addEventListener('touchstart', hideSafariUI, { once: true })
      
      // Try to enter fullscreen mode
      setTimeout(() => {
        if (document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen().catch(() => {})
        } else if (document.documentElement.webkitRequestFullscreen) {
          document.documentElement.webkitRequestFullscreen().catch(() => {})
        }
      }, 500)
    }
    
    // Set CSS custom properties for proper viewport height
    const setViewportHeight = () => {
      const vh = window.innerHeight * 0.01
      document.documentElement.style.setProperty('--vh', `${vh}px`)
    }
    setViewportHeight()
    window.addEventListener('resize', setViewportHeight)
    window.addEventListener('orientationchange', setViewportHeight)
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
      onSwipeLeft: () => {
        console.log('Swipe left detected, isZoomed:', isZoomed)
        if (!isZoomed) nextImage()
      },
      onSwipeRight: () => {
        console.log('Swipe right detected, isZoomed:', isZoomed)
        if (!isZoomed) previousImage()
      },
      onSwipeUp: () => {
        console.log('Swipe up detected, isZoomed:', isZoomed)
        if (!isZoomed) nextImage()
      },
      onSwipeDown: () => {
        console.log('Swipe down detected, isZoomed:', isZoomed)
        if (!isZoomed) previousImage()
      }
    }}
    on:click={closeModal}
    on:keydown={handleKeydown}
    role="dialog"
    aria-modal="true"
    tabindex="-1"
  >
    <div class="modal-content" on:click|stopPropagation on:keydown role="button" tabindex="0">
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
                class:zoomed={isDoubleTabZoomed}
                on:load={handleMediaLoad}
              />
            {:else}
              <video 
                src={$currentMedia.url}
                class="modal-video"
                class:zoomed={isDoubleTabZoomed}
                controls
                autoplay
                muted
                loop
                playsinline
                preload="metadata"
                on:loadedmetadata={handleMediaLoad}>
                <track kind="captions" src="" label="No captions available" />
              </video>
            {/if}
          </div>
        {/key}
        
      </div>
      
      <div class="modal-info" class:hidden={!showInfo}>
        <h3>{$currentMedia.name}</h3>
        <div class="modal-details">
          <span>{$currentMedia.size}</span>
          <span>{formatDate($currentMedia.date)}</span>
        </div>
      </div>
      
      <button 
        class="info-toggle" 
        on:click={toggleInfo} 
        aria-label={showInfo ? "Hide info" : "Show info"}
        title={showInfo ? "Hide info (I)" : "Show info (I)"}
      >
        ℹ️
      </button>
      
      <button 
        class="menu-toggle" 
        on:click={toggleMenu} 
        aria-label={showMenu ? "Hide menu" : "Show menu"}
        title={showMenu ? "Hide menu (M)" : "Show menu (M)"}
      >
        ☰
      </button>
      
      {#if showMenu}
        <div class="hamburger-menu" in:fade={{ duration: 200 }} out:fade={{ duration: 200 }}>
          <button class="menu-item generate-btn" on:click={generateNewImage}>
            ✨ Generate New
          </button>
          <button class="menu-item delete-btn" on:click={deleteCurrentMedia}>
            🗑️ Delete
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    width: 100dvw;
    height: 100vh;
    height: 100dvh;
    height: calc(var(--vh, 1vh) * 100);
    background-color: rgba(0, 0, 0, 0.95);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    padding: 1rem;
    -webkit-overflow-scrolling: touch;
    
    /* Force full viewport on iOS Safari */
    -webkit-transform: translate3d(0, 0, 0);
    transform: translate3d(0, 0, 0);
  }
  
  /* iOS Safari specific fixes */
  @supports (-webkit-touch-callout: none) {
    .modal {
      height: -webkit-fill-available;
      min-height: 100vh;
      min-height: 100dvh;
    }
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
    width: 100vw;
    height: 100vh;
    height: calc(var(--vh, 1vh) * 100);
    display: flex;
    align-items: center;
    justify-content: center;
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
    height: 100%;
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
    transform-origin: center;
    cursor: pointer;
  }
  
  .modal-image.zoomed, .modal-video.zoomed {
    cursor: grab;
  }
  
  .modal-image.zoomed:active, .modal-video.zoomed:active {
    cursor: grabbing;
  }
  
  .modal-image:hover:not(.zoomed), .modal-video:hover:not(.zoomed) {
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
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    text-align: center;
    color: white;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    padding: 1rem;
    z-index: 1002;
    transition: transform 0.3s ease, opacity 0.3s ease;
  }
  
  .modal-info.hidden {
    transform: translateY(100%);
    opacity: 0;
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
  
  .info-toggle {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border: none;
    color: white;
    font-size: 1.2rem;
    padding: 0.5rem;
    cursor: pointer;
    border-radius: 50%;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1003;
    transition: background-color 0.2s, transform 0.2s;
  }
  
  .info-toggle:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
  }
  
  .menu-toggle {
    position: absolute;
    bottom: 1rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border: none;
    color: white;
    font-size: 1.2rem;
    padding: 0.5rem;
    cursor: pointer;
    border-radius: 50%;
    width: 2.5rem;
    height: 2.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1003;
    transition: background-color 0.2s, transform 0.2s;
  }
  
  .menu-toggle:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.1);
  }
  
  .hamburger-menu {
    position: absolute;
    bottom: 4rem;
    right: 1rem;
    background: rgba(0, 0, 0, 0.9);
    backdrop-filter: blur(15px);
    border-radius: 8px;
    padding: 0.5rem;
    z-index: 1004;
    min-width: 120px;
  }
  
  .menu-item {
    display: block;
    width: 100%;
    background: none;
    border: none;
    color: white;
    padding: 0.75rem 1rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
    font-size: 0.9rem;
    text-align: left;
  }
  
  .menu-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .delete-btn:hover {
    background: rgba(255, 59, 48, 0.2);
    color: #ff3b30;
  }
  
  .generate-btn:hover {
    background: rgba(52, 199, 89, 0.2);
    color: #34c759;
  }
  
  /* Mobile optimizations */
  @media (max-width: 768px) {
    .modal {
      padding: 0;
    }
    
    .modal-content {
      width: 100vw;
      height: 100vh;
    }
    
    .modal-media-container {
      width: 100vw;
      height: 100vh;
      height: calc(var(--vh, 1vh) * 100);
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