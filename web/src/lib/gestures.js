// Touch gesture handling for Svelte
export function swipe(node, options = {}) {
  let startX, startY, startTime
  let isScrolling = false
  
  const {
    onSwipeLeft = () => {},
    onSwipeRight = () => {},
    onSwipeUp = () => {},
    onSwipeDown = () => {},
    threshold = 50,
    timeLimit = 500
  } = options
  
  function handleTouchStart(event) {
    // Ignore multi-touch gestures (pinch/zoom)
    if (event.touches.length > 1) {
      startX = null
      startY = null
      return
    }
    
    const touch = event.touches[0]
    startX = touch.clientX
    startY = touch.clientY
    startTime = Date.now()
    isScrolling = false
  }
  
  function handleTouchMove(event) {
    if (!startX || !startY) return
    
    // Ignore multi-touch gestures
    if (event.touches.length > 1) {
      startX = null
      startY = null
      return
    }
    
    const touch = event.touches[0]
    const deltaX = Math.abs(touch.clientX - startX)
    const deltaY = Math.abs(touch.clientY - startY)
    
    // Determine if this is a navigation gesture
    if (deltaY > deltaX && deltaY > 10) {
      isScrolling = false // Vertical swipe for navigation
      event.preventDefault() // Prevent page scroll
    } else if (deltaX > deltaY && deltaX > 10) {
      isScrolling = false // Horizontal swipe for navigation
      event.preventDefault()
    } else if (deltaY > 10 && deltaX < 10) {
      isScrolling = true // Pure vertical scroll
    }
  }
  
  function handleTouchEnd(event) {
    if (!startX || !startY) return
    
    const touch = event.changedTouches[0]
    const deltaX = touch.clientX - startX
    const deltaY = touch.clientY - startY
    const duration = Date.now() - startTime
    
    // Reset values
    startX = null
    startY = null
    
    // Only process swipes, not scrolls
    if (isScrolling || duration > timeLimit) return
    
    // Prioritize vertical swipes for mobile
    if (Math.abs(deltaY) > threshold) {
      // Vertical swipe (primary navigation)
      if (deltaY > 0) {
        onSwipeDown() // Swipe down = previous
      } else {
        onSwipeUp() // Swipe up = next
      }
    } else if (Math.abs(deltaX) > threshold) {
      // Horizontal swipe (secondary navigation)
      if (deltaX > 0) {
        onSwipeRight() // Swipe right = previous
      } else {
        onSwipeLeft() // Swipe left = next
      }
    }
  }
  
  // Add event listeners
  node.addEventListener('touchstart', handleTouchStart, { passive: true })
  node.addEventListener('touchmove', handleTouchMove, { passive: false })
  node.addEventListener('touchend', handleTouchEnd, { passive: true })
  
  return {
    destroy() {
      node.removeEventListener('touchstart', handleTouchStart)
      node.removeEventListener('touchmove', handleTouchMove)
      node.removeEventListener('touchend', handleTouchEnd)
    },
    update(newOptions) {
      Object.assign(options, newOptions)
    }
  }
}