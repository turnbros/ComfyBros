# ComfyUI Gallery

A mobile-friendly web gallery for reviewing images and videos generated with ComfyUI.

## Features

- **Mobile-Optimized**: Responsive design that works great on phones and tablets
- **Drag & Drop**: Simply drag a folder containing your ComfyUI outputs to load them
- **Multiple Formats**: Supports JPG, PNG, GIF, WebP images and MP4, WebM videos
- **Touch Navigation**: Swipe left/right to navigate between media in the modal view
- **Sorting & Filtering**: Sort by date or name, filter by media type
- **Video Thumbnails**: Automatically generates thumbnails for video files
- **Full-Screen Preview**: Click any media to view it in full-screen modal
- **Keyboard Navigation**: Use arrow keys to navigate, Escape to close

## Usage

1. Open `gallery.html` in your web browser
2. Click "Load Folder" or drag a folder containing your ComfyUI outputs onto the page
3. Browse your media using the responsive grid layout
4. Click any item to view it in full-screen
5. Use touch gestures or keyboard arrows to navigate between items

## File Structure

- `gallery.html` - Main gallery page
- `gallery.css` - Responsive styles and mobile optimizations
- `gallery.js` - Gallery functionality and media handling

## Mobile Features

- Touch-friendly interface with larger tap targets
- Swipe gestures for navigation
- Optimized grid layout for small screens
- Fast loading with lazy image loading
- Responsive controls that work well on mobile

## Browser Compatibility

Works on all modern browsers that support:
- File API
- Drag and Drop API
- HTML5 Video
- CSS Grid

This includes all recent versions of Chrome, Firefox, Safari, and Edge.