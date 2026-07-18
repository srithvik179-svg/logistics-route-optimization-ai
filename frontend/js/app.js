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
    initNavigation();
    fetchDatasetStatus();
});

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
        
    } catch (error) {
        console.error("API Connection Error:", error);
        apiIndicator.className = "status-indicator";
        apiIndicator.querySelector(".status-text").textContent = "API Offline";
        renderOfflineState();
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
// EXECUTIVE ANALYTICS DASHBOARD CONTROLLER
// ==========================================

async function loadExecutiveDashboard() {
    console.log("Dashboard Loaded event logged.");
    
    // Set loading placeholders
    const views = ["dashboard-kpi-grid-1", "dashboard-kpi-grid-2"];
    views.forEach(v => {
        document.querySelectorAll(`#${v} .metric-value`).forEach(val => {
            val.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="font-size: 14px;"></i>';
        });
    });

    try {
        const res = await fetch(API_DASHBOARD_URL);
        if (!res.ok) throw new Error("Failed fetching executive dashboard payload");
        const data = await res.json();
        
        console.log("Metrics Calculated and Summary Generated event logged.");
        
        // 1. Populate KPI Cards
        renderDashboardKPIs(data.kpis);
        
        // 2. Populate Summary Strip
        renderDashboardSummary(data.summary_info);
        
        // 3. Populate Tables
        renderDashboardTables(data.distributions);
        
        // 4. Render Plotly Charts
        renderDashboardCharts(data);
        
        console.log("Charts Generated event logged.");
        
    } catch (err) {
        console.error("loadExecutiveDashboard Error:", err);
        // Show placeholders
        views.forEach(v => {
            document.querySelectorAll(`#${v} .metric-value`).forEach(val => {
                val.textContent = "Error";
            });
        });
        alert("Failed loading analytics dashboard. Verify backend service is operational.");
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
    // Helper to render simple count/cost table rows
    const populateSummaryTable = (elementId, dataList, categoryKey) => {
        const tbody = document.getElementById(elementId);
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

function renderDashboardCharts(data) {
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

    // 1. Time Series Chart (Shipments & Costs over time)
    const ts = data.time_series || [];
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
    Plotly.newPlot('chart-time-series', [traceVol, traceCost], tsLayout, { responsive: true, displayModeBar: false });

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
    Plotly.newPlot('chart-flow-type', [flowTrace], flowLayout, { responsive: true, displayModeBar: false });

    // 3. SLA & Priority Distributions (Grouped/Stacked Bar chart)
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
    Plotly.newPlot('chart-sla-prio', [prioTrace], defaultLayoutProps, { responsive: true, displayModeBar: false });

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
    Plotly.newPlot('chart-part-cat', [catTrace], catLayout, { responsive: true, displayModeBar: false });

    // 5. Logistics Cost Distribution (Histogram box type)
    // Pull list of raw transaction costs
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

    // 6. Hub Types & Service Coverage (Bar chart)
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
}


