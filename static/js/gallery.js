lucide.createIcons();
let allRecordings = [];

async function loadGallery() {
    try {
        const res = await fetch('/api/recordings');
        const data = await res.json();
        allRecordings = data.recordings;
        renderGallery(allRecordings);
        document.getElementById('videoCount').textContent = allRecordings.length;
    } catch (e) {
        console.error(e);
    }
}

function renderGallery(items) {
    const grid = document.getElementById('galleryGrid');
    
    if (items.length === 0) {
        grid.innerHTML = '<div style="grid-column:1/-1; text-align:center; padding:50px; color:#94a3b8;">No Media Found</div>';
        return;
    }

    grid.innerHTML = items.map(r => {
        // Parse source
        let source = 'SYSTEM';
        if (r.filename.includes('cam0')) source = 'CAMERA 00';
        else if (r.filename.includes('cam1')) source = 'CAMERA 01';
        else if (r.filename.includes('rtsp')) source = 'RTSP STREAM';

        // Thumbnail URL (fallback to video placeholder if no thumb)
        const thumbUrl = r.thumbnail ? `/thumbnails/${r.thumbnail}` : '';
        
        let thumbContent = '';
        if (thumbUrl) {
            thumbContent = `<img src="${thumbUrl}" loading="lazy" alt="Thumbnail">`;
        } else {
            // Placeholder pattern
            thumbContent = `
            <div style="width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; background:#1e293b;">
                <i data-lucide="video" size="32" color="#475569"></i>
                <span style="font-size:10px; color:#475569; margin-top:8px;">NO PREVIEW</span>
            </div>`;
        }
        
        
        // Time format: YYYYMMDD_HHMMSS -> Friendly format
        // Example: public_cam0_20251231_230553.mp4
        let dateDisplay = r.filename;
        const timeMatch = r.filename.match(/(\d{8})_(\d{6})/);
        if (timeMatch) {
            const dStr = timeMatch[1]; // 20251231
            const tStr = timeMatch[2]; // 230553
            
            // Format: 31/12/2025 23:05:53
            dateDisplay = `${dStr.substr(6,2)}/${dStr.substr(4,2)}/${dStr.substr(0,4)} ${tStr.substr(0,2)}:${tStr.substr(2,2)}:${tStr.substr(4,2)}`;
        }
        
        return `
        <div class="media-card" onclick="location.href='/replay-page/${r.filename}'">
            <div class="thumb-wrapper">
                ${thumbContent}
                <div class="play-overlay">
                    <div class="play-icon">
                        <i data-lucide="play" fill="white"></i>
                    </div>
                </div>
                ${r.is_active ? 
                    '<div style="position:absolute; top:8px; right:8px; background:#ef4444; color:white; font-size:9px; padding:2px 6px; border-radius:4px; font-weight:700;">REC</div>' 
                    : ''}
            </div>
            <div class="meta-info">
                <div class="filename" title="${r.filename}">${dateDisplay}</div>
                <div class="meta-details">
                    <div class="tag">${source}</div>
                    <span>${r.size_mb} MB</span>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    lucide.createIcons();
}

// Filters
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.onclick = () => {
        // UI
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const filter = btn.dataset.filter;
        let filtered = allRecordings;
        
        if (filter !== 'all') {
            filtered = allRecordings.filter(r => r.filename.toLowerCase().includes(filter));
        }
        
        renderGallery(filtered);
    };
});

loadGallery();
