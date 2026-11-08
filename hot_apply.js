const { WebSocket } = globalThis;
const fs = require('fs');
const path = require('path');

async function run() {
  const devPortFile = path.join(process.env.APPDATA, 'antigravity', 'DevToolsActivePort');
  if (!fs.existsSync(devPortFile)) {
    console.error('DevToolsActivePort not found');
    return;
  }
  const lines = fs.readFileSync(devPortFile, 'utf8').split(/\r?\n/);
  const port = lines[0].trim();

  const res = await fetch(`http://127.0.0.1:${port}/json`);
  const targets = await res.json();
  const page = targets.find(t => t.type === 'page' && t.url.startsWith('https://127.0.0.1:'));
  if (!page) {
    console.error('Main page target not found among targets:', targets);
    return;
  }

  const localePath = path.join(__dirname, 'tr-locale.js');
  const scriptCode = fs.readFileSync(localePath, 'utf8');

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(r => ws.onopen = r);

  let id = 1;
  function call(method, params = {}) {
    return new Promise(resolve => {
      const msgId = id++;
      const handler = (evt) => {
        const data = JSON.parse(evt.data);
        if (data.id === msgId) {
          ws.removeEventListener('message', handler);
          resolve(data.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  const evalRes = await call('Runtime.evaluate', {
    expression: scriptCode,
    returnByValue: true
  });

  console.log('[+] Hot apply completed successfully:', evalRes);
  ws.close();
}

run().catch(console.error);
