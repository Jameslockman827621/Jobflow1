const DEFAULTS = {
  api_base: 'http://localhost:8000/api/v1',
  dashboard_url: 'http://localhost:3000',
};

function originPattern(url) {
  try {
    const u = new URL(url);
    return `${u.protocol}//${u.host}/*`;
  } catch {
    return null;
  }
}

async function load() {
  const data = await chrome.storage.local.get(['api_base', 'dashboard_url']);
  document.getElementById('api_base').value = data.api_base || DEFAULTS.api_base;
  document.getElementById('dashboard_url').value = data.dashboard_url || DEFAULTS.dashboard_url;
}

document.getElementById('save').addEventListener('click', async () => {
  const api_base = document.getElementById('api_base').value.trim().replace(/\/$/, '');
  const dashboard_url = document.getElementById('dashboard_url').value.trim().replace(/\/$/, '');
  await chrome.storage.local.set({ api_base, dashboard_url });

  const origins = [originPattern(api_base), originPattern(dashboard_url)].filter(Boolean);
  const status = document.getElementById('status');
  if (origins.length && chrome.permissions?.request) {
    try {
      const granted = await chrome.permissions.request({ origins });
      status.textContent = granted
        ? 'Saved — host access granted for your API/dashboard.'
        : 'Saved — host permission denied; Connect may fail on this domain until granted.';
      return;
    } catch (e) {
      status.textContent = 'Saved (could not request host permissions — reload extension).';
      return;
    }
  }
  status.textContent = 'Saved — reload the extension if Connect was open.';
});

load();
