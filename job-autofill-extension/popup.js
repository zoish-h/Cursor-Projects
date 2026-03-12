const ENABLED_GLOBAL_KEY = "jobAutofillEnabled";
const ENABLED_SITES_KEY = "jobAutofillSitesEnabled";
const STORAGE_KEY = "jobAutofillFields";

const globalToggle = document.getElementById("globalToggle");
const searchInput = document.getElementById("search");
const sitesContainer = document.getElementById("sites");

let state = {
  globalEnabled: true,
  siteEnabled: {},
  fields: {}
};

async function loadState() {
  const [syncData, localData] = await Promise.all([
    chrome.storage.sync.get([ENABLED_GLOBAL_KEY, ENABLED_SITES_KEY]),
    chrome.storage.local.get(STORAGE_KEY)
  ]);

  state.globalEnabled = syncData[ENABLED_GLOBAL_KEY] !== false;
  state.siteEnabled = syncData[ENABLED_SITES_KEY] || {};
  state.fields = localData[STORAGE_KEY] || {};

  globalToggle.checked = state.globalEnabled;
  render();
}

function saveGlobalEnabled(enabled) {
  state.globalEnabled = enabled;
  return chrome.storage.sync.set({ [ENABLED_GLOBAL_KEY]: enabled });
}

function saveSiteEnabledMap() {
  return chrome.storage.sync.set({ [ENABLED_SITES_KEY]: state.siteEnabled });
}

function saveFields() {
  return chrome.storage.local.set({ [STORAGE_KEY]: state.fields });
}

function onGlobalToggleChange() {
  const enabled = globalToggle.checked;
  saveGlobalEnabled(enabled);
}

function onSiteToggleChange(hostname, enabled) {
  state.siteEnabled[hostname] = enabled;
  saveSiteEnabledMap();
  render();
}

function clearSite(hostname) {
  if (!state.fields[hostname]) return;
  delete state.fields[hostname];
  saveFields().then(render);
}

function clearField(hostname, fieldKey) {
  if (!state.fields[hostname]) return;
  delete state.fields[hostname][fieldKey];
  if (Object.keys(state.fields[hostname]).length === 0) {
    delete state.fields[hostname];
  }
  saveFields().then(render);
}

function matchesSearch(hostname, fieldEntry, query) {
  if (!query) return true;
  const q = query.toLowerCase();
  if (hostname.toLowerCase().includes(q)) return true;
  if ((fieldEntry.label || "").toLowerCase().includes(q)) return true;
  if ((fieldEntry.value || "").toLowerCase().includes(q)) return true;
  return false;
}

function render() {
  const query = searchInput.value.trim().toLowerCase();
  sitesContainer.innerHTML = "";

  const hostnames = Object.keys(state.fields).sort();
  if (hostnames.length === 0) {
    sitesContainer.textContent = "No saved answers yet.";
    return;
  }

  for (const hostname of hostnames) {
    const fieldsMap = state.fields[hostname] || {};
    const entries = Object.entries(fieldsMap);

    const filteredEntries = entries.filter(([key, entry]) =>
      matchesSearch(hostname, entry, query)
    );
    if (filteredEntries.length === 0) continue;

    const siteDiv = document.createElement("div");
    siteDiv.className = "site";

    const siteHeader = document.createElement("div");
    siteHeader.className = "site-header";

    const titleSpan = document.createElement("span");
    titleSpan.className = "site-title";
    titleSpan.textContent = `${hostname} (${entries.length})`;

    const actionsDiv = document.createElement("div");
    actionsDiv.className = "site-actions";

    const siteToggleLabel = document.createElement("label");
    siteToggleLabel.className = "switch";
    const siteToggleInput = document.createElement("input");
    siteToggleInput.type = "checkbox";
    const enabledForSite =
      state.siteEnabled[hostname] === undefined
        ? true
        : state.siteEnabled[hostname];
    siteToggleInput.checked = enabledForSite;
    siteToggleInput.addEventListener("change", () =>
      onSiteToggleChange(hostname, siteToggleInput.checked)
    );
    const sliderSpan = document.createElement("span");
    sliderSpan.className = "slider";
    siteToggleLabel.appendChild(siteToggleInput);
    siteToggleLabel.appendChild(sliderSpan);

    const clearSiteBtn = document.createElement("button");
    clearSiteBtn.textContent = "Clear site";
    clearSiteBtn.addEventListener("click", () => clearSite(hostname));

    actionsDiv.appendChild(siteToggleLabel);
    actionsDiv.appendChild(clearSiteBtn);

    siteHeader.appendChild(titleSpan);
    siteHeader.appendChild(actionsDiv);

    siteDiv.appendChild(siteHeader);

    for (const [key, entry] of filteredEntries) {
      const fieldDiv = document.createElement("div");
      fieldDiv.className = "field";

      const labelSpan = document.createElement("span");
      labelSpan.className = "field-label";
      const labelText = entry.label || key.split("::")[0];
      labelSpan.textContent = labelText;

      const clearBtn = document.createElement("button");
      clearBtn.textContent = "×";
      clearBtn.title = "Clear this answer";
      clearBtn.addEventListener("click", () => clearField(hostname, key));

      fieldDiv.appendChild(labelSpan);
      fieldDiv.appendChild(clearBtn);
      siteDiv.appendChild(fieldDiv);
    }

    sitesContainer.appendChild(siteDiv);
  }

  if (!sitesContainer.hasChildNodes()) {
    sitesContainer.textContent = "No matches for your search.";
  }
}

globalToggle.addEventListener("change", onGlobalToggleChange);
searchInput.addEventListener("input", render);

loadState();

