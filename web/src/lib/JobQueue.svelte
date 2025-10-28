<script>
  import { onMount, onDestroy } from 'svelte'
  import { fade, slide } from 'svelte/transition'
  
  let jobs = []
  let isVisible = false
  let refreshInterval = null
  let isLoading = false
  
  function toggleQueue() {
    isVisible = !isVisible
    if (isVisible) {
      fetchJobs()
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  }
  
  async function fetchJobs() {
    if (isLoading) return
    
    try {
      isLoading = true
      const response = await fetch('/api/jobs')
      if (response.ok) {
        const data = await response.json()
        jobs = data.jobs || []
      } else {
        console.error('Failed to fetch jobs')
      }
    } catch (error) {
      console.error('Error fetching jobs:', error)
    } finally {
      isLoading = false
    }
  }
  
  function startAutoRefresh() {
    if (refreshInterval) return
    refreshInterval = setInterval(fetchJobs, 2000) // Refresh every 2 seconds
  }
  
  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
  
  async function cancelJob(jobId) {
    try {
      const response = await fetch(`/api/jobs/${jobId}/cancel`, {
        method: 'POST'
      })
      if (response.ok) {
        fetchJobs() // Refresh the list
      } else {
        alert('Failed to cancel job')
      }
    } catch (error) {
      console.error('Error canceling job:', error)
      alert('Error canceling job')
    }
  }
  
  function getJobStatusIcon(status) {
    switch (status) {
      case 'pending': return '⏳'
      case 'running': return '⚙️'
      case 'completed': return '✅'
      case 'failed': return '❌'
      case 'cancelled': return '🚫'
      default: return '❓'
    }
  }
  
  function getJobStatusColor(status) {
    switch (status) {
      case 'pending': return '#ffa500'
      case 'running': return '#007aff'
      case 'completed': return '#34c759'
      case 'failed': return '#ff3b30'
      case 'cancelled': return '#8e8e93'
      default: return '#8e8e93'
    }
  }
  
  function formatTimestamp(timestamp) {
    return new Date(timestamp).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }
  
  onDestroy(() => {
    stopAutoRefresh()
  })
</script>

<div class="job-queue-container">
  <button class="queue-toggle" on:click={toggleQueue} title="Job Queue">
    🔄 Queue ({jobs.filter(j => j.status === 'pending' || j.status === 'running').length})
  </button>
  
  {#if isVisible}
    <div class="job-queue" in:slide={{ duration: 300 }} out:slide={{ duration: 300 }}>
      <div class="queue-header">
        <h3>Job Queue</h3>
        <button class="refresh-btn" on:click={fetchJobs} disabled={isLoading}>
          {isLoading ? '🔄' : '↻'}
        </button>
      </div>
      
      <div class="job-list">
        {#if jobs.length === 0}
          <div class="empty-state">
            <p>No jobs in queue</p>
          </div>
        {:else}
          {#each jobs as job (job.id)}
            <div class="job-item" in:fade={{ duration: 200 }}>
              <div class="job-status">
                <span class="status-icon">{getJobStatusIcon(job.status)}</span>
                <span class="status-text" style="color: {getJobStatusColor(job.status)}">
                  {job.status.toUpperCase()}
                </span>
              </div>
              
              <div class="job-details">
                <div class="job-name">{job.name || 'Image Generation'}</div>
                <div class="job-meta">
                  <span>Started: {formatTimestamp(job.created)}</span>
                  {#if job.progress}
                    <span>Progress: {job.progress}%</span>
                  {/if}
                </div>
                {#if job.error}
                  <div class="job-error">{job.error}</div>
                {/if}
              </div>
              
              <div class="job-actions">
                {#if job.status === 'pending' || job.status === 'running'}
                  <button class="cancel-btn" on:click={() => cancelJob(job.id)}>
                    Cancel
                  </button>
                {/if}
              </div>
            </div>
          {/each}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .job-queue-container {
    position: relative;
    z-index: 1000;
  }
  
  .queue-toggle {
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(10px);
    border: none;
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s, transform 0.2s;
    white-space: nowrap;
  }
  
  .queue-toggle:hover {
    background: rgba(0, 0, 0, 0.9);
    transform: scale(1.05);
  }
  
  .job-queue {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    width: 350px;
    max-height: 400px;
    background: rgba(0, 0, 0, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }
  
  .queue-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .queue-header h3 {
    margin: 0;
    color: white;
    font-size: 1.1rem;
  }
  
  .refresh-btn {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0.25rem;
    border-radius: 4px;
    transition: background-color 0.2s;
  }
  
  .refresh-btn:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .refresh-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .job-list {
    max-height: 300px;
    overflow-y: auto;
    padding: 0.5rem;
  }
  
  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #8e8e93;
  }
  
  .job-item {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.75rem;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    transition: background-color 0.2s;
  }
  
  .job-item:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .job-status {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }
  
  .status-icon {
    font-size: 1.2rem;
  }
  
  .status-text {
    font-size: 0.7rem;
    font-weight: 500;
    text-align: center;
  }
  
  .job-details {
    min-width: 0;
  }
  
  .job-name {
    color: white;
    font-weight: 500;
    margin-bottom: 0.25rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  
  .job-meta {
    font-size: 0.8rem;
    color: #8e8e93;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  
  .job-error {
    font-size: 0.8rem;
    color: #ff3b30;
    margin-top: 0.25rem;
    background: rgba(255, 59, 48, 0.1);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  
  .job-actions {
    display: flex;
    align-items: center;
  }
  
  .cancel-btn {
    background: rgba(255, 59, 48, 0.2);
    border: 1px solid rgba(255, 59, 48, 0.3);
    color: #ff3b30;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
    transition: background-color 0.2s;
  }
  
  .cancel-btn:hover {
    background: rgba(255, 59, 48, 0.3);
  }
  
  /* Mobile adjustments */
  @media (max-width: 768px) {
    .job-queue {
      width: 300px;
      max-height: 350px;
    }
    
    .job-item {
      grid-template-columns: auto 1fr;
      grid-template-rows: auto auto;
    }
    
    .job-actions {
      grid-column: 1 / -1;
      justify-content: center;
      margin-top: 0.5rem;
    }
  }
</style>