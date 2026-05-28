/* ============================================================
   Hej Assistant — Frontend Application
   ============================================================ */

const API = '';  // Same origin — works on Railway
let selectedBu = 1;
let sessionId = crypto.randomUUID();
let currentUser = null;  // { username, display_name, role, initials }

// ---- Login ----
async function loadLoginUsers() {
    try {
        const res = await fetch(`${API}/api/users`);
        const users = await res.json();
        const grid = document.getElementById('user-grid');
        grid.innerHTML = users.map(u => `
            <div class="user-option" data-username="${u.username}" onclick="selectUser(this, '${u.username}')">
                <div class="user-avatar">${u.initials}</div>
                <div class="user-info">
                    <div class="user-name">${u.display_name}</div>
                    <div class="user-role">${u.role}</div>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load users:', e);
    }
}

function selectUser(el, username) {
    document.querySelectorAll('.user-option').forEach(o => o.classList.remove('selected'));
    el.classList.add('selected');
    document.getElementById('login-username').value = username;
    document.getElementById('login-btn').disabled = false;
    document.getElementById('login-password').focus();
}

function toggleCreateUser() {
    const form = document.getElementById('create-user-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function createUser() {
    const name = document.getElementById('new-user-name').value.trim();
    const role = document.getElementById('new-user-role').value.trim();
    const errEl = document.getElementById('create-user-error');
    errEl.style.display = 'none';
    if (!name) { errEl.textContent = 'Name is required'; errEl.style.display = 'block'; return; }
    try {
        const res = await fetch(`${API}/api/users`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ display_name: name, role: role || 'Team Member' }),
        });
        if (!res.ok) {
            const err = await res.json();
            errEl.textContent = err.detail || 'Failed to create user';
            errEl.style.display = 'block';
            return;
        }
        const newUser = await res.json();
        // Reload user list and auto-select the new user
        document.getElementById('create-user-form').style.display = 'none';
        document.getElementById('new-user-name').value = '';
        document.getElementById('new-user-role').value = '';
        await loadLoginUsers();
        // Select the newly created user
        const newOption = document.querySelector(`.user-option[data-username="${newUser.username}"]`);
        if (newOption) selectUser(newOption, newUser.username);
    } catch {
        errEl.textContent = 'Connection error';
        errEl.style.display = 'block';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const pw = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');
    if (!username) { errEl.textContent = 'Please select a user'; errEl.style.display = 'block'; return; }
    try {
        const res = await fetch(`${API}/api/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password: pw }),
        });
        if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            sessionStorage.setItem('auth_token', data.token);
            sessionStorage.setItem('current_user', JSON.stringify(data.user));
            document.getElementById('login-overlay').classList.add('hidden');
            updateUserDisplay();
        } else {
            errEl.textContent = 'Incorrect password';
            errEl.style.display = 'block';
        }
    } catch {
        errEl.textContent = 'Connection error';
        errEl.style.display = 'block';
    }
}

function updateUserDisplay() {
    if (!currentUser) return;
    const subtitle = document.querySelector('.sidebar .subtitle');
    if (subtitle) subtitle.textContent = `Hej, ${currentUser.display_name.split(' ')[0]}!`;
}

function handleLogout() {
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('current_user');
    currentUser = null;
    document.getElementById('login-overlay').classList.remove('hidden');
    document.getElementById('login-password').value = '';
    document.getElementById('login-username').value = '';
    document.getElementById('login-btn').disabled = true;
    document.getElementById('login-error').style.display = 'none';
    document.querySelectorAll('.user-option').forEach(o => o.classList.remove('selected'));
    const subtitle = document.querySelector('.sidebar .subtitle');
    if (subtitle) subtitle.textContent = 'Your commercial intelligence co-worker';
}

// ---- Initialization ----
document.addEventListener('DOMContentLoaded', () => {
    // Check if already authenticated
    const savedUser = sessionStorage.getItem('current_user');
    if (sessionStorage.getItem('auth_token') && savedUser) {
        currentUser = JSON.parse(savedUser);
        document.getElementById('login-overlay').classList.add('hidden');
        updateUserDisplay();
    }
    loadLoginUsers();
    initTabs();
    loadStores();
});

// ---- Tab navigation ----
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
            tab.classList.add('active');
            const target = document.getElementById('tab-' + tab.dataset.tab);
            if (target) target.classList.add('active');
        });
    });
}

// ---- Store loading ----
async function loadStores() {
    try {
        const res = await fetch(`${API}/api/stores`);
        const stores = await res.json();
        const select = document.getElementById('store-select');
        select.innerHTML = stores.map(s =>
            `<option value="${s.bu_sk}">${s.bu_short_name} (${s.city})</option>`
        ).join('');
        select.addEventListener('change', () => {
            selectedBu = parseInt(select.value);
            sessionId = crypto.randomUUID(); // Reset chat session on store change
            document.getElementById('chat-messages').innerHTML = '';
            loadSnapshot();
            loadDataView();
            loadInsights();
        });
        selectedBu = stores[0].bu_sk;
        loadSnapshot();
        loadHealth();
        loadDataView();
        loadInsights();
    } catch (e) {
        console.error('Failed to load stores:', e);
    }
}

async function loadHealth() {
    try {
        const res = await fetch(`${API}/api/health`);
        const data = await res.json();
        document.getElementById('data-date').textContent = `Data as of: ${data.data_date}`;
    } catch {
        document.getElementById('data-date').textContent = 'Data loading...';
    }
}

// ---- Snapshot cards ----
async function loadSnapshot() {
    const grid = document.getElementById('snapshot-grid');
    const storeLabel = document.getElementById('briefing-store-label');
    const select = document.getElementById('store-select');
    storeLabel.textContent = select.options[select.selectedIndex]?.text || '';

    grid.innerHTML = '<div class="loading"><div class="spinner"></div><p class="loading-text">Loading snapshot...</p></div>';

    try {
        const res = await fetch(`${API}/api/snapshot/${selectedBu}`);
        const data = await res.json();

        const s7 = data.sales_7d;
        const s30 = data.sales_30d;
        const stock = data.stock_alerts;
        const margin = data.margin_7d;

        const deltaClass = (v) => v >= 0 ? 'positive' : 'negative';
        const deltaSign = (v) => v >= 0 ? '+' : '';

        grid.innerHTML = `
            <div class="snapshot-card">
                <div class="card-label">7-Day Sales</div>
                <div class="card-value">${s7.actual_sales_units.toLocaleString()} units</div>
                <div class="card-delta ${deltaClass(s7.gap_percent)}">
                    ${deltaSign(s7.gap_percent)}${s7.gap_percent}% vs forecast
                </div>
            </div>
            <div class="snapshot-card">
                <div class="card-label">7-Day Revenue</div>
                <div class="card-value">€${Math.round(s7.actual_sales_net_euro).toLocaleString()}</div>
                <div class="card-delta ${deltaClass(s7.gap_units)}">
                    ${deltaSign(s7.gap_units)}${Math.round(s7.gap_units)} units gap
                </div>
            </div>
            <div class="snapshot-card">
                <div class="card-label">30-Day Sales</div>
                <div class="card-value">${s30.actual_sales_units.toLocaleString()} units</div>
                <div class="card-delta ${deltaClass(s30.gap_percent)}">
                    ${deltaSign(s30.gap_percent)}${s30.gap_percent}% vs forecast
                </div>
            </div>
            <div class="snapshot-card">
                <div class="card-label">Stock Health</div>
                <div class="card-value">${stock.healthy_count} / ${stock.total_items}</div>
                <div class="card-delta ${stock.out_of_stock_count > 0 ? 'negative' : 'positive'}">
                    🔴 ${stock.out_of_stock_count} OOS · 🟡 ${stock.low_stock_count} low
                </div>
            </div>
            <div class="snapshot-card">
                <div class="card-label">Gross Margin (7d)</div>
                <div class="card-value">${margin.margin_percent}%</div>
                <div class="card-delta neutral">
                    €${Math.round(margin.total_margin_euro).toLocaleString()} margin
                </div>
            </div>
        `;

        // Sidebar metrics
        document.getElementById('sidebar-metrics').innerHTML = `
            <div class="sidebar-metric">
                <div class="metric-value">${s7.actual_sales_units.toLocaleString()}</div>
                <div class="metric-label">7d Units</div>
            </div>
            <div class="sidebar-metric">
                <div class="metric-value">${deltaSign(s7.gap_percent)}${s7.gap_percent}%</div>
                <div class="metric-label">vs Forecast</div>
            </div>
            <div class="sidebar-metric">
                <div class="metric-value">${stock.out_of_stock_count}</div>
                <div class="metric-label">OOS Items</div>
            </div>
            <div class="sidebar-metric">
                <div class="metric-value">${margin.margin_percent}%</div>
                <div class="metric-label">Margin</div>
            </div>
        `;
    } catch (e) {
        grid.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span><h3>Failed to load snapshot</h3><p>${e.message}</p></div>`;
    }
}

// ---- Report generation ----
async function generateReport(forceRefresh = false) {
    const area = document.getElementById('report-area');
    const btn = document.getElementById('btn-generate');
    const pdfBtn = document.getElementById('btn-pdf');
    const warnings = document.getElementById('report-warnings');

    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    if (forceRefresh || !area.querySelector('.report-content')) {
        area.innerHTML = '<div class="loading"><div class="spinner"></div><p class="loading-text">Analysing your store data with AI... This may take 30-60 seconds.</p></div>';
    }
    warnings.style.display = 'none';

    try {
        const res = await fetch(`${API}/api/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bu_sk: selectedBu, force_refresh: forceRefresh }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Report generation failed');
        }

        const data = await res.json();

        // Build report with timestamp header
        let headerHtml = '';
        if (data.generated_at) {
            headerHtml = `<div class="report-meta">
                <span class="report-timestamp">📅 Generated at ${data.generated_at}${data.cached ? ' (cached)' : ''}</span>
                <button class="btn btn-small btn-regenerate" onclick="generateReport(true)">🔄 Regenerate</button>
            </div>`;
        }

        area.innerHTML = headerHtml + '<div class="report-content">' + marked.parse(data.report) + '</div>';
        pdfBtn.style.display = 'inline-flex';

        if (data.warnings && data.warnings.length > 0) {
            warnings.innerHTML = data.warnings.map(w => `<p>${w}</p>`).join('');
            warnings.style.display = 'block';
        }
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><span class="empty-icon">❌</span><h3>Error generating report</h3><p>${e.message}</p></div>`;
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Generate Report';
    }
}

// ---- PDF export ----
async function exportPDF() {
    try {
        const res = await fetch(`${API}/api/export-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bu_sk: selectedBu }),
        });

        if (!res.ok) throw new Error('PDF export failed');

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `daily_briefing.pdf`;
        a.click();
        URL.revokeObjectURL(url);
    } catch (e) {
        alert('PDF export failed: ' + e.message);
    }
}

// ---- Chat ----
function askSuggestion(el) {
    document.getElementById('chat-input').value = el.textContent;
    sendChat();
}

async function sendChat() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    const container = document.getElementById('chat-messages');

    // Add user message
    container.innerHTML += `
        <div class="message user">
            <div class="message-avatar">You</div>
            <div class="message-content">${escapeHtml(message)}</div>
        </div>
    `;

    // Add loading indicator
    const loadingId = 'loading-' + Date.now();
    container.innerHTML += `
        <div class="message assistant" id="${loadingId}">
            <div class="message-avatar">H</div>
            <div class="message-content">
                <div class="loading" style="padding: 8px 0;">
                    <div class="spinner" style="width: 20px; height: 20px;"></div>
                    <p class="loading-text">Analysing...</p>
                </div>
            </div>
        </div>
    `;
    container.scrollTop = container.scrollHeight;

    try {
        const res = await fetch(`${API}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                bu_sk: selectedBu,
                message: message,
            }),
        });

        const loading = document.getElementById(loadingId);

        if (!res.ok) {
            const err = await res.json();
            if (loading) {
                loading.querySelector('.message-content').innerHTML =
                    `<p style="color: rgb(var(--colour-negative));">Error: ${escapeHtml(err.detail || 'Request failed')}</p>`;
            }
            return;
        }

        const data = await res.json();
        if (loading) {
            loading.querySelector('.message-content').innerHTML = marked.parse(data.response);
        }
    } catch (e) {
        const loading = document.getElementById(loadingId);
        if (loading) {
            loading.querySelector('.message-content').innerHTML =
                `<p style="color: rgb(var(--colour-negative));">Connection error: ${escapeHtml(e.message)}</p>`;
        }
    }

    container.scrollTop = container.scrollHeight;
}

function clearChat() {
    document.getElementById('chat-messages').innerHTML = '';
    sessionId = crypto.randomUUID();
    fetch(`${API}/api/chat/reset?session_id=${sessionId}&bu_sk=${selectedBu}`, { method: 'POST' });
}

// ---- Data Explorer ----
async function loadDataView() {
    const view = document.getElementById('data-view-select').value;
    const period = document.getElementById('data-period-select').value;
    const area = document.getElementById('data-table-area');

    area.innerHTML = '<div class="loading"><div class="spinner"></div><p class="loading-text">Loading data...</p></div>';

    try {
        let url, data;

        switch (view) {
            case 'top-articles':
                url = `${API}/api/top-articles/${selectedBu}?period=${period}&n=15`;
                data = await (await fetch(url)).json();
                renderArticlesTable(area, data.articles);
                break;
            case 'hfb':
                url = `${API}/api/hfb-performance/${selectedBu}?period=${period}`;
                data = await (await fetch(url)).json();
                renderHfbTable(area, data.hfbs);
                break;
            case 'stock-alerts':
                url = `${API}/api/stock-alerts/${selectedBu}`;
                data = await (await fetch(url)).json();
                renderStockTable(area, data);
                break;
            case 'availability-risks':
                url = `${API}/api/availability-risks/${selectedBu}`;
                data = await (await fetch(url)).json();
                renderRisksTable(area, data.risks);
                break;
            case 'declining':
                url = `${API}/api/declining-articles/${selectedBu}`;
                data = await (await fetch(url)).json();
                renderDecliningTable(area, data.articles);
                break;
            case 'priorities':
                url = `${API}/api/daily-priorities/${selectedBu}`;
                data = await (await fetch(url)).json();
                renderPrioritiesTable(area, data.actions);
                break;
        }
    } catch (e) {
        area.innerHTML = `<div class="empty-state"><span class="empty-icon">⚠️</span><h3>Failed to load data</h3><p>${e.message}</p></div>`;
    }
}

function renderArticlesTable(container, articles) {
    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No data available</h3></div>';
        return;
    }
    const rows = articles.map((a, i) => `
        <tr>
            <td>${i + 1}</td>
            <td><strong>${a.series || ''}</strong> ${a.description || ''}</td>
            <td>${a.colour || ''}</td>
            <td>${a.total_qty?.toLocaleString() || 0}</td>
            <td>€${Math.round(a.total_net || 0).toLocaleString()}</td>
            <td>€${Math.round(a.margin_euro || 0).toLocaleString()}</td>
            <td>${a.margin_pct || 0}%</td>
        </tr>
    `).join('');
    container.innerHTML = `<table class="data-table">
        <thead><tr><th>#</th><th>Article</th><th>Colour</th><th>Qty</th><th>Net Sales</th><th>Margin €</th><th>Margin %</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function renderHfbTable(container, hfbs) {
    if (!hfbs || hfbs.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No data available</h3></div>';
        return;
    }
    const rows = hfbs.map(h => `
        <tr>
            <td>${h.home_furnishing_business_no || ''}</td>
            <td><strong>${h.home_furnishing_business_name || ''}</strong></td>
            <td>${(h.total_qty || 0).toLocaleString()}</td>
            <td>€${Math.round(h.total_net || 0).toLocaleString()}</td>
            <td>${h.margin_pct || 0}%</td>
            <td class="${(h.growth_pct || 0) >= 0 ? 'card-delta positive' : 'card-delta negative'}">${h.growth_pct !== undefined ? h.growth_pct + '%' : '—'}</td>
        </tr>
    `).join('');
    container.innerHTML = `<table class="data-table">
        <thead><tr><th>HFB #</th><th>Name</th><th>Qty</th><th>Net Sales</th><th>Margin %</th><th>Growth</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function renderStockTable(container, data) {
    const items = [...(data.out_of_stock || []), ...(data.low_stock || [])];
    if (items.length === 0) {
        container.innerHTML = '<div class="empty-state"><span class="empty-icon">🟢</span><h3>All items healthy</h3></div>';
        return;
    }
    const rows = items.map(s => {
        const isOOS = (s.available_stock || 0) <= 0;
        return `
            <tr>
                <td>${s.series || ''} ${s.description || ''}</td>
                <td>${s.available_stock ?? '—'}</td>
                <td>${s.demand_stock ?? '—'}</td>
                <td><span class="badge ${isOOS ? 'badge-critical' : 'badge-warning'}">${isOOS ? '🔴 OOS' : '🟡 Low'}</span></td>
            </tr>
        `;
    }).join('');
    container.innerHTML = `
        <div style="padding: 12px 16px; font-size: 0.85rem; color: rgb(var(--colour-text-and-icon-3));">
            ${data.out_of_stock_count} out of stock · ${data.low_stock_count} low stock · ${data.healthy_count} healthy
        </div>
        <table class="data-table">
        <thead><tr><th>Article</th><th>Available</th><th>Demand</th><th>Status</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function renderRisksTable(container, risks) {
    if (!risks || risks.length === 0) {
        container.innerHTML = '<div class="empty-state"><span class="empty-icon">🟢</span><h3>No immediate risks</h3></div>';
        return;
    }
    const rows = risks.map(r => `
        <tr>
            <td>${r.series || ''} ${r.description || ''}</td>
            <td>${r.current_stock}</td>
            <td>${r.daily_burn_rate}/day</td>
            <td>${r.days_until_oos} days</td>
            <td><span class="badge ${r.severity === 'critical' ? 'badge-critical' : 'badge-warning'}">${r.severity}</span></td>
        </tr>
    `).join('');
    container.innerHTML = `<table class="data-table">
        <thead><tr><th>Article</th><th>Stock</th><th>Burn Rate</th><th>Days Until OOS</th><th>Severity</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function renderDecliningTable(container, articles) {
    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="empty-state"><span class="empty-icon">📈</span><h3>No declining articles</h3></div>';
        return;
    }
    const rows = articles.map(a => `
        <tr>
            <td>${a.series || ''} ${a.description || ''}</td>
            <td>€${Math.round(a.recent_net || 0).toLocaleString()}</td>
            <td>€${Math.round(a.prior_net || 0).toLocaleString()}</td>
            <td class="card-delta negative">${a.change_pct}%</td>
        </tr>
    `).join('');
    container.innerHTML = `<table class="data-table">
        <thead><tr><th>Article</th><th>Recent (7d)</th><th>Prior (7d)</th><th>Change</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function renderPrioritiesTable(container, actions) {
    if (!actions || actions.length === 0) {
        container.innerHTML = '<div class="empty-state"><h3>No priorities generated</h3></div>';
        return;
    }
    const priorityBadge = (p) => {
        const cls = p === 'critical' ? 'badge-critical' : p === 'high' ? 'badge-warning' : 'badge-info';
        return `<span class="badge ${cls}">${p}</span>`;
    };
    const rows = actions.map((a, i) => `
        <tr>
            <td>${i + 1}</td>
            <td>${priorityBadge(a.priority)}</td>
            <td><span class="badge badge-info">${a.category}</span></td>
            <td>${a.action}</td>
        </tr>
    `).join('');
    container.innerHTML = `<table class="data-table">
        <thead><tr><th>#</th><th>Priority</th><th>Category</th><th>Action</th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

// ---- Utilities ----
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ---- Proactive Insights ----
async function loadInsights() {
    const banner = document.getElementById('insights-banner');
    try {
        const res = await fetch(`${API}/api/insights/${selectedBu}`);
        const data = await res.json();
        const insights = data.insights || [];

        if (insights.length === 0) {
            banner.style.display = 'none';
            return;
        }

        // Fetch existing actions for this store
        const actionsRes = await fetch(`${API}/api/alerts/actions/${selectedBu}`);
        const actions = await actionsRes.json();

        banner.style.display = 'block';
        const critCount = data.critical_count || 0;
        const warnCount = data.warning_count || 0;
        document.getElementById('insights-count').textContent =
            `${critCount} critical · ${warnCount} warning`;

        const list = document.getElementById('insights-list');
        list.innerHTML = insights.map((i, idx) => {
            const action = actions[String(idx)];
            const actionedHtml = action
                ? `<div class="insight-actioned">
                       <span class="actioned-badge">✅ Action taken by <strong>${escapeHtml(action.actioned_by)}</strong> at ${action.actioned_at}</span>
                       <button class="btn btn-tiny" onclick="undoAlertAction(${idx})">Undo</button>
                   </div>`
                : `<button class="btn btn-small btn-action" onclick="markAlertActioned(${idx})">✋ Mark as actioned</button>`;
            return `
            <div class="insight-item severity-${i.severity} ${action ? 'actioned' : ''}">
                <span class="insight-icon">${i.icon || '⚡'}</span>
                <div class="insight-content">
                    <div class="insight-title">${escapeHtml(i.title)}</div>
                    <div class="insight-message">${escapeHtml(i.message)}</div>
                    <div class="insight-action">→ ${escapeHtml(i.action)}</div>
                    ${actionedHtml}
                </div>
                <span class="insight-badge badge-${i.severity}">${i.severity}</span>
            </div>
        `}).join('');
    } catch (e) {
        banner.style.display = 'none';
    }
}

async function markAlertActioned(alertIndex) {
    if (!currentUser) { alert('Please log in first'); return; }
    try {
        await fetch(`${API}/api/alerts/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bu_sk: selectedBu, alert_index: alertIndex, username: currentUser.username }),
        });
        loadInsights();  // Refresh to show updated state
    } catch (e) {
        console.error('Failed to mark alert:', e);
    }
}

async function undoAlertAction(alertIndex) {
    try {
        await fetch(`${API}/api/alerts/action?bu_sk=${selectedBu}&alert_index=${alertIndex}`, { method: 'DELETE' });
        loadInsights();
    } catch (e) {
        console.error('Failed to undo alert action:', e);
    }
}

function toggleInsights() {
    const list = document.getElementById('insights-list');
    const btn = document.getElementById('insights-toggle');
    if (list.style.display === 'none') {
        list.style.display = 'flex';
        btn.textContent = 'Hide';
    } else {
        list.style.display = 'none';
        btn.textContent = 'Show';
    }
}


