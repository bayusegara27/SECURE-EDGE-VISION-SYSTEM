        lucide.createIcons();

        // System Uptime
        const startTime = Date.now();
        function updateUptime() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const h = Math.floor(elapsed / 3600);
            const m = Math.floor((elapsed % 3600) / 60);
            document.getElementById('uptime').textContent = `${h}h ${m}m`;
        }
        setInterval(updateUptime, 30000);
        updateUptime();

        // Clock
        function updateClock() {
            document.getElementById('liveClock').textContent = new Date().toLocaleTimeString('id-ID');
        }
        setInterval(updateClock, 1000);
        updateClock();

        // Navigation & Modal
        function scrollToWidget(id) {
            const el = document.getElementById(id);
            if(el) {
                el.closest('.widget').style.borderColor = 'var(--primary)';
                el.scrollIntoView({behavior:'smooth', block:'center'});
                setTimeout(() => el.closest('.widget').style.borderColor = 'var(--border)', 2000);
            }
        }

        function toggleSettings() {
            const modal = document.getElementById('settingsModal');
            modal.style.display = modal.style.display === 'none' ? 'flex' : 'none';
        }

        // Focus Mode
        function openFocus(idx) {
            const card = document.getElementById(`card-${idx}`);
            const bg = document.getElementById('focusBg');
            const target = document.getElementById('focusContent');
            
            target.innerHTML = `
                <div class="cam-card" style="width:100%;">
                    ${card.innerHTML}
                </div>
            `;
            // Remove the onclick from the cloned card inside focus
            target.querySelector('.cam-card').onclick = null;
            bg.style.display = 'flex';
        }

        function closeFocus() {
            document.getElementById('focusBg').style.display = 'none';
        }

        // Live Status Update
        async function updateStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                
                data.cameras.forEach(cam => {
                    const fps = document.getElementById(`fps-${cam.id}`);
                    const det = document.getElementById(`det-` + cam.id);
                    const img = document.getElementById(`stream-` + cam.id);
                    const badge = document.getElementById(`badge-` + cam.id);
                    const overlay = document.getElementById(`offline-` + cam.id);
                    const msg = document.getElementById(`offline-msg-` + cam.id);

                    if (fps) fps.textContent = cam.fps.toFixed(1);
                    if (det) det.textContent = cam.detections;

                    if (cam.state === 'online') {
                        overlay.style.display = 'none';
                        img.style.opacity = '1';
                        // User requested REC removed from CCTV view
                        badge.className = 'status-badge badge-live';
                        badge.textContent = '● LIVE';
                        // Remove recording Pulse border from CCTV
                        document.getElementById('card-' + cam.id).classList.remove('recording');
                    } else {
                        overlay.style.display = 'flex';
                        img.style.opacity = '0.05';
                        badge.className = 'status-badge badge-off';
                        badge.textContent = cam.state.toUpperCase();
                        msg.textContent = cam.state === 'connecting' ? 'Establishing Handshake' : 'SYSTEM OFFLINE';
                        // Remove recording class
                        document.getElementById('card-' + cam.id).classList.remove('recording');
                    }
                });
            } catch (e) {}
        }
        setInterval(updateStatus, 1500);

        // Data Lists
        async function refreshLists() {
            try {
                const resRec = await fetch('/api/recordings');
                const dRec = await resRec.json();
                document.getElementById('logList').innerHTML = dRec.recordings.slice(0, 8).map(r => {
                    // Start assuming generic
                    let source = 'SYS';
                    let time = r.filename.slice(-12, -4).replace(/(\d{2})(\d{2})(\d{2})/, '$1:$2:$3');
                    
                    // Parse "public_cam0_..."
                    const camMatch = r.filename.match(/cam(\d+)/);
                    if (camMatch) {
                        source = `CAM 0${camMatch[1]}`;
                    } else if (r.filename.includes('rtsp')) {
                        source = 'RTSP';
                    }

                    let activeBadge = r.is_active ? 
                        `<span style="color:#ef4444; font-weight:700; font-size:9px; margin-left:6px; display:inline-flex; align-items:center; animation:pulse-text 1.5s infinite;">
                            <span style="width:6px; height:6px; background:#ef4444; border-radius:50%; margin-right:4px;"></span> REC
                         </span>` : '';

                    return `
                    <div class="item-row ${r.is_active ? 'recording-active' : ''}" onclick="window.open('/replay-page/${r.filename}', '_blank')">
                        <div class="row-icon"><i data-lucide="${r.is_active ? 'disc' : 'play'}" size="14px" class="${r.is_active ? 'spin-slow' : ''}"></i></div>
                        <div class="row-info">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4>Motion Event${activeBadge}</h4>
                                <span style="font-size:9px; background:var(--bg-hover); padding:2px 4px; border-radius:4px; color:var(--accent);">${source}</span>
                            </div>
                            <p>${time} | ${r.size_mb}MB</p>
                        </div>
                    </div>
                `}).join('');

                const resEv = await fetch('/api/evidence');
                const dEv = await resEv.json();
                
                // Build active encryption indicator
                let activeHtml = '';
                if (dEv.active_encryption && dEv.active_encryption.length > 0) {
                    activeHtml = dEv.active_encryption.map(a => `
                        <div class="item-row recording-active" style="border-left:3px solid #ef4444;">
                            <div class="row-icon spin-slow" style="color:#ef4444"><i data-lucide="lock" size="14px"></i></div>
                            <div class="row-info">
                                <h4 style="color:#ef4444;">Encrypting... CAM ${String(a.camera).padStart(2,'0')}</h4>
                                <p>${a.frames_buffered} frames buffered</p>
                            </div>
                        </div>
                    `).join('');
                }

                // Combine active + completed evidence
                const completedHtml = dEv.evidence.slice(0, 5).map(e => `
                    <div class="item-row">
                        <div class="row-icon" style="color:var(--accent)"><i data-lucide="shield-check" size="14px"></i></div>
                        <div class="row-info">
                            <h4>Forensic Evidence</h4>
                            <p>AES-256 Protected | ${new Date(e.created).toLocaleTimeString()}</p>
                        </div>
                    </div>
                `).join('');

                document.getElementById('evList').innerHTML = activeHtml + completedHtml;
                
                lucide.createIcons();
            } catch (e) {}
        }
        setInterval(refreshLists, 5000);
        refreshLists();
