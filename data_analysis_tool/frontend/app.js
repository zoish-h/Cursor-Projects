const API = ""; // same origin

let currentSessionId = null;

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const uploadStatus = document.getElementById("upload-status");
const analysisSection = document.getElementById("analysis-section");
const explainabilityEl = document.getElementById("explainability");
const metricsEl = document.getElementById("metrics");
const profileContent = document.getElementById("profile-content");
const questionInput = document.getElementById("question-input");
const askBtn = document.getElementById("ask-btn");
const answerEl = document.getElementById("answer");
const exportPpt = document.getElementById("export-ppt");
const exportPdf = document.getElementById("export-pdf");
const exportDocx = document.getElementById("export-docx");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) fileInput.files = e.dataTransfer.files;
  fileInput.dispatchEvent(new Event("change"));
});
fileInput.addEventListener("change", uploadFiles);

async function uploadFiles() {
  const files = fileInput.files;
  if (!files.length) return;
  uploadStatus.textContent = "Uploading...";
  uploadStatus.className = "";
  const form = new FormData();
  for (let i = 0; i < files.length; i++) form.append("files", files[i]);
  try {
    const r = await fetch(`${API}/upload`, { method: "POST", body: form });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    currentSessionId = data.session_id;
    uploadStatus.textContent = `Loaded ${data.analysis.row_count} rows, ${data.analysis.column_count} columns.`;
    uploadStatus.className = "success";
    renderAnalysis(data.analysis);
    analysisSection.classList.remove("hidden");
  } catch (e) {
    uploadStatus.textContent = e.message || "Upload failed";
    uploadStatus.className = "error";
  }
}

function renderAnalysis(analysis) {
  if (analysis.error) {
    explainabilityEl.textContent = analysis.error;
    return;
  }
  explainabilityEl.innerHTML = (analysis.explainability || []).map((m) => `<p>${escapeHtml(m)}</p>`).join("");
  const metrics = analysis.dataset_level?.metrics || {};
  const names = analysis.dataset_level?.metric_names || Object.keys(metrics);
  metricsEl.innerHTML = names
    .filter((k) => k in metrics && k !== "explanation_type")
    .map((k) => `<div class="metric-card"><div class="name">${escapeHtml(k)}</div><div class="value">${formatVal(metrics[k])}</div></div>`)
    .join("");
  const profile = analysis.data_profile || [];
  if (profile.length) {
    const cols = ["column", "type", "non_null_count", "null_count", "mean", "p50", "min", "max"];
    let table = "<table><thead><tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr></thead><tbody>";
    profile.forEach((row) => {
      table += "<tr>" + cols.map((c) => `<td>${formatVal(row[c])}</td>`).join("") + "</tr>";
    });
    table += "</tbody></table>";
    profileContent.innerHTML = table;
  } else {
    profileContent.innerHTML = "<p>No column profile.</p>";
  }
}

function formatVal(v) {
  if (v == null) return "—";
  if (typeof v === "object") return JSON.stringify(v).slice(0, 80);
  return String(v);
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

askBtn.addEventListener("click", askQuestion);
questionInput.addEventListener("keydown", (e) => { if (e.key === "Enter") askQuestion(); });

async function askQuestion() {
  const q = questionInput.value.trim();
  if (!q) return;
  answerEl.textContent = "";
  answerEl.classList.add("streaming");
  askBtn.disabled = true;
  try {
    const r = await fetch(`${API}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q }),
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.detail || r.statusText);
    }
    const reader = r.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith("data:")) {
          const data = line.slice(5).trim();
          if (data) {
            try {
              const parsed = JSON.parse(data);
              const text = typeof parsed === "string" ? parsed : (parsed && parsed.data);
              if (text) answerEl.textContent += text;
            } catch {
              answerEl.textContent += data;
            }
          }
        }
      }
    }
  } catch (e) {
    answerEl.textContent = "Error: " + e.message;
  }
  answerEl.classList.remove("streaming");
  askBtn.disabled = false;
}

function doExport(format) {
  if (!currentSessionId) {
    alert("Upload a file first.");
    return;
  }
  fetch(`${API}/export`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ format }),
  })
    .then((r) => {
      if (!r.ok) return r.json().then((d) => Promise.reject(new Error(d.detail || r.statusText)));
      return r.blob();
    })
    .then((blob) => {
      const ext = format === "ppt" ? "pptx" : format === "docx" ? "docx" : "pdf";
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `analysis_report.${ext}`;
      a.click();
      URL.revokeObjectURL(a.href);
    })
    .catch((e) => alert(e.message));
}

exportPpt.addEventListener("click", () => doExport("ppt"));
exportPdf.addEventListener("click", () => doExport("pdf"));
exportDocx.addEventListener("click", () => doExport("docx"));
