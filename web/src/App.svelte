<script>
  import Gallery from './lib/Gallery.svelte'
  import { mediaStore } from './lib/stores.js'
  
  let loading = true
  let error = null
  
  async function loadMedia() {
    try {
      const response = await fetch('/api/files')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const files = await response.json()
      const mediaFiles = files.map(file => ({
        name: file.name,
        path: file.path,
        size: formatFileSize(file.size),
        date: new Date(file.modified),
        type: file.type,
        url: `/api/file/${file.path}`,
        thumbnail: `/api/thumbnail/${file.path}`
      }))
      
      mediaStore.set(mediaFiles)
      error = null
    } catch (err) {
      console.error('Error loading files:', err)
      error = 'Failed to load media files. Make sure the API server is running on port 8000.'
      mediaStore.set([])
    } finally {
      loading = false
    }
  }
  
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }
  
  // Load media on component mount
  loadMedia()
</script>

<main>
  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <p>Loading media gallery...</p>
    </div>
  {:else if error}
    <div class="error">
      <div class="error-icon">⚠️</div>
      <h2>Connection Error</h2>
      <p>{error}</p>
      <button class="retry-btn" on:click={loadMedia}>Retry</button>
    </div>
  {:else}
    <Gallery />
  {/if}
</main>

<style>
  main {
    min-height: 100vh;
    width: 100%;
  }
  
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
    padding: 2rem;
  }
  
  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #333;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .loading p {
    color: var(--text-secondary);
  }

  .error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    text-align: center;
    padding: 2rem;
  }

  .error-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .error h2 {
    color: #ff3b30;
    margin-bottom: 1rem;
  }

  .error p {
    color: var(--text-secondary);
    margin-bottom: 2rem;
    max-width: 500px;
  }

  .retry-btn {
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1rem;
    transition: background-color 0.2s;
  }

  .retry-btn:hover {
    background: #1a73e8;
  }
</style>