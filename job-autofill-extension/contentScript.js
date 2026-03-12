const ENABLED_GLOBAL_KEY = "jobAutofillEnabled";
const ENABLED_SITES_KEY = "jobAutofillSitesEnabled";
const STORAGE_KEY = "jobAutofillFields";

function normalizeLabel(text) {
  return (text || "")
    .toLowerCase()
    .replace(/\s+/g, " ")
    .replace(/[*:?]/g, "")
    .trim();
}

function getFieldLabel(input) {
  const id = input.id;
  if (id) {
    const label = document.querySelector(`label[for="${CSS.escape(id)}"]`);
    if (label && label.innerText.trim()) return label.innerText;
  }

  let el = input;
  for (let i = 0; i < 3 && el; i++) {
    if (el.tagName === "LABEL" && el.innerText.trim()) {
      return el.innerText;
    }
    el = el.parentElement;
  }

  if (input.getAttribute("aria-label")) {
    return input.getAttribute("aria-label");
  }
  if (input.placeholder) return input.placeholder;

  const prev = input.previousElementSibling;
  if (prev && prev.innerText && prev.innerText.trim().length > 0) {
    return prev.innerText;
  }

  return "";
}

function getFieldKey(input) {
  const label = getFieldLabel(input);
  const normLabel = normalizeLabel(label);
  const type = input.type || input.tagName.toLowerCase();
  return normLabel ? `${normLabel}::${type}` : "";
}

async function isGloballyEnabled() {
  const data = await chrome.storage.sync.get(ENABLED_GLOBAL_KEY);
  return data[ENABLED_GLOBAL_KEY] !== false; // default: true
}

async function isSiteEnabled(hostname) {
  const data = await chrome.storage.sync.get(ENABLED_SITES_KEY);
  const map = data[ENABLED_SITES_KEY] || {};
  if (map[hostname] === undefined) return true; // default per-site: true
  return map[hostname];
}

async function loadAllFields() {
  const data = await chrome.storage.local.get(STORAGE_KEY);
  return data[STORAGE_KEY] || {};
}

async function saveAllFields(allFields) {
  await chrome.storage.local.set({ [STORAGE_KEY]: allFields });
}

async function setupCapture() {
  const hostname = location.hostname;
  let allFields = await loadAllFields();

  const handler = async (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement || input instanceof HTMLTextAreaElement)) return;
    if (input.type === "password") return;

    const key = getFieldKey(input);
    const value = input.value;
    if (!key || !value || value.trim() === "") return;

    const label = getFieldLabel(input);
    const type = input.type || input.tagName.toLowerCase();

    allFields[hostname] = allFields[hostname] || {};
    allFields[hostname][key] = {
      label: label || key,
      value,
      type,
      site: hostname,
      updatedAt: Date.now()
    };
    await saveAllFields(allFields);
  };

  document.addEventListener("change", handler, true);
  document.addEventListener("blur", handler, true);
}

async function autofill() {
  const hostname = location.hostname;
  const [globalOn, siteOn, allFields] = await Promise.all([
    isGloballyEnabled(),
    isSiteEnabled(hostname),
    loadAllFields()
  ]);
  if (!globalOn || !siteOn) return;

  const siteFields = allFields[hostname] || {};

  const inputs = Array.from(
    document.querySelectorAll("input, textarea, select")
  );

  for (const input of inputs) {
    if (
      input instanceof HTMLInputElement &&
      (input.type === "password" || input.type === "hidden")
    ) {
      continue;
    }
    if (input.value && input.value.trim() !== "") continue;

    const key = getFieldKey(input);
    if (!key) continue;

    const saved = siteFields[key];
    if (!saved || !saved.value) continue;

    if (input instanceof HTMLSelectElement) {
      const option = Array.from(input.options).find(
        (opt) => normalizeLabel(opt.text) === normalizeLabel(saved.value)
      );
      if (option) {
        input.value = option.value;
        input.dispatchEvent(new Event("change", { bubbles: true }));
      }
    } else {
      input.value = saved.value;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }
  }
}

(async function init() {
  try {
    await setupCapture();
    await autofill();
    setTimeout(autofill, 3000);
    setTimeout(autofill, 7000);
  } catch (e) {
    console.error("Job Autofill error:", e);
  }
})();

