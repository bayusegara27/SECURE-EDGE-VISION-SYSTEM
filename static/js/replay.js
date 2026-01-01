lucide.createIcons();
const player = document.getElementById('mainPlayer');
const currentFilename = window.location.pathname.split('/').pop();

// Init
async function loadPlaylist() {
    try {
        const res = await fetch('/api/recordings');
        const data = await res.json();
        const recordings = data.recordings;
        
        // Find current file stats
        const currentFile = recordings.find(r => r.filename === currentFilename);
        if (currentFile) {
            document.getElementById('propSize').textContent = `${currentFile.size_mb} MB`;
            // Parse Source
            let source = 'SYSTEM';
            if (currentFilename.includes('cam0')) source = 'CAMERA 00';
            else if (currentFilename.includes('cam1')) source = 'CAMERA 01';
            else if (currentFilename.includes('rtsp')) source = 'RTSP INPUT';
            document.getElementById('propSource').textContent = source;
            document.getElementById('vidTimestamp').textContent = new Date(currentFile.created).toLocaleString('id-ID');
        }

        const list = document.getElementById('playlist');
        list.innerHTML = recordings.map(r => {
            const isActive = r.filename === currentFilename ? 'active' : '';
            return `
            <div class="clip-item ${isActive}" onclick="location.href='/replay-page/${r.filename}'">
                <div class="clip-icon">
                    <i data-lucide="${isActive ? 'play' : 'video'}" size="16"></i>
                </div>
                <div class="clip-info">
                    <div style="font-weight:600; font-size:13px; margin-bottom:2px; color:${isActive ? '#fff' : '#cbd5e1'}">${r.filename}</div>
                    <div style="font-size:11px; color:var(--text-dim);">${r.size_mb} MB</div>
                </div>
            </div>
            `;
        }).join('');
        lucide.createIcons();
        
        // Set Source
        document.getElementById('vidName').textContent = currentFilename;
        player.src = `/replay/${currentFilename}`;
        
    } catch(e) { console.error(e); }
}

loadPlaylist();

// Controls
function togglePlay() {
    if (player.paused) {
        player.play();
        document.getElementById('playIcon').innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
        document.getElementById('playIcon').setAttribute('fill', 'white');
    } else {
        player.pause();
        document.getElementById('playIcon').innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
    }
}

function setSpeed(s) {
    player.playbackRate = s;
    document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`spd${s}`).classList.add('active');
}

player.ontimeupdate = () => {
    if (!player.duration) return;
    const pct = (player.currentTime / player.duration) * 100;
    
    // Update visual bars
    document.getElementById('progress').style.width = `${pct}%`;
    document.getElementById('thumb').style.left = `${pct}%`;
    
    // Timecode
    const cur = new Date(player.currentTime * 1000).toISOString().substr(14, 5);
    const dur = new Date(player.duration * 1000).toISOString().substr(14, 5);
    document.getElementById('timecode').textContent = `${cur} / ${dur}`;
};

function snap() {
    const cvs = document.createElement('canvas');
    cvs.width = player.videoWidth;
    cvs.height = player.videoHeight;
    cvs.getContext('2d').drawImage(player, 0, 0);
    const a = document.createElement('a');
    a.href = cvs.toDataURL('image/jpeg');
    a.download = `snapshot_${Date.now()}.jpg`;
    a.click();
}

// Click seek
function seek(e) {
    const rect = document.getElementById('timeline').getBoundingClientRect();
    const pos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    player.currentTime = pos * player.duration;
}

function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.querySelector('.video-container').requestFullscreen();
    } else {
        document.exitFullscreen();
    }
}

// Keyboard Layout
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        e.preventDefault();
        togglePlay();
    }
    if (e.code === 'ArrowRight') {
        player.currentTime += 5;
    }
    if (e.code === 'ArrowLeft') {
        player.currentTime -= 5;
    }
});
