class MediaGallery {
    constructor() {
        this.mediaFiles = [];
        this.currentIndex = 0;
        this.filteredFiles = [];
        
        this.initializeElements();
        this.bindEvents();
        this.loadFromServer();
    }

    initializeElements() {
        this.elements = {
            refreshBtn: document.getElementById('refreshBtn'),
            sortSelect: document.getElementById('sortSelect'),
            filterSelect: document.getElementById('filterSelect'),
            dropzone: document.getElementById('dropzone'),
            gallery: document.getElementById('gallery'),
            mediaGrid: document.getElementById('mediaGrid'),
            loading: document.getElementById('loadingIndicator'),
            modal: document.getElementById('modal'),
            modalClose: document.getElementById('modalClose'),
            modalImage: document.getElementById('modalImage'),
            modalVideo: document.getElementById('modalVideo'),
            modalTitle: document.getElementById('modalTitle'),
            modalSize: document.getElementById('modalSize'),
            modalDate: document.getElementById('modalDate'),
            prevBtn: document.getElementById('prevBtn'),
            nextBtn: document.getElementById('nextBtn')
        };
    }

    bindEvents() {
        this.elements.refreshBtn.addEventListener('click', () => {
            this.loadFromServer();
        });

        this.elements.sortSelect.addEventListener('change', () => {
            this.sortAndFilterMedia();
        });

        this.elements.filterSelect.addEventListener('change', () => {
            this.sortAndFilterMedia();
        });

        this.elements.modalClose.addEventListener('click', () => {
            this.closeModal();
        });

        this.elements.prevBtn.addEventListener('click', () => {
            this.navigateModal(-1);
        });

        this.elements.nextBtn.addEventListener('click', () => {
            this.navigateModal(1);
        });

        // Close modal on escape key or click outside
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            } else if (e.key === 'ArrowLeft') {
                this.navigateModal(-1);
            } else if (e.key === 'ArrowRight') {
                this.navigateModal(1);
            }
        });

        this.elements.modal.addEventListener('click', (e) => {
            if (e.target === this.elements.modal) {
                this.closeModal();
            }
        });

        // Prevent video context menu on mobile
        this.elements.modalVideo.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }

    async loadFromServer() {
        this.showLoading();
        try {
            const response = await fetch('/api/files');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const files = await response.json();
            this.mediaFiles = files.map(file => ({
                name: file.name,
                path: file.path,
                size: this.formatFileSize(file.size),
                date: new Date(file.modified),
                type: file.type,
                url: `/api/file/${file.path}`,
                thumbnail: `/api/thumbnail/${file.path}`
            }));
            
            this.sortAndFilterMedia();
            this.hideLoading();
            this.showGallery();
        } catch (error) {
            console.error('Error loading files from server:', error);
            this.hideLoading();
            this.showDropzone();
        }
    }

    showDropzone() {
        this.elements.dropzone.classList.remove('hidden');
        this.elements.gallery.classList.add('hidden');
    }

    setupDropzone() {
        const dropzone = this.elements.dropzone;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, () => {
                dropzone.classList.remove('dragover');
            }, false);
        });

        dropzone.addEventListener('drop', (e) => {
            const items = Array.from(e.dataTransfer.items);
            this.handleDroppedItems(items);
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    async handleDroppedItems(items) {
        this.showLoading();
        const files = [];
        
        for (const item of items) {
            if (item.kind === 'file') {
                const entry = item.webkitGetAsEntry();
                if (entry) {
                    await this.traverseFileTree(entry, files);
                }
            }
        }
        
        this.handleFileSelection(files);
    }

    async traverseFileTree(item, files, path = '') {
        return new Promise((resolve) => {
            if (item.isFile) {
                item.file((file) => {
                    if (this.isMediaFile(file)) {
                        files.push(file);
                    }
                    resolve();
                });
            } else if (item.isDirectory) {
                const dirReader = item.createReader();
                dirReader.readEntries(async (entries) => {
                    for (const entry of entries) {
                        await this.traverseFileTree(entry, files, path + item.name + '/');
                    }
                    resolve();
                });
            }
        });
    }

    isMediaFile(file) {
        const supportedTypes = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/webm', 'video/ogg'
        ];
        return supportedTypes.includes(file.type);
    }

    async handleFileSelection(files) {
        if (!files || files.length === 0) return;
        
        this.showLoading();
        this.mediaFiles = [];

        const fileArray = Array.from(files).filter(file => this.isMediaFile(file));
        
        for (const file of fileArray) {
            const mediaItem = await this.processFile(file);
            if (mediaItem) {
                this.mediaFiles.push(mediaItem);
            }
        }

        this.sortAndFilterMedia();
        this.hideLoading();
        this.showGallery();
    }

    async processFile(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const mediaItem = {
                    file: file,
                    url: e.target.result,
                    name: file.name,
                    size: this.formatFileSize(file.size),
                    date: new Date(file.lastModified),
                    type: file.type.startsWith('video/') ? 'video' : 'image'
                };

                if (mediaItem.type === 'image') {
                    const img = new Image();
                    img.onload = () => {
                        mediaItem.thumbnail = e.target.result;
                        resolve(mediaItem);
                    };
                    img.src = e.target.result;
                } else {
                    // For videos, create a thumbnail
                    this.createVideoThumbnail(file, e.target.result).then(thumbnail => {
                        mediaItem.thumbnail = thumbnail;
                        resolve(mediaItem);
                    });
                }
            };
            reader.readAsDataURL(file);
        });
    }

    async createVideoThumbnail(file, videoUrl) {
        return new Promise((resolve) => {
            const video = document.createElement('video');
            video.crossOrigin = 'anonymous';
            video.currentTime = 1; // Get frame at 1 second
            
            video.onloadeddata = () => {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                resolve(canvas.toDataURL('image/jpeg', 0.7));
            };
            
            video.onerror = () => {
                // Fallback to a default video icon
                resolve('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIyMDAiIGhlaWdodD0iMjAwIiBmaWxsPSIjMzMzIi8+Cjxwb2x5Z29uIHBvaW50cz0iNzUsNTAgMTUwLDEwMCA3NSwxNTAiIGZpbGw9IiM2NjYiLz4KPC9zdmc+');
            };
            
            video.src = videoUrl;
        });
    }

    sortAndFilterMedia() {
        const sortValue = this.elements.sortSelect.value;
        const filterValue = this.elements.filterSelect.value;

        // Filter
        this.filteredFiles = this.mediaFiles.filter(item => {
            if (filterValue === 'all') return true;
            if (filterValue === 'images') return item.type === 'image';
            if (filterValue === 'videos') return item.type === 'video';
            return true;
        });

        // Sort
        this.filteredFiles.sort((a, b) => {
            switch (sortValue) {
                case 'date-desc':
                    return b.date - a.date;
                case 'date-asc':
                    return a.date - b.date;
                case 'name-asc':
                    return a.name.localeCompare(b.name);
                case 'name-desc':
                    return b.name.localeCompare(a.name);
                default:
                    return 0;
            }
        });

        this.renderGallery();
    }

    renderGallery() {
        this.elements.mediaGrid.innerHTML = '';

        this.filteredFiles.forEach((item, index) => {
            const mediaElement = this.createMediaElement(item, index);
            this.elements.mediaGrid.appendChild(mediaElement);
        });
    }

    createMediaElement(item, index) {
        const div = document.createElement('div');
        div.className = 'media-item';
        div.addEventListener('click', () => this.openModal(index));

        const img = document.createElement('img');
        img.src = item.thumbnail;
        img.alt = item.name;
        img.className = 'media-thumbnail';
        img.loading = 'lazy';

        const overlay = document.createElement('div');
        overlay.className = 'media-overlay';

        const name = document.createElement('div');
        name.className = 'media-name';
        name.textContent = item.name;

        const details = document.createElement('div');
        details.className = 'media-details';

        const size = document.createElement('span');
        size.textContent = item.size;

        const date = document.createElement('span');
        date.textContent = this.formatDate(item.date);

        details.appendChild(size);
        details.appendChild(date);

        overlay.appendChild(name);
        overlay.appendChild(details);

        div.appendChild(img);
        div.appendChild(overlay);

        if (item.type === 'video') {
            const videoIndicator = document.createElement('div');
            videoIndicator.className = 'video-indicator';
            videoIndicator.innerHTML = '▶ Video';
            div.appendChild(videoIndicator);
        }

        return div;
    }

    openModal(index) {
        this.currentIndex = index;
        const item = this.filteredFiles[index];

        this.elements.modalTitle.textContent = item.name;
        this.elements.modalSize.textContent = item.size;
        this.elements.modalDate.textContent = this.formatDate(item.date);

        if (item.type === 'image') {
            this.elements.modalImage.src = item.url;
            this.elements.modalImage.style.display = 'block';
            this.elements.modalVideo.style.display = 'none';
            this.elements.modalVideo.pause();
        } else {
            this.elements.modalVideo.src = item.url;
            this.elements.modalVideo.style.display = 'block';
            this.elements.modalImage.style.display = 'none';
        }

        this.elements.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        // Update navigation buttons
        this.elements.prevBtn.style.display = this.filteredFiles.length > 1 ? 'flex' : 'none';
        this.elements.nextBtn.style.display = this.filteredFiles.length > 1 ? 'flex' : 'none';
    }

    closeModal() {
        this.elements.modal.classList.add('hidden');
        this.elements.modalVideo.pause();
        document.body.style.overflow = '';
    }

    navigateModal(direction) {
        if (this.filteredFiles.length <= 1) return;

        this.currentIndex += direction;
        if (this.currentIndex < 0) {
            this.currentIndex = this.filteredFiles.length - 1;
        } else if (this.currentIndex >= this.filteredFiles.length) {
            this.currentIndex = 0;
        }

        this.openModal(this.currentIndex);
    }

    showLoading() {
        this.elements.loading.classList.remove('hidden');
        this.elements.gallery.classList.add('hidden');
        this.elements.dropzone.classList.add('hidden');
    }

    hideLoading() {
        this.elements.loading.classList.add('hidden');
    }

    showGallery() {
        this.elements.gallery.classList.remove('hidden');
        this.elements.dropzone.classList.add('hidden');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(date) {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the gallery when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MediaGallery();
});

// Add touch gesture support for mobile navigation in modal
let touchStartX = 0;
let touchEndX = 0;

document.addEventListener('touchstart', (e) => {
    if (!document.getElementById('modal').classList.contains('hidden')) {
        touchStartX = e.changedTouches[0].screenX;
    }
});

document.addEventListener('touchend', (e) => {
    if (!document.getElementById('modal').classList.contains('hidden')) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }
});

function handleSwipe() {
    const swipeThreshold = 50;
    const diff = touchStartX - touchEndX;
    
    if (Math.abs(diff) > swipeThreshold) {
        if (diff > 0) {
            // Swiped left - next image
            document.getElementById('nextBtn').click();
        } else {
            // Swiped right - previous image
            document.getElementById('prevBtn').click();
        }
    }
}