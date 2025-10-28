import { writable, derived } from 'svelte/store'

// Media files store
export const mediaStore = writable([])

// Filter and sort options
export const sortOption = writable('date-desc')
export const filterOption = writable('all')

// Modal state
export const modalOpen = writable(false)
export const currentIndex = writable(0)

// Filtered and sorted media files
export const filteredMedia = derived(
  [mediaStore, sortOption, filterOption],
  ([$mediaStore, $sortOption, $filterOption]) => {
    // Filter
    let filtered = $mediaStore.filter(item => {
      if ($filterOption === 'all') return true
      if ($filterOption === 'images') return item.type === 'image'
      if ($filterOption === 'videos') return item.type === 'video'
      return true
    })
    
    // Sort
    filtered.sort((a, b) => {
      switch ($sortOption) {
        case 'date-desc':
          return b.date - a.date
        case 'date-asc':
          return a.date - b.date
        case 'name-asc':
          return a.name.localeCompare(b.name)
        case 'name-desc':
          return b.name.localeCompare(a.name)
        default:
          return 0
      }
    })
    
    return filtered
  }
)

// Current media item
export const currentMedia = derived(
  [filteredMedia, currentIndex],
  ([$filteredMedia, $currentIndex]) => {
    return $filteredMedia[$currentIndex] || null
  }
)