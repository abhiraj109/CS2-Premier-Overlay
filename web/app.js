(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const query = new URLSearchParams(location.search);
  const demo = query.get('demo') === '1';
  const sampleGsi = query.get('gsi-test') === '1';
  const timestamp = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' });
  const datedTimestamp = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
  const results = { W: ['win', 'Win'], L: ['loss', 'Loss'], T: ['draw', 'Draw'] };
  const matchModes = { premier: 'Premier', competitive: 'Matchmaking', wingman: 'Wingman', scrimcomp2v2: 'Wingman' };
  const phaseNames = { live: 'Live', warmup: 'Warmup', intermission: 'Halftime', gameover: 'Final', over: 'Final' };
  const metricDigits = { kd: 2, kr: 2, adr: 1, avg_kills: 1, hs_percent: 1, win_percent: 1 };
  const profileStatuses = { starting: 'Starting sync', setup: 'Waiting for Steam', syncing: 'Syncing',
    unavailable: 'Profile unavailable', offline: 'Profile sync disabled' };

  function text(id, value) {
    const element = $(id);
    if (element.textContent !== value) element.textContent = value;
  }

  function signed(value) {
    return (value > 0 ? '+' : '') + value.toLocaleString('en-US');
  }

  function form(items = []) {
    const display = items.slice(0, 5).reverse();
    const tiles = $('form').children;
    for (let index = 0; index < tiles.length; index += 1) {
      const item = display[index - (tiles.length - display.length)];
      const [className, label] = results[item?.result] || ['', 'Unknown result'];
      const change = item?.rating_change;
      const value = Number.isFinite(change) ? signed(change) : (className ? item.result : '–');
      const tile = tiles[index];
      if (tile.textContent !== value) tile.textContent = value;
      const style = className ? 'tile ' + className : 'tile';
      if (tile.className !== style) tile.className = style;
      const title = Number.isFinite(change) ? label + ' · ' + value + ' Premier rating' : label;
      if (tile.title !== title) tile.title = title;
      if (tile.getAttribute('aria-label') !== title) tile.setAttribute('aria-label', title);
    }
  }

  function liveDescription(map, player, result) {
    const label = phaseNames[map?.phase];
    if (!map?.name || !label) return '';
    const mapName = map.name.replace(/^de_/, '').replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase());
    const parts = [matchModes[map.mode], mapName, label];
    const ct = map.team_ct?.score;
    const t = map.team_t?.score;
    if (Number.isInteger(ct) && Number.isInteger(t)) parts.push('CT ' + ct + '–' + t + ' T');
    if (result) parts.push({ win: 'Win', loss: 'Loss', tie: 'Draw' }[result]);
    if (map.phase === 'live' && Number.isInteger(map.round)) parts.push('R' + (map.round + 1));
    if (player.team === 'CT' || player.team === 'T') parts.push(player.team);
    const { kills, deaths, assists } = player.match_stats || {};
    if (Number.isInteger(kills) && Number.isInteger(deaths)) {
      parts.push(kills + '/' + deaths + (Number.isInteger(assists) ? '/' + assists : '') + ' KDA');
    }
    return parts.filter(Boolean).join(' · ');
  }

  const avatar = $('avatar');
  avatar.addEventListener('error', () => { avatar.hidden = true; });
  avatar.addEventListener('load', () => { avatar.hidden = false; });

  function render(profile = {}, state = {}) {
    const game = state.connected ? state.data || {} : {};
    const player = game.player?.steamid && game.player.steamid === game.provider?.steamid
      && (!profile.steam_id || profile.steam_id === game.provider.steamid) ? game.player : {};
    const matchingAccount = !profile.steam_id || !game.provider?.steamid || profile.steam_id === game.provider.steamid;
    const live = matchingAccount ? liveDescription(game.map, player, game.result) : '';
    const id = profile.steam_id || game.provider?.steamid;
    const name = player.name || profile.name || (id ? 'Steam player' : 'Waiting for Steam');
    text('name', name);
    text('initials', player.name || profile.name ? Array.from(name.trim()).slice(0, 2).join('').toUpperCase() || 'CS' : 'CS');
    text('account', demo || sampleGsi ? 'Sample player' : id ? 'SteamID ' + id : 'No account detected');
    const avatarUrl = profile.avatar || null;
    if (avatar.getAttribute('src') !== avatarUrl) {
      avatar.hidden = true;
      if (avatarUrl) avatar.src = avatarUrl;
      else avatar.removeAttribute('src');
    }
    text('live', live);
    $('live').hidden = !live;

    const band = profile.rating_band || 'unrated';
    if ($('widget').dataset.band !== band) $('widget').dataset.band = band;
    text('rating', Number.isFinite(profile.premier_rating) ? profile.premier_rating.toLocaleString('en-US') : '—');
    const delta = profile.rating_change;
    $('delta').hidden = !Number.isFinite(delta);
    if (Number.isFinite(delta)) {
      text('delta', signed(delta));
      $('delta').className = 'delta ' + (delta > 0 ? 'up' : delta < 0 ? 'down' : '');
    }
    form(profile.recent_form);
    const stats = profile.last20 || {};
    for (const [id, digits] of Object.entries(metricDigits)) {
      const value = stats[id];
      const suffix = id.endsWith('_percent') ? '%' : '';
      text(id, Number.isFinite(value) ? value.toFixed(digits).replace(/\.0$/, '') + suffix : '—');
    }
    text('match-count', (stats.match_count || 0) + ' / 20');

    const locallyRecorded = profile.history_source === 'local';
    const updated = locallyRecorded ? profile.history_updated_at : profile.updated_at;
    const date = updated ? new Date(updated * 1000) : null;
    const isStale = ['cached', 'partial'].includes(profile.status);
    const source = locallyRecorded ? 'Local history' : isStale ? 'Limited sync' : 'Updated';
    const clock = date?.toDateString() === new Date().toDateString() ? timestamp : datedTimestamp;
    text('updated', date ? source + ' ' + clock.format(date) : profileStatuses[profile.status] || 'Waiting for profile');
    if (date) $('updated').dateTime = date.toISOString();
    else $('updated').removeAttribute('datetime');
    $('updated').title = profile.error || (locallyRecorded ? 'History recorded from CS2 Game State Integration' : '');

    const link = $('profile-link');
    link.hidden = !profile.profile_url;
    $('attribution').hidden = link.hidden;
    if (profile.profile_url && link.href !== profile.profile_url) link.href = profile.profile_url;
  }

  async function poll() {
    try {
      const response = await fetch(sampleGsi ? '/api/test-state' : '/api/overlay',
        { cache: 'no-store', signal: AbortSignal.timeout(5000) });
      if (!response.ok) throw new Error('Overlay request failed');
      const data = await response.json();
      if (sampleGsi) render({}, data);
      else render(data.profile, data.state);
    } catch {
      text('updated', 'Reconnecting…');
      text('live', '');
      $('live').hidden = true;
    } finally {
      window.setTimeout(poll, 2000);
    }
  }

  $('sample').hidden = !(demo || sampleGsi);
  if (demo) {
    render({
      name: 'Astra', premier_rating: 18420, rating_band: 'purple',
      rating_change: 274, updated_at: Date.now() / 1000,
      last20: { kd: 1.28, kr: 0.86, adr: 90.3, avg_kills: 17.9, hs_percent: 53, win_percent: 70, match_count: 20 },
      recent_form: ['W', 'W', 'T', 'L', 'W'].map((result) => ({ result })),
    }, {
      connected: true,
      data: {
        provider: { steamid: 'sample' },
        map: { name: 'de_mirage', mode: 'premier', phase: 'live', round: 13, team_ct: { score: 8 }, team_t: { score: 5 } },
        player: { steamid: 'sample', name: 'Astra', team: 'CT', match_stats: { kills: 18, deaths: 9, assists: 4 } },
      },
    });
    text('updated', 'Preview');
  } else {
    poll();
  }
})();
