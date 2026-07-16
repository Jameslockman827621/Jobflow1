const DEFAULTS = {
  api_base: 'http://localhost:8000/api/v1',
  dashboard_url: 'http://localhost:3000',
};

async function load() {
  const data = await chrome.storage.local.get(['api_base', 'dashboard_url']);
  document.getElementById('api_base').value = data.api_base || DEFAULTS.api_base;
  document.getElementById('dashboard_url').value = data.dashboard_url || DEFAULTS.dashboard_url;
}

document.getElementById('save').addEventListener('click', async () => {
  const api_base = document.getElementById('api_base').value.trim().replace(/\/$/, '');
  const dashboard_url = document.getElementById('dashboard_url').value.trim().replace(/\/$/, '');
  await chrome.storage.local.set({ api_base, dashboard_url });
  document.getElementById('status').textContent = 'Saved — reload the extension if Connect was open.';
});

load();
