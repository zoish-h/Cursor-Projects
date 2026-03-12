# Job Application Autofill (Chrome Extension)

A Chrome extension that securely saves and reuses your job application answers across common Applicant Tracking Systems (ATS) such as Workday, Greenhouse, Lever, Jobvite, SmartRecruiters, Eightfold, and Uber careers.

All data is stored **locally in your browser** using `chrome.storage` and never sent to a server.

---

## Features

- **Automatic capture of answers**  
  - Watches inputs and textareas on supported job application pages.  
  - Stores values per **site** and per **field label** (e.g. job title, company, dates, text answers).

- **Auto-fill on new applications**  
  - When you open another application on the same platform, empty fields with matching labels are filled automatically.  
  - Works with many common ATS platforms (Workday, Greenhouse, Lever, Jobvite, SmartRecruiters, Eightfold, Uber).

- **Global and per-site toggles**  
  - Global on/off switch for auto-fill.  
  - Per-site switches so you can enable/disable auto-fill for individual hostnames.

- **Search and selective clear**  
  - Popup UI shows saved answers grouped by site.  
  - Search by site, field label, or value text.  
  - Clear all answers for a site or a single saved field.

- **Privacy-first**  
  - Uses `chrome.storage.local`/`chrome.storage.sync`.  
  - Does **not** capture password fields.  
  - No network calls or external servers.

---

## Files

- `manifest.json` – Extension configuration (permissions, content scripts, popup).  
- `background.js` – Service worker (currently a placeholder for future features).  
- `contentScript.js` – Logic injected into job application pages; captures and auto-fills fields.  
- `popup.html` – UI for toggles, search, and clearing saved answers.  
- `popup.js` – Popup logic: reads/writes settings, renders per-site data, handles search and clear buttons.

---

## Installing the extension (development mode)

1. Open Chrome and go to `chrome://extensions`.
2. Enable **Developer mode** (top-right).
3. Click **“Load unpacked”**.
4. Select the `job-autofill-extension/` folder from this repository.
5. Pin the extension in the Chrome toolbar if you want quick access.

---

## Using the extension

1. **Enable auto-fill**
   - Click the extension icon.  
   - Ensure **Global auto-fill** is turned **ON**.  
   - For each site you care about (Workday, Greenhouse, etc.), leave its site toggle **ON** in the list.

2. **Capture answers**
   - Go to a job application page on a supported site.  
   - Fill in your experience, dates, text answers, etc.  
   - As you leave fields (change/blur), values are stored locally per site and field label.

3. **Auto-fill later applications**
   - Open another application form on the same platform.  
   - With global + site toggles ON, the extension will auto-fill **empty** fields whose labels match previously saved ones.

4. **Review and clear data**
   - Open the popup to see a list of hostnames with saved answers.  
   - Use the search box to filter by site or label.  
   - Use **“Clear site”** to remove all answers for a platform, or **“×”** next to a field to remove just one saved answer.

---

## Supported platforms (default)

Configured in `manifest.json`:

- `*.workday.com`, `*.myworkdayjobs.com`
- `*.greenhouse.io`
- `*.lever.co`
- `*.jobvite.com`
- `*.smartrecruiters.com`
- `*.eightfold.ai`
- `*.uber.com`

To add more, update both `host_permissions` and `content_scripts.matches` in `manifest.json` with additional URL patterns.

---

## Notes and limitations

- Matching is based on **normalized field labels and input types**, so label changes on a site may require re-entering data once.  
- Password fields and hidden fields are never captured.  
- This is intended as a personal productivity tool; always review what is auto-filled before submitting applications.

