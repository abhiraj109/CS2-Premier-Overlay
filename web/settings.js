(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const steam = $('steam-id');
  const title = $('detect-title');
  const detail = $('detect-detail');
  const dot = $('status-dot');
  const feedback = $('feedback');
  const save = $('save');
  const refresh = $('refresh');

  async function getJson(url, options = {}) {
    const response = await fetch(url, { cache: 'no-store', ...options });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    return data;
  }

  async function load() {
    try {
      const [settings, profile] = await Promise.all([
        getJson('/api/settings'), getJson('/api/profile'),
      ]);
      steam.value = settings.steam_id || '';
      const active = settings.effective_steam_id || settings.detected_steam_id;
      if (active) {
        title.textContent = 'Steam account detected';
        detail.textContent = `${active}${settings.using_auto_detect ? ' · automatic selection' : ' · saved one-time override'}`;
        dot.className = 'status-dot online';
      } else {
        title.textContent = 'Steam account not detected yet';
        detail.textContent = 'Open Steam and run this page again. Add SteamID64 below only if auto-detection keeps failing.';
        dot.className = 'status-dot offline';
      }
      const rating = profile.premier_rating;
      feedback.textContent = profile.error || (rating !== null && rating !== undefined
        ? `Profile connected · Premier Rating ${Number(rating).toLocaleString('en-US')}`
        : 'Waiting for public profile data…');
    } catch (error) {
      feedback.textContent = `Could not load setup: ${error.message}`;
    }
  }

  save.addEventListener('click', async () => {
    save.disabled = true;
    feedback.textContent = 'Saving Steam account override…';
    try {
      await getJson('/api/settings', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steam_id: steam.value.trim() }),
      });
      feedback.textContent = 'Saved once. Future profile refreshes are automatic.';
      await load();
    } catch (error) {
      feedback.textContent = `Could not save: ${error.message}`;
    } finally { save.disabled = false; }
  });

  refresh.addEventListener('click', async () => {
    refresh.disabled = true;
    feedback.textContent = 'Requesting a fresh profile sync…';
    try {
      await getJson('/api/refresh-profile', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}',
      });
      feedback.textContent = 'Sync requested. Automatic rate limits and retry delays still apply.';
    } catch (error) {
      feedback.textContent = `Could not request sync: ${error.message}`;
    } finally { refresh.disabled = false; }
  });

  load();
})();
