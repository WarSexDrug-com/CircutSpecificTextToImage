let currentJobId = null;
let pollInterval = null;
let zoomLevel = 1;
let presets = [];
let history = [];

function showToast(message, type = "error") {
    let container = document.getElementById("toastContainer");
    if (!container) {
        container = document.createElement("div");
        container.id = "toastContainer";
        container.style.cssText = "position:fixed;top:16px;right:16px;z-index:10000;display:flex;flex-direction:column;gap:8px;";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    const bg = type === "error" ? "#d32f2f" : type === "success" ? "#2e7d32" : "#1565c0";
    toast.style.cssText = `background:${bg};color:#fff;padding:12px 20px;border-radius:8px;font-size:14px;max-width:380px;box-shadow:0 4px 12px rgba(0,0,0,.4);animation:fadeIn .2s;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => { toast.style.opacity = "0"; toast.style.transition = "opacity .3s"; setTimeout(() => toast.remove(), 300); }, 5000);
}

document.addEventListener("DOMContentLoaded", () => {
    if (pollInterval) { clearInterval(pollInterval); pollInterval = null; }
    currentJobId = null;
    loadPalettes();
    updateColorPickers();
    setupSliders();
    document.getElementById("layerCount").addEventListener("change", updateColorPickers);
    document.getElementById("promptInput").addEventListener("keydown", (e) => {
        if (e.key === "Enter") generateDesign();
    });
});

async function loadPalettes() {
    try {
        const resp = await fetch("/api/palettes");
        presets = await resp.json();
        const select = document.getElementById("presetSelect");
        presets.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.name;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    } catch (e) {
        console.error("Failed to load palettes:", e);
    }
}

function setupSliders() {
    const sliders = [
        ["filterSpeckle", "filterSpeckleVal"],
        ["cornerThreshold", "cornerThresholdVal"],
    ];
    sliders.forEach(([id, valId]) => {
        const slider = document.getElementById(id);
        const val = document.getElementById(valId);
        slider.addEventListener("input", () => { val.textContent = slider.value; });
    });
}

function togglePaletteMode() {
    const mode = document.querySelector('input[name="paletteMode"]:checked').value;
    document.getElementById("colorPickers").style.display = mode === "manual" ? "flex" : "none";
    document.getElementById("palettePresets").style.display = mode === "manual" ? "block" : "none";
}

function updateColorPickers() {
    const count = parseInt(document.getElementById("layerCount").value);
    const container = document.getElementById("colorPickers");
    container.innerHTML = "";
    const defaults = ["#FF0000", "#0057B7", "#FFD700", "#228B22", "#FF6600", "#800080", "#00CED1", "#8B4513"];
    for (let i = 0; i < count; i++) {
        const item = document.createElement("div");
        item.className = "color-picker-item";
        item.innerHTML = `
            <input type="color" value="${defaults[i] || "#999999"}" data-layer="${i}">
            <span>L${i + 1}</span>
        `;
        container.appendChild(item);
    }
}

function applyPreset() {
    const name = document.getElementById("presetSelect").value;
    const preset = presets.find((p) => p.name === name);
    if (!preset) return;

    const count = parseInt(document.getElementById("layerCount").value);
    document.querySelector('input[name="paletteMode"][value="manual"]').checked = true;
    togglePaletteMode();

    const pickers = document.querySelectorAll('#colorPickers input[type="color"]');
    pickers.forEach((picker, i) => {
        if (i < preset.colors.length) {
            picker.value = preset.colors[i];
        }
    });
}

function toggleAdvanced() {
    const body = document.getElementById("advancedSettings");
    const arrow = document.getElementById("advancedArrow");
    const isOpen = body.style.display !== "none";
    body.style.display = isOpen ? "none" : "block";
    arrow.classList.toggle("open", !isOpen);
}

function getSelectedPalette() {
    const mode = document.querySelector('input[name="paletteMode"]:checked').value;
    if (mode !== "manual") return null;
    const pickers = document.querySelectorAll('#colorPickers input[type="color"]');
    return Array.from(pickers).map((p) => p.value);
}

async function generateDesign() {
    const prompt = document.getElementById("promptInput").value.trim();
    if (!prompt) {
        document.getElementById("promptInput").focus();
        return;
    }

    const btn = document.getElementById("generateBtn");
    btn.disabled = true;

    showProgress();

    const body = {
        prompt,
        num_layers: parseInt(document.getElementById("layerCount").value),
        canvas_inches: parseFloat(document.getElementById("canvasSize").value),
        include_background: document.getElementById("includeBackground").checked,
        palette: getSelectedPalette(),
        filter_speckle: parseInt(document.getElementById("filterSpeckle").value),
        corner_threshold: parseInt(document.getElementById("cornerThreshold").value),
    };

    try {
        const resp = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!resp.ok) {
            const err = await resp.json();
            showToast(err.detail || "Generation failed");
            hideProgress();
            btn.disabled = false;
            return;
        }

        const data = await resp.json();
        currentJobId = data.job_id;
        startPolling();
    } catch (e) {
        showToast("Network error: " + e.message);
        hideProgress();
        btn.disabled = false;
    }
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);
    pollInterval = setInterval(pollStatus, 1000);
}

async function pollStatus() {
    if (!currentJobId) return;

    try {
        const resp = await fetch(`/api/status/${currentJobId}`);
        if (!resp.ok) {
            clearInterval(pollInterval);
            pollInterval = null;
            hideProgress();
            document.getElementById("generateBtn").disabled = false;
            if (resp.status === 404) {
                showToast("Job lost (server may have restarted). Please try again.");
            } else {
                showToast("Status check failed: HTTP " + resp.status);
            }
            return;
        }
        const status = await resp.json();

        updateProgress(status.stage, status.progress);

        if (status.status === "complete") {
            clearInterval(pollInterval);
            pollInterval = null;
            hideProgress();
            document.getElementById("generateBtn").disabled = false;
            await loadPreview(currentJobId, status);
        } else if (status.status === "error") {
            clearInterval(pollInterval);
            pollInterval = null;
            hideProgress();
            document.getElementById("generateBtn").disabled = false;
            showToast("Error: " + (status.error || "Unknown error"));
        }
    } catch (e) {
        console.error("Poll error:", e);
    }
}

function showProgress() {
    document.getElementById("progressOverlay").style.display = "flex";
    updateProgress("starting", 0);
}

function hideProgress() {
    document.getElementById("progressOverlay").style.display = "none";
}

function updateProgress(stage, progress) {
    const stageNames = {
        starting: "Initializing...",
        generating: "Generating image with AI...",
        quantizing: "Reducing to target colors...",
        separating: "Separating color layers...",
        vectorizing: "Converting to vector paths...",
        assembling: "Building Cricut-ready SVG...",
        done: "Complete!",
    };

    document.getElementById("progressStage").textContent = stageNames[stage] || stage;
    document.getElementById("progressBar").style.width = `${Math.round(progress * 100)}%`;
    document.getElementById("progressPercent").textContent = `${Math.round(progress * 100)}%`;
}

async function loadPreview(jobId, status) {
    try {
        const resp = await fetch(`/api/preview/${jobId}`);
        if (!resp.ok) throw new Error("Preview is unavailable");
        const svgText = await resp.text();

        const preview = document.getElementById("svgPreview");
        const emptyState = document.getElementById("emptyState");
        if (emptyState) emptyState.style.display = "none";
        preview.innerHTML = svgText;

        renderLayers(status.layers, jobId);
        showDownloads(status.layers, jobId);
        addToHistory(jobId, status);
    } catch (e) {
        console.error("Preview load error:", e);
        showToast("Design generated but preview failed to load: " + e.message);
    }
}

function renderLayers(layers, jobId) {
    const list = document.getElementById("layersList");
    list.innerHTML = "";

    if (!layers || layers.length === 0) {
        list.innerHTML = '<div class="empty-layers">No layers</div>';
        return;
    }

    layers.forEach((layer) => {
        const item = document.createElement("div");
        item.className = "layer-item";
        item.dataset.layerIndex = layer.index;
        item.innerHTML = `
            <div class="layer-swatch" style="background:${layer.color}"></div>
            <span class="layer-name">Layer ${layer.index} — ${layer.label}</span>
            <span class="layer-paths">${layer.path_count}p</span>
            <button class="layer-visibility" data-layer="${layer.index}" onclick="toggleLayerVisibility(event, ${layer.index})" title="Toggle visibility">&#128065;</button>
        `;
        item.addEventListener("click", (e) => {
            if (e.target.closest(".layer-visibility")) return;
            highlightLayer(layer.index);
        });
        list.appendChild(item);
    });
}

function toggleLayerVisibility(event, layerIndex) {
    event.stopPropagation();
    const btn = event.currentTarget;
    btn.classList.toggle("hidden");

    const svg = document.querySelector("#svgPreview svg");
    if (!svg) return;

    const group = Array.from(svg.querySelectorAll("g")).find((group) => group.id.startsWith(`Layer_${layerIndex}_`));
    if (group) {
        const isHidden = group.style.display === "none";
        group.style.display = isHidden ? "" : "none";
    }
}

function highlightLayer(layerIndex) {
    document.querySelectorAll(".layer-item").forEach((item) => {
        item.classList.toggle("active", parseInt(item.dataset.layerIndex) === layerIndex);
    });

    const svg = document.querySelector("#svgPreview svg");
    if (!svg) return;

    const selectedGroup = Array.from(svg.querySelectorAll("g")).find((group) => group.id.startsWith(`Layer_${layerIndex}_`));
    const groups = svg.querySelectorAll("g");
    groups.forEach((group) => {
        group.style.opacity = group === selectedGroup ? "1" : "0.25";
    });

    setTimeout(() => {
        groups.forEach((g) => { g.style.opacity = "1"; });
    }, 1500);
}

function showDownloads(layers, jobId) {
    const section = document.getElementById("downloadSection");
    section.style.display = "block";

    const container = document.getElementById("layerDownloads");
    container.innerHTML = "";

    if (!layers) return;

    layers.forEach((layer) => {
        const btn = document.createElement("button");
        btn.className = "layer-download-btn";
        btn.innerHTML = `
            <span class="swatch" style="background:${layer.color}"></span>
            Layer ${layer.index} — ${layer.label}
        `;
        btn.onclick = () => downloadLayer(jobId, layer.index);
        container.appendChild(btn);
    });
}

function downloadAll() {
    if (!currentJobId) return;
    window.open(`/api/download/${currentJobId}`, "_blank");
}

function downloadLayer(jobId, layerNum) {
    window.open(`/api/download/${jobId}/layer/${layerNum}`, "_blank");
}

function addToHistory(jobId, status) {
    history.unshift({ jobId, prompt: document.getElementById("promptInput").value, layers: status.layers });
    if (history.length > 10) history.pop();
    renderHistory();
}

function renderHistory() {
    const section = document.getElementById("historySection");
    const list = document.getElementById("historyList");

    if (history.length === 0) {
        section.style.display = "none";
        return;
    }

    section.style.display = "block";
    list.innerHTML = "";

    history.forEach((item) => {
        const el = document.createElement("div");
        el.className = "history-item";
        el.innerHTML = `
            <div class="history-thumb" id="thumb-${item.jobId}"></div>
            <span>${item.prompt.substring(0, 30)}${item.prompt.length > 30 ? "..." : ""}</span>
        `;
        el.onclick = async () => {
            currentJobId = item.jobId;
            const resp = await fetch(`/api/status/${item.jobId}`);
            const status = await resp.json();
            if (status.status === "complete") {
                await loadPreview(item.jobId, status);
            }
        };
        list.appendChild(el);
    });
}

/* Zoom controls */
function zoomIn() {
    zoomLevel = Math.min(zoomLevel + 0.2, 3);
    applyZoom();
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel - 0.2, 0.3);
    applyZoom();
}

function zoomReset() {
    zoomLevel = 1;
    applyZoom();
}

function applyZoom() {
    const grid = document.getElementById("matGrid");
    grid.style.transform = `scale(${zoomLevel})`;
}





