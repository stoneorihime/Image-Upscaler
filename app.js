/* ═══════════════════════════════════════════════════════════════════
   MangaScale — Frontend Application Logic
   ═══════════════════════════════════════════════════════════════════ */

const API = "";  // same-origin
let selectedFiles = [];
let currentJobId = null;
let pollTimer = null;

// ── DOM refs ───────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const statusBadge     = $("#statusBadge");
const badgeDot        = statusBadge.querySelector(".badge-dot");
const badgeText       = statusBadge.querySelector(".badge-text");

const dropZone        = $("#dropZone");
const fileInput       = $("#fileInput");
const browseBtn       = $("#browseBtn");
const fileList        = $("#fileList");
const fileCount       = $("#fileCount");
const fileItems       = $("#fileItems");
const clearFilesBtn   = $("#clearFilesBtn");

const settingsSection = $("#settingsSection");
const outputDirInput  = $("#outputDirInput");
const engineSelect     = $("#engineSelect");

const startBtn        = $("#startBtn");

const progressSection = $("#progressSection");
const progressCard    = $("#progressCard");
const progressLabel   = $("#progressLabel");
const progressCount   = $("#progressCount");
const progressBarFill = $("#progressBarFill");
const progressFile    = $("#progressFile");
const progressSpinner = $("#progressSpinner");
const warningsBox     = $("#warningsBox");
const warningsList    = $("#warningsList");

const resultsSection  = $("#resultsSection");
const resultsSummary  = $("#resultsSummary");
const resultsGrid     = $("#resultsGrid");
const downloadZipBtn  = $("#downloadZipBtn");
const newJobBtn       = $("#newJobBtn");
const outputPath      = $("#outputPath");
const uploadSection   = $("#uploadSection");
const previewModal    = $("#previewModal");
const previewImage    = $("#previewImage");
const previewTitle    = $("#previewTitle");
const previewDownload = $("#previewDownloadBtn");
const closeModalBtn   = $("#closeModalBtn");

badgeDot.className = "badge-dot online";
badgeText.textContent = "Lanczos Ready";
// ── File helpers ───────────────────────────────────────────────────
function humanSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function isAllowed(name) {
    const ext = name.split(".").pop().toLowerCase();
    return ["png","jpg","jpeg","webp","bmp","tiff","tif","zip"].includes(ext);
}

function fileIcon(name) {
    const ext = name.split(".").pop().toLowerCase();
    if (ext === "zip") return "";
    return "";
}

function renderFileList() {
    fileItems.innerHTML = "";
    selectedFiles.forEach((f, i) => {
        const li = document.createElement("li");
        li.style.animationDelay = `${i * 0.04}s`;
        li.className = "fadeInUp";
        li.innerHTML = `
            <span class="file-icon">${fileIcon(f.name)}</span>
            <span class="file-name">${f.name}</span>
            <span class="file-size">${humanSize(f.size)}</span>
        `;
        fileItems.appendChild(li);
    });
    fileCount.textContent = `${selectedFiles.length} file${selectedFiles.length !== 1 ? "s" : ""} selected`;
    fileList.hidden = selectedFiles.length === 0;
    settingsSection.hidden = selectedFiles.length === 0;
}

function addFiles(fileListObj) {
    for (const f of fileListObj) {
        if (isAllowed(f.name) && !selectedFiles.some(sf => sf.name === f.name && sf.size === f.size)) {
            selectedFiles.push(f);
        }
    }
    renderFileList();
}

// ── Drop Zone events ───────────────────────────────────────────────
browseBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
    addFiles(fileInput.files);
    fileInput.value = "";
});

dropZone.addEventListener("click", (e) => {
    if (e.target !== browseBtn) fileInput.click();
});

["dragenter","dragover"].forEach(ev => {
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.add("drag-over");
    });
});
["dragleave","drop"].forEach(ev => {
    dropZone.addEventListener(ev, (e) => {
        e.preventDefault();
        dropZone.classList.remove("drag-over");
    });
});
dropZone.addEventListener("drop", (e) => {
    addFiles(e.dataTransfer.files);
});

clearFilesBtn.addEventListener("click", () => {
    selectedFiles = [];
    renderFileList();
});

// ── Start upscaling ────────────────────────────────────────────────
startBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) return;

    startBtn.disabled = true;
    startBtn.textContent = "Uploading…";

    const formData = new FormData();
    selectedFiles.forEach(f => formData.append("files", f));
    const customDir = outputDirInput.value.trim();
    if (customDir) formData.append("output_dir", customDir);
    formData.append("method", engineSelect.value);

    try {
        const res = await fetch(`${API}/api/upscale`, { method: "POST", body: formData });
        const data = await res.json();
        if (!res.ok) {
            alert(data.error || "Upload failed");
            startBtn.disabled = false;
            startBtn.textContent = "⚡ Start Upscaling";
            return;
        }

        currentJobId = data.job_id;
        showProgress(data.total_images);
        startPolling();
    } catch (err) {
        alert("Connection error: " + err.message);
        startBtn.disabled = false;
        startBtn.textContent = "Start Upscaling";
    }
});

// ── Progress polling ───────────────────────────────────────────────
function showProgress(total) {
    uploadSection.hidden = true;
    settingsSection.hidden = true;
    progressSection.hidden = false;
    resultsSection.hidden = true;

    progressCount.textContent = `0 / ${total}`;
    progressBarFill.style.width = "0%";
    progressFile.textContent = "Starting…";
    progressLabel.textContent = "Upscaling…";
    progressCard.classList.remove("done");
    warningsBox.hidden = true;
    warningsList.innerHTML = "";
}

function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(pollJob, 1500);
}

async function pollJob() {
    if (!currentJobId) return;
    try {
        const res = await fetch(`${API}/api/job/${currentJobId}`);
        const job = await res.json();

        const pct = job.total > 0 ? Math.round((job.progress / job.total) * 100) : 0;
        progressBarFill.style.width = pct + "%";
        progressCount.textContent = `${job.progress} / ${job.total}`;
        progressFile.textContent = job.current_file || "Processing…";

        // warnings
        if (job.warnings && job.warnings.length > 0) {
            warningsBox.hidden = false;
            warningsList.innerHTML = job.warnings.map(w => `<li>${w}</li>`).join("");
        }

        if (job.status === "done") {
            clearInterval(pollTimer);
            pollTimer = null;
            progressLabel.textContent = "Complete!";
            progressCard.classList.add("done");
            showResults(job);
        }
    } catch (err) {
        console.error("Poll error:", err);
    }
}

// ── Results ────────────────────────────────────────────────────────
function showResults(job) {
    resultsSection.hidden = false;

    const count = job.files.length;
    resultsSummary.textContent = `${count} image${count !== 1 ? "s" : ""} upscaled to 4K successfully.`;
    outputPath.textContent = job.output_dir;

    resultsGrid.innerHTML = "";
    job.files.forEach((fp, i) => {
        const fname = fp.split(/[/\\]/).pop();
        const card = document.createElement("div");
        card.className = "result-card";
        card.style.animationDelay = `${i * 0.08}s`;
        const imgUrl = `${API}/api/job/${currentJobId}/file/${encodeURIComponent(fname)}`;
        card.innerHTML = `
            <img src="${imgUrl}" alt="${fname}" loading="lazy" />
            <div class="result-card-info">${fname}</div>
        `;
        card.addEventListener("click", () => openPreview(imgUrl, fname));
        resultsGrid.appendChild(card);
    });
}

// ── Preview Modal ──────────────────────────────────────────────────
function openPreview(url, name) {
    previewImage.src = url;
    previewTitle.textContent = name;
    previewDownload.href = url;
    previewModal.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closePreview() {
    previewModal.classList.remove("active");
    document.body.style.overflow = "";
    // Clear src after fade out to avoid flash on next open
    setTimeout(() => { if (!previewModal.classList.contains("active")) previewImage.src = ""; }, 300);
}

closeModalBtn.addEventListener("click", closePreview);
previewModal.addEventListener("click", (e) => {
    if (e.target === previewModal) closePreview();
});
window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && previewModal.classList.contains("active")) closePreview();
});

downloadZipBtn.addEventListener("click", () => {
    if (!currentJobId) return;
    window.open(`${API}/api/job/${currentJobId}/download`, "_blank");
});

newJobBtn.addEventListener("click", () => {
    currentJobId = null;
    selectedFiles = [];
    renderFileList();

    uploadSection.hidden = false;
    settingsSection.hidden = true;
    progressSection.hidden = true;
    resultsSection.hidden = true;

    startBtn.disabled = false;
    startBtn.textContent = "Start Upscaling";
});
