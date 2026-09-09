/* ═══════════════════════════════════════════════════════════
   TruthLens – main.js
   All UI helpers in one place, no duplicates.
═══════════════════════════════════════════════════════════ */

// ── Tab switching (input-tab / input-section pairs) ──────────────────────────
function switchTab(targetId, group, btn) {
    document.querySelectorAll(`.input-section[data-group="${group}"]`).forEach(el => el.classList.remove('active'));
    document.querySelectorAll(`.input-tab`).forEach(el => {
        // only deactivate tabs in the same visual group (closest parent)
        if (btn.parentElement.contains(el)) el.classList.remove('active');
    });
    document.getElementById(targetId)?.classList.add('active');
    btn.classList.add('active');
}

// ── Main module tabs (Module 3 / Module 4) ───────────────────────────────────
function showMainTab(tabId, btn) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId)?.classList.add('active');
    btn.classList.add('active');
}

// Alias kept for backward compat
function showTab(tabId, btn) { showMainTab(tabId, btn); }

// ── Sub-tabs (Image+Audio / Video) ───────────────────────────────────────────
function showSubTab(tabId, btn) {
    document.querySelectorAll('.sub-tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.sub-tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(tabId)?.classList.add('active');
    btn.classList.add('active');
}

// ── Image preview on file input change ───────────────────────────────────────
function previewImage(event, previewId) {
    const file = event.target.files[0];
    if (!file) return;
    const img = document.getElementById(previewId);
    if (!img) return;
    img.src = URL.createObjectURL(file);
    img.style.display = 'block';
}

// ── Image preview from URL ────────────────────────────────────────────────────
function previewFromUrl(url, previewId) {
    const img = document.getElementById(previewId);
    if (!img) return;
    if (url && url.startsWith('http')) {
        img.src = url;
        img.style.display = 'block';
        img.onerror = () => { img.style.display = 'none'; };
    } else {
        img.style.display = 'none';
    }
}

// ── Handle paste image (Ctrl+V into paste-zone) ───────────────────────────────
function handlePasteImage(event, previewId, dataInputId) {
    const items = event.clipboardData?.items;
    if (!items) return;
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = e => {
                const img = document.getElementById(previewId);
                const input = document.getElementById(dataInputId);
                if (img) { img.src = e.target.result; img.style.display = 'block'; }
                if (input) input.value = e.target.result;
                const zone = event.currentTarget;
                if (zone) zone.innerHTML = '<i class="fas fa-check-circle" style="color:#44ff44"></i><p>Image pasted — ready to analyse</p>';
            };
            reader.readAsDataURL(blob);
            event.preventDefault();
            break;
        }
    }
}

// ── Show selected filename ────────────────────────────────────────────────────
function showFileName(event, labelId) {
    const label = document.getElementById(labelId);
    if (!label) return;
    const file = event.target.files[0];
    label.textContent = file ? '📎 ' + file.name : '';
}

// ── Clipboard paste into textarea ─────────────────────────────────────────────
async function pasteFromClipboard(textareaId) {
    try {
        const text = await navigator.clipboard.readText();
        const ta = document.getElementById(textareaId);
        if (ta) ta.value = text;
    } catch {
        alert('Clipboard access denied. Please paste manually with Ctrl+V.');
    }
}

// ── Clear textarea ────────────────────────────────────────────────────────────
function clearField(textareaId) {
    const ta = document.getElementById(textareaId);
    if (ta) ta.value = '';
}

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(msg) {
    let t = document.getElementById('_toast');
    if (!t) {
        t = document.createElement('div');
        t.id = '_toast';
        t.style.cssText = [
            'position:fixed','bottom:30px','left:50%','transform:translateX(-50%)',
            'background:#1a1a2e','border:1.5px solid #00d4ff','color:#e0e0e0',
            'padding:14px 24px','border-radius:10px','font-size:14px',
            'z-index:9999','max-width:80vw','text-align:center',
            'box-shadow:0 4px 20px rgba(0,212,255,0.3)'
        ].join(';');
        document.body.appendChild(t);
    }
    t.textContent = msg;
    t.style.display = 'block';
    clearTimeout(t._hide);
    t._hide = setTimeout(() => { t.style.display = 'none'; }, 3500);
}
