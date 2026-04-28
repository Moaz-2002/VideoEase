// ─── Toast Notification System ───────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
    const container = document.getElementById('toast-container');
    const icons = { success: '✅', error: '❌', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ─── Format Numbers ───────────────────────────────────────────────────────────
function formatCount(n) {
    if (!n) return '—';
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return n.toString();
}

function formatSpeed(bytesPerSec) {
    if (!bytesPerSec) return '';
    if (bytesPerSec >= 1_048_576) return `${(bytesPerSec / 1_048_576).toFixed(1)} MB/s`;
    return `${(bytesPerSec / 1024).toFixed(0)} KB/s`;
}

function formatETA(seconds) {
    if (!seconds) return '';
    if (seconds < 60) return `${seconds}s left`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s left`;
}

// ─── Download History (localStorage) ─────────────────────────────────────────
const HISTORY_KEY = 'videoease_history';

function getHistory() {
    try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
    catch { return []; }
}

function saveHistory(history) {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, 20)));
}

function addToHistory(title, quality, type) {
    const history = getHistory();
    history.unshift({
        title,
        quality,
        type,
        date: new Date().toLocaleDateString(),
    });
    saveHistory(history);
    renderHistory();
}

function renderHistory() {
    const list = document.getElementById('history-list');
    const history = getHistory();

    if (!history.length) {
        list.innerHTML = '<div class="history-empty">No downloads yet. Your download history will appear here.</div>';
        return;
    }

    list.innerHTML = history.map((item, idx) => `
        <div class="history-item" id="hist-${idx}">
            <span class="history-item-icon">${item.type === 'audio' ? '🎵' : '🎬'}</span>
            <div class="history-item-info">
                <div class="history-item-title">${escapeHtml(item.title)}</div>
                <div class="history-item-meta">${escapeHtml(item.quality)} · ${item.date}</div>
            </div>
            <button class="history-item-clear" onclick="removeHistoryItem(${idx})" title="Remove">✕</button>
        </div>
    `).join('');
}

function removeHistoryItem(idx) {
    const history = getHistory();
    history.splice(idx, 1);
    saveHistory(history);
    renderHistory();
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// ─── FAQ Accordion ────────────────────────────────────────────────────────────
function initFAQ() {
    document.querySelectorAll('.faq-question').forEach(btn => {
        btn.addEventListener('click', () => {
            const item = btn.closest('.faq-item');
            const isOpen = item.classList.contains('open');
            document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
            if (!isOpen) item.classList.add('open');
        });
    });
}

// ─── Main App ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {
    // Element refs
    const fetchBtn       = document.getElementById('fetch-btn');
    const pasteBtn       = document.getElementById('paste-btn');
    const videoUrlInput  = document.getElementById('video-url');
    const videoPreview   = document.getElementById('video-preview');
    const videoThumbnail = document.getElementById('video-thumbnail');
    const videoTitle     = document.getElementById('video-title');
    const videoDuration  = document.getElementById('video-duration');
    const videoAuthor    = document.getElementById('video-author');
    const statViews      = document.getElementById('stat-views');
    const statLikes      = document.getElementById('stat-likes');
    const qualityOptions = document.getElementById('quality-options');
    const downloadBtn    = document.getElementById('download-btn');
    const downloadModal  = document.getElementById('download-modal');
    const modalClose     = document.getElementById('modal-close');
    const modalTitle     = document.getElementById('modal-title');
    const modalSubtitle  = document.getElementById('modal-subtitle');
    const modalIcon      = document.getElementById('modal-icon');
    const progressFill   = document.getElementById('progress-fill');
    const progressText   = document.getElementById('progress-text');
    const progressEta    = document.getElementById('progress-eta');

    let selectedQuality   = null;
    let selectedFormatId  = null;
    let selectedType      = null;
    let currentVideoUrl   = null;
    let currentVideoTitle = null;

    // Init
    renderHistory();
    initFAQ();

    // ─── Clipboard paste button ───────────────────────────────────────────────
    pasteBtn.addEventListener('click', async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text) {
                videoUrlInput.value = text;
                showToast('URL pasted from clipboard', 'success', 2500);
                videoUrlInput.focus();
            }
        } catch {
            showToast('Could not access clipboard. Please paste manually.', 'error');
        }
    });

    // ─── Enter key shortcut ───────────────────────────────────────────────────
    videoUrlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') fetchBtn.click();
    });

    // ─── Fetch Video Info ─────────────────────────────────────────────────────
    fetchBtn.addEventListener('click', function () {
        const url = videoUrlInput.value.trim();

        if (!url) {
            showToast('Please enter a valid YouTube URL', 'error');
            return;
        }

        fetchBtn.textContent = 'Fetching…';
        fetchBtn.disabled = true;
        videoPreview.style.display = 'none';
        selectedQuality = null;
        selectedFormatId = null;
        selectedType = null;
        downloadBtn.disabled = true;

        fetch('/api/fetch-video-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);

            // Populate video info
            videoThumbnail.src = data.thumbnail || '/api/placeholder/180/120';
            videoTitle.textContent = data.title;
            videoDuration.textContent = `Duration: ${data.duration}`;
            videoAuthor.textContent = `By: ${data.author}`;
            statViews.textContent = `👁 ${formatCount(data.view_count)}`;
            statLikes.textContent = `👍 ${formatCount(data.like_count)}`;

            currentVideoUrl   = url;
            currentVideoTitle = data.title;

            buildQualityOptions(data.formats);
            videoPreview.style.display = 'block';
            showToast('Video info loaded!', 'success', 2500);
        })
        .catch(err => {
            console.error(err);
            showToast(`Error: ${err.message}`, 'error', 6000);
        })
        .finally(() => {
            fetchBtn.textContent = 'Fetch Video';
            fetchBtn.disabled = false;
        });
    });

    // ─── Build quality option cards ───────────────────────────────────────────
    function buildQualityOptions(formats) {
        qualityOptions.innerHTML = '';

        if (!formats || !formats.length) {
            qualityOptions.innerHTML = '<p style="color:var(--text-muted);font-size:.85rem;">No formats found for this video.</p>';
            return;
        }

        formats.forEach(fmt => {
            const card = document.createElement('div');
            const isAudio = fmt.type === 'audio';
            card.className = 'quality-option' + (isAudio ? ' audio-option' : '');
            card.dataset.quality   = fmt.quality;
            card.dataset.formatId  = fmt.format_id;
            card.dataset.type      = fmt.type || 'video';

            const sizeText = fmt.filesize_formatted ? ` · ${fmt.filesize_formatted}` : '';
            card.innerHTML = `
                <h4>${fmt.quality}</h4>
                <p>${isAudio ? 'Audio Only' : `Video${sizeText}`}</p>
            `;

            card.addEventListener('click', () => {
                document.querySelectorAll('.quality-option').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                selectedQuality  = fmt.quality;
                selectedFormatId = fmt.format_id;
                selectedType     = fmt.type || 'video';
                downloadBtn.disabled = false;
            });

            qualityOptions.appendChild(card);
        });
    }

    // ─── Start Download ───────────────────────────────────────────────────────
    downloadBtn.addEventListener('click', function () {
        if (!selectedQuality || !currentVideoUrl) {
            showToast('Please select a quality option first', 'error');
            return;
        }

        // Reset and open modal
        progressFill.style.width = '0%';
        progressText.textContent = '0%';
        progressEta.textContent = '';
        modalIcon.textContent = '⬇';
        modalTitle.textContent = 'Preparing Download…';
        modalSubtitle.textContent = 'Please wait while we process your video.';
        downloadModal.classList.add('visible');

        fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: currentVideoUrl,
                format_id: selectedFormatId,
                quality: selectedQuality,
            }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) throw new Error(data.error);
            pollStatus(data.download_token);
        })
        .catch(err => {
            downloadModal.classList.remove('visible');
            showToast(`Download failed: ${err.message}`, 'error', 6000);
        });
    });

    // ─── Poll download status ─────────────────────────────────────────────────
    function pollStatus(token) {
        const interval = setInterval(() => {
            fetch(`/api/download-status/${token}`)
            .then(r => r.json())
            .then(data => {
                if (data.error && data.status !== 'error') throw new Error(data.error);

                const pct = Math.round(data.progress || 0);
                progressFill.style.width = `${pct}%`;
                progressText.textContent = `${pct}%`;

                if (data.speed) progressEta.textContent = `${formatSpeed(data.speed)} · ${formatETA(data.eta)}`;

                if (data.status === 'downloading') {
                    modalTitle.textContent = 'Downloading…';
                    modalSubtitle.textContent = 'Hang tight, your video is being downloaded.';
                } else if (data.status === 'processing') {
                    modalTitle.textContent = 'Merging Streams…';
                    modalSubtitle.textContent = 'Combining video and audio tracks.';
                    progressEta.textContent = '';
                }

                if (data.status === 'complete') {
                    clearInterval(interval);
                    progressFill.style.width = '100%';
                    progressText.textContent = '100%';
                    modalIcon.textContent = '✅';
                    modalTitle.textContent = 'Ready to Save!';
                    modalSubtitle.textContent = 'Your file is downloading now…';
                    progressEta.textContent = '';

                    // Add to local history
                    addToHistory(currentVideoTitle, selectedQuality, selectedType);

                    // Trigger file download; keep modal a moment then close
                    const link = document.createElement('a');
                    link.href = `/api/download-file/${token}`;
                    link.style.display = 'none';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);

                    setTimeout(() => {
                        downloadModal.classList.remove('visible');
                        showToast('Download complete! Check your Downloads folder.', 'success', 5000);
                    }, 2500);
                }

                if (data.status === 'error') {
                    clearInterval(interval);
                    downloadModal.classList.remove('visible');
                    showToast(`Download error: ${data.error || 'Unknown error'}`, 'error', 8000);
                }
            })
            .catch(err => {
                clearInterval(interval);
                downloadModal.classList.remove('visible');
                showToast(`Status check failed: ${err.message}`, 'error', 6000);
            });
        }, 1000);
    }

    // ─── Close modal ──────────────────────────────────────────────────────────
    modalClose.addEventListener('click', () => downloadModal.classList.remove('visible'));

    window.addEventListener('click', (e) => {
        if (e.target === downloadModal) downloadModal.classList.remove('visible');
    });
});