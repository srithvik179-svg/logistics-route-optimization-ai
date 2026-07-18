// API Endpoints
const API_STATUS_URL = "/api/dataset/status";
const API_RELOAD_URL = "/api/dataset/reload";

// Global state holding loaded dataset report details
let currentReport = null;

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
            } else if (targetId === "dataset-section") {
                headerTitle.textContent = "Dataset Loading & Validation";
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
        const [datasetRes, repositoryRes] = await Promise.all([
            fetch(API_STATUS_URL),
            fetch("/api/repository/status")
        ]);

        if (!datasetRes.ok || !repositoryRes.ok) {
            throw new Error("HTTP error fetching platform status");
        }

        const datasetData = await datasetRes.json();
        const repositoryData = await repositoryRes.json();
        
        // Update connection status UI
        apiIndicator.className = "status-indicator connected";
        apiIndicator.querySelector(".status-text").textContent = "Connected to API";
        
        currentReport = datasetData;
        renderDashboard(datasetData);
        renderRepository(repositoryData);
        
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

        // Fetch repository status concurrently
        const repositoryRes = await fetch("/api/repository/status");
        if (repositoryRes.ok) {
            const repositoryData = await repositoryRes.json();
            renderRepository(repositoryData);
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
