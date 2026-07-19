// API Endpoints
const API_STATUS_URL = "/api/dataset/status";
const API_RELOAD_URL = "/api/dataset/reload";
const API_EXPLORER_DATASETS = "/api/explorer/datasets";
const API_EXPLORER_QUERY = "/api/explorer/query";
const API_EXPLORER_PROFILE = "/api/explorer/column-profile";
const API_DASHBOARD_URL = "/api/analytics/dashboard";

// Global state holding loaded dataset report details
let currentReport = null;

// Explorer query states
let explorerState = {
    datasetName: "",
    columns: [], // Array of {name, type}
    records: [],
    totalRecords: 0,
    page: 1,
    pageSize: 10,
    sortBy: null,
    sortOrder: "asc",
    searchQuery: "",
    filters: [] // Array of {column, operator, value}
};

let searchDebounceTimer = null;

document.addEventListener("DOMContentLoaded", () => {
    console.log("[Observability] Layout Initialized");
    initNavigation();
    console.log("[Observability] Navigation Loaded");
    fetchDatasetStatus();
    initCollapsibleSidebar();
    if (typeof initWorkspaceGlobalUX === 'function') {
        initWorkspaceGlobalUX();
    }
    console.log("[Observability] UI Components Loaded");
});

/**
 * Collapsible Sidebar logic.
 */
function initCollapsibleSidebar() {
    const toggleBtn = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("sidebar");
    
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            
            // Flip chevron icon
            const icon = toggleBtn.querySelector("i");
            if (sidebar.classList.contains("collapsed")) {
                icon.className = "fa-solid fa-chevron-right";
                localStorage.setItem("sidebar_state", "collapsed");
            } else {
                icon.className = "fa-solid fa-chevron-left";
                localStorage.setItem("sidebar_state", "expanded");
            }
        });
        
        // Restore preferences
        const savedState = localStorage.getItem("sidebar_state");
        if (savedState === "collapsed") {
            sidebar.classList.add("collapsed");
            const icon = toggleBtn.querySelector("i");
            if (icon) icon.className = "fa-solid fa-chevron-right";
        }
    }
}

// Setup navigation tabs
function initNavigation() {
    const navLinks = document.querySelectorAll(".nav-link");
    const sections = document.querySelectorAll(".viewport-section");
    const headerTitle = document.getElementById("header-title");

    navLinks.forEach(link => {
        link.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = link.getAttribute("data-target");

            // Remove active classes
            navLinks.forEach(l => l.classList.remove("active"));
            sections.forEach(s => s.classList.remove("active"));

            // Add active class to clicked link & target section
            link.classList.add("active");
            document.getElementById(targetId).classList.add("active");

            // Update Header Title
            if (targetId === "overview-section") {
                headerTitle.textContent = "Platform Overview";
            } else if (targetId === "dashboard-section") {
                headerTitle.textContent = "Executive Analytics Dashboard";
                loadExecutiveDashboard();
            } else if (targetId === "dataset-section") {
                headerTitle.textContent = "Dataset Loading & Validation";
            } else if (targetId === "explorer-section") {
                headerTitle.textContent = "Enterprise Dataset Explorer";
                loadExplorerDatasets();
            } else if (targetId === "network-map-section") {
                headerTitle.textContent = "Logistics Network Map";
                loadNetworkMap();
            } else if (targetId === "routes-section") {
                headerTitle.textContent = "Route Intelligence & Network Analysis";
                loadRouteIntelligence();
            } else if (targetId === "performance-section") {
                headerTitle.textContent = "Logistics Performance Monitoring";
                loadLogisticsPerformance();
            } else if (targetId === "workspace-section") {
                headerTitle.textContent = "AI Insights Workspace";
                loadWorkspace();
            } else if (targetId === "executive-section") {
                headerTitle.textContent = "Executive Command Center";
                loadExecutiveCommandCenter();
            } else if (targetId === "admin-section") {
                headerTitle.textContent = "Administration & Operations Center";
                loadAdminCenter();
            }
        });
    });
}

function navigateToDataset() {
    const datasetLink = document.getElementById("nav-dataset");
    if (datasetLink) {
        datasetLink.click();
    }
}

// Fetch current dataset loading and validation status
async function fetchDatasetStatus() {
    const apiIndicator = document.getElementById("api-status");
    try {
        const [datasetRes, repositoryRes, pipelineRes] = await Promise.all([
            fetch(API_STATUS_URL),
            fetch("/api/repository/status"),
            fetch("/api/pipeline/report")
        ]);

        if (!datasetRes.ok || !repositoryRes.ok || !pipelineRes.ok) {
            throw new Error("HTTP error fetching platform status");
        }

        const datasetData = await datasetRes.json();
        const repositoryData = await repositoryRes.json();
        const pipelineData = await pipelineRes.json();
        
        // Update connection status UI
        apiIndicator.className = "status-indicator connected";
        apiIndicator.querySelector(".status-text").textContent = "Connected to API";
        
        currentReport = datasetData;
        renderDashboard(datasetData);
        renderRepository(repositoryData);
        renderPipeline(pipelineData);
        
        // Load real-time system monitoring details
        await loadSystemMonitoring();
        
    } catch (error) {
        console.error("API Connection Error:", error);
        apiIndicator.className = "status-indicator";
        apiIndicator.querySelector(".status-text").textContent = "API Offline";
        renderOfflineState();
    }
}

/**
 * Fetches health data from Phase 28 Enterprise Monitoring service and updates Overview cards.
 */
async function loadSystemMonitoring() {
    try {
        const report = await fetch("/api/v1/monitoring/health").then(r => r.json());
        const moduleList = document.querySelector(".modules-card .module-list");
        if (!moduleList) return;

        moduleList.innerHTML = "";
        report.services.forEach(svc => {
            const isUp = svc.status === "UP";
            const li = document.createElement("li");
            li.className = `module-item ${isUp ? "active" : "disabled"}`;
            li.innerHTML = `
                <span class="module-status ${isUp ? "active" : "degraded"}">
                    <i class="fa-solid ${isUp ? "fa-circle-check" : "fa-circle-exclamation"}"></i>
                </span>
                <div class="module-info">
                    <h4>${svc.name}</h4>
                    <p>${svc.detail} (Latency: ${svc.response_time_ms} ms)</p>
                </div>
            `;
            moduleList.appendChild(li);
        });

        // Also update overview badge at top of overview section
        const badge = document.getElementById("overview-badge");
        if (badge) {
            badge.textContent = report.overall_status;
            badge.className = `badge ${report.overall_status === "UP" ? "success" : "warning"}`;
        }
    } catch (err) {
        console.error("loadSystemMonitoring Error:", err);
    }
}

// Reload and validate workbook on request
async function reloadData() {
    const btn = document.getElementById("btn-reload");
    const icon = document.getElementById("reload-icon");
    const text = document.getElementById("reload-text");
    
    // Set loading state
    btn.disabled = true;
    icon.className = "fa-solid fa-spinner fa-spin";
    text.textContent = "Reloading Workbook...";

    try {
        const reloadRes = await fetch(API_RELOAD_URL, { method: "POST" });
        if (!reloadRes.ok) {
            throw new Error(`HTTP error! status: ${reloadRes.status}`);
        }
        const data = await reloadRes.json();
        currentReport = data;
        renderDashboard(data);

        // Fetch repository and pipeline status concurrently
        const [repositoryRes, pipelineRes] = await Promise.all([
            fetch("/api/repository/status"),
            fetch("/api/pipeline/report")
        ]);
        
        if (repositoryRes.ok) {
            const repositoryData = await repositoryRes.json();
            renderRepository(repositoryData);
        }
        if (pipelineRes.ok) {
            const pipelineData = await pipelineRes.json();
            renderPipeline(pipelineData);
        }
        
        // Brief visual delay for smooth transition
        setTimeout(() => {
            btn.disabled = false;
            icon.className = "fa-solid fa-arrows-rotate";
            text.textContent = "Reload Workbook";
        }, 300);
        
    } catch (error) {
        console.error("Failed to reload dataset:", error);
        alert("Failed to reload workbook. Verify server is running.");
        btn.disabled = false;
        icon.className = "fa-solid fa-arrows-rotate";
        text.textContent = "Reload Workbook";
    }
}

// Render dynamic elements in dashboard
function renderDashboard(data) {
    const metadata = data.metadata;
    const report = data.validation_report;
    
    // Overview Status Card rendering
    const overviewBadge = document.getElementById("overview-badge");
    const overviewTitle = document.getElementById("overview-status-title");
    const overviewDesc = document.getElementById("overview-status-desc");
    const overviewIcon = document.getElementById("overview-status-icon");
    
    // Stats elements
    const metricStatus = document.getElementById("metric-status");
    const metricSheets = document.getElementById("metric-sheet-count");
    const metricErrors = document.getElementById("metric-errors");
    const metricWarnings = document.getElementById("metric-warnings");
    
    // File details row
    const fileStats = document.getElementById("file-details-stats");
    const filePath = document.getElementById("file-details-path");
    
    // Clear lists
    const errorBlock = document.getElementById("errors-log-block");
    const warnBlock = document.getElementById("warnings-log-block");
    const errorList = document.getElementById("errors-log-list");
    const warnList = document.getElementById("warnings-log-list");
    const diagCard = document.getElementById("validation-details-card");
    
    errorList.innerHTML = "";
    warnList.innerHTML = "";
    
    // Default stats
    filePath.textContent = metadata.file_path;
    if (metadata.exists) {
        const sizeMb = (metadata.file_size_bytes / (1024 * 1024)).toFixed(2);
        fileStats.textContent = `Size: ${sizeMb} MB | Last Modified: ${formatDate(metadata.last_modified)}`;
    } else {
        fileStats.textContent = "File not found or unreadable.";
    }

    if (!metadata.exists) {
        // Missing Dataset State
        setOverviewStatus("danger", "Missing", "Dataset File Not Found", "Please check if Dell_Logistics_Route_Optimization.xlsx exists in backend/data/.");
        
        metricStatus.textContent = "Missing";
        metricStatus.className = "metric-value text-danger";
        metricSheets.textContent = "0";
        metricErrors.textContent = "1";
        metricWarnings.textContent = "0";
        
        diagCard.style.display = "block";
        errorBlock.style.display = "block";
        warnBlock.style.display = "none";
        errorList.innerHTML = "<li>CRITICAL: Dataset workbook is missing from the configured path.</li>";
        
        renderSheetsTable(null);
        return;
    }

    if (metadata.is_corrupt || metadata.is_empty) {
        // Corrupt / Empty File State
        const errMsg = metadata.is_empty ? "Dataset workbook is empty." : "Excel workbook is corrupted and cannot be opened.";
        setOverviewStatus("danger", "Corrupt", "Failed to Load Workbook", errMsg);
        
        metricStatus.textContent = "Corrupt";
        metricStatus.className = "metric-value text-danger";
        metricSheets.textContent = "0";
        metricErrors.textContent = "1";
        metricWarnings.textContent = "0";
        
        diagCard.style.display = "block";
        errorBlock.style.display = "block";
        warnBlock.style.display = "none";
        errorList.innerHTML = `<li>CRITICAL: ${errMsg}</li>`;
        
        renderSheetsTable(null);
        return;
    }

    // Active Dataset Case - calculate total issue counts
    let totalErrors = report.global_errors.length;
    let totalWarnings = report.global_warnings.length;
    
    for (const sheetName in report.sheets) {
        const sh = report.sheets[sheetName];
        totalErrors += sh.errors.length;
        totalWarnings += sh.warnings.length;
    }
    
    metricSheets.textContent = metadata.sheet_names.length;
    metricErrors.textContent = totalErrors;
    metricWarnings.textContent = totalWarnings;
    
    // Set validation logs lists
    let allErrors = [...report.global_errors];
    let allWarnings = [...report.global_warnings];
    
    for (const sheetName in report.sheets) {
        const sh = report.sheets[sheetName];
        sh.errors.forEach(e => allErrors.push(`[${sheetName}] ${e}`));
        sh.warnings.forEach(w => allWarnings.push(`[${sheetName}] ${w}`));
    }
    
    if (allErrors.length > 0) {
        diagCard.style.display = "block";
        errorBlock.style.display = "block";
        allErrors.forEach(err => {
            const li = document.createElement("li");
            li.textContent = err;
            errorList.appendChild(li);
        });
    } else {
        errorBlock.style.display = "none";
    }
    
    if (allWarnings.length > 0) {
        diagCard.style.display = "block";
        warnBlock.style.display = "block";
        allWarnings.forEach(wrn => {
            const li = document.createElement("li");
            li.textContent = wrn;
            warnList.appendChild(li);
        });
    } else {
        warnBlock.style.display = "none";
    }
    
    if (allErrors.length === 0 && allWarnings.length === 0) {
        diagCard.style.display = "none";
    }

    // Determine overall status
    if (!report.is_valid) {
        setOverviewStatus("danger", "Invalid", "Validation Failures Encountered", `The workbook contains ${totalErrors} schema errors and ${totalWarnings} warnings.`);
        metricStatus.textContent = "Failures";
        metricStatus.className = "metric-value text-danger";
    } else if (totalWarnings > 0) {
        setOverviewStatus("warning", "Warnings", "Workbook Validation Warnings", `Workbook loaded successfully with ${totalWarnings} quality warnings.`);
        metricStatus.textContent = "Warnings";
        metricStatus.className = "metric-value text-warning";
    } else {
        setOverviewStatus("success", "Valid", "Workbook Loaded & Verified", "The workbook matches all expected column shapes and data types.");
        metricStatus.textContent = "Verified";
        metricStatus.className = "metric-value text-success";
    }

    renderSheetsTable(report.sheets);
}

// Helper to update Welcome/Overview page card status
function setOverviewStatus(badgeClass, badgeText, title, description) {
    const badge = document.getElementById("overview-badge");
    const titleEl = document.getElementById("overview-status-title");
    const descEl = document.getElementById("overview-status-desc");
    const iconEl = document.getElementById("overview-status-icon");

    badge.className = `badge ${badgeClass}`;
    badge.textContent = badgeText;
    titleEl.textContent = title;
    descEl.textContent = description;

    let iconHtml = '<i class="fa-solid fa-triangle-exclamation"></i>';
    if (badgeClass === "success") {
        iconHtml = '<i class="fa-solid fa-circle-check"></i>';
    } else if (badgeClass === "danger") {
        iconHtml = '<i class="fa-solid fa-circle-xmark"></i>';
    }
    
    iconEl.className = `status-icon-box ${badgeClass}`;
    iconEl.innerHTML = iconHtml;
}

// Render the main table listing sheets
function renderSheetsTable(sheetsReport) {
    const tbody = document.getElementById("sheets-table-body");
    tbody.innerHTML = "";
    
    if (!sheetsReport) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-muted">No workbook sheets available. Please check file path.</td>
            </tr>
        `;
        return;
    }

    for (const sheetName in sheetsReport) {
        const sh = sheetsReport[sheetName];
        const tr = document.createElement("tr");
        
        let statusBadge = "";
        let detailsButton = "";
        
        if (!sh.exists) {
            statusBadge = '<span class="badge danger">Missing</span>';
            detailsButton = '<button class="btn btn-secondary" disabled>Unavailable</button>';
        } else if (sh.errors.length > 0) {
            statusBadge = '<span class="badge danger">Schema Error</span>';
            detailsButton = `<button class="btn btn-secondary" onclick="viewSheetDetails('${sheetName}')">Inspect</button>`;
        } else if (sh.warnings.length > 0) {
            statusBadge = '<span class="badge warning">Warnings</span>';
            detailsButton = `<button class="btn btn-secondary" onclick="viewSheetDetails('${sheetName}')">Inspect</button>`;
        } else {
            statusBadge = '<span class="badge success">Valid</span>';
            detailsButton = `<button class="btn btn-secondary" onclick="viewSheetDetails('${sheetName}')">Inspect</button>`;
        }

        tr.innerHTML = `
            <td><strong>${sheetName}</strong></td>
            <td class="text-center">${sh.exists ? sh.row_count : "-"}</td>
            <td class="text-center">${sh.exists ? sh.col_count : "-"}</td>
            <td>${statusBadge}</td>
            <td class="text-center text-danger">${sh.exists ? sh.errors.length : "-"}</td>
            <td class="text-center text-warning">${sh.exists ? sh.warnings.length : "-"}</td>
            <td>${detailsButton}</td>
        `;
        tbody.appendChild(tr);
    }
}

// View schema detailed mapping in a Modal overlay
function viewSheetDetails(sheetName) {
    if (!currentReport || !currentReport.validation_report) return;
    
    const sheetData = currentReport.validation_report.sheets[sheetName];
    if (!sheetData) return;

    document.getElementById("modal-title").textContent = `Schema Audit: ${sheetName}`;
    const tbody = document.getElementById("modal-columns-body");
    tbody.innerHTML = "";

    sheetData.invalid_columns.forEach(col => {
        const tr = document.createElement("tr");
        
        const typeStatus = col.is_valid 
            ? '<span class="text-success"><i class="fa-solid fa-circle-check"></i> Valid</span>' 
            : '<span class="text-danger"><i class="fa-solid fa-circle-xmark"></i> Mismatch</span>';
            
        tr.innerHTML = `
            <td><code>${col.name}</code></td>
            <td><code>${col.expected_type}</code></td>
            <td><code>${col.actual_type}</code></td>
            <td>${typeStatus}</td>
            <td class="text-center ${col.missing_count > 0 ? 'text-warning' : 'text-muted'}">${col.missing_count}</td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById("details-modal").classList.add("active");
}

function closeModal() {
    document.getElementById("details-modal").classList.remove("active");
}

// Fallback visual display when API is offline
function renderOfflineState() {
    setOverviewStatus("danger", "Offline", "FastAPI Server Offline", "Unable to establish connection to the backend service. Ensure `python backend/main.py` is running.");
    
    document.getElementById("metric-status").textContent = "Offline";
    document.getElementById("metric-status").className = "metric-value text-danger";
    document.getElementById("metric-sheet-count").textContent = "-";
    document.getElementById("metric-errors").textContent = "-";
    document.getElementById("metric-warnings").textContent = "-";
    document.getElementById("file-details-path").textContent = "API Server Not Responding";
    document.getElementById("file-details-stats").textContent = "Verify terminal application outputs.";
    
    document.getElementById("sheets-table-body").innerHTML = `
        <tr>
            <td colspan="7" class="text-center text-danger">Connection refused. Ensure backend service port 8000 is open.</td>
        </tr>
    `;
    document.getElementById("validation-details-card").style.display = "none";

    // Reset repository status UI
    document.getElementById("repo-health-badge").className = "badge danger";
    document.getElementById("repo-health-badge").textContent = "Offline";
    document.getElementById("repo-status-text").textContent = "Connection Lost";
    document.getElementById("repo-status-text").className = "detail-value text-danger";
    document.getElementById("repo-health-text").textContent = "OFFLINE";
    document.getElementById("repo-health-text").className = "detail-value text-danger";
    document.getElementById("repo-last-sync").textContent = "-";

    updateStateFlag("flag-dataset", false);
    updateStateFlag("flag-validation", false);
    updateStateFlag("flag-repo", false);
    updateStateFlag("flag-app", false);

    // Reset pipeline status UI
    document.getElementById("pipeline-status-badge").className = "badge danger";
    document.getElementById("pipeline-status-badge").textContent = "Offline";
    document.getElementById("pipeline-status-text").textContent = "OFFLINE";
    document.getElementById("pipeline-status-text").className = "stat-value text-danger";
    document.getElementById("pipeline-duration").textContent = "0.0 ms";
    document.getElementById("pipeline-quality-score").textContent = "0.0%";
    document.getElementById("pipeline-quality-score").className = "stat-value text-danger";
    document.getElementById("pipeline-records-count").textContent = "-";
    document.getElementById("pipeline-report-body").innerHTML = `
        <tr>
            <td colspan="6" class="text-center text-danger">Connection refused. Pipeline offline.</td>
        </tr>
    `;
}

// Render Repository metadata and State Manager flags
function renderRepository(repoData) {
    const state = repoData.state;
    const healthBadge = document.getElementById("repo-health-badge");
    const statusText = document.getElementById("repo-status-text");
    const lastSync = document.getElementById("repo-last-sync");
    const healthText = document.getElementById("repo-health-text");

    // Set badge classes
    if (state.repository_health === "HEALTHY") {
        healthBadge.className = "badge success";
        healthBadge.textContent = "Healthy";
        statusText.textContent = "Ready / Operational";
        statusText.className = "detail-value text-success";
        healthText.textContent = "HEALTHY";
        healthText.className = "detail-value text-success";
    } else if (state.repository_health === "WARNING") {
        healthBadge.className = "badge warning";
        healthBadge.textContent = "Warning";
        statusText.textContent = "Warnings Present";
        statusText.className = "detail-value text-warning";
        healthText.textContent = "WARNING";
        healthText.className = "detail-value text-warning";
    } else {
        healthBadge.className = "badge danger";
        healthBadge.textContent = "Degraded";
        statusText.textContent = "Not Loaded / Offline";
        statusText.className = "detail-value text-danger";
        healthText.textContent = "DEGRADED";
        healthText.className = "detail-value text-danger";
    }

    lastSync.textContent = formatDate(state.last_load_time);

    // Update state flags lists
    updateStateFlag("flag-dataset", state.dataset_loaded);
    updateStateFlag("flag-validation", state.validation_passed);
    updateStateFlag("flag-repo", state.repository_ready);
    updateStateFlag("flag-app", state.application_ready);
}

function updateStateFlag(elementId, isReady) {
    const item = document.getElementById(elementId);
    if (!item) return;

    const icon = item.querySelector(".flag-icon i");
    if (isReady) {
        item.className = "state-flag-item ready";
        icon.className = "fa-solid fa-circle-check";
    } else {
        item.className = "state-flag-item not-ready";
        icon.className = "fa-solid fa-circle-xmark";
    }
}

// Render Processing Pipeline report and metrics
function renderPipeline(pipelineData) {
    const badge = document.getElementById("pipeline-status-badge");
    const statusText = document.getElementById("pipeline-status-text");
    const duration = document.getElementById("pipeline-duration");
    const score = document.getElementById("pipeline-quality-score");
    const records = document.getElementById("pipeline-records-count");
    const tbody = document.getElementById("pipeline-report-body");

    if (pipelineData.status === "FAILED") {
        badge.className = "badge danger";
        badge.textContent = "Failed";
        statusText.textContent = "FAILED";
        statusText.className = "stat-value text-danger";
        duration.textContent = "-";
        score.textContent = "-";
        records.textContent = "-";
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">${pipelineData.message || 'Pipeline execution failed.'}</td>
            </tr>
        `;
        return;
    }

    const summary = pipelineData.summary;
    
    // Update badge status
    if (summary.status === "SUCCESS") {
        badge.className = "badge success";
        badge.textContent = "Success";
        statusText.textContent = "SUCCESS";
        statusText.className = "stat-value text-success";
    } else if (summary.status === "WARNING") {
        badge.className = "badge warning";
        badge.textContent = "Warnings";
        statusText.textContent = "WARNING";
        statusText.className = "stat-value text-warning";
    } else {
        badge.className = "badge danger";
        badge.textContent = "Failed";
        statusText.textContent = "FAILED";
        statusText.className = "stat-value text-danger";
    }

    duration.textContent = `${summary.duration_ms} ms`;
    records.textContent = summary.rows_processed;
    score.textContent = `${summary.quality_score}%`;
    
    if (summary.quality_score >= 90) {
        score.className = "stat-value text-success";
    } else if (summary.quality_score >= 70) {
        score.className = "stat-value text-warning";
    } else {
        score.className = "stat-value text-danger";
    }

    // Render detailed sheet table rows
    tbody.innerHTML = "";
    const sheetSummaries = pipelineData.sheet_summaries;
    
    for (const sheetName in sheetSummaries) {
        const sh = sheetSummaries[sheetName];
        const tr = document.createElement("tr");
        
        let statusBadge = "";
        if (sh.status === "SUCCESS") {
            statusBadge = '<span class="badge success">Success</span>';
        } else if (sh.status === "WARNING") {
            statusBadge = '<span class="badge warning">Warning</span>';
        } else {
            statusBadge = '<span class="badge danger">Failed</span>';
        }

        tr.innerHTML = `
            <td><strong>${sheetName}</strong></td>
            <td class="text-center">${sh.rows_processed}</td>
            <td class="text-center ${sh.missing_values_handled > 0 ? 'text-warning' : 'text-muted'}">${sh.missing_values_handled}</td>
            <td class="text-center ${sh.duplicates_removed > 0 ? 'text-warning' : 'text-muted'}">${sh.duplicates_removed}</td>
            <td class="text-center"><strong>${sh.quality_score}%</strong></td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    }
}

// Format Datetime stamps helper
function formatDate(isoStr) {
    if (!isoStr) return "-";
    try {
        const d = new Date(isoStr);
        return d.toLocaleString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });
    } catch {
        return isoStr;
    }
}

// ==========================================
// DATASET EXPLORER CONTROLLER & BINDINGS
// ==========================================

async function loadExplorerDatasets() {
    try {
        const res = await fetch(API_EXPLORER_DATASETS);
        if (!res.ok) throw new Error("Failed to load explorer datasets list");
        const datasets = await res.json();
        
        const select = document.getElementById("dataset-select");
        const currentVal = select.value;
        select.innerHTML = '<option value="">-- Select a Dataset --</option>';
        
        datasets.forEach(ds => {
            const opt = document.createElement("option");
            opt.value = ds;
            opt.textContent = ds.replace(/_/g, ' ');
            select.appendChild(opt);
        });
        
        if (currentVal && datasets.includes(currentVal)) {
            select.value = currentVal;
        }
    } catch (err) {
        console.error("loadExplorerDatasets Error:", err);
    }
}

async function onDatasetChange() {
    const select = document.getElementById("dataset-select");
    const name = select.value;
    
    explorerState.datasetName = name;
    explorerState.page = 1;
    explorerState.sortBy = null;
    explorerState.sortOrder = "asc";
    explorerState.searchQuery = "";
    explorerState.filters = [];
    
    // Clear DOM controls
    document.getElementById("explorer-search").value = "";
    document.getElementById("filter-rows-container").innerHTML = "";
    document.getElementById("filter-actions-bar").style.display = "none";
    
    // Reset Inspector panel
    resetColumnInspector();
    
    if (!name) {
        resetExplorerTable("Please select a dataset to start browsing.");
        resetExplorerSummary();
        return;
    }
    
    console.log("Dataset Selected:", name);
    
    try {
        // Fetch summary & columns
        const [summaryRes, columnsRes] = await Promise.all([
            fetch(`/api/explorer/summary/${name}`),
            fetch(`/api/explorer/columns/${name}`)
        ]);
        
        if (!summaryRes.ok || !columnsRes.ok) throw new Error("Failed fetching metadata");
        
        const summary = await summaryRes.json();
        const columns = await columnsRes.json();
        
        explorerState.columns = columns;
        
        // Render summary
        renderExplorerSummary(summary);
        
        // Load table rows
        await fetchQueryResults();
        
    } catch (err) {
        console.error("onDatasetChange Error:", err);
        resetExplorerTable("Failed loading metadata details for " + name);
        resetExplorerSummary();
    }
}

async function fetchQueryResults() {
    if (!explorerState.datasetName) return;
    
    const tbody = document.getElementById("explorer-table-body");
    tbody.innerHTML = `
        <tr>
            <td colspan="100" class="text-center" style="padding: 4rem;">
                <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2rem; color: var(--primary-color);"></i>
                <p style="margin-top: 1rem;">Loading query results...</p>
            </td>
        </tr>
    `;
    
    try {
        const payload = {
            page: explorerState.page,
            page_size: explorerState.pageSize,
            sort_by: explorerState.sortBy,
            sort_order: explorerState.sortOrder,
            search_query: explorerState.searchQuery,
            filters: explorerState.filters
        };
        
        const res = await fetch(`${API_EXPLORER_QUERY}/${explorerState.datasetName}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error("Query execution failed");
        
        const data = await res.json();
        explorerState.records = data.records;
        explorerState.totalRecords = data.total_records;
        
        renderExplorerTable();
        renderExplorerPagination();
    } catch (err) {
        console.error("fetchQueryResults Error:", err);
        tbody.innerHTML = `
            <tr>
                <td colspan="100" class="text-center text-danger" style="padding: 4rem;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 2rem;"></i>
                    <p style="margin-top: 1rem;">Error running query filter results. Please try again.</p>
                </td>
            </tr>
        `;
    }
}

function renderExplorerSummary(s) {
    document.getElementById("exp-summary-rows").textContent = s.rows;
    document.getElementById("exp-summary-cols").textContent = s.columns;
    document.getElementById("exp-summary-memory").textContent = s.memory_usage;
    
    const badge = document.getElementById("exp-summary-status");
    badge.textContent = s.processing_status;
    if (s.processing_status === "PROCESSED") {
        badge.className = "badge success";
    } else {
        badge.className = "badge warning";
    }
}

function renderExplorerTable() {
    const thead = document.getElementById("explorer-table-header");
    const tbody = document.getElementById("explorer-table-body");
    
    if (explorerState.columns.length === 0) {
        thead.innerHTML = "";
        tbody.innerHTML = '<tr><td class="text-center text-muted">No columns found.</td></tr>';
        return;
    }
    
    // 1. Render headers with sorting bindings
    thead.innerHTML = "";
    explorerState.columns.forEach(col => {
        const th = document.createElement("th");
        th.className = "interactive-header";
        if (explorerState.sortBy === col.name) {
            th.classList.add("active-sort");
        }
        
        // Icon for sorting status
        let sortIcon = '<i class="fa-solid fa-sort sort-icon"></i>';
        if (explorerState.sortBy === col.name) {
            sortIcon = explorerState.sortOrder === "asc" 
                ? '<i class="fa-solid fa-sort-up sort-icon"></i>' 
                : '<i class="fa-solid fa-sort-down sort-icon"></i>';
        }
        
        th.innerHTML = `${col.name} ${sortIcon}`;
        th.onclick = () => onHeaderClick(col.name);
        thead.appendChild(th);
    });
    
    // 2. Render rows
    tbody.innerHTML = "";
    if (explorerState.records.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="${explorerState.columns.length}" class="text-center text-muted" style="padding: 4rem;">
                    No records found matching query criteria.
                </td>
            </tr>
        `;
        return;
    }
    
    explorerState.records.forEach(row => {
        const tr = document.createElement("tr");
        explorerState.columns.forEach(col => {
            const td = document.createElement("td");
            const val = row[col.name];
            
            if (val === null || val === undefined) {
                td.textContent = "-";
                td.className = "text-muted";
            } else if (col.type === "boolean") {
                td.innerHTML = val 
                    ? '<span class="badge success" style="padding: 2px 6px;">True</span>' 
                    : '<span class="badge danger" style="padding: 2px 6px;">False</span>';
            } else {
                td.textContent = val;
            }
            
            td.style.cursor = "pointer";
            td.onclick = (e) => {
                document.querySelectorAll(".interactive-table td").forEach(c => c.style.backgroundColor = "");
                td.style.backgroundColor = "rgba(0, 168, 204, 0.08)";
                selectColumn(col.name);
            };
            
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    window.EnhancedTable.init(tbody.closest("table"));
}

function onHeaderClick(colName) {
    if (explorerState.sortBy === colName) {
        explorerState.sortOrder = explorerState.sortOrder === "asc" ? "desc" : "asc";
    } else {
        explorerState.sortBy = colName;
        explorerState.sortOrder = "asc";
    }
    explorerState.page = 1;
    console.log("Sorting Applied:", colName, explorerState.sortOrder);
    fetchQueryResults();
}

function renderExplorerPagination() {
    const total = explorerState.totalRecords;
    const size = explorerState.pageSize;
    const page = explorerState.page;
    
    const prevBtn = document.getElementById("btn-exp-prev");
    const nextBtn = document.getElementById("btn-exp-next");
    const summary = document.getElementById("explorer-pagination-summary");
    
    if (total === 0) {
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        summary.textContent = "Showing 0-0 of 0 records";
        return;
    }
    
    const start = (page - 1) * size + 1;
    const end = Math.min(page * size, total);
    
    summary.textContent = `Showing ${start}-${end} of ${total} records`;
    
    prevBtn.disabled = page <= 1;
    nextBtn.disabled = end >= total;
}

function changePage(delta) {
    explorerState.page += delta;
    fetchQueryResults();
}

function onPageSizeChange() {
    const select = document.getElementById("explorer-page-size");
    explorerState.pageSize = parseInt(select.value) || 10;
    explorerState.page = 1;
    fetchQueryResults();
}

function addFilterRow() {
    if (explorerState.columns.length === 0) return;
    
    const container = document.getElementById("filter-rows-container");
    const bar = document.getElementById("filter-actions-bar");
    bar.style.display = "flex";
    
    const row = document.createElement("div");
    row.className = "filter-row";
    
    let colOptions = "";
    explorerState.columns.forEach(col => {
        colOptions += `<option value="${col.name}" data-type="${col.type}">${col.name}</option>`;
    });
    
    row.innerHTML = `
        <select class="filter-col" onchange="onFilterColumnChange(this)">
            ${colOptions}
        </select>
        <select class="filter-op">
            <!-- Populated dynamically -->
        </select>
        <input type="text" class="filter-val" placeholder="Value..." style="flex-grow: 1;">
        <button class="btn-remove" onclick="removeFilterRow(this)"><i class="fa-solid fa-trash-can"></i></button>
    `;
    
    container.appendChild(row);
    
    const colSelect = row.querySelector(".filter-col");
    onFilterColumnChange(colSelect);
}

function onFilterColumnChange(selectEl) {
    const row = selectEl.parentElement;
    const opSelect = row.querySelector(".filter-op");
    const valInput = row.querySelector(".filter-val");
    
    const optSelected = selectEl.options[selectEl.selectedIndex];
    const type = optSelected.getAttribute("data-type");
    
    let opOptions = "";
    if (type === "numeric") {
        opOptions = `
            <option value="==">Equals (==)</option>
            <option value=">">Greater than (&gt;)</option>
            <option value="<">Less than (&lt;)</option>
            <option value=">=">Greater or Equal (&gt;=)</option>
            <option value="<=">Less or Equal (&lt;=)</option>
        `;
        valInput.type = "number";
        valInput.placeholder = "Number...";
    } else if (type === "datetime") {
        opOptions = `
            <option value="on_date">On Date</option>
            <option value="before">Before Date</option>
            <option value="after">After Date</option>
        `;
        valInput.type = "date";
        valInput.placeholder = "Select Date...";
    } else if (type === "boolean") {
        opOptions = `
            <option value="is_true">Is True</option>
            <option value="is_false">Is False</option>
        `;
        valInput.type = "hidden";
        valInput.value = "true";
    } else { // text
        opOptions = `
            <option value="contains">Contains</option>
            <option value="equals">Equals</option>
            <option value="starts_with">Starts With</option>
        `;
        valInput.type = "text";
        valInput.placeholder = "Text pattern...";
    }
    
    opSelect.innerHTML = opOptions;
}

function removeFilterRow(btnEl) {
    const row = btnEl.parentElement;
    row.remove();
    
    const container = document.getElementById("filter-rows-container");
    if (container.children.length === 0) {
        document.getElementById("filter-actions-bar").style.display = "none";
        clearAllFilters();
    }
}

function clearAllFilters() {
    document.getElementById("filter-rows-container").innerHTML = "";
    document.getElementById("filter-actions-bar").style.display = "none";
    explorerState.filters = [];
    explorerState.page = 1;
    console.log("Filters Cleared");
    fetchQueryResults();
}

function applyQueries() {
    const container = document.getElementById("filter-rows-container");
    const filterRows = container.querySelectorAll(".filter-row");
    
    const collectedFilters = [];
    filterRows.forEach(row => {
        const col = row.querySelector(".filter-col").value;
        const op = row.querySelector(".filter-op").value;
        const val = row.querySelector(".filter-val").value;
        
        collectedFilters.push({ column: col, operator: op, value: val });
    });
    
    explorerState.filters = collectedFilters;
    explorerState.page = 1;
    console.log("Filters Applied:", collectedFilters);
    fetchQueryResults();
}

function debounceSearch() {
    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        const searchInput = document.getElementById("explorer-search");
        explorerState.searchQuery = searchInput.value.trim();
        explorerState.page = 1;
        console.log("Search Executed:", explorerState.searchQuery);
        fetchQueryResults();
    }, 400);
}

async function selectColumn(colName) {
    if (!explorerState.datasetName) return;
    
    const body = document.getElementById("column-inspector-body");
    body.innerHTML = `
        <div class="text-center" style="padding: 3rem 0;">
            <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 2rem; color: var(--primary-color);"></i>
            <p style="margin-top: 1rem;">Profiling column statistics...</p>
        </div>
    `;
    
    try {
        const res = await fetch(`${API_EXPLORER_PROFILE}/${explorerState.datasetName}/${colName}`);
        if (!res.ok) throw new Error("Failed to profile column");
        const profile = await res.json();
        
        console.log("Column Selected:", colName);
        renderColumnInspector(profile);
    } catch (err) {
        console.error("selectColumn Error:", err);
        body.innerHTML = `
            <div class="text-center text-danger" style="padding: 3rem 0;">
                <i class="fa-solid fa-circle-exclamation" style="font-size: 2rem;"></i>
                <p style="margin-top: 1rem;">Failed to profile column metadata.</p>
            </div>
        `;
    }
}

function renderColumnInspector(p) {
    const body = document.getElementById("column-inspector-body");
    
    let sampleRows = "";
    if (p.sample_values.length === 0) {
        sampleRows = '<li class="text-muted">No non-null sample values.</li>';
    } else {
        p.sample_values.forEach(v => {
            sampleRows += `<li>${v}</li>`;
        });
    }
    
    body.innerHTML = `
        <div class="inspector-detail-item">
            <label>Column Name</label>
            <div class="value-box mono">${p.column_name}</div>
        </div>
        <div class="inspector-detail-item">
            <label>Data Type</label>
            <div class="value-box">${p.data_type.toUpperCase()}</div>
        </div>
        <div class="inspector-detail-item">
            <label>Distinct Values</label>
            <div class="value-box">${p.unique_count}</div>
        </div>
        <div class="inspector-detail-item">
            <label>Missing Values (Nulls)</label>
            <div class="value-box ${p.null_count > 0 ? 'text-warning' : ''}">${p.null_count} / ${p.total_count}</div>
        </div>
        <div class="inspector-detail-item">
            <label>Duplicate Values</label>
            <div class="value-box ${p.duplicate_count > 0 ? 'text-warning' : ''}">${p.duplicate_count}</div>
        </div>
        <div class="inspector-detail-item">
            <label>Sample Values</label>
            <ul class="sample-values-list">
                ${sampleRows}
            </ul>
        </div>
    `;
}

function resetColumnInspector() {
    const body = document.getElementById("column-inspector-body");
    body.innerHTML = `
        <div class="text-center text-muted" style="padding: 3rem 0;">
            <i class="fa-solid fa-table-columns" style="font-size: 2rem; margin-bottom: 1rem; opacity: 0.5;"></i>
            <p>Select any column header or cell in the table to inspect details.</p>
        </div>
    `;
}

function resetExplorerTable(msg) {
    const thead = document.getElementById("explorer-table-header");
    const tbody = document.getElementById("explorer-table-body");
    thead.innerHTML = "";
    tbody.innerHTML = `
        <tr>
            <td class="text-center text-muted" style="padding: 4rem;">${msg}</td>
        </tr>
    `;
}

function resetExplorerSummary() {
    document.getElementById("exp-summary-rows").textContent = "-";
    document.getElementById("exp-summary-cols").textContent = "-";
    document.getElementById("exp-summary-memory").textContent = "-";
    const badge = document.getElementById("exp-summary-status");
    badge.textContent = "-";
    badge.className = "badge";
}

// ==========================================
// EXECUTIVE ANALYTICS DASHBOARD & BI CONTROLLER
// ==========================================

const API_BI_DASHBOARD = "/api/bi/dashboard";
const API_BI_COMPARE = "/api/bi/compare";
const API_BI_EXPORT = "/api/bi/export";

let biState = {
    filters: {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        partner: "",
        part_category: "",
        priority: "",
        flow_type: ""
    },
    transactions: [], // Full list of filtered transactions
    filteredTransactions: [], // Filtered + searched transactions
    tablePage: 1,
    tablePageSize: 10,
    tableSortBy: "Transaction_ID",
    tableSortOrder: "asc",
    tableSearch: "",
    dropdownsPopulated: false
};

// Drilldown-specific modal state
let drilldownState = {
    transactions: [],
    title: ""
};

async function loadExecutiveDashboard() {
    console.log("Dashboard Loaded event logged.");
    
    // Set loading placeholders
    const views = ["dashboard-kpi-grid-1", "dashboard-kpi-grid-2"];
    views.forEach(v => {
        const grid = document.getElementById(v);
        if (grid) {
            grid.querySelectorAll(".metric-value").forEach(val => {
                val.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size: 14px;"></i>';
            });
        }
    });

    try {
        // Fetch BI payload via POST
        const res = await fetch(API_BI_DASHBOARD, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filters: biState.filters })
        });
        if (!res.ok) throw new Error("Failed fetching BI dashboard payload");
        const data = await res.json();
        
        console.log("Metrics Calculated and Summary Generated event logged.");
        
        // 1. Populate KPI Cards & wire drilldown click listeners
        renderDashboardKPIs(data.kpis);
        wireKPIDrilldownClicks();

        // 2. Populate Summary Strip
        renderDashboardSummary(data.summary_info);
        
        // 3. Populate Tables
        renderDashboardTables(data.distributions);
        
        // 4. Render Plotly Charts
        renderDashboardCharts(data);
        console.log("Charts Generated event logged.");

        // 5. Populate rankings lists (top/bottom performers)
        renderDashboardPerformers(data.performers);

        // 6. Store transactions and populate interactive table
        biState.transactions = data.transactions || [];
        applyBITableSearchAndSort();

        // 7. Populate filter panel dropdown values dynamically once
        if (!biState.dropdownsPopulated) {
            populateFilterPanelDropdowns(data.distributions);
        }

        console.log("[Observability] Dashboard Rendered");
        console.log("[Observability] Dashboard Updated");

    } catch (err) {
        console.error("loadExecutiveDashboard Error:", err);
        views.forEach(v => {
            const grid = document.getElementById(v);
            if (grid) {
                grid.querySelectorAll(".metric-value").forEach(val => {
                    val.textContent = "Error";
                });
            }
        });
        alert("Failed loading BI dashboard. Verify backend service is operational.");
    }
}

function renderDashboardKPIs(kpis) {
    document.querySelector("#kpi-shipments .metric-value").textContent = kpis.total_shipments.value;
    document.querySelector("#kpi-total-cost .metric-value").textContent = kpis.total_cost.value;
    document.querySelector("#kpi-avg-cost .metric-value").textContent = kpis.avg_cost.value;
    document.querySelector("#kpi-avg-transit .metric-value").textContent = kpis.avg_transit_days.value;
    document.querySelector("#kpi-inventory .metric-value").textContent = kpis.avg_inventory_level.value;
    
    document.querySelector("#kpi-hubs .metric-value").textContent = kpis.total_hubs.value;
    document.querySelector("#kpi-tprs .metric-value").textContent = kpis.total_tprs.value;
    document.querySelector("#kpi-parts .metric-value").textContent = kpis.total_parts.value;
    document.querySelector("#kpi-hub-util .metric-value").textContent = kpis.avg_hub_utilization.value;
    document.querySelector("#kpi-tpr-util .metric-value").textContent = kpis.avg_rc_utilization.value;
}

function renderDashboardSummary(info) {
    const datasetBadge = document.getElementById("dash-summary-dataset");
    datasetBadge.textContent = info.dataset_status;
    datasetBadge.className = info.dataset_status === "LOADED" ? "badge success" : "badge danger";
    
    const repoBadge = document.getElementById("dash-summary-repo");
    repoBadge.textContent = info.repository_status;
    repoBadge.className = info.repository_status === "HEALTHY" ? "badge success" : (info.repository_status === "WARNING" ? "badge warning" : "badge danger");
    
    const procBadge = document.getElementById("dash-summary-proc");
    procBadge.textContent = info.processing_status;
    procBadge.className = info.processing_status === "SUCCESS" ? "badge success" : "badge warning";
    
    document.getElementById("dash-summary-records").textContent = info.total_processed_records;
    document.getElementById("dash-summary-refresh-time").textContent = formatDate(info.last_refresh_time);
}

function renderDashboardTables(dists) {
    const populateSummaryTable = (elementId, dataList, categoryKey) => {
        const tbody = document.getElementById(elementId);
        if (!tbody) return;
        tbody.innerHTML = "";
        
        if (!dataList || dataList.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center text-muted">No data available.</td></tr>';
            return;
        }
        
        dataList.forEach(r => {
            const tr = document.createElement("tr");
            const cat = r[categoryKey];
            const count = r.count;
            const cost = r.cost !== undefined ? `$${r.cost.toFixed(2)}` : null;
            
            if (cost !== null) {
                tr.innerHTML = `<td><strong>${cat}</strong></td><td class="text-right">${count}</td><td class="text-right">${cost}</td>`;
            } else {
                tr.innerHTML = `<td><strong>${cat}</strong></td><td class="text-right">${count}</td>`;
            }
            tbody.appendChild(tr);
        });
    };

    populateSummaryTable("tbl-flow-types", dists.flow_types, "Flow_Type");
    populateSummaryTable("tbl-priorities", dists.priorities, "Priority");
    populateSummaryTable("tbl-partners", dists.partners, "Logistics_Partner");
    populateSummaryTable("tbl-categories", dists.part_categories, "Category");
    populateSummaryTable("tbl-sla-statuses", dists.sla_statuses, "SLA_Status");
    populateSummaryTable("tbl-hub-types", dists.hub_types, "Hub_Type");
    populateSummaryTable("tbl-tpr-locations", dists.tpr_locations, "Coverage_Region");
}

function renderDashboardPerformers(perf) {
    const populateList = (elementId, list, nameKey, valKey, suffix = "") => {
        const ul = document.getElementById(elementId);
        if (!ul) return;
        ul.innerHTML = "";
        
        if (!list || list.length === 0) {
            ul.innerHTML = '<li class="text-center text-muted">No data</li>';
            return;
        }
        
        list.slice(0, 5).forEach((item, index) => {
            const li = document.createElement("li");
            const val = item[valKey];
            const formattedVal = typeof val === "number" ? val.toLocaleString() : val;
            li.innerHTML = `
                <div>
                    <span style="color: var(--text-muted); font-size: 10px; margin-right: 4px;">#${index+1}</span>
                    <span class="perf-name">${item[nameKey]}</span>
                </div>
                <span class="perf-val">${formattedVal}${suffix}</span>
            `;
            ul.appendChild(li);
        });
    };

    populateList("rank-top-partners", perf.top_partners, "Logistics_Partner", "shipments", " Shipments");
    populateList("rank-top-hubs", perf.top_hubs, "Hub_ID", "shipments", " Vol");
    populateList("rank-top-tprs", perf.top_tprs, "rc_name", "Rating", " ★");
    populateList("rank-bottom-hubs", perf.bottom_hubs, "Hub_ID", "shipments", " Vol");
    populateList("rank-bottom-tprs", perf.bottom_tprs, "rc_name", "Rating", " ★");
    populateList("rank-top-parts", perf.top_parts, "Part_Name", "volume", " Units");
}

function renderDashboardCharts(data) {
    console.log("[Observability] Visualization Loaded");
    const defaultLayoutProps = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#a1a1aa', family: 'Inter, sans-serif', size: 10 },
        margin: { t: 40, b: 40, l: 40, r: 20 },
        showlegend: false,
        xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zeroline: false },
        yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zeroline: false }
    };
    
    const colors = ['#00a8cc', '#8624e1', '#f59e0b', '#10b981', '#ef4444'];

    // 1. Time Series Chart
    const ts = data.trends?.daily || [];
    const dates = ts.map(x => x.Order_Date_Str);
    const costs = ts.map(x => x.cost);
    const shipments = ts.map(x => x.shipments);
    
    const traceCost = {
        x: dates,
        y: costs,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Shipment Cost ($)',
        line: { color: '#8624e1', width: 2 },
        marker: { color: '#8624e1', size: 6 },
        yaxis: 'y2'
    };
    const traceVol = {
        x: dates,
        y: shipments,
        type: 'bar',
        name: 'Shipments Volume',
        marker: { color: 'rgba(0, 168, 204, 0.4)' }
    };
    
    const tsLayout = {
        ...defaultLayoutProps,
        showlegend: true,
        legend: { orientation: 'h', x: 0, y: 1.1, font: { size: 9 } },
        margin: { t: 50, b: 30, l: 40, r: 40 },
        yaxis: { title: 'Shipments', gridcolor: 'rgba(255,255,255,0.05)' },
        yaxis2: {
            title: 'Cost ($)',
            overlaying: 'y',
            side: 'right',
            gridcolor: 'rgba(0,0,0,0)'
        }
    };
    
    const divTS = document.getElementById("chart-time-series");
    if (divTS) {
        Plotly.newPlot('chart-time-series', [traceVol, traceCost], tsLayout, { responsive: true, displayModeBar: false });
        divTS.on('plotly_click', (evt) => handleChartNodeClick("Time_Series", evt));
    }

    // 2. Flow Type Distribution (Pie Chart)
    const ft = data.distributions.flow_types || [];
    const flowLabels = ft.map(x => x.Flow_Type);
    const flowValues = ft.map(x => x.count);
    
    const flowTrace = {
        labels: flowLabels,
        values: flowValues,
        type: 'pie',
        hole: 0.4,
        marker: { colors: colors },
        textinfo: 'percent',
        hoverinfo: 'label+value+percent'
    };
    const flowLayout = {
        ...defaultLayoutProps,
        showlegend: true,
        legend: { orientation: 'h', x: 0, y: -0.1, font: { size: 9 } },
        margin: { t: 20, b: 40, l: 20, r: 20 }
    };
    const divFT = document.getElementById("chart-flow-type");
    if (divFT) {
        Plotly.newPlot('chart-flow-type', [flowTrace], flowLayout, { responsive: true, displayModeBar: false });
        divFT.on('plotly_click', (evt) => handleChartNodeClick("Flow_Type", evt));
    }

    // 3. SLA & Priority Distributions
    const prio = data.distributions.priorities || [];
    const prioLabels = prio.map(x => x.Priority);
    const prioValues = prio.map(x => x.count);
    
    const prioTrace = {
        x: prioLabels,
        y: prioValues,
        type: 'bar',
        name: 'Priority Count',
        marker: { color: colors.slice(0, prioLabels.length) }
    };
    const divSLA = document.getElementById("chart-sla-prio");
    if (divSLA) {
        Plotly.newPlot('chart-sla-prio', [prioTrace], defaultLayoutProps, { responsive: true, displayModeBar: false });
        divSLA.on('plotly_click', (evt) => handleChartNodeClick("Priority", evt));
    }

    // 4. Part Category Distribution (Horizontal Bar)
    const pc = data.distributions.part_categories || [];
    const catLabels = pc.map(x => x.Category);
    const catValues = pc.map(x => x.count);
    
    const catTrace = {
        y: catLabels,
        x: catValues,
        type: 'bar',
        orientation: 'h',
        marker: { color: '#00a8cc' }
    };
    const catLayout = {
        ...defaultLayoutProps,
        margin: { t: 20, b: 30, l: 80, r: 20 }
    };
    const divPC = document.getElementById("chart-part-cat");
    if (divPC) {
        Plotly.newPlot('chart-part-cat', [catTrace], catLayout, { responsive: true, displayModeBar: false });
        divPC.on('plotly_click', (evt) => handleChartNodeClick("Part_Category", evt));
    }

    // 5. Logistics Cost Distribution
    const txCosts = data.distributions.partners.map(x => x.cost);
    const costTrace = {
        y: txCosts,
        type: 'box',
        name: 'Costs',
        marker: { color: '#8624e1' },
        boxpoints: 'all',
        jitter: 0.3,
        pointpos: -1.8
    };
    Plotly.newPlot('chart-cost-dist', [costTrace], defaultLayoutProps, { responsive: true, displayModeBar: false });

    // 6. Hub Types & Service Coverage
    const ht = data.distributions.hub_types || [];
    const hubLabels = ht.map(x => x.Hub_Type);
    const hubValues = ht.map(x => x.count);
    
    const hubTrace = {
        x: hubLabels,
        y: hubValues,
        type: 'bar',
        name: 'Hubs',
        marker: { color: '#10b981' }
    };
    Plotly.newPlot('chart-hub-tpr', [hubTrace], defaultLayoutProps, { responsive: true, displayModeBar: false });
    console.log("[Observability] Charts Rendered");
}

// ==========================================
// BI FILTER PANEL FUNCTIONS
// ==========================================

function toggleFilterPanel() {
    const panel = document.getElementById("bi-filter-panel");
    panel.style.display = panel.style.display === "none" ? "block" : "none";
}

function populateFilterPanelDropdowns(dists) {
    const fillDropdown = (elementId, list, key) => {
        const select = document.getElementById(elementId);
        if (!select) return;
        
        // Save first option
        const firstOpt = select.options[0];
        select.innerHTML = "";
        select.appendChild(firstOpt);
        
        list.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item[key];
            opt.textContent = item[key];
            select.appendChild(opt);
        });
    };

    fillDropdown("filter-partner", dists.partners, "Logistics_Partner");
    fillDropdown("filter-category", dists.part_categories, "Category");
    
    // Fill hubs dropdown options from hub summary types or static names mapping
    const hubsList = [
        { name: "HUB-A" }, { name: "HUB-B" }, { name: "HUB-C" }, { name: "HUB-D" }, { name: "HUB-E" }
    ];
    fillDropdown("filter-hub", hubsList, "name");

    const rcsList = [
        { name: "TPR-001" }, { name: "TPR-002" }, { name: "TPR-003" }
    ];
    fillDropdown("filter-rc", rcsList, "name");

    biState.dropdownsPopulated = true;
    populateComparisonDropdowns();
}

function clearBIFilters() {
    biState.filters = {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        partner: "",
        part_category: "",
        priority: "",
        flow_type: ""
    };
    
    document.getElementById("filter-start-date").value = "";
    document.getElementById("filter-end-date").value = "";
    document.getElementById("filter-hub").value = "";
    document.getElementById("filter-rc").value = "";
    document.getElementById("filter-partner").value = "";
    document.getElementById("filter-category").value = "";
    document.getElementById("filter-priority").value = "";
    document.getElementById("filter-flow-type").value = "";
    
    loadExecutiveDashboard();
}

function applyBIFilters() {
    console.log("[Observability] Filters Applied");
    logger.info("Filter Applied event logged.");
    
    biState.filters.start_date = document.getElementById("filter-start-date").value;
    biState.filters.end_date = document.getElementById("filter-end-date").value;
    biState.filters.hub = document.getElementById("filter-hub").value;
    biState.filters.repair_center = document.getElementById("filter-rc").value;
    biState.filters.partner = document.getElementById("filter-partner").value;
    biState.filters.part_category = document.getElementById("filter-category").value;
    biState.filters.priority = document.getElementById("filter-priority").value;
    biState.filters.flow_type = document.getElementById("filter-flow-type").value;
    
    biState.tablePage = 1;
    loadExecutiveDashboard();
}

// ==========================================
// DRILL-DOWN ANALYTICS FUNCTIONS
// ==========================================

function wireKPIDrilldownClicks() {
    const shipmentsCard = document.getElementById("kpi-shipments");
    if (shipmentsCard) {
        shipmentsCard.style.cursor = "pointer";
        shipmentsCard.onclick = () => openKPIDrilldown("All Transactions", biState.transactions);
    }
}

function handleChartNodeClick(chartType, evt) {
    if (!evt || !evt.points || evt.points.length === 0) return;
    const pt = evt.points[0];
    const categoryVal = pt.label || pt.x || pt.y;
    
    let drilldownList = [];
    if (chartType === "Flow_Type") {
        logger.info("Drill-down Opened event logged.");
        drilldownList = biState.transactions.filter(x => {
            const dest = x.Destination_Hub.toUpperCase();
            if (categoryVal === "Outbound to TPR") return dest.startsWith("TPR");
            if (categoryVal === "Hub-to-Hub Transfer") return dest.startsWith("HUB");
            return !dest.startsWith("TPR") && !dest.startsWith("HUB");
        });
    } else if (chartType === "Priority") {
        logger.info("Drill-down Opened event logged.");
        drilldownList = biState.transactions.filter(x => {
            const dist = x.Route_Distance || 0;
            const cost = x.Shipment_Cost || 0;
            let p = "Low Priority";
            if (dist > 300 || cost > 300) p = "High Priority";
            else if (dist > 100 || cost > 100) p = "Medium Priority";
            return p === categoryVal;
        });
    } else if (chartType === "Part_Category") {
        logger.info("Drill-down Opened event logged.");
        // Categories joining requires mapping or filter
        drilldownList = biState.transactions; // fallback
    } else {
        drilldownList = biState.transactions;
    }
    
    openKPIDrilldown(`Drill-down: ${categoryVal}`, drilldownList);
}

function openKPIDrilldown(title, list) {
    logger.info("Drill-down Opened event logged.");
    drilldownState.title = title;
    drilldownState.transactions = list;
    
    document.getElementById("drilldown-modal-title").textContent = title;
    document.getElementById("drilldown-records-summary").textContent = `Found ${list.length} transactions contributing to this summary.`;
    
    const tbody = document.getElementById("drilldown-table-body");
    tbody.innerHTML = "";
    
    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No contributing records.</td></tr>';
    } else {
        list.forEach(tx => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${tx.Transaction_ID}</strong></td>
                <td>${formatDate(tx.Order_Date)}</td>
                <td>${formatDate(tx.Delivery_Date)}</td>
                <td>${tx.Origin_Hub}</td>
                <td>${tx.Destination_Hub}</td>
                <td>${tx.Part_Number}</td>
                <td>${tx.Quantity}</td>
                <td><span class="badge ${tx.SLA_Status === 'MET' ? 'success' : 'danger'}">${tx.SLA_Status}</span></td>
                <td>$${tx.Shipment_Cost.toFixed(2)}</td>
                <td>${tx.Route_Distance.toFixed(1)} miles</td>
            `;
            tbody.appendChild(tr);
        });
    }
    
    document.getElementById("drilldown-modal").style.display = "flex";
}

function closeDrilldownModal() {
    document.getElementById("drilldown-modal").style.display = "none";
}

// ==========================================
// COMPARISON ANALYTICS FUNCTIONS
// ==========================================

const entityOptionsMap = {
    hub: ["HUB-A", "HUB-B", "HUB-C", "HUB-D", "HUB-E"],
    rc: ["TPR-001", "TPR-002", "TPR-003"],
    partner: ["Swift LogiCo", "Apex Freight", "LoneStar Delivery"],
    priority: ["High Priority", "Medium Priority", "Low Priority"],
    flow_type: ["Hub-to-Hub Transfer", "Outbound to TPR", "Standard Delivery"]
};

function populateComparisonDropdowns() {
    onCompareTypeChange();
}

function onCompareTypeChange() {
    const type = document.getElementById("compare-entity-type").value;
    const options = entityOptionsMap[type] || [];
    
    const selectA = document.getElementById("compare-entity-a");
    const selectB = document.getElementById("compare-entity-b");
    
    selectA.innerHTML = "";
    selectB.innerHTML = "";
    
    options.forEach((opt, idx) => {
        const optionA = document.createElement("option");
        optionA.value = opt;
        optionA.textContent = opt;
        selectA.appendChild(optionA);
        
        const optionB = document.createElement("option");
        optionB.value = opt;
        optionB.textContent = opt;
        if (idx === 1 || options.length === 1) {
            optionB.selected = true;
        }
        selectB.appendChild(optionB);
    });
}

async function runEntityComparison() {
    logger.info("Comparison Generated event logged.");
    
    const type = document.getElementById("compare-entity-type").value;
    const a = document.getElementById("compare-entity-a").value;
    const b = document.getElementById("compare-entity-b").value;
    
    try {
        const res = await fetch(API_BI_COMPARE, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                entity_type: type,
                entity_a: a,
                entity_b: b,
                filters: biState.filters
            })
        });
        if (!res.ok) throw new Error("Failed fetching comparison metrics");
        const data = await res.json();
        
        // Render comparisons
        const renderEntityStats = (cardId, name, stats) => {
            const card = document.getElementById(cardId);
            card.querySelector(".entity-title").textContent = name;
            card.querySelector(".val-shipments").textContent = stats.count;
            card.querySelector(".val-cost").textContent = `$${stats.cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            card.querySelector(".val-avg-cost").textContent = `$${stats.avg_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            card.querySelector(".val-sla-rate").textContent = `${stats.sla_rate.toFixed(1)}%`;
            card.querySelector(".val-transit").textContent = `${stats.avg_transit.toFixed(1)} Days`;
        };
        
        renderEntityStats("compare-card-a", a, data.entity_a);
        renderEntityStats("compare-card-b", b, data.entity_b);
        
        document.getElementById("comparison-results-body").style.display = "block";
        
    } catch (err) {
        console.error("runEntityComparison Error:", err);
        alert("Failed loading comparison metrics.");
    }
}

// ==========================================
// INTERACTIVE DATA TABLE FUNCTIONS
// ==========================================

function debounceBISearch() {
    clearTimeout(biState.searchTimeout);
    biState.searchTimeout = setTimeout(() => {
        biState.tableSearch = document.getElementById("bi-table-search").value.trim().toLowerCase();
        biState.tablePage = 1;
        applyBITableSearchAndSort();
    }, 300);
}

function sortBITable(column) {
    if (biState.tableSortBy === column) {
        biState.tableSortOrder = biState.tableSortOrder === "asc" ? "desc" : "asc";
    } else {
        biState.tableSortBy = column;
        biState.tableSortOrder = "asc";
    }
    applyBITableSearchAndSort();
}

function applyBITableSearchAndSort() {
    let list = [...biState.transactions];
    
    // 1. Apply Search
    if (biState.tableSearch) {
        list = list.filter(item => {
            return (
                item.Transaction_ID.toLowerCase().includes(biState.tableSearch) ||
                item.Origin_Hub.toLowerCase().includes(biState.tableSearch) ||
                item.Destination_Hub.toLowerCase().includes(biState.tableSearch) ||
                item.Part_Number.toLowerCase().includes(biState.tableSearch) ||
                item.SLA_Status.toLowerCase().includes(biState.tableSearch)
            );
        });
    }
    
    // 2. Apply Sort
    const col = biState.tableSortBy;
    const ord = biState.tableSortOrder === "asc" ? 1 : -1;
    list.sort((x, y) => {
        let valX = x[col];
        let valY = y[col];
        
        if (typeof valX === "string") valX = valX.toLowerCase();
        if (typeof valY === "string") valY = valY.toLowerCase();
        
        if (valX < valY) return -1 * ord;
        if (valX > valY) return 1 * ord;
        return 0;
    });
    
    biState.filteredTransactions = list;
    renderBITable();
}

function renderBITable() {
    const tbody = document.getElementById("bi-table-body");
    tbody.innerHTML = "";
    
    const startIdx = (biState.tablePage - 1) * biState.tablePageSize;
    const endIdx = startIdx + biState.tablePageSize;
    const pageRecords = biState.filteredTransactions.slice(startIdx, endIdx);
    
    if (pageRecords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center text-muted" style="padding: 3rem 0;">No matching records found.</td></tr>';
        document.getElementById("bi-table-pagination-summary").textContent = "Showing 0-0 of 0 records";
        document.getElementById("btn-bi-prev").disabled = true;
        document.getElementById("btn-bi-next").disabled = true;
        return;
    }
    
    pageRecords.forEach(tx => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><strong>${tx.Transaction_ID}</strong></td>
            <td>${formatDate(tx.Order_Date)}</td>
            <td>${formatDate(tx.Delivery_Date)}</td>
            <td>${tx.Origin_Hub}</td>
            <td>${tx.Destination_Hub}</td>
            <td>${tx.Part_Number}</td>
            <td>${tx.Quantity}</td>
            <td><span class="badge ${tx.SLA_Status === 'MET' ? 'success' : 'danger'}">${tx.SLA_Status}</span></td>
            <td>$${tx.Shipment_Cost.toFixed(2)}</td>
            <td>${tx.Route_Distance.toFixed(1)} miles</td>
        `;
        tbody.appendChild(tr);
    });
    window.EnhancedTable.init(tbody.closest("table"));
    
    const tot = biState.filteredTransactions.length;
    document.getElementById("bi-table-pagination-summary").textContent = `Showing ${startIdx + 1}-${Math.min(endIdx, tot)} of ${tot} records`;
    document.getElementById("btn-bi-prev").disabled = biState.tablePage === 1;
    document.getElementById("btn-bi-next").disabled = endIdx >= tot;
}

function changeBIPage(delta) {
    biState.tablePage += delta;
    renderBITable();
}

// ==========================================
// EXPORT & REPORT DOWNLOAD FUNCTIONS
// ==========================================

async function exportKPIs() {
    logger.info("Export Created event logged.");
    
    try {
        const res = await fetch(API_BI_EXPORT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filters: biState.filters,
                report_type: "kpis"
            })
        });
        if (!res.ok) throw new Error("Failed exporting KPIs summary report");
        const blob = await res.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "kpi_summary_report.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (err) {
        console.error("exportKPIs Error:", err);
        alert("Failed exporting KPI summary report.");
    }
}

async function exportFilteredCSV() {
    logger.info("Export Created event logged.");
    
    try {
        const res = await fetch(API_BI_EXPORT, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filters: biState.filters,
                report_type: "transactions"
            })
        });
        if (!res.ok) throw new Error("Failed exporting filtered transaction records");
        const blob = await res.blob();
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "filtered_transactions_report.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch (err) {
        console.error("exportFilteredCSV Error:", err);
        alert("Failed exporting filtered CSV report.");
    }
}

function exportDrilldownCSV() {
    logger.info("Export Created event logged.");
    if (drilldownState.transactions.length === 0) return;
    
    const headers = ["Transaction_ID", "Order_Date", "Delivery_Date", "Origin_Hub", "Destination_Hub", "Part_Number", "Quantity", "SLA_Status", "Shipment_Cost", "Route_Distance"];
    let csvContent = headers.join(",") + "\n";
    
    drilldownState.transactions.forEach(tx => {
        const row = [
            tx.Transaction_ID,
            tx.Order_Date,
            tx.Delivery_Date,
            tx.Origin_Hub,
            tx.Destination_Hub,
            tx.Part_Number,
            tx.Quantity,
            tx.SLA_Status,
            tx.Shipment_Cost,
            tx.Route_Distance
        ];
        csvContent += row.join(",") + "\n";
    });
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${drilldownState.title.replace(/[:\s]/g, "_")}_report.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

// ==========================================
// GEOSPATIAL LOGISTICS NETWORK MAP CONTROLLER
// ==========================================

const API_GEOSPATIAL_NETWORK = "/api/geospatial/network";

let mapState = {
    map: null,
    markersGroup: null,
    flowsGroup: null,
    legendControl: null,
    filters: {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: "",
        status: ""
    },
    dropdownsPopulated: false
};

async function loadNetworkMap() {
    console.log("Map Loaded event logged.");
    
    // Ensure map container has correct size and Leaflet is initialized
    if (!mapState.map) {
        initLeafletMap();
    } else {
        setTimeout(() => {
            mapState.map.invalidateSize();
        }, 100);
    }
     window.LoadingSkeleton.showMapOverlay("network-map", true);
    try {
        const payload = await fetchGeospatialNetwork();
        window.LoadingSkeleton.showMapOverlay("network-map", false);
        
        // Populate Summary Stats panel
        updateMapSummaryPanel(payload.summary);
        
        // Render locations (hubs, TPRs) and flows (lines)
        renderMapLayers(payload);
        
        // Populate filter dropdowns dynamically once
        if (!mapState.dropdownsPopulated) {
            populateMapDropdowns(payload);
        }
        
        console.log("[Observability] Optimization Layer Loaded");
        
    } catch (err) {
        console.error("loadNetworkMap Error:", err);
        window.LoadingSkeleton.showMapOverlay("network-map", false);
        window.ErrorState.renderMapError("network-map", "Failed loading geospatial network map details.", () => loadNetworkMap());
    }
}

function initLeafletMap() {
    // 1. Initialize map centered on Texas
    mapState.map = L.map("network-map", {
        center: [31.25, -99.25],
        zoom: 6,
        zoomControl: true
    });
    
    // 2. Add modern dark-theme CartoDB Dark Matter tile layer
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(mapState.map);
    
    // 3. Create active feature groups
    mapState.markersGroup = L.markerClusterGroup({
        showCoverageOnHover: false,
        spiderfyOnMaxZoom: true,
        disableClusteringAtZoom: 8
    }).addTo(mapState.map);
    
    mapState.flowsGroup = L.layerGroup().addTo(mapState.map);
    
    // 4. Create and mount Legend control
    mapState.legendControl = L.control({ position: "bottomright" });
    mapState.legendControl.onAdd = function() {
        const div = L.DomUtil.create("div", "map-legend");
        div.innerHTML = `
            <h4>Logistics Legend</h4>
            <div class="legend-item"><span class="legend-key dist-hub"></span><span>Distribution Hub</span></div>
            <div class="legend-item"><span class="legend-key reg-hub"></span><span>Regional Hub</span></div>
            <div class="legend-item"><span class="legend-key rc-center"></span><span>Repair Center (TPR)</span></div>
            <div class="legend-item"><span class="legend-key flow-hub"></span><span>Hub-to-Hub Transfer</span></div>
            <div class="legend-item"><span class="legend-key flow-tpr" style="border-top: 2px dashed #f59e0b; background: none; width: 20px;"></span><span>Outbound to TPR</span></div>
        `;
        return div;
    };
    mapState.legendControl.addTo(mapState.map);
    
    console.log("[Observability] Map Initialized");

    // 5. Wire log on popup open
    mapState.map.on("popupopen", function(e) {
        console.log("Popup Opened event logged.");
    });
}

async function fetchGeospatialNetwork() {
    const res = await fetch(API_GEOSPATIAL_NETWORK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: mapState.filters })
    });
    if (!res.ok) throw new Error("Failed fetching geospatial payload");
    return await res.json();
}

function renderMapLayers(data) {
    // Clear active groups
    mapState.markersGroup.clearLayers();
    mapState.flowsGroup.clearLayers();
    
    // 1. Draw Hub markers
    const hubs = data.hubs || [];
    hubs.forEach(h => {
        const color = h.type === "Distribution Hub" ? "#00a8cc" : "#10b981";
        const marker = L.circleMarker([h.lat, h.lon], {
            radius: 8,
            fillColor: color,
            color: "#ffffff",
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.85
        });
        
        const popupHtml = `
            <div style="font-family: 'Inter', sans-serif; min-width: 190px;">
                <h4 style="margin: 0 0 0.5rem 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.25rem; font-size: 13px; color: var(--text-color);">${h.name}</h4>
                <div style="font-size: 11px; display: flex; flex-direction: column; gap: 0.25rem; color: var(--text-color);">
                    <div><span style="color: var(--text-muted);">Type:</span> <strong>${h.type}</strong></div>
                    <div><span style="color: var(--text-muted);">Location:</span> <strong>${h.city}, ${h.state}</strong></div>
                    <div><span style="color: var(--text-muted);">Capacity:</span> <strong>${h.capacity.toLocaleString()} units/day</strong></div>
                    <div><span style="color: var(--text-muted);">Utilization:</span> <strong>${h.utilization}%</strong></div>
                    <div><span style="color: var(--text-muted);">Status:</span> <strong>${h.inventory_summary}</strong></div>
                </div>
            </div>
        `;
        marker.bindPopup(popupHtml);
        mapState.markersGroup.addLayer(marker);
    });
    console.log("Markers Generated event logged.");

    // 2. Draw Repair Center markers
    const rcs = data.repair_centers || [];
    rcs.forEach(rc => {
        const marker = L.circleMarker([rc.lat, rc.lon], {
            radius: 8,
            fillColor: "#f59e0b",
            color: "#ffffff",
            weight: 1.5,
            opacity: 1,
            fillOpacity: 0.85
        });
        
        const popupHtml = `
            <div style="font-family: 'Inter', sans-serif; min-width: 190px;">
                <h4 style="margin: 0 0 0.5rem 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.25rem; font-size: 13px; color: var(--text-color);">${rc.name}</h4>
                <div style="font-size: 11px; display: flex; flex-direction: column; gap: 0.25rem; color: var(--text-color);">
                    <div><span style="color: var(--text-muted);">Type:</span> <strong>${rc.type}</strong></div>
                    <div><span style="color: var(--text-muted);">Location:</span> <strong>${rc.city}, ${rc.state}</strong></div>
                    <div><span style="color: var(--text-muted);">Supported Parts:</span> <strong>${rc.supported_parts.join(", ")}</strong></div>
                    <div><span style="color: var(--text-muted);">Workload Capacity:</span> <strong>${rc.capacity} units</strong></div>
                    <div><span style="color: var(--text-muted);">Utilization:</span> <strong>${rc.utilization}%</strong></div>
                </div>
            </div>
        `;
        marker.bindPopup(popupHtml);
        mapState.markersGroup.addLayer(marker);
    });
    
    // 3. Draw Flow vectors (Lines)
    const flows = data.flows || [];
    flows.forEach(fl => {
        const isTPR = fl.flow_type === "Outbound to TPR";
        const color = isTPR ? "#f59e0b" : "#00a8cc";
        const options = {
            color: color,
            weight: 3.5,
            opacity: 0.7,
            dashArray: isTPR ? "6, 6" : null
        };
        
        const line = L.polyline([[fl.origin_lat, fl.origin_lon], [fl.dest_lat, fl.dest_lon]], options);
        
        const tooltipHtml = `
            <div style="font-family: 'Inter', sans-serif; padding: 0.25rem; font-size: 11px;">
                <strong>${fl.origin_id} &rarr; ${fl.destination_id}</strong><br/>
                <span class="text-muted">Type:</span> ${fl.flow_type}<br/>
                <span class="text-muted">Shipments count:</span> <strong>${fl.shipment_count}</strong><br/>
                <span class="text-muted">Avg Transit Time:</span> <strong>${fl.avg_transit_time} Days</strong><br/>
                <span class="text-muted">Avg Logistics Cost:</span> <strong>$${fl.avg_cost.toFixed(2)}</strong>
            </div>
        `;
        line.bindTooltip(tooltipHtml, { sticky: true });
        mapState.flowsGroup.addLayer(line);
    });
    console.log("Flows Rendered event logged.");
    
    console.log("[Observability] Locations Loaded");
    console.log("[Observability] Routes Rendered");
}

function updateMapSummaryPanel(sum) {
    document.getElementById("map-summary-hubs").textContent = sum.total_hubs;
    document.getElementById("map-summary-rcs").textContent = sum.total_rcs;
    document.getElementById("map-summary-shipments").textContent = sum.visible_shipments;
    document.getElementById("map-summary-connections").textContent = sum.visible_connections;
    document.getElementById("map-summary-transit").textContent = `${sum.avg_transit_time} Days`;
    document.getElementById("map-summary-cost").textContent = `$${sum.avg_cost.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

function populateMapDropdowns(data) {
    const fillSelect = (elementId, list, keyField, labelField) => {
        const select = document.getElementById(elementId);
        if (!select) return;
        
        // Save first option
        const firstOpt = select.options[0];
        select.innerHTML = "";
        select.appendChild(firstOpt);
        
        list.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item[keyField];
            opt.textContent = item[labelField || keyField];
            select.appendChild(opt);
        });
    };

    fillSelect("map-filter-hub", data.hubs, "id", "name");
    fillSelect("map-filter-rc", data.repair_centers, "id", "name");
    
    // Fetch unique categories & partners from active dashboard distributions
    const categoriesList = [
        { name: "Electronics" }, { name: "Mechanical" }, { name: "Cooling" }
    ];
    fillSelect("map-filter-category", categoriesList, "name");

    const partnersList = [
        { name: "Swift LogiCo" }, { name: "Apex Freight" }, { name: "LoneStar Delivery" }
    ];
    fillSelect("map-filter-partner", partnersList, "name");

    mapState.dropdownsPopulated = true;
}

function applyMapFilters() {
    console.log("[Observability] Filters Applied");
    console.log("Filters Applied event logged.");
    
    mapState.filters.start_date = document.getElementById("map-filter-start-date").value;
    mapState.filters.end_date = document.getElementById("map-filter-end-date").value;
    mapState.filters.hub = document.getElementById("map-filter-hub").value;
    mapState.filters.repair_center = document.getElementById("map-filter-rc").value;
    mapState.filters.part_category = document.getElementById("map-filter-category").value;
    mapState.filters.partner = document.getElementById("map-filter-partner").value;
    mapState.filters.priority = document.getElementById("map-filter-priority").value;
    mapState.filters.status = document.getElementById("map-filter-status").value;
    
    loadNetworkMap();
}

function clearMapFilters() {
    mapState.filters = {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: "",
        status: ""
    };
    
    document.getElementById("map-filter-start-date").value = "";
    document.getElementById("map-filter-end-date").value = "";
    document.getElementById("map-filter-hub").value = "";
    document.getElementById("map-filter-rc").value = "";
    document.getElementById("map-filter-category").value = "";
    document.getElementById("map-filter-partner").value = "";
    document.getElementById("map-filter-priority").value = "";
    document.getElementById("map-filter-status").value = "";
    
    loadNetworkMap();
}

function resetMapView() {
    if (mapState.map) {
        mapState.map.setView([31.25, -99.25], 6);
    }
}

// ==========================================
// ROUTE INTELLIGENCE & NETWORK GRAPH CONTROLLER
// ==========================================

const API_ROUTE_ANALYSIS = "/api/route-analysis/payload";

let routeState = {
    filters: {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: ""
    },
    data: null,
    dropdownsPopulated: false
};

async function loadRouteIntelligence() {
    console.log("Routes Loaded event logged.");
    
    try {
        const payload = await fetchRouteAnalysis();
        routeState.data = payload;
        
        // 1. Populate Overview Metrics
        updateRouteOverviewPanel(payload.overview);
        
        // 2. Populate Dropdowns dynamically
        if (!routeState.dropdownsPopulated) {
            populateRouteFiltersDropdowns(payload);
        }
        
        // 3. Render Network Graph via Plotly
        renderNetworkGraph(payload.graph);
        
        // 4. Render Bottlenecks panel
        renderBottlenecksPanel(payload.bottlenecks);
        
        // 5. Render Route Performance Table Directory
        renderRouteTable(payload.routes);
        
        // 6. Render Hub Load imbalance analysis table
        renderFlowAnalysis(payload.flows);
        
    } catch (err) {
        console.error("loadRouteIntelligence Error:", err);
        window.ErrorState.renderTableError("routes-table-body", 9, "Connection Error", "Failed to fetch route records.", () => loadRouteIntelligence());
        window.ErrorState.renderTableError("flows-table-body", 5, "Connection Error", "Failed to fetch flow analysis.", () => loadRouteIntelligence());
    }
}

async function fetchRouteAnalysis() {
    const res = await fetch(API_ROUTE_ANALYSIS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: routeState.filters })
    });
    if (!res.ok) throw new Error("Failed fetching route analysis payload");
    return await res.json();
}

function updateRouteOverviewPanel(ov) {
    document.getElementById("route-overview-active").textContent = ov.total_active_routes;
    document.getElementById("route-overview-hubs").textContent = ov.total_hub_connections;
    document.getElementById("route-overview-rcs").textContent = ov.total_rc_connections;
    document.getElementById("route-overview-distance").textContent = `${ov.avg_route_distance} mi`;
    document.getElementById("route-overview-transit").textContent = `${ov.avg_transit_time} Days`;
    document.getElementById("route-overview-cost").textContent = `$${ov.avg_logistics_cost.toFixed(2)}`;
    document.getElementById("route-overview-shipments").textContent = ov.avg_shipments_per_route;
}

function populateRouteFiltersDropdowns(data) {
    const fillSelect = (elementId, list, keyField, labelField) => {
        const select = document.getElementById(elementId);
        if (!select) return;
        
        const firstOpt = select.options[0];
        select.innerHTML = "";
        select.appendChild(firstOpt);
        
        list.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item[keyField];
            opt.textContent = item[labelField || keyField];
            select.appendChild(opt);
        });
    };

    const hubsList = (data.graph.nodes || []).filter(n => n.type !== "Repair Center");
    fillSelect("route-filter-hub", hubsList, "id", "name");

    const rcsList = (data.graph.nodes || []).filter(n => n.type === "Repair Center");
    fillSelect("route-filter-rc", rcsList, "id", "name");

    const categoriesList = [
        { name: "Electronics" }, { name: "Mechanical" }, { name: "Cooling" }
    ];
    fillSelect("route-filter-category", categoriesList, "name");

    const partnersList = [
        { name: "Swift LogiCo" }, { name: "Apex Freight" }, { name: "LoneStar Delivery" }
    ];
    fillSelect("route-filter-partner", partnersList, "name");

    routeState.dropdownsPopulated = true;
}

function renderNetworkGraph(graphData) {
    console.log("Network Graph Built event logged.");
    
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    
    // Map nodes to easy coordinate lookups
    const nodeCoords = {};
    nodes.forEach(n => {
        nodeCoords[n.id] = { lat: n.lat, lon: n.lon, name: n.name, type: n.type };
    });
    
    const traces = [];
    
    // 1. Draw Edges (Shipment Flow lines)
    edges.forEach(e => {
        const src = nodeCoords[e.source];
        const tgt = nodeCoords[e.target];
        
        if (src && tgt) {
            const lineColor = e.is_bottleneck ? "#ef4444" : "#4a5568";
            const lineWeight = e.is_bottleneck ? 4 : 2;
            const lineDash = e.flow_type === "Outbound to TPR" ? "dash" : "solid";
            
            traces.push({
                x: [src.lon, tgt.lon],
                y: [src.lat, tgt.lat],
                type: "scatter",
                mode: "lines",
                line: {
                    color: lineColor,
                    width: lineWeight,
                    dash: lineDash
                },
                hoverinfo: "text",
                text: `Route: ${e.source} &rarr; ${e.target}<br/>Type: ${e.flow_type}<br/>Volume: ${e.volume} shipments<br/>Avg Cost: $${e.avg_cost.toFixed(2)}<br/>Avg Transit: ${e.avg_transit} Days`,
                opacity: 0.8
            });
        }
    });
    
    // 2. Draw Nodes (Hubs and RCs)
    const nodeX = [];
    const nodeY = [];
    const nodeColors = [];
    const nodeSizes = [];
    const nodeTexts = [];
    
    nodes.forEach(n => {
        nodeX.push(n.lon);
        nodeY.push(n.lat);
        
        // Style node color by Type
        if (n.type === "Repair Center") {
            nodeColors.push("#f59e0b"); // Orange
        } else if (n.type === "Distribution Hub") {
            nodeColors.push("#00a8cc"); // Cyan
        } else {
            nodeColors.push("#10b981"); // Green (Regional Hub)
        }
        
        // Node marker size proportional to overall workload volume
        const size = Math.max(12, Math.min(30, 10 + n.volume * 2.5));
        nodeSizes.push(size);
        
        nodeTexts.push(`Node: ${n.name} (${n.id})<br/>Type: ${n.type}<br/>Total volume handled: ${n.volume} units`);
    });
    
    traces.push({
        x: nodeX,
        y: nodeY,
        type: "scatter",
        mode: "markers+text",
        marker: {
            size: nodeSizes,
            color: nodeColors,
            line: { color: "#ffffff", width: 1.5 }
        },
        hoverinfo: "text",
        text: nodes.map(n => n.id),
        textposition: "top center",
        textfont: {
            color: "#e2e8f0",
            size: 10,
            family: "Inter"
        },
        hovertext: nodeTexts
    });
    
    const layout = {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        hovermode: "closest",
        showlegend: false,
        margin: { l: 20, r: 20, t: 20, b: 20 },
        xaxis: { showgrid: false, zeroline: false, showticklabels: false },
        yaxis: { showgrid: false, zeroline: false, showticklabels: false }
    };
    
    Plotly.newPlot("chart-network-graph", traces, layout, { responsive: true, displayModeBar: false });
}

function renderBottlenecksPanel(bottlenecks) {
    const listPanel = document.getElementById("routes-bottlenecks-list");
    listPanel.innerHTML = "";
    
    if (bottlenecks.length === 0) {
        listPanel.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 2rem;">
                <i class="fa-solid fa-circle-check text-success" style="font-size: 2rem; margin-bottom: 0.5rem;"></i>
                <p>No operational bottlenecks detected in the current network segment.</p>
            </div>
        `;
        return;
    }
    
    bottlenecks.forEach(b => {
        const item = document.createElement("div");
        item.className = "bottleneck-card-item";
        item.style.cursor = "pointer";
        item.onclick = () => showRouteDetailsModal(b.origin, b.destination);
        item.innerHTML = `
            <h5>${b.origin} &rarr; ${b.destination}</h5>
            <p>Type: <strong>${b.route_type}</strong> | Volume: <strong>${b.shipment_count} shipments</strong></p>
            <p>Avg Cost: <strong>$${b.avg_cost.toFixed(2)}</strong> | Avg Transit: <strong>${b.transit_time} Days</strong></p>
            <span class="reasons-tag"><i class="fa-solid fa-triangle-exclamation"></i> ${b.bottleneck_reason}</span>
        `;
        listPanel.appendChild(item);
    });
}

function renderRouteTable(routes) {
    const tbody = document.getElementById("routes-table-body");
    tbody.innerHTML = "";
    
    routes.forEach(r => {
        const tr = document.createElement("tr");
        tr.style.cursor = "pointer";
        tr.onclick = () => showRouteDetailsModal(r.origin, r.destination);
        
        const complMet = r.status_dist["MET"] || 0;
        const complMissed = r.status_dist["MISSED"] || 0;
        const complianceRate = r.shipment_count > 0 
            ? ((complMet / r.shipment_count) * 100.0).toFixed(0) 
            : 0;
        
        const complianceColor = complianceRate >= 80 ? "text-success" : complianceRate >= 50 ? "text-warning" : "text-danger";
        
        const bottleneckBadge = r.is_bottleneck 
            ? `<span class="badge badge-danger"><i class="fa-solid fa-triangle-exclamation"></i> Bottleneck</span>` 
            : `<span class="badge badge-success"><i class="fa-solid fa-circle-check"></i> Nominal</span>`;
            
        tr.innerHTML = `
            <td><strong>${r.origin}</strong></td>
            <td><strong>${r.destination}</strong></td>
            <td><span class="text-muted" style="font-size: 12px;">${r.route_type}</span></td>
            <td class="text-right">${r.distance} mi</td>
            <td class="text-right">${r.transit_time} Days</td>
            <td class="text-right"><strong>${r.shipment_count}</strong></td>
            <td class="text-right">$${r.avg_cost.toFixed(2)}</td>
            <td><span class="${complianceColor}"><strong>${complianceRate}%</strong></span> <span class="text-muted" style="font-size: 11px;">(${complMet}/${r.shipment_count})</span></td>
            <td>${bottleneckBadge}</td>
        `;
        
        tbody.appendChild(tr);
    });
    window.EnhancedTable.init(tbody.closest("table"));
}

function renderFlowAnalysis(flows) {
    const tbody = document.getElementById("flows-table-body");
    tbody.innerHTML = "";
    
    // Sort hubs alphabetically
    const hubs = Object.keys(flows.hubs).sort();
    
    hubs.forEach(h => {
        const stats = flows.hubs[h];
        const tr = document.createElement("tr");
        
        const total = stats.inbound + stats.outbound;
        const outboundPct = total > 0 ? ((stats.outbound / total) * 100.0).toFixed(0) : 50;
        
        const imbalanceColor = stats.net > 0 ? "text-success" : stats.net < 0 ? "text-danger" : "text-muted";
        const imbalanceText = stats.net > 0 ? `+${stats.net} Outbound` : `${stats.net} Inbound`;
        
        tr.innerHTML = `
            <td><strong>${h} Hub Node</strong></td>
            <td class="text-right">${stats.inbound} units</td>
            <td class="text-right">${stats.outbound} units</td>
            <td class="text-right"><span class="${imbalanceColor}"><strong>${imbalanceText}</strong></span></td>
            <td>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span class="text-muted" style="font-size: 11px;">In</span>
                    <div class="flow-split-bar">
                        <div class="flow-split-fill" style="width: ${outboundPct}%;"></div>
                    </div>
                    <span class="text-muted" style="font-size: 11px;">Out</span>
                </div>
            </td>
        `;
        
        tbody.appendChild(tr);
    });
    window.EnhancedTable.init(tbody.closest("table"));
}

function showRouteDetailsModal(origin, dest) {
    console.log(`Route Selected event logged. Route: ${origin} -> ${dest}`);
    
    const routes = routeState.data.routes || [];
    const r = routes.find(item => item.origin === origin && item.destination === dest);
    if (!r) return;
    
    // Populate simple tags
    document.getElementById("route-modal-origin").textContent = r.origin;
    document.getElementById("route-modal-dest").textContent = r.destination;
    document.getElementById("route-modal-type").textContent = r.route_type;
    document.getElementById("route-modal-distance").textContent = `${r.distance} mi`;
    document.getElementById("route-modal-transit").textContent = `${r.transit_time} Days`;
    document.getElementById("route-modal-cost").textContent = `$${r.avg_cost.toFixed(2)}`;
    
    document.getElementById("route-modal-shipments").textContent = r.shipment_count;
    
    const metCount = r.status_dist["MET"] || 0;
    const missedCount = r.status_dist["MISSED"] || 0;
    const metPct = r.shipment_count > 0 
        ? ((metCount / r.shipment_count) * 100.0).toFixed(0) 
        : 0;
    
    document.getElementById("route-modal-sla-met").textContent = `${metCount} shipments`;
    document.getElementById("route-modal-sla-missed").textContent = `${missedCount} shipments`;
    document.getElementById("route-modal-sla-rate").textContent = `${metPct}% Compliance`;
    
    const bTag = document.getElementById("route-modal-bottleneck");
    if (r.is_bottleneck) {
        bTag.innerHTML = `<span class="text-danger"><i class="fa-solid fa-triangle-exclamation"></i> Bottleneck Alert (${r.bottleneck_reason})</span>`;
    } else {
        bTag.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check"></i> Nominal Performance</span>`;
    }
    
    // Populate parts list
    const partsUl = document.getElementById("route-modal-parts-list");
    partsUl.innerHTML = "";
    r.parts.forEach(p => {
        const li = document.createElement("li");
        li.textContent = p;
        partsUl.appendChild(li);
    });
    
    // Populate partners list
    const partnersUl = document.getElementById("route-modal-partners-list");
    partnersUl.innerHTML = "";
    r.partners.forEach(partner => {
        const li = document.createElement("li");
        li.textContent = partner;
        partnersUl.appendChild(li);
    });
    
    // Fetch individual transactions from dashboard memory if available, or just render placeholders
    const txBody = document.getElementById("route-modal-table-body");
    txBody.innerHTML = "";
    
    // Query actual filtered shipments if we can scan the loaded dashboard transactions
    const matchingTxns = [];
    // Search in global dashboard state transactions if loaded
    if (dashboardState && dashboardState.data && dashboardState.data.transactions) {
        dashboardState.data.transactions.forEach(tx => {
            if (tx.Origin_Hub === r.origin && (tx.Destination_Hub === r.destination || (tx.Logistics_Partner === r.destination && r.route_type === "Outbound to TPR"))) {
                matchingTxns.push(tx);
            }
        });
    }
    
    if (matchingTxns.length === 0) {
        // Fallback: render dummy records derived from statistical breakdown if dashboard state isn't active
        for (let i = 0; i < r.shipment_count; i++) {
            const isMissed = i < missedCount;
            txBody.innerHTML += `
                <tr>
                    <td>TX-EST-${1000 + i}</td>
                    <td>2026-07-0${i + 1}</td>
                    <td>2026-07-0${i + 3}</td>
                    <td class="text-right">5</td>
                    <td><span class="badge badge-${isMissed ? "danger" : "success"}">${isMissed ? "MISSED" : "MET"}</span></td>
                    <td class="text-right">$${r.avg_cost.toFixed(2)}</td>
                </tr>
            `;
        }
    } else {
        matchingTxns.forEach(tx => {
            const isMissed = tx.SLA_Status === "MISSED";
            txBody.innerHTML += `
                <tr>
                    <td><strong>${tx.Transaction_ID}</strong></td>
                    <td>${tx.Order_Date.split("T")[0]}</td>
                    <td>${tx.Delivery_Date.split("T")[0]}</td>
                    <td class="text-right">${tx.Quantity}</td>
                    <td><span class="badge badge-${isMissed ? "danger" : "success"}">${tx.SLA_Status}</span></td>
                    <td class="text-right">$${parseFloat(tx.Shipment_Cost).toFixed(2)}</td>
                </tr>
            `;
        });
    }
    
    document.getElementById("route-details-modal").style.display = "flex";
}

function closeRouteDetailsModal() {
    document.getElementById("route-details-modal").style.display = "none";
}

function applyRouteFilters() {
    console.log("[Observability] Filters Applied");
    console.log("Filters Applied event logged.");
    
    routeState.filters.start_date = document.getElementById("route-filter-start-date").value;
    routeState.filters.end_date = document.getElementById("route-filter-end-date").value;
    routeState.filters.hub = document.getElementById("route-filter-hub").value;
    routeState.filters.repair_center = document.getElementById("route-filter-rc").value;
    routeState.filters.part_category = document.getElementById("route-filter-category").value;
    routeState.filters.partner = document.getElementById("route-filter-partner").value;
    routeState.filters.priority = document.getElementById("route-filter-priority").value;
    
    loadRouteIntelligence();
}

function clearRouteFilters() {
    routeState.filters = {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: ""
    };
    
    document.getElementById("route-filter-start-date").value = "";
    document.getElementById("route-filter-end-date").value = "";
    document.getElementById("route-filter-hub").value = "";
    document.getElementById("route-filter-rc").value = "";
    document.getElementById("route-filter-category").value = "";
    document.getElementById("route-filter-partner").value = "";
    document.getElementById("route-filter-priority").value = "";
    
    loadRouteIntelligence();
}

// ==========================================
// LOGISTICS PERFORMANCE MONITORING CONTROLLER
// ==========================================

const API_PERFORMANCE = "/api/performance/payload";

let perfState = {
    filters: {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: "",
        status: ""
    },
    data: null,
    dropdownsPopulated: false
};

async function loadLogisticsPerformance() {
    console.log("Performance Dashboard Loaded event logged.");
    
    try {
        const payload = await fetchPerformanceData();
        perfState.data = payload;
        
        // 1. Update 10 Overview KPI Cards
        updatePerfOverviewPanel(payload.kpis);
        
        // 2. Populate Dropdowns dynamically once
        if (!perfState.dropdownsPopulated) {
            populatePerfDropdowns(payload);
        }
        
        // 3. Render Distribution & Trend Charts via Plotly
        renderPerfCharts(payload);
        
        // 4. Render Hub & Repair Center Performance Scorecards
        renderPerfScorecards(payload.hub_scorecard, payload.rc_scorecard);
        
    } catch (err) {
        console.error("loadLogisticsPerformance Error:", err);
        window.ErrorState.renderTableError("tbl-perf-hub-scorecard", 5, "Connection Error", "Failed to fetch hub performance scores.", () => loadLogisticsPerformance());
        window.ErrorState.renderTableError("tbl-perf-rc-scorecard", 5, "Connection Error", "Failed to fetch center performance scores.", () => loadLogisticsPerformance());
    }
}

async function fetchPerformanceData() {
    const res = await fetch(API_PERFORMANCE, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filters: perfState.filters })
    });
    if (!res.ok) throw new Error("Failed fetching performance monitoring payload");
    return await res.json();
}

function updatePerfOverviewPanel(kpis) {
    kpis = kpis || {};
    document.getElementById("kpi-perf-transit").textContent = window.Formatters.safeDuration(kpis.avg_transit_time);
    document.getElementById("kpi-perf-cost").textContent = window.Formatters.safeCurrency(kpis.avg_logistics_cost);
    document.getElementById("kpi-perf-route-util").textContent = window.Formatters.safePercentage(kpis.avg_route_utilization);
    document.getElementById("kpi-perf-delay").textContent = window.Formatters.safeDuration(kpis.avg_shipment_delay);
    document.getElementById("kpi-perf-hub-util").textContent = window.Formatters.safePercentage(kpis.avg_hub_utilization);
    document.getElementById("kpi-perf-rc-util").textContent = window.Formatters.safePercentage(kpis.avg_rc_utilization);
    document.getElementById("kpi-perf-otd").textContent = window.Formatters.safePercentage(kpis.on_time_delivery_pct);
    document.getElementById("kpi-perf-delayed-pct").textContent = window.Formatters.safePercentage(kpis.delayed_shipment_pct);
    document.getElementById("kpi-perf-day-vol").textContent = window.Formatters.safeNumber(kpis.avg_shipments_per_day);
    document.getElementById("kpi-perf-route-vol").textContent = window.Formatters.safeNumber(kpis.avg_shipments_per_route);
    
    console.log("KPIs Calculated event logged.");
}

function populatePerfDropdowns(data) {
    const fillSelect = (elementId, list, keyField, labelField) => {
        const select = document.getElementById(elementId);
        if (!select) return;
        
        const firstOpt = select.options[0];
        select.innerHTML = "";
        select.appendChild(firstOpt);
        
        list.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item[keyField];
            opt.textContent = item[labelField || keyField];
            select.appendChild(opt);
        });
    };

    const hubsList = (data.hub_scorecard || []);
    fillSelect("perf-filter-hub", hubsList, "id", "name");

    const rcsList = (data.rc_scorecard || []);
    fillSelect("perf-filter-rc", rcsList, "id", "name");

    const categoriesList = [
        { name: "Electronics" }, { name: "Mechanical" }, { name: "Cooling" }
    ];
    fillSelect("perf-filter-category", categoriesList, "name");

    const partnersList = [
        { name: "Swift LogiCo" }, { name: "Apex Freight" }, { name: "LoneStar Delivery" }
    ];
    fillSelect("perf-filter-partner", partnersList, "name");

    perfState.dropdownsPopulated = true;
}

function renderPerfCharts(payload) {
    console.log("Charts Rendered event logged.");
    
    const daily = payload.trends.daily || [];
    
    // Layout template for dashboard consistency
    const getBaseLayout = (title) => ({
        title: { text: title, font: { color: "#e2e8f0", size: 13, family: "Inter" } },
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        margin: { l: 40, r: 20, t: 40, b: 40 },
        xaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 10 } },
        yaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 10 } }
    });

    // 1. Tabbed Charts: Distributions
    // Transit Distribution (bar histogram)
    const transitVals = daily.map(d => d.avg_transit_time);
    const transitCounts = {};
    transitVals.forEach(v => {
        const key = Math.round(v);
        transitCounts[key] = (transitCounts[key] || 0) + 1;
    });
    
    const transitX = Object.keys(transitCounts).sort((a,b)=>a-b);
    const transitY = transitX.map(x => transitCounts[x]);
    
    Plotly.newPlot("chart-perf-transit-dist", [{
        x: transitX.map(x => `${x} Days`),
        y: transitY,
        type: "bar",
        marker: { color: "#00a8cc" }
    }], getBaseLayout("Transit Duration Frequency Distribution"), { responsive: true, displayModeBar: false });

    // Cost Distribution (histogram representation)
    const costVals = daily.map(d => d.avg_cost);
    Plotly.newPlot("chart-perf-cost-dist", [{
        x: costVals,
        type: "histogram",
        marker: { color: "#10b981" },
        nbinsx: 10
    }], getBaseLayout("Average Daily Shipment Cost Distribution"), { responsive: true, displayModeBar: false });

    // 2. Tabbed Charts: Trends (Daily Series)
    const dates = daily.map(d => d.date);
    const volumes = daily.map(d => d.shipment_volume);
    const costs = daily.map(d => d.avg_cost);
    
    // Daily Volume Line
    Plotly.newPlot("chart-perf-daily-volume", [{
        x: dates,
        y: volumes,
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#00a8cc", width: 2.5 },
        marker: { size: 6 }
    }], getBaseLayout("Daily Shipment Volume Timeline"), { responsive: true, displayModeBar: false });

    // Daily Cost Line
    Plotly.newPlot("chart-perf-daily-cost", [{
        x: dates,
        y: costs,
        type: "scatter",
        mode: "lines+markers",
        line: { color: "#10b981", width: 2.5 },
        marker: { size: 6 }
    }], getBaseLayout("Average Daily Shipment Cost Timeline"), { responsive: true, displayModeBar: false });

    // 3. Cost & Delay Analysis Breakdowns
    const da = payload.delay_analysis;
    const ca = payload.cost_analysis;

    // Delay by Priority Bar
    const prioX = Object.keys(da.by_priority);
    const prioY = prioX.map(x => da.by_priority[x]);
    Plotly.newPlot("chart-perf-delay-priority", [{
        x: prioX,
        y: prioY,
        type: "bar",
        marker: { color: "#ef4444" }
    }], {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        margin: { l: 30, r: 10, t: 20, b: 30 },
        xaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } },
        yaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } }
    }, { responsive: true, displayModeBar: false });

    // Delay by Partner Pie Chart
    const partnerKeys = Object.keys(da.by_partner);
    const partnerVals = partnerKeys.map(k => da.by_partner[k]);
    Plotly.newPlot("chart-perf-delay-partner", [{
        labels: partnerKeys,
        values: partnerVals,
        type: "pie",
        hole: 0.4,
        marker: { colors: ["#3b82f6", "#10b981", "#f59e0b"] }
    }], {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        margin: { l: 10, r: 10, t: 20, b: 10 },
        legend: { font: { color: "#9ca3af", size: 9 } }
    }, { responsive: true, displayModeBar: false });

    // Cost by Category Horizontal Bar
    const catKeys = Object.keys(ca.by_category);
    const catVals = catKeys.map(k => ca.by_category[k]);
    Plotly.newPlot("chart-perf-cost-category", [{
        y: catKeys,
        x: catVals,
        type: "bar",
        orientation: "h",
        marker: { color: "#10b981" }
    }], {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        margin: { l: 80, r: 10, t: 20, b: 30 },
        xaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } },
        yaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } }
    }, { responsive: true, displayModeBar: false });

    // Cost by Hub Vertical Bar
    const hubKeys = Object.keys(ca.by_hub);
    const hubVals = hubKeys.map(k => ca.by_hub[k]);
    Plotly.newPlot("chart-perf-cost-hub", [{
        x: hubKeys,
        y: hubVals,
        type: "bar",
        marker: { color: "#00a8cc" }
    }], {
        paper_bgcolor: "#111827",
        plot_bgcolor: "#111827",
        margin: { l: 40, r: 10, t: 20, b: 30 },
        xaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } },
        yaxis: { gridcolor: "#1f2937", tickfont: { color: "#9ca3af", size: 9 } }
    }, { responsive: true, displayModeBar: false });
}

function renderPerfScorecards(hubs, rcs) {
    console.log("Scorecards Generated event logged.");
    
    // Render Hub Scorecard
    const hubBody = document.getElementById("tbl-perf-hub-scorecard");
    hubBody.innerHTML = "";
    hubs.forEach(h => {
        const scoreColor = h.performance_score >= 80 ? "text-success" : h.performance_score >= 50 ? "text-warning" : "text-danger";
        hubBody.innerHTML += `
            <tr>
                <td><strong>${h.name}</strong></td>
                <td class="text-right">${h.total_shipments}</td>
                <td class="text-right">$${h.avg_logistics_cost.toFixed(2)}</td>
                <td class="text-right"><strong>${h.capacity_utilization}%</strong></td>
                <td class="text-right"><span class="${scoreColor}"><strong>${h.performance_score}</strong></span></td>
            </tr>
        `;
    });

    // Render RC Scorecard
    const rcBody = document.getElementById("tbl-perf-rc-scorecard");
    rcBody.innerHTML = "";
    rcs.forEach(rc => {
        const scoreColor = rc.performance_score >= 80 ? "text-success" : rc.performance_score >= 50 ? "text-warning" : "text-danger";
        rcBody.innerHTML += `
            <tr>
                <td><strong>${rc.name}</strong></td>
                <td class="text-right">${rc.incoming_shipments}</td>
                <td class="text-right">${rc.avg_processing_time} Days</td>
                <td class="text-right"><strong>${rc.capacity_utilization}%</strong></td>
                <td class="text-right"><span class="${scoreColor}"><strong>${rc.performance_score}</strong></span></td>
            </tr>
        `;
    });
}

function switchPerfTab(tabName) {
    const distTabBtn = document.getElementById("btn-tab-distributions");
    const trendsTabBtn = document.getElementById("btn-tab-trends");
    
    const distContent = document.getElementById("perf-tab-distributions-content");
    const trendsContent = document.getElementById("perf-tab-trends-content");
    
    if (tabName === "distributions") {
        distTabBtn.classList.add("active");
        trendsTabBtn.classList.remove("active");
        distContent.style.display = "grid";
        trendsContent.style.display = "none";
    } else {
        distTabBtn.classList.remove("active");
        trendsTabBtn.classList.add("active");
        distContent.style.display = "none";
        trendsContent.style.display = "grid";
        
        // Trigger relayout on Plotly charts to fix sizing in hidden viewports
        setTimeout(() => {
            Plotly.Plots.resize("chart-perf-daily-volume");
            Plotly.Plots.resize("chart-perf-daily-cost");
        }, 50);
    }
}

function applyPerfFilters() {
    console.log("[Observability] Filters Applied");
    console.log("Filters Applied event logged.");
    
    perfState.filters.start_date = document.getElementById("perf-filter-start-date").value;
    perfState.filters.end_date = document.getElementById("perf-filter-end-date").value;
    perfState.filters.hub = document.getElementById("perf-filter-hub").value;
    perfState.filters.repair_center = document.getElementById("perf-filter-rc").value;
    perfState.filters.part_category = document.getElementById("perf-filter-category").value;
    perfState.filters.partner = document.getElementById("perf-filter-partner").value;
    perfState.filters.priority = document.getElementById("perf-filter-priority").value;
    perfState.filters.status = document.getElementById("perf-filter-status").value;
    
    loadLogisticsPerformance();
}

function clearPerfFilters() {
    perfState.filters = {
        start_date: "",
        end_date: "",
        hub: "",
        repair_center: "",
        part_category: "",
        partner: "",
        priority: "",
        status: ""
    };
    
    document.getElementById("perf-filter-start-date").value = "";
    document.getElementById("perf-filter-end-date").value = "";
    document.getElementById("perf-filter-hub").value = "";
    document.getElementById("perf-filter-rc").value = "";
    document.getElementById("perf-filter-category").value = "";
    document.getElementById("perf-filter-partner").value = "";
    document.getElementById("perf-filter-priority").value = "";
    document.getElementById("perf-filter-status").value = "";
    
    loadLogisticsPerformance();
}



// ==========================================
// ADMINISTRATION & OPERATIONS CENTER (PHASE 33)
// ==========================================

// API endpoint constants for admin center
const API_MONITORING_HEALTH    = "/api/v1/monitoring/health";
const API_MONITORING_METRICS   = "/api/v1/monitoring/metrics";
const API_MONITORING_DIAG      = "/api/v1/monitoring/diagnostics";
const API_SECURITY_AUDIT_LOGS  = "/api/v1/security/audit-logs";

/**
 * Loads the Administration & Operations Center:
 * Fetches system health, telemetry metrics, and audit logs.
 */
async function loadAdminCenter() {
    console.log("[Observability] Admin Dashboard Loaded");
    await Promise.allSettled([
        loadAdminHealth(),
        loadAdminMetrics(),
        loadAdminAuditLogs()
    ]);
    console.log("[Observability] Operations Center Loaded");
}

/**
 * Fetches system health and populates the services table and KPI cards.
 */
async function loadAdminHealth() {
    try {
        const res = await fetch(API_MONITORING_HEALTH);
        if (!res.ok) throw new Error("Health check failed");
        const data = await res.json();

        // Update KPI card — overall health status
        const healthEl = document.getElementById("admin-system-health");
        if (healthEl) {
            const status = data.overall_status || "UNKNOWN";
            healthEl.textContent = status;
            healthEl.className = "metric-value " + (status === "UP" ? "text-success" : "text-danger");
        }

        // Populate services table
        const tbody = document.getElementById("tbl-admin-services");
        if (tbody && data.services) {
            tbody.innerHTML = "";
            data.services.forEach(svc => {
                const isUp = svc.status === "UP" || svc.status === "HEALTHY" || svc.status === "OPERATIONAL";
                const badgeClass = isUp ? "success" : "danger";
                tbody.innerHTML += `
                    <tr>
                        <td><strong>${svc.name || svc.service || "-"}</strong></td>
                        <td><span class="badge ${badgeClass}">${svc.status || "UNKNOWN"}</span></td>
                        <td style="font-size: 11px; color: var(--text-muted);">${svc.detail || svc.version || "-"}</td>
                    </tr>`;
            });
        }

        console.log("[Observability] Health Refreshed");
    } catch (err) {
        console.error("[Admin] loadAdminHealth Error:", err);
    }
}

/**
 * Fetches telemetry metrics snapshot and populates diagnostics panel + KPI tiles.
 */
async function loadAdminMetrics() {
    try {
        const res = await fetch(API_MONITORING_METRICS);
        if (!res.ok) throw new Error("Metrics fetch failed");
        const data = await res.json();

        // KPI tiles
        const latencyEl = document.getElementById("admin-api-latency");
        if (latencyEl && data.api_response_time_avg != null) {
            latencyEl.textContent = data.api_response_time_avg.toFixed(2) + " ms";
        }
        const reqEl = document.getElementById("admin-api-requests");
        if (reqEl && data.active_requests != null) {
            reqEl.textContent = data.active_requests;
        }

        // Diagnostics table
        const memEl = document.getElementById("diagnostics-memory");
        if (memEl && data.memory_usage_bytes != null) {
            memEl.textContent = (data.memory_usage_bytes / (1024 * 1024)).toFixed(1) + " MB";
        }
        const errRateEl = document.getElementById("diagnostics-error-rate");
        if (errRateEl && data.error_rate != null) {
            errRateEl.textContent = (data.error_rate * 100).toFixed(2) + "%";
        }
        const cacheHitsEl = document.getElementById("diagnostics-cache-hits");
        if (cacheHitsEl && data.cache_hit_ratio != null) {
            cacheHitsEl.textContent = (data.cache_hit_ratio * 100).toFixed(1) + "%";
        }
        const cacheMissEl = document.getElementById("diagnostics-cache-misses");
        if (cacheMissEl && data.cache_miss_ratio != null) {
            cacheMissEl.textContent = (data.cache_miss_ratio * 100).toFixed(1) + "%";
        }

        console.log("[Observability] System Status Updated");
    } catch (err) {
        console.error("[Admin] loadAdminMetrics Error:", err);
    }
}

/**
 * Fetches security audit logs and renders them in the audit table.
 */
async function loadAdminAuditLogs() {
    try {
        const res = await fetch(API_SECURITY_AUDIT_LOGS);
        if (!res.ok) throw new Error("Audit logs fetch failed");
        const logs = await res.json();

        const tbody = document.getElementById("tbl-admin-audit-logs");
        if (!tbody) return;
        tbody.innerHTML = "";

        if (!logs || logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted" style="padding: 1.5rem;">No audit events recorded.</td></tr>`;
            return;
        }

        const STATUS_COLOR = { SUCCESS: "success", FAILED: "danger", PARTIAL: "warning" };
        const recent = [...logs].reverse().slice(0, 50);
        recent.forEach(log => {
            const badgeClass = STATUS_COLOR[log.status] || "";
            tbody.innerHTML += `
                <tr>
                    <td style="font-size: 11px; color: var(--text-muted); white-space: nowrap;">${log.timestamp || "-"}</td>
                    <td><strong>${log.event_type || "-"}</strong><br/><span style="font-size: 11px; color: var(--text-muted);">${log.user_id || "System"}</span></td>
                    <td><span class="badge ${badgeClass}">${log.status || "-"}</span></td>
                    <td style="font-size: 11px; color: var(--text-muted); max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${(log.detail || "").replace(/"/g, "&quot;")}">${log.detail || "-"}</td>
                </tr>`;
        });
    } catch (err) {
        console.error("[Admin] loadAdminAuditLogs Error:", err);
        const tbody = document.getElementById("tbl-admin-audit-logs");
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted" style="padding: 1.5rem;">Unable to retrieve audit logs. Insufficient permissions or connection error.</td></tr>`;
        }
    }
}

/**
 * Refreshes admin health data on demand (triggered by Refresh button).
 */
async function refreshAdminHealth() {
    console.log("[Observability] Health Refreshed");
    await Promise.allSettled([loadAdminHealth(), loadAdminMetrics()]);
}

/**
 * Saves the operational configuration to localStorage and logs the action.
 */
function saveAdminConfig(event) {
    event.preventDefault();
    const config = {
        optimization_mode:  document.getElementById("config-opt-mode")?.value,
        log_level:          document.getElementById("config-log-level")?.value,
        security_level:     document.getElementById("config-security-level")?.value,
        cache_timeout:      document.getElementById("config-cache-timeout")?.value
    };
    localStorage.setItem("dell_admin_config", JSON.stringify(config));
    console.log("[Observability] Configuration Loaded", config);
    alert("Configuration saved successfully.");
}

/**
 * Restores previously saved configuration from localStorage on admin section load.
 */
function restoreAdminConfig() {
    try {
        const saved = JSON.parse(localStorage.getItem("dell_admin_config") || "null");
        if (!saved) return;
        if (saved.optimization_mode) {
            const el = document.getElementById("config-opt-mode");
            if (el) el.value = saved.optimization_mode;
        }
        if (saved.log_level) {
            const el = document.getElementById("config-log-level");
            if (el) el.value = saved.log_level;
        }
        if (saved.security_level) {
            const el = document.getElementById("config-security-level");
            if (el) el.value = saved.security_level;
        }
        if (saved.cache_timeout) {
            const el = document.getElementById("config-cache-timeout");
            if (el) el.value = saved.cache_timeout;
        }
    } catch (e) {
        // ignore parse errors
    }
}

