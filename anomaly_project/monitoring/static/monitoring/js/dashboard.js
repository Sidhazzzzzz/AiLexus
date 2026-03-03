// ─── STATE ───
let tab = 'hosts', selHost = null, timer = null;
let charts = { donuts: {}, sparks: {}, c1: null, c2: null, health: null };
let builtHosts = new Set();

// ─── SCRAMBLE CLOCK ───
const clockEl = document.getElementById('live-time');
let lastTimeStr = '';
const scambleChars = '0123456789';

function updateClock() {
    if (!clockEl) return;
    const timeStr = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    if (timeStr === lastTimeStr) return;

    // Find which digits changed
    const changedIndices = [];
    for (let i = 0; i < timeStr.length; i++) {
        if (timeStr[i] !== lastTimeStr[i] && timeStr[i] !== ':') {
            changedIndices.push(i);
        }
    }
    lastTimeStr = timeStr;
    clockEl.setAttribute('data-time', timeStr); // For CSS glitch compatibility

    let iteration = 0;
    const maxIterations = 12; // Scramble for ~480ms per second
    clearInterval(clockEl.scrambleInterval);

    clockEl.scrambleInterval = setInterval(() => {
        clockEl.textContent = timeStr.split('').map((char, index) => {
            if (char === ':') return ':';
            // Only scramble digits that changed this second!
            if (changedIndices.includes(index) && iteration < maxIterations) {
                return scambleChars[Math.floor(Math.random() * scambleChars.length)];
            }
            return char;
        }).join('');

        if (iteration >= maxIterations) {
            clearInterval(clockEl.scrambleInterval);
            clockEl.textContent = timeStr;
        }
        iteration++;
    }, 40);
}
setInterval(updateClock, 1000);
updateClock();

// ═══════════════════════════════════
//  INTERACTIVE: Velocity Tech Scanner Cursor
// ═══════════════════════════════════
const tCursorDot = document.getElementById('tech-cursor-dot');
const tCursorScanner = document.getElementById('tech-cursor-scanner');
let mouseX = window.innerWidth / 2, mouseY = window.innerHeight / 2;
let scanX = mouseX, scanY = mouseY;
let lastMouseX = mouseX, lastMouseY = mouseY;
let isHovering = false;

document.addEventListener('mousemove', e => {
    mouseX = e.clientX; mouseY = e.clientY;
    if (tCursorDot) {
        tCursorDot.style.left = mouseX - 2 + 'px';
        tCursorDot.style.top = mouseY - 2 + 'px';
    }
});

function animateTechCursor() {
    // Smooth follow for the scanner reticle
    scanX += (mouseX - scanX) * 0.2;
    scanY += (mouseY - scanY) * 0.2;

    // Calculate velocity for stretching effect
    const dx = mouseX - lastMouseX;
    const dy = mouseY - lastMouseY;
    const speed = Math.min(Math.sqrt(dx * dx + dy * dy) * 0.5, 20); // Cap extreme speeds

    lastMouseX = mouseX;
    lastMouseY = mouseY;

    if (tCursorScanner) {
        // If moving fast and NOT hovering over a button, stretch in direction of motion
        if (speed > 1 && !isHovering) {
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            const stretch = 1 + (speed * 0.04); // Stretch X
            const squish = 1 - (speed * 0.015);  // Squish Y slightly
            // We use absolute positioning for left/top and transform for rotation/scale
            tCursorScanner.style.left = scanX + 'px';
            tCursorScanner.style.top = scanY + 'px';
            tCursorScanner.style.transform = `translate(-50%, -50%) rotate(${angle}deg) scale(${stretch}, ${Math.max(0.6, squish)})`;
            tCursorScanner.classList.remove('spin');
        } else {
            // Reset to normal shape, maybe spin if hovering
            tCursorScanner.style.left = scanX + 'px';
            tCursorScanner.style.top = scanY + 'px';
            tCursorScanner.style.transform = `translate(-50%, -50%)`;
            if (isHovering) tCursorScanner.classList.add('spin');
            else tCursorScanner.classList.remove('spin');
        }
    }
    requestAnimationFrame(animateTechCursor);
}
animateTechCursor();

// Spawn floating background particles
function createParticles() {
    for (let i = 0; i < 35; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        const size = Math.random() * 4 + 2;
        p.style.width = p.style.height = size + 'px';
        p.style.left = Math.random() * 100 + 'vw';
        p.style.animationDuration = (Math.random() * 20 + 15) + 's';
        p.style.animationDelay = (Math.random() * -20) + 's';

        // Use the amber/gold/purple AI colors
        const colors = ['#f59e0b', '#fbbf24', '#fcd34d', '#8b5cf6'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        p.style.background = color;
        p.style.opacity = Math.random() * 0.15 + 0.05;
        p.style.color = color; // For glow
        document.body.appendChild(p);
    }
}
createParticles();

// Hover detection for scanner lock-on, cross, and hand/text states
document.addEventListener('mouseover', e => {
    // 1. Lock-on & Hand state (interactive elements)
    const t = e.target.closest('.btn-primary, .btn-secondary, .nav-btn, .icon-btn, .hcard, .wcard, .alert-card, .close-btn, a');
    if (t && tCursorScanner && tCursorDot) {
        isHovering = true;
        tCursorDot.classList.add('hand-mode');
        tCursorScanner.classList.add('hand-mode');
    }

    // 2. Cross state (Charts)
    const chartArea = e.target.closest('canvas, .chart-wrapper');
    if (chartArea && tCursorDot && tCursorScanner) {
        tCursorDot.classList.add('cross-mode');
        tCursorScanner.classList.add('cross-mode');
    }

    // 3. Text Input state (Inputs, Textareas)
    const inputArea = e.target.closest('input, textarea, [contenteditable="true"]');
    if (inputArea && tCursorDot && tCursorScanner) {
        tCursorDot.classList.add('text-mode');
        tCursorScanner.classList.add('text-mode');
    }
});
document.addEventListener('mouseout', e => {
    // 1. Lock-on & Hand state
    const t = e.target.closest('.btn-primary, .btn-secondary, .nav-btn, .icon-btn, .hcard, .wcard, .alert-card, .close-btn, a');
    if (t && tCursorScanner && tCursorDot) {
        isHovering = false;
        tCursorDot.classList.remove('hand-mode');
        tCursorScanner.classList.remove('hand-mode');
    }

    // 2. Cross state
    const chartArea = e.target.closest('canvas, .chart-wrapper');
    if (chartArea && tCursorDot && tCursorScanner) {
        tCursorDot.classList.remove('cross-mode');
        tCursorScanner.classList.remove('cross-mode');
    }

    // 3. Text Input state
    const inputArea = e.target.closest('input, textarea, [contenteditable="true"]');
    if (inputArea && tCursorDot && tCursorScanner) {
        tCursorDot.classList.remove('text-mode');
        tCursorScanner.classList.remove('text-mode');
    }
});

// ═══════════════════════════════
//  INTERACTIVE: 3D Card Tilt
// ═══════════════════════════════
function initTilt() {
    document.querySelectorAll('.hcard, .wcard, .gauge').forEach(card => {
        if (card.dataset.tiltInit) return;
        card.dataset.tiltInit = '1';
        card.addEventListener('mousemove', e => {
            const r = card.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            card.style.transform = `perspective(600px) rotateY(${x * 6}deg) rotateX(${-y * 6}deg) translateY(-3px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });
}

// ═══════════════════════════
//  INTERACTIVE: Ripple Click
// ═══════════════════════════
document.addEventListener('click', e => {
    const btn = e.target.closest('.btn-primary');
    if (!btn) return;
    const r = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    const size = Math.max(r.width, r.height) * 2;
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = e.clientX - r.left - size / 2 + 'px';
    ripple.style.top = e.clientY - r.top - size / 2 + 'px';
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

// ═══════════════════════════════════
//  INTERACTIVE: Stagger Card Delays
// ═══════════════════════════════════
function staggerCards(container) {
    const cards = container.querySelectorAll('.hcard, .wcard');
    cards.forEach((c, i) => { c.style.animationDelay = i * 60 + 'ms'; });
}

// ═══════════════════════════════════
//  INTERACTIVE: Stack Scroll Cards
// ═══════════════════════════════════
const stackObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Add a small delay based on index if multiple cards appear at once to get stacking effect
            setTimeout(() => {
                entry.target.classList.add('stack-visible');
            }, entry.target.dataset.stackDelay || 0);
        } else {
            // Remove the class when scrolled out of view so it animates back in when scrolled down again
            entry.target.classList.remove('stack-visible');
        }
    });
}, {
    threshold: 0.1, // Trigger when 10% visible
    rootMargin: '0px 0px -50px 0px' // Trigger slightly before it hits the bottom
});

function initStackCards(container) {
    const cards = container.querySelectorAll('.advice-card, .alert-card');
    cards.forEach((c, i) => {
        c.dataset.stackDelay = (i % 10) * 80; // Stagger up to 10 cards at once
        stackObserver.observe(c);
    });
}

// ─── NAV ───
function switchTab(t) {
    tab = t;
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelector(`[data-tab="${t}"]`)?.classList.add('active');
    document.getElementById(`panel-${t}`)?.classList.add('active');
    clearInterval(timer);
    refresh();
    timer = setInterval(refresh, 5000);
}

function refresh() {
    loadHosts();
    if (selHost) loadDetail(selHost);
    loadWebsites();
    loadAdvice();
    loadAnoms();
    updateAlertCount();
}

function openDetail(id, name) {
    if (selHost !== id) { if (charts.c1) { charts.c1.destroy(); charts.c1 = null; } if (charts.c2) { charts.c2.destroy(); charts.c2 = null; } if (charts.health) { charts.health.destroy(); charts.health = null; } }
    selHost = id;
    document.getElementById('detail-tab').style.display = '';
    document.getElementById('detail-tab-lbl').textContent = name;
    switchTab('detail');
}

// ─── UTILS ───
const U = {
    mColor: v => v > 90 ? '#f87171' : v > 70 ? '#fbbf24' : '#34d399',
    sClass: s => s === 'CRIT' ? 'crit' : s === 'WARN' ? 'warn' : 'ok',
    sLabel: s => s === 'CRIT' ? 'Critical' : s === 'WARN' ? 'Warning' : 'Healthy',
    ago: iso => { if (!iso) return 'Never'; const d = (Date.now() - new Date(iso).getTime()) / 1000; if (d < 10) return 'Just now'; if (d < 60) return Math.floor(d) + 's ago'; if (d < 3600) return Math.floor(d / 60) + 'm ago'; return Math.floor(d / 3600) + 'h ago'; },
    ftime: iso => new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }),
    fdate: iso => new Date(iso).toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }),
    mName: m => ({ cpu: 'CPU', ram: 'RAM', disk: 'Disk', net_sent: 'Upload', net_recv: 'Download', ping_ms: 'Ping' }[m] || m),
    mIcon: m => ({ cpu: '⚡', ram: '🧠', disk: '💾', net_sent: '📤', net_recv: '📥', ping_ms: '📡', website_down: '🔴', website_slow: '🐢', ssl_invalid: '🔒' }[m] || '📊'),
    sevColor: s => s >= 3 ? 'var(--crit)' : s >= 2 ? 'var(--warn)' : 'var(--brand-1)',
    sevBg: s => s >= 3 ? 'var(--crit-dim)' : s >= 2 ? 'var(--warn-dim)' : 'rgba(99,102,241,0.08)',
};

const tooltipStyle = { backgroundColor: 'rgba(12,18,36,0.95)', titleColor: '#f1f5f9', bodyColor: '#94a3b8', borderColor: 'rgba(99,102,241,0.15)', borderWidth: 1, cornerRadius: 8, padding: 10, titleFont: { family: 'Inter', weight: '600', size: 12 }, bodyFont: { family: 'JetBrains Mono', size: 11 }, displayColors: true, boxPadding: 3 };
const gridStyle = { color: 'rgba(255,255,255,0.03)', drawBorder: false };
const tickStyle = { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } };

// ─── DONUT (fixed 56px) ───
function mkDonut(canvas, val, color) {
    canvas.width = 56; canvas.height = 56; canvas.style.width = '56px'; canvas.style.height = '56px';
    return new Chart(canvas, {
        type: 'doughnut',
        data: { datasets: [{ data: [val, Math.max(0, 100 - val)], backgroundColor: [color, 'rgba(100,116,139,0.06)'], borderWidth: 0 }] },
        options: { responsive: false, cutout: '72%', plugins: { legend: { display: false }, tooltip: { enabled: false } }, animation: { duration: 500 } }
    });
}
function updDonut(key, val, color) { const c = charts.donuts[key]; if (c) { c.data.datasets[0].data = [val, Math.max(0, 100 - val)]; c.data.datasets[0].backgroundColor = [color, 'rgba(100,116,139,0.06)']; c.update('none'); } }

// ─── START SCRAMBLE ALERT ───
let _lastAlertCount = null;

function autoScrambleAlerts(el, finalStr, onComplete) {
    const chars = '0123456789!@#$%&*?';
    let iter = 0;
    const maxIter = 22; // Slightly fewer iterations
    clearTimeout(el.sTimeout);
    let delay = 40; // Starts a bit faster

    // Ensure element is visible during animation
    if (el.style.display === 'none') el.style.display = '';

    function step() {
        el.textContent = finalStr.split('').map((ch, i) => {
            if (ch === ' ') return ' ';
            if (iter >= maxIter) return ch;
            // Left to right lock point
            const lockPoint = (i / Math.max(1, finalStr.length)) * (maxIter * 0.4) + (maxIter * 0.4);
            if (iter > lockPoint) return ch;
            return chars[Math.floor(Math.random() * chars.length)];
        }).join('');

        iter++;
        if (iter <= maxIter) {
            delay += 5; // Slows down less aggressively
            el.sTimeout = setTimeout(step, delay);
        } else {
            el.textContent = finalStr;
            if (onComplete) onComplete();
        }
    }
    step();
}

// ─── ALERT COUNT ───
async function updateAlertCount() {
    try {
        const r = await fetch(`/api/anomalies/?_t=${Date.now()}`); const d = await r.json();

        if (_lastAlertCount === d.events.length) return; // Only scramble on change
        _lastAlertCount = d.events.length;

        const countStr = String(d.events.length);
        const b = document.getElementById('alert-badge');
        if (b) autoScrambleAlerts(b, countStr);

        const t = document.getElementById('top-alert-count');
        if (t) {
            autoScrambleAlerts(t, countStr + ' alerts', () => {
                if (d.events.length === 0) t.style.display = 'none';
            });
        }
    } catch (e) { }
}

// ─── TAB 1: HOSTS ───
async function loadHosts() {
    try {
        const res = await fetch(`/api/hosts/?_t=${Date.now()}`); const data = await res.json(); const grid = document.getElementById('host-grid');
        if (!data.hosts.length) { grid.innerHTML = `<div class="empty-state"><div class="empty-icon">📡</div><p class="empty-text">No devices connected yet.<br>Click <strong>+ Add Device</strong> to start.</p></div>`; return; }

        const needsRebuild = data.hosts.some(h => !builtHosts.has(h.id)) || builtHosts.size !== new Set(data.hosts.map(h => h.id)).size;
        if (needsRebuild) {
            for (let k in charts.donuts) charts.donuts[k].destroy(); for (let k in charts.sparks) charts.sparks[k].destroy();
            charts.donuts = {}; charts.sparks = {}; builtHosts = new Set();

            grid.innerHTML = data.hosts.map(h => `
                <div class="hcard" id="hcard-${h.id}">
                    <div class="hcard-top">
                        <div class="hcard-name"><div class="status-dot" style="background:var(--${U.sClass(h.status)})"></div><span id="hname-${h.id}">${h.hostname}</span></div>
                        <div style="display:flex;align-items:center;gap:6px;">
                            <button class="icon-btn" onclick="event.stopPropagation();renameHost(${h.id},'${h.hostname}')" title="Rename">✏️</button>
                            <button class="icon-btn icon-btn-danger" onclick="event.stopPropagation();deleteHost(${h.id},'${h.hostname}')" title="Delete">🗑️</button>
                            <div class="status-badge" id="badge-${h.id}" style="background:${U.sevBg(h.status === 'CRIT' ? 3 : h.status === 'WARN' ? 2 : 0)};color:var(--${U.sClass(h.status)})">${U.sLabel(h.status)}</div>
                        </div>
                    </div>
                    <div class="donut-row" onclick="openDetail(${h.id},'${h.hostname}')">
                        ${['cpu', 'ram', 'disk'].map(m => `<div class="donut-wrap"><div class="donut-ring"><canvas id="d${m}-${h.id}"></canvas><div class="donut-center" id="lbl-${m}-${h.id}" style="color:${U.mColor(h[m])}">${h[m] || '-'}</div></div><div class="donut-label">${m.toUpperCase()}</div></div>`).join('')}
                    </div>
                    <div class="spark-wrap" onclick="openDetail(${h.id},'${h.hostname}')"><canvas id="spark-${h.id}"></canvas></div>
                    <div class="hcard-footer" onclick="openDetail(${h.id},'${h.hostname}')"><span id="ls-${h.id}">Last seen: ${U.ago(h.last_seen)}</span><span>View Details →</span></div>
                </div>
            `).join('');

            staggerCards(grid);
            data.hosts.forEach(h => {
                builtHosts.add(h.id);
                ['cpu', 'ram', 'disk'].forEach(m => { charts.donuts[`${m}-${h.id}`] = mkDonut(document.getElementById(`d${m}-${h.id}`), h[m] || 0, U.mColor(h[m])); });
                fetch(`/api/hosts/${h.id}/?_t=${Date.now()}`).then(r => r.json()).then(d => {
                    const cpuD = d.samples.slice().reverse().slice(-30).map(s => s.cpu);
                    charts.sparks[h.id] = new Chart(document.getElementById(`spark-${h.id}`), {
                        type: 'line', data: { labels: cpuD.map(() => ''), datasets: [{ data: cpuD, borderColor: '#818cf8', borderWidth: 1.5, pointRadius: 0, tension: 0.4, fill: true, backgroundColor: ctx => { const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, 40); g.addColorStop(0, 'rgba(129,140,248,0.12)'); g.addColorStop(1, 'transparent'); return g; } }] },
                        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { enabled: false } }, scales: { x: { display: false }, y: { display: false, min: 0, max: 100 } }, animation: { duration: 0 } }
                    });
                });
            });
            setTimeout(initTilt, 100);
        } else {
            data.hosts.forEach(h => {
                ['cpu', 'ram', 'disk'].forEach(m => { const el = document.getElementById(`lbl-${m}-${h.id}`); if (el) { el.textContent = h[m] || '-'; el.style.color = U.mColor(h[m]); } updDonut(`${m}-${h.id}`, h[m] || 0, U.mColor(h[m])); });
                const ls = document.getElementById(`ls-${h.id}`); if (ls) ls.textContent = 'Last seen: ' + U.ago(h.last_seen);
                fetch(`/api/hosts/${h.id}/?_t=${Date.now()}`).then(r => r.json()).then(d => { const cpuD = d.samples.slice().reverse().slice(-30).map(s => s.cpu); if (charts.sparks[h.id]) { charts.sparks[h.id].data.datasets[0].data = cpuD; charts.sparks[h.id].update('none'); } });
            });
        }
    } catch (e) { console.error(e); }
}

// ─── TAB 2: DETAIL ───
async function loadDetail(id) {
    try {
        const res = await fetch(`/api/hosts/${id}/?_t=${Date.now()}`); const d = await res.json();
        const L = d.samples[0] || { cpu: 0, ram: 0, disk: 0, net_sent: 0, net_recv: 0, ping_ms: 0, cpu_temp: null, cpu_freq: null };
        const penalty = Math.max(0, L.cpu - 50) * 0.5 + Math.max(0, L.ram - 50) * 0.4 + Math.max(0, L.disk - 50) * 0.1;
        const score = Math.max(0, Math.round(100 - penalty)); const sCol = U.mColor(100 - score);
        document.getElementById('dh-score').textContent = score; document.getElementById('dh-score').style.color = sCol;
        if (!charts.health) { charts.health = mkDonut(document.getElementById('dh-ring'), score, sCol); document.getElementById('dh-ring').width = 90; document.getElementById('dh-ring').height = 90; document.getElementById('dh-ring').style.width = '90px'; document.getElementById('dh-ring').style.height = '90px'; charts.health.resize(90, 90); }
        else { charts.health.data.datasets[0].data = [score, 100 - score]; charts.health.data.datasets[0].backgroundColor[0] = sCol; charts.health.update('none'); }

        ['cpu', 'ram', 'disk'].forEach(m => { const v = L[m]; const c = U.mColor(v); document.getElementById(`hb-${m}-fill`).style.width = v + '%'; document.getElementById(`hb-${m}-fill`).style.background = c; document.getElementById(`hb-${m}-val`).textContent = v + '%'; document.getElementById(`hb-${m}-val`).style.color = c; });

        const gauges = [{ l: 'CPU', v: L.cpu, u: '%', i: '⚡' }, { l: 'RAM', v: L.ram, u: '%', i: '🧠' }, { l: 'Disk', v: L.disk, u: '%', i: '💾' }, { l: 'Upload', v: (L.net_sent / 1024).toFixed(1), u: 'KB/s', i: '📤' }, { l: 'Download', v: (L.net_recv / 1024).toFixed(1), u: 'KB/s', i: '📥' }, { l: 'Ping', v: L.ping_ms, u: 'ms', i: '📡' }];
        if (L.cpu_temp) gauges.push({ l: 'Temp', v: L.cpu_temp, u: '°C', i: '🌡️' });
        if (L.cpu_freq) gauges.push({ l: 'Freq', v: L.cpu_freq, u: 'MHz', i: '🔄' });
        if (L.disk_read_kb !== undefined) gauges.push({ l: 'D-Read', v: L.disk_read_kb, u: 'KB/s', i: '📖' });
        if (L.disk_write_kb !== undefined) gauges.push({ l: 'D-Write', v: L.disk_write_kb, u: 'KB/s', i: '✍️' });
        document.getElementById('dgauges').innerHTML = gauges.map(m => `<div class="gauge"><div class="g-lbl">${m.i} ${m.l}</div><div class="g-val">${m.v}<span class="g-unit">${m.u}</span></div></div>`).join('');

        const pCont = document.getElementById('dprocs');
        if (L.top_processes && L.top_processes.length > 0) {
            pCont.innerHTML = L.top_processes.map(p => `<div style="background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.2); padding: 6px 10px; border-radius: 6px; font-size: 0.8rem; color: #e2e8f0; display: flex; align-items: center; gap: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);"><span style="color: #818cf8; font-family: monospace; font-weight: bold;">${p.name}</span><span style="background: rgba(167,139,250,0.15); padding: 2px 6px; border-radius: 4px; color: #c4b5fd;">${p.mem}% RAM</span></div>`).join('');
        } else {
            pCont.innerHTML = '<div style="font-size:0.8rem; color:var(--text-3); font-style: italic; margin-left:10px;">Waiting for process telemetry... (Requires updated agent script)</div>';
        }

        setTimeout(initTilt, 50);

        const samples = d.samples.slice().reverse(); const labels = samples.map(s => U.ftime(s.timestamp));

        // Helper to build a neon canvas gradient fill
        const mkGrad = (ctx, color1, color2) => {
            const g = ctx.chart.ctx.createLinearGradient(0, 0, 0, ctx.chart.height || 240);
            g.addColorStop(0, color1);
            g.addColorStop(0.5, color2);
            g.addColorStop(1, 'transparent');
            return g;
        };

        const cOpts = {
            responsive: true, maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { labels: { color: '#e2e8f0', font: { family: 'Inter', size: 11, weight: '600' }, padding: 18, usePointStyle: true, pointStyle: 'circle' } },
                tooltip: { ...tooltipStyle, mode: 'index', intersect: false }
            },
            scales: {
                x: { grid: { color: 'rgba(99,102,241,0.06)', borderColor: 'transparent' }, ticks: { color: '#64748b', font: { size: 10 } } },
                y: { grid: { color: 'rgba(99,102,241,0.06)', borderColor: 'transparent' }, ticks: { color: '#64748b', font: { size: 10 } } }
            },
            animation: { duration: 0 }
        };

        if (charts.c1) {
            charts.c1.data.labels = labels; charts.c1.data.datasets[0].data = samples.map(s => s.cpu); charts.c1.data.datasets[1].data = samples.map(s => s.ram); charts.c1.update('none');
            charts.c2.data.labels = labels; charts.c2.data.datasets[0].data = samples.map(s => s.disk); charts.c2.data.datasets[1].data = samples.map(s => +(s.net_recv / 1024).toFixed(1)); charts.c2.update('none');
        } else {
            charts.c1 = new Chart(document.getElementById('c1'), {
                type: 'line', data: {
                    labels, datasets: [
                        {
                            label: '⚡ CPU %', data: samples.map(s => s.cpu),
                            borderColor: '#818cf8', borderWidth: 2.5,
                            fill: true, backgroundColor: ctx => mkGrad(ctx, 'rgba(129,140,248,0.35)', 'rgba(129,140,248,0.05)'),
                            pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#818cf8', pointHoverBorderWidth: 2,
                            tension: 0.45,
                        },
                        {
                            label: '🧠 RAM %', data: samples.map(s => s.ram),
                            borderColor: '#e879f9', borderWidth: 2.5,
                            fill: true, backgroundColor: ctx => mkGrad(ctx, 'rgba(232,121,249,0.3)', 'rgba(232,121,249,0.04)'),
                            pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#e879f9', pointHoverBorderWidth: 2,
                            tension: 0.45,
                        }
                    ]
                }, options: cOpts
            });
            charts.c2 = new Chart(document.getElementById('c2'), {
                type: 'line', data: {
                    labels, datasets: [
                        {
                            label: '💾 Disk %', data: samples.map(s => s.disk),
                            borderColor: '#2dd4bf', borderWidth: 2.5,
                            fill: true, backgroundColor: ctx => mkGrad(ctx, 'rgba(45,212,191,0.3)', 'rgba(45,212,191,0.04)'),
                            pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#2dd4bf', pointHoverBorderWidth: 2,
                            tension: 0.45,
                        },
                        {
                            label: '📶 Net KB/s', data: samples.map(s => +(s.net_recv / 1024).toFixed(1)),
                            borderColor: '#fb923c', borderWidth: 2.5,
                            fill: true, backgroundColor: ctx => mkGrad(ctx, 'rgba(251,146,60,0.3)', 'rgba(251,146,60,0.04)'),
                            pointRadius: 0, pointHoverRadius: 5, pointHoverBackgroundColor: '#fff',
                            pointHoverBorderColor: '#fb923c', pointHoverBorderWidth: 2,
                            tension: 0.45,
                        }
                    ]
                }, options: cOpts
            });
        }
    } catch (e) { console.error(e); }
}

// ─── TAB 3: WEBSITES (Colorful) ───
const W_COLORS = [
    { gradient: 'linear-gradient(135deg, rgba(99,102,241,0.12), rgba(139,92,246,0.06))', border: 'rgba(99,102,241,0.2)', accent: '#818cf8' },
    { gradient: 'linear-gradient(135deg, rgba(244,63,94,0.12), rgba(251,113,133,0.06))', border: 'rgba(244,63,94,0.2)', accent: '#fb7185' },
    { gradient: 'linear-gradient(135deg, rgba(52,211,153,0.12), rgba(16,185,129,0.06))', border: 'rgba(52,211,153,0.2)', accent: '#34d399' },
    { gradient: 'linear-gradient(135deg, rgba(251,191,36,0.12), rgba(245,158,11,0.06))', border: 'rgba(251,191,36,0.2)', accent: '#fbbf24' },
    { gradient: 'linear-gradient(135deg, rgba(56,189,248,0.12), rgba(14,165,233,0.06))', border: 'rgba(56,189,248,0.2)', accent: '#38bdf8' },
    { gradient: 'linear-gradient(135deg, rgba(168,85,247,0.12), rgba(192,132,252,0.06))', border: 'rgba(168,85,247,0.2)', accent: '#a855f7' },
];

async function loadWebsites() {
    try {
        const res = await fetch(`/api/websites/?_t=${Date.now()}`); const d = await res.json(); const grid = document.getElementById('web-grid');
        if (!d.websites.length) { grid.innerHTML = `<div class="empty-state"><div class="empty-icon">🌐</div><p class="empty-text">No websites monitored yet.</p></div>`; return; }
        grid.innerHTML = d.websites.map((w, i) => {
            const clr = W_COLORS[i % W_COLORS.length]; const init = (w.name || 'W')[0].toUpperCase();
            const rtC = (w.response_time_ms || 0) > 3000 ? 'var(--crit)' : (w.response_time_ms || 0) > 1000 ? 'var(--warn)' : clr.accent;
            return `<div class="wcard" style="background:${clr.gradient};border:1px solid ${clr.border};--wcard-accent:${clr.accent}">
                <div class="wcard-top">
                    <div style="display:flex;align-items:center;gap:12px;"><div class="wcard-avatar" style="background:${clr.accent}18;color:${clr.accent}">${init}</div><div><div class="wcard-title">${w.name}</div><div class="wcard-url">${w.url}</div></div></div>
                    <div style="display:flex;gap:6px;"><button class="icon-btn" onclick="editWebsite(${w.id},'${w.name.replace(/'/g, "\\'")}','${w.url.replace(/'/g, "\\'")}')" title="Edit">✏️</button><button class="icon-btn icon-btn-danger" onclick="deleteWebsite(${w.id},'${w.name.replace(/'/g, "\\'")}')" title="Delete">🗑️</button></div>
                </div>
                <div class="wcard-status-row"><div class="wbadge" style="background:var(--${w.is_up ? 'ok-dim' : 'crit-dim'});color:var(--${w.is_up ? 'ok' : 'crit'})"><span class="wbadge-dot" style="background:var(--${w.is_up ? 'ok' : 'crit'})"></span>${w.is_up ? 'ONLINE' : 'OFFLINE'}</div><div class="wcard-rt" style="color:${rtC}">${w.response_time_ms || 0}<span class="g-unit">ms</span></div></div>
                <div class="wcard-stats"><div class="wstat"><div class="wstat-bar-track"><div class="wstat-bar-fill" style="width:${w.uptime_24h}%;background:${clr.accent}"></div></div><div class="wstat-row"><span class="wstat-lbl">Uptime 24h</span><span class="wstat-val" style="color:${clr.accent}">${w.uptime_24h}%</span></div></div><div class="wstat-row" style="margin-top:6px;"><span class="wstat-lbl">SSL</span><span class="wstat-val" style="color:var(--${w.ssl_valid ? (w.ssl_expiry_days !== null && w.ssl_expiry_days < 14 ? 'warn' : 'ok') : 'crit'});font-size:0.8rem;">${w.ssl_valid ? (w.ssl_expiry_days !== null ? `🔒 Valid (${w.ssl_expiry_days}d)` : '🔒 Valid') : '⚠️ Invalid'}</span></div></div>
            </div>`;
        }).join('');
        staggerCards(grid); setTimeout(initTilt, 100);
    } catch (e) { console.error(e); }
}

// ─── TAB 4: ADVICE (Compact) ───
let _lastAdviceLen = -1;
async function loadAdvice() {
    try {
        const res = await fetch(`/api/advice/?_t=${Date.now()}`); const d = await res.json(); const c = document.getElementById('adv-list');
        if (!d.advice.length) { c.innerHTML = `<div class="empty-state"><div class="empty-icon">✨</div><p class="empty-text">All systems healthy.</p></div>`; _lastAdviceLen = 0; return; }
        if (_lastAdviceLen === d.advice.length) return; // Prevent layout trashing/re-animating
        _lastAdviceLen = d.advice.length;

        c.innerHTML = d.advice.map((a, i) => `
            <div class="advice-card sev-${a.severity}" data-metric="${a.metric}" data-host="${a.host}">
                <div class="adv-header">
                    <div class="adv-icon-wrap" style="background:${U.sevBg(a.severity)}"><span class="adv-icon">${U.mIcon(a.metric)}</span></div>
                    <div class="adv-header-text">
                        <div class="adv-title">${a.what_happened}</div>
                        <div class="adv-meta"><span class="adv-source-badge" style="background:${a.source === 'website' ? 'rgba(244,114,182,0.1);color:#f472b6' : 'rgba(99,102,241,0.1);color:#818cf8'}">${a.source === 'website' ? '🌐 Web' : '🖥️ Device'}</span><span>${a.host}</span><span style="color:var(--text-3)">·</span><span>${U.fdate(a.timestamp)}</span></div>
                    </div>
                    <div class="adv-urgency" style="background:${U.sevBg(a.severity)};color:${U.sevColor(a.severity)}">${a.urgency}</div>
                </div>
                <div class="adv-body">
                    <div class="adv-col"><h4>⚠️ Why This Matters</h4><p class="adv-text">${a.why_it_matters}</p></div>
                    <div class="adv-col"><h4>🛠️ Actions</h4><ol class="adv-list">${a.recommended_actions.map((r, j) => `<li><span class="step-num">${j + 1}</span>${r}</li>`).join('')}</ol></div>
                </div>
            </div>
        `).join('');
        initStackCards(c);
    } catch (e) { console.error(e); }
}

// ─── TAB 5: ALERTS → Click goes to Advice ───
let _lastAnomLen = -1;
async function loadAnoms() {
    try {
        const res = await fetch(`/api/anomalies/?_t=${Date.now()}`); const d = await res.json(); const c = document.getElementById('alert-list');
        if (!d.events.length) { c.innerHTML = '<div class="empty-state"><div class="empty-icon">🔔</div><p class="empty-text">No alerts.</p></div>'; _lastAnomLen = 0; return; }
        if (_lastAnomLen === d.events.length) return; // Prevent layout trashing/re-animating
        _lastAnomLen = d.events.length;

        c.innerHTML = d.events.map(e => {
            const isNet = e.metric_name === 'net_sent' || e.metric_name === 'net_recv';
            const dv = isNet ? (e.value / 1024).toFixed(1) + ' KB/s' : e.value + (e.metric_name === 'ping_ms' ? 'ms' : '%');

            const resolvedCls = e.is_resolved ? ' resolved' : '';
            const resolvedBadge = e.is_resolved ? `<span class="adv-source-badge" style="background:var(--ok-dim);color:var(--ok);margin-left:8px;font-size:0.65rem;font-weight:bold;border:1px solid rgba(52,211,153,0.2)">✓ RESOLVED</span>` : '';
            const mColor = e.is_resolved ? 'var(--text-3)' : U.sevColor(e.severity);
            const vColor = e.is_resolved ? 'var(--text-3)' : '';

            return `<div class="alert-card${resolvedCls}" onclick="goToAdvice('${e.metric_name}','${e.host}')"><div class="alert-sev" style="background:${U.sevColor(e.severity)}"></div><div class="alert-content"><div class="alert-main"><span style="color:${mColor};font-weight:700">${U.mName(e.metric_name)}</span> <span style="color:var(--text-3)">spiked to</span> <strong class="metric-val" style="color:${vColor}">${dv}</strong> <span style="color:var(--text-3)">on</span> <strong style="color:var(--text-2)">${e.host}</strong>${resolvedBadge}</div></div><div class="alert-time">${U.fdate(e.timestamp)}</div></div>`;
        }).join('');
        initStackCards(c);
    } catch (e) { console.error(e); }
}

// ═══ ALERT → ADVICE NAVIGATION ═══
function goToAdvice(metric, host) {
    switchTab('advice');
    // Wait for advice to load, then scroll to matching card
    setTimeout(() => {
        const cards = document.querySelectorAll('.advice-card');
        for (const card of cards) {
            if (card.dataset.metric === metric || card.dataset.host === host) {
                card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                card.style.boxShadow = '0 0 0 2px rgba(99,102,241,0.5), 0 8px 28px rgba(0,0,0,0.3)';
                setTimeout(() => { card.style.boxShadow = ''; }, 2500);
                break;
            }
        }
    }, 600);
}

// ─── MODALS ───
function openAddDevice() {
    document.getElementById('modal-device').style.display = 'flex';
    document.getElementById('inp-hostname').addEventListener('input', function (e) {
        document.getElementById('lbl-ph').textContent = e.target.value.trim() || 'name';
    });
}
function closeAddDevice() { document.getElementById('modal-device').style.display = 'none'; document.getElementById('btn-add-dev').style.display = ''; }
function openAddWeb() { document.getElementById('modal-web').style.display = 'flex'; }
function closeAddWeb() { document.getElementById('modal-web').style.display = 'none'; }
function openWebhook() { document.getElementById('modal-webhook').style.display = 'flex'; }
function closeWebhook() { document.getElementById('modal-webhook').style.display = 'none'; }

async function submitWebhook() {
    const u = document.getElementById('inp-webhook').value.trim();
    const res = await fetch('/api/set-webhook/', { method: 'POST', body: JSON.stringify({ url: u }) });
    const data = await res.json();
    if (data.error) { alert(data.error); return; }
    alert(data.msg);
    closeWebhook();
}

async function submitDevice() { const hn = document.getElementById('inp-hostname').value.trim(); if (!hn) return; const res = await fetch('/api/add-host/', { method: 'POST', body: JSON.stringify({ hostname: hn }) }); const data = await res.json(); if (data.error) { alert(data.error); return; } const blob = new Blob([data.agent_config], { type: "text/plain;charset=utf-8" }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `ailexus_agent_${hn}.py`; document.body.appendChild(a); a.click(); document.body.removeChild(a); URL.revokeObjectURL(url); closeAddDevice(); refresh(); }
async function submitWeb() { const n = document.getElementById('inp-wname').value.trim(); const u = document.getElementById('inp-wurl').value.trim(); const k = document.getElementById('inp-wkeyword').value.trim(); if (!n || !u) return; const res = await fetch('/api/add-website/', { method: 'POST', body: JSON.stringify({ name: n, url: u, keyword: k }) }); const data = await res.json(); if (data.error) { alert(data.error); return; } document.getElementById('inp-wkeyword').value = ''; closeAddWeb(); if (tab === 'websites') loadWebsites(); }

// ─── CRUD ───
async function deleteWebsite(id, name) { if (!confirm(`Remove "${name}" from monitoring?`)) return; await fetch(`/api/websites/${id}/delete/`, { method: 'POST' }); loadWebsites(); }
async function editWebsite(id, name, url) { const nn = prompt('Edit name:', name); if (nn === null) return; const nu = prompt('Edit URL:', url); if (nu === null) return; const nk = prompt('Edit Expected Keyword (Leave blank to disable):', ''); if (nk === null) return; await fetch(`/api/websites/${id}/edit/`, { method: 'POST', body: JSON.stringify({ name: nn, url: nu, keyword: nk }) }); loadWebsites(); }
async function renameHost(id, name) { const nn = prompt('Rename device:', name); if (!nn || nn === name) return; const r = await fetch(`/api/hosts/${id}/rename/`, { method: 'POST', body: JSON.stringify({ hostname: nn }) }); const d = await r.json(); if (d.error) { alert(d.error); return; } builtHosts = new Set(); loadHosts(); }
async function deleteHost(id, name) { if (!confirm(`Delete device "${name}" and all its history?`)) return; await fetch(`/api/hosts/${id}/delete/`, { method: 'POST' }); builtHosts = new Set(); loadHosts(); }

// Init
switchTab('hosts');
