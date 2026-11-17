// Optional QA runner. Uses Node 22+ and an installed Chrome; the overlay runtime is Python-only.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { existsSync } from 'node:fs';
import { mkdir, mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';
import { inflateSync } from 'node:zlib';

const chromePath = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
assert(existsSync(chromePath), 'Set CHROME_PATH to a Chrome executable.');
const temp = await mkdtemp(join(tmpdir(), 'premier-overlay-browser-'));
const fixtureServer = [
  'from http.server import ThreadingHTTPServer',
  'import server',
  'server.detect_steam_id = lambda: ""',
  'http = ThreadingHTTPServer((server.HOST, 0), server.Handler)',
  'print(http.server_port, flush=True)',
  'http.serve_forever()',
].join('\n');
const python = spawn(process.env.OVERLAY_PYTHON || 'python', ['-c', fixtureServer], {
  windowsHide: true, env: { ...process.env, LOCALAPPDATA: temp },
});
const chrome = spawn(chromePath, ['--headless', '--disable-gpu', '--no-first-run',
  '--no-default-browser-check', '--disable-background-networking', '--disable-component-update',
  '--remote-debugging-port=0', '--user-data-dir=' + temp, 'about:blank'],
{ windowsHide: true, stdio: 'ignore' });
let socket;

try {
  const [portData] = await Promise.race([once(python.stdout, 'data'), delay(6000).then(() => [])]);
  const port = Number(portData?.toString().trim());
  assert(port > 0, 'Fixture server did not start');
  const site = 'http://127.0.0.1:' + port;
  const portFile = join(temp, 'DevToolsActivePort');
  for (let attempt = 0; attempt < 100 && !existsSync(portFile); attempt += 1) await delay(100);
  const devtoolsPort = Number((await readFile(portFile, 'utf8')).split('\n')[0]);
  const devtools = 'http://127.0.0.1:' + devtoolsPort;
  const target = await (await fetch(devtools + '/json/new?about:blank', { method: 'PUT' })).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await once(socket, 'open');
  let id = 0;
  const pending = new Map();
  const errors = [];
  socket.addEventListener('message', ({ data }) => {
    const event = JSON.parse(data);
    if (event.method === 'Runtime.exceptionThrown') errors.push(event.params.exceptionDetails);
    const handler = pending.get(event.id);
    if (!handler) return;
    pending.delete(event.id);
    if (event.error) handler.reject(new Error(event.error.message));
    else handler.resolve(event.result);
  });
  const cdp = (method, params = {}) => new Promise((resolve, reject) => {
    pending.set(++id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
  const evaluate = async (expression) => {
    const result = await cdp('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    assert(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
    return result.result.value;
  };
  async function navigate(url, width, height, deviceScaleFactor = 1) {
    await cdp('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor, mobile: false });
    const loaded = new Promise((resolve) => {
      const listener = ({ data }) => {
        if (JSON.parse(data).method === 'Page.loadEventFired') {
          socket.removeEventListener('message', listener);
          resolve();
        }
      };
      socket.addEventListener('message', listener);
    });
    await cdp('Page.navigate', { url });
    await loaded;
  }

  await cdp('Page.enable');
  await cdp('Runtime.enable');
  await cdp('Emulation.setDefaultBackgroundColorOverride', { color: { r: 0, g: 0, b: 0, a: 0 } });
  await navigate(site + '/?demo=1', 640, 180);
  const native = await evaluate(`(() => {
    const widget = document.getElementById('widget');
    const box = widget.getBoundingClientRect();
    const styles = getComputedStyle(widget);
    return {
      box: [box.x, box.y, box.width, box.height], transform: styles.transform,
      background: getComputedStyle(document.body).backgroundColor,
      viewport: [innerWidth, innerHeight, devicePixelRatio],
      overflow: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
      sample: !document.getElementById('sample').hidden,
      account: document.getElementById('account').textContent,
      values: [...document.querySelectorAll('.stats dd')].map(node => node.textContent),
      visibleTiles: [...document.querySelectorAll('.tile')].map(node => node.textContent),
      fits: [...document.querySelectorAll('.tile, .stats, .rating, .identity')].every(node => {
        const rect = node.getBoundingClientRect();
        return rect.right <= box.right && rect.bottom <= box.bottom;
      }),
    };
  })()`);
  assert.deepEqual(native.box, [0, 0, 640, 180]);
  assert.deepEqual(native.viewport, [640, 180, 1]);
  assert.deepEqual(native.overflow, [640, 180]);
  assert.equal(native.transform, 'none');
  assert.equal(native.background, 'rgba(0, 0, 0, 0)');
  assert(native.sample && native.fits);
  assert.equal(native.account, 'Sample player');
  assert.deepEqual(native.values, ['1.28', '0.86', '90.3', '17.9', '53%', '70%']);
  assert.deepEqual(native.visibleTiles, ['W', 'L', 'T', 'W', 'W']);
  const png = Buffer.from((await cdp('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })).data, 'base64');
  assert.equal(png.readUInt32BE(16), 640);
  assert.equal(png.readUInt32BE(20), 180);
  assert.equal(png[25], 6, 'Screenshot should contain an alpha channel');
  const idat = [];
  for (let offset = 8; offset + 12 <= png.length;) {
    const size = png.readUInt32BE(offset);
    if (png.toString('ascii', offset + 4, offset + 8) === 'IDAT') {
      idat.push(png.subarray(offset + 8, offset + 8 + size));
    }
    offset += size + 12;
  }
  assert.equal(inflateSync(Buffer.concat(idat))[4], 0, 'The rounded top-left corner should be transparent');
  const screenshot = resolve(process.argv[2] || 'dist/browser-smoke.png');
  await mkdir(dirname(screenshot), { recursive: true });
  await writeFile(screenshot, png);
  console.log('Native OBS source: 640 × 180, DPR 1, transparent PNG, no scroll or CSS transform.');

  await navigate(site + '/', 640, 180, 2);
  await delay(400);
  assert.deepEqual(await evaluate(`[
    innerWidth, innerHeight, devicePixelRatio, document.querySelector('.widget').offsetWidth,
    document.getElementById('rating').textContent, document.getElementById('sample').hidden
  ]`), [640, 180, 2, 640, '—', true]);
  await navigate(site + '/?gsi-test=1', 640, 180);
  await delay(200);
  assert(await evaluate("!document.getElementById('sample').hidden"));
  await navigate(site + '/settings', 800, 720);
  await delay(300);
  assert(await evaluate("document.getElementById('save') && document.getElementById('refresh')"));

  for (const [width, height] of [[1920, 1080], [2560, 1440], [3840, 2160]]) {
    await navigate(site + '/?demo=1', width, height);
    // Model an OBS position/scale around an independent 640 × 180 Browser Source.
    const scale = width / 1920;
    const left = Math.round(width - scale * 672);
    const top = Math.round(128 * scale);
    const layout = await evaluate(`(async () => {
      const frame = document.createElement('iframe');
      frame.src = '/?demo=1';
      frame.style.cssText = 'position:absolute;left:${left}px;top:${top}px;width:640px;height:180px;border:0;transform-origin:0 0;transform:scale(${scale})';
      const loaded = new Promise(resolve => frame.onload = resolve);
      document.body.replaceChildren(frame);
      await loaded;
      const rect = frame.getBoundingClientRect();
      const view = frame.contentWindow;
      return { position: [rect.x, rect.y], size: [rect.width, rect.height], visible: rect.right <= innerWidth && rect.bottom <= innerHeight,
        sourceSize: [view.innerWidth, view.innerHeight], statSize: parseFloat(view.getComputedStyle(frame.contentDocument.querySelector('.stats dd')).fontSize) * ${scale},
        labelSize: parseFloat(view.getComputedStyle(frame.contentDocument.querySelector('.stats dt')).fontSize) * ${scale} };
    })()`);
    assert(layout.visible && layout.statSize >= 22 && layout.labelSize >= 10);
    assert.deepEqual(layout.position, [left, top]);
    assert.deepEqual(layout.sourceSize, [640, 180]);
    assert(Math.abs(layout.size[0] - 640 * scale) < 0.1);
    console.log(width + ' × ' + height + ' simulated OBS: ' + JSON.stringify(layout));
  }
  assert.deepEqual(errors, []);
} finally {
  socket?.close();
  for (const process of [chrome, python]) {
    if (process.exitCode === null) {
      const exited = once(process, 'exit');
      process.kill();
      await exited;
    }
  }
  await rm(temp, { recursive: true, force: true, maxRetries: 5, retryDelay: 150 }).catch((error) => {
    console.warn('Could not remove isolated browser profile:', error.message);
  });
}
