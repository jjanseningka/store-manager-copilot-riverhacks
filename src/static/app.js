/* ============================================================
   Hej Assistant — Frontend Application
   ============================================================ */

const API = '';  // Same origin — works on Railway
let selectedBu = 1;
let sessionId = crypto.randomUUID();

// ---- Initialization ----
document.addEventListener('DOMContentLoaded', () => {
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
            // Load what-if context on tab switch
            if (tab.dataset.tab === 'whatif') loadExternalContext();
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
async function generateReport() {
    const area = document.getElementById('report-area');
    const btn = document.getElementById('btn-generate');
    const pdfBtn = document.getElementById('btn-pdf');
    const warnings = document.getElementById('report-warnings');

    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    area.innerHTML = '<div class="loading"><div class="spinner"></div><p class="loading-text">Analysing your store data with AI... This may take 30-60 seconds.</p></div>';
    warnings.style.display = 'none';

    try {
        const res = await fetch(`${API}/api/report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bu_sk: selectedBu }),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Report generation failed');
        }

        const data = await res.json();
        area.innerHTML = marked.parse(data.report);
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

        banner.style.display = 'block';
        const critCount = data.critical_count || 0;
        const warnCount = data.warning_count || 0;
        document.getElementById('insights-count').textContent =
            `${critCount} critical · ${warnCount} warning`;

        const list = document.getElementById('insights-list');
        list.innerHTML = insights.map(i => `
            <div class="insight-item severity-${i.severity}">
                <span class="insight-icon">${i.icon || '⚡'}</span>
                <div class="insight-content">
                    <div class="insight-title">${escapeHtml(i.title)}</div>
                    <div class="insight-message">${escapeHtml(i.message)}</div>
                    <div class="insight-action">→ ${escapeHtml(i.action)}</div>
                </div>
                <span class="insight-badge badge-${i.severity}">${i.severity}</span>
            </div>
        `).join('');
    } catch (e) {
        banner.style.display = 'none';
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

// ---- External Context ----
async function loadExternalContext() {
    const grid = document.getElementById('context-grid');
    try {
        const res = await fetch(`${API}/api/external-context/${selectedBu}`);
        const data = await res.json();
        const seasonal = data.seasonal || {};
        const events = data.upcoming_events || [];
        const promos = data.active_promotions || [];

        let cards = '';

        cards += `
            <div class="context-card">
                <h4>🌤️ Season</h4>
                <p>${seasonal.season || '—'}: ${seasonal.trend || ''}</p>
                <small>${seasonal.demand_label || ''} (${seasonal.demand_factor || 1}x)</small>
            </div>
        `;

        if (events.length > 0) {
            const eventList = events.slice(0, 3).map(e =>
                `${e.name} (in ${e.days_until}d)`
            ).join(', ');
            cards += `
                <div class="context-card">
                    <h4>📅 Upcoming Events</h4>
                    <p>${eventList}</p>
                </div>
            `;
        }

        if (promos.length > 0) {
            const promoList = promos.map(p =>
                `${p.name} (${p.discount_pct}% off, ${p.days_remaining}d left)`
            ).join(', ');
            cards += `
                <div class="context-card">
                    <h4>🏷️ Active Promotions</h4>
                    <p>${promoList}</p>
                </div>
            `;
        } else {
            cards += `
                <div class="context-card">
                    <h4>🏷️ Promotions</h4>
                    <p>No active promotions</p>
                </div>
            `;
        }

        cards += `
            <div class="context-card">
                <h4>🌍 Region</h4>
                <p>${data.region || '—'}</p>
            </div>
        `;

        grid.innerHTML = cards;
    } catch (e) {
        grid.innerHTML = `<p>Failed to load context: ${e.message}</p>`;
    }
}

// ---- What-If Analysis ----
async function runPriceWhatIf() {
    const itemNo = parseInt(document.getElementById('whatif-item-no').value);
    const pricePct = parseFloat(document.getElementById('whatif-price-pct').value);
    const result = document.getElementById('whatif-price-result');

    if (!itemNo || isNaN(pricePct)) {
        result.innerHTML = '<p style="color: rgb(var(--colour-negative));">Please enter article number and price change %.</p>';
        return;
    }

    result.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/api/whatif/price/${selectedBu}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ item_no: itemNo, price_change_pct: pricePct }),
        });
        const data = await res.json();

        if (data.error) {
            result.innerHTML = `<p style="color: rgb(var(--colour-negative));">${escapeHtml(data.error)}</p>`;
            return;
        }

        const c = data.current;
        const p = data.projected;
        const d = data.delta;
        const deltaClass = (v) => v >= 0 ? 'positive' : 'negative';
        const sign = (v) => v >= 0 ? '+' : '';

        result.innerHTML = `
            <p><strong>${escapeHtml(data.article)}</strong> — ${escapeHtml(data.scenario)}</p>
            <div class="whatif-result-grid">
                <div class="whatif-metric">
                    <div class="label">Current Revenue</div>
                    <div class="value">€${Math.round(c.gross_euro).toLocaleString()}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Projected Revenue</div>
                    <div class="value">€${Math.round(p.gross_euro).toLocaleString()}</div>
                    <div class="delta ${deltaClass(d.revenue_change_euro)}">${sign(d.revenue_change_euro)}€${Math.round(d.revenue_change_euro).toLocaleString()}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Current Volume</div>
                    <div class="value">${c.qty.toLocaleString()} units</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Projected Volume</div>
                    <div class="value">${p.qty.toLocaleString()} units</div>
                    <div class="delta ${deltaClass(d.qty_change)}">${sign(d.qty_change)}${d.qty_change} units (${p.volume_change_pct}%)</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Current Margin</div>
                    <div class="value">€${Math.round(c.margin_euro).toLocaleString()}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Projected Margin</div>
                    <div class="value">€${Math.round(p.margin_euro).toLocaleString()}</div>
                    <div class="delta ${deltaClass(d.margin_change_euro)}">${sign(d.margin_change_euro)}€${Math.round(d.margin_change_euro).toLocaleString()}</div>
                </div>
            </div>
            <p style="font-size: 0.8rem; color: rgb(var(--colour-text-and-icon-3)); margin-top: 8px;">${data.note}</p>
        `;
    } catch (e) {
        result.innerHTML = `<p style="color: rgb(var(--colour-negative));">Error: ${e.message}</p>`;
    }
}

async function runAvailabilityWhatIf() {
    const result = document.getElementById('whatif-availability-result');
    result.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/api/whatif/availability/${selectedBu}`);
        const data = await res.json();

        if (data.message) {
            result.innerHTML = `<p style="color: rgb(var(--colour-positive));">🟢 ${escapeHtml(data.message)}</p>`;
            return;
        }

        let topItems = '';
        if (data.top_items && data.top_items.length > 0) {
            const rows = data.top_items.map(i => `
                <tr><td>${escapeHtml(i.article)}</td><td>€${Math.round(i.est_daily_revenue_euro).toLocaleString()}/day</td></tr>
            `).join('');
            topItems = `<table class="data-table" style="margin-top: 12px;">
                <thead><tr><th>Article</th><th>Est. Daily Revenue</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
        }

        result.innerHTML = `
            <div class="whatif-result-grid">
                <div class="whatif-metric">
                    <div class="label">OOS Items</div>
                    <div class="value">${data.oos_item_count}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Daily Uplift</div>
                    <div class="value delta positive">+€${Math.round(data.estimated_daily_uplift_euro).toLocaleString()}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Weekly Uplift</div>
                    <div class="value delta positive">+€${Math.round(data.estimated_weekly_uplift_euro).toLocaleString()}</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Monthly Uplift</div>
                    <div class="value delta positive">+€${Math.round(data.estimated_monthly_uplift_euro).toLocaleString()}</div>
                </div>
            </div>
            ${topItems}
        `;
    } catch (e) {
        result.innerHTML = `<p style="color: rgb(var(--colour-negative));">Error: ${e.message}</p>`;
    }
}

async function runDemandWhatIf() {
    const demandPct = parseFloat(document.getElementById('whatif-demand-pct').value);
    const result = document.getElementById('whatif-demand-result');

    if (isNaN(demandPct)) {
        result.innerHTML = '<p style="color: rgb(var(--colour-negative));">Please enter demand increase %.</p>';
        return;
    }

    result.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

    try {
        const res = await fetch(`${API}/api/whatif/demand/${selectedBu}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ demand_increase_pct: demandPct }),
        });
        const data = await res.json();

        let risksTable = '';
        if (data.items_at_risk && data.items_at_risk.length > 0) {
            const rows = data.items_at_risk.slice(0, 10).map(r => `
                <tr>
                    <td>${escapeHtml(r.article)}</td>
                    <td>${r.current_stock}</td>
                    <td>${r.normal_daily_rate}/day</td>
                    <td>${r.surge_daily_rate}/day</td>
                    <td><span class="badge ${r.days_cover_surge < 3 ? 'badge-critical' : 'badge-warning'}">${r.days_cover_surge}d</span></td>
                </tr>
            `).join('');
            risksTable = `<table class="data-table" style="margin-top: 12px;">
                <thead><tr><th>Article</th><th>Stock</th><th>Normal Rate</th><th>Surge Rate</th><th>Days Cover</th></tr></thead>
                <tbody>${rows}</tbody>
            </table>`;
        }

        result.innerHTML = `
            <div class="whatif-result-grid">
                <div class="whatif-metric">
                    <div class="label">Scenario</div>
                    <div class="value">+${demandPct}% demand</div>
                </div>
                <div class="whatif-metric">
                    <div class="label">Items at Risk</div>
                    <div class="value ${data.at_risk_count > 0 ? 'delta negative' : ''}">${data.at_risk_count} / ${data.total_items_analysed}</div>
                </div>
            </div>
            ${risksTable || '<p style="color: rgb(var(--colour-positive)); margin-top: 8px;">🟢 All items have sufficient stock for this scenario.</p>'}
            <p style="font-size: 0.8rem; color: rgb(var(--colour-text-and-icon-3)); margin-top: 8px;">${data.note || ''}</p>
        `;
    } catch (e) {
        result.innerHTML = `<p style="color: rgb(var(--colour-negative));">Error: ${e.message}</p>`;
    }
}
