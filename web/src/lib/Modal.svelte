<script>
  import { onMount, onDestroy } from 'svelte'
  import { modalOpen, currentIndex, currentMedia, filteredMedia, mediaStore } from './stores.js'
  import { fade } from 'svelte/transition'
  
  let swiperInstance
  let swiperContainer
  let scrollY = 0
  let showInfo = true
  let showMenu = false
  let currentSlideIndex = $currentIndex

  function closeModal() {
    modalOpen.set(false)
  }

  function onSlideChange() {
    if (swiperInstance) {
      const realIndex = swiperInstance.realIndex !== undefined ? swiperInstance.realIndex : swiperInstance.activeIndex
      currentSlideIndex = realIndex
      currentIndex.set(realIndex)
    }
  }

  function toggleInfo() {
    showInfo = !showInfo
  }

  function toggleMenu() {
    showMenu = !showMenu
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
          if (swiperInstance) {
            swiperInstance.slideTo(newIndex)
          }
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
        if (swiperInstance) swiperInstance.slidePrev()
        break
      case 'ArrowRight':
        if (swiperInstance) swiperInstance.slideNext()
        break
      case 'i':
      case 'I':
        toggleInfo()
        break
      case 'm':
      case 'M':
        toggleMenu()
        break
    }
  }

  function formatDate(date) {
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  function handleVideoLoad(event) {
    const video = event.target
    // Force autoplay for videos
    setTimeout(() => {
      video.play().catch(e => {
        console.log('Autoplay prevented:', e)
      })
    }, 100)
  }

  // Prevent body scrolling when modal is open
  onMount(async () => {
    scrollY = window.scrollY
    document.body.style.position = 'fixed'
    document.body.style.width = '100%'
    document.body.style.top = `-${scrollY}px`
    document.body.style.overflow = 'hidden'
    
    // Import Swiper dynamically to avoid SSR issues
    const Swiper = (await import('swiper/bundle')).default
    await import('swiper/css/bundle')
    
    // Initialize Swiper
    if (swiperContainer) {
      swiperInstance = new Swiper(swiperContainer, {
        initialSlide: $currentIndex,
        spaceBetween: 0,
        slidesPerView: 1,
        loop: $filteredMedia.length > 1,
        navigation: {
          prevEl: '.swiper-button-prev',
          nextEl: '.swiper-button-next',
        },
        zoom: {
          maxRatio: 3,
          minRatio: 1,
          toggle: true,
        },
        on: {
          slideChange: onSlideChange,
        }
      })
    }
    
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
    if (swiperInstance) {
      swiperInstance.destroy(true, true)
    }
    document.body.style.position = ''
    document.body.style.width = ''
    document.body.style.top = ''
    document.body.style.overflow = ''
    window.scrollTo(0, scrollY)
  })

  // Update swiper when currentIndex changes externally
  $: if (swiperInstance && $currentIndex !== currentSlideIndex) {
    swiperInstance.slideTo($currentIndex)
    currentSlideIndex = $currentIndex
  }
</script>

<svelte:window on:keydown={handleKeydown} />

{#if $filteredMedia.length > 0}
  <div 
    class="modal" 
    style="--bg-image: url({$currentMedia?.url})"
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
      
      <div class="swiper" bind:this={swiperContainer}>
        <div class="swiper-wrapper">
          {#each $filteredMedia as item, index (item.path)}
            <div class="swiper-slide">
              <div class="swiper-zoom-container">
                {#if item.type === 'image'}
                  <img 
                    src={item.url} 
                    alt={item.name}
                    class="modal-image"
                  />
                {:else}
                  <video 
                    src={item.url}
                    class="modal-video"
                    controls
                    autoplay
                    muted
                    loop
                    playsinline
                    preload="metadata"
                    on:loadedmetadata={handleVideoLoad}>
                    <track kind="captions" src="" label="No captions available" />
                  </video>
                {/if}
              </div>
            </div>
          {/each}
        </div>
        
        <!-- Navigation buttons -->
        <div class="swiper-button-prev"></div>
        <div class="swiper-button-next"></div>
      </div>
      
      <div class="modal-info" class:hidden={!showInfo}>
        <h3>{$currentMedia?.name}</h3>
        <div class="modal-details">
          <span>{$currentMedia?.size}</span>
          <span>{$currentMedia ? formatDate($currentMedia.date) : ''}</span>
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
  :global(.swiper) {
    width: 100%;
    height: 100%;
  }

  :global(.swiper-slide) {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    background: transparent;
  }

  :global(.swiper-zoom-container) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
  }

  :global(.swiper-button-next),
  :global(.swiper-button-prev) {
    color: white !important;
    background: rgba(0, 0, 0, 0.5) !important;
    border-radius: 50% !important;
    width: 44px !important;
    height: 44px !important;
    margin-top: -22px !important;
  }

  :global(.swiper-button-next:after),
  :global(.swiper-button-prev:after) {
    font-size: 16px !important;
    font-weight: bold !important;
  }

  :global(.swiper-button-next:hover),
  :global(.swiper-button-prev:hover) {
    background: rgba(0, 0, 0, 0.8) !important;
  }

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

  .modal-image, .modal-video {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    object-fit: contain;
    border-radius: 8px;
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
    
    .modal-details {
      flex-direction: column;
      gap: 0.5rem;
    }
  }
  
  @media (max-width: 480px) {
    :global(.swiper-button-next),
    :global(.swiper-button-prev) {
      width: 36px !important;
      height: 36px !important;
      margin-top: -18px !important;
    }
    
    :global(.swiper-button-next:after),
    :global(.swiper-button-prev:after) {
      font-size: 14px !important;
    }
  }
  
  /* Touch-friendly interactions */
  @media (hover: none) and (pointer: coarse) {
    :global(.swiper-button-next:hover),
    :global(.swiper-button-prev:hover) {
      background: rgba(0, 0, 0, 0.5) !important;
    }
  }

  /* Hide navigation buttons when zoomed to avoid interference */
  :global(.swiper-slide-zoomed .swiper-button-next),
  :global(.swiper-slide-zoomed .swiper-button-prev) {
    opacity: 0;
    pointer-events: none;
  }
</style>