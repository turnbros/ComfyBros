<script>
  import { filteredMedia, sortOption, filterOption, modalOpen, currentIndex } from './stores.js'
  import Modal from './Modal.svelte'
  import MediaItem from './MediaItem.svelte'
  
  function openModal(index) {
    currentIndex.set(index)
    modalOpen.set(true)
  }
  
  function refreshMedia() {
    window.location.reload()
  }
  
  async function generateNewImage() {
    try {
      const response = await fetch('/api/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          trigger: 'gallery_main',
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
</script>

<div class="gallery">
  <header class="header">
    <h1>Media Gallery</h1>
    <div class="controls">
      <button class="btn generate-btn" on:click={generateNewImage}>
        ✨ Generate
      </button>
      
      <button class="btn" on:click={refreshMedia}>
        Refresh
      </button>
      
      <select class="select" bind:value={$sortOption}>
        <option value="date-desc">Newest First</option>
        <option value="date-asc">Oldest First</option>
        <option value="name-asc">Name A-Z</option>
        <option value="name-desc">Name Z-A</option>
      </select>
      
      <select class="select" bind:value={$filterOption}>
        <option value="all">All Media</option>
        <option value="images">Images Only</option>
        <option value="videos">Videos Only</option>
      </select>
    </div>
  </header>
  
  <main class="main">
    {#if $filteredMedia.length === 0}
      <div class="empty">
        <div class="empty-icon">🖼️</div>
        <p>No media files found</p>
        <p class="empty-hint">Make sure the server is running and files exist in the output directory</p>
      </div>
    {:else}
      <div class="media-grid">
        {#each $filteredMedia as item, index (item.path)}
          <MediaItem 
            {item} 
            {index}
            on:click={() => openModal(index)}
          />
        {/each}
      </div>
    {/if}
  </main>
</div>

{#if $modalOpen}
  <Modal />
{/if}

<style>
  .gallery {
    min-height: 100vh;
  }
  
  .header {
    background-color: var(--bg-medium);
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .header h1 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: var(--primary-color);
  }
  
  .controls {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    align-items: center;
  }
  
  .btn, .select {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--bg-light);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
  }
  
  .btn:hover {
    background-color: #4d4d4d;
  }
  
  .generate-btn {
    background: linear-gradient(135deg, #34c759, #30d158);
    color: white;
    border: none;
    font-weight: 500;
  }
  
  .generate-btn:hover {
    background: linear-gradient(135deg, #30d158, #34c759);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);
  }
  
  .main {
    padding: 1rem;
    min-height: calc(100vh - 120px);
  }
  
  .media-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    padding: 0;
  }
  
  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 3rem 1rem;
    min-height: 50vh;
  }
  
  .empty-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .empty-hint {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }
  
  /* Mobile optimizations */
  @media (max-width: 768px) {
    .header {
      padding: 0.5rem;
    }
    
    .header h1 {
      font-size: 1.3rem;
      margin-bottom: 0.5rem;
    }
    
    .controls {
      gap: 0.3rem;
      flex-direction: column;
      align-items: stretch;
    }
    
    .btn, .select {
      padding: 0.7rem;
      font-size: 1rem;
    }
    
    .main {
      padding: 0.5rem;
    }
    
    .media-grid {
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 0.5rem;
    }
  }
  
  @media (max-width: 480px) {
    .media-grid {
      grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
    
    .controls {
      gap: 0.5rem;
    }
    
    .btn, .select {
      padding: 0.8rem;
    }
  }
</style>