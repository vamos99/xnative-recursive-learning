#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP_DIR="$(mktemp -d -t xnative-background-api.XXXXXX)"
DB_PATH="$TMP_DIR/xnative-background.sqlite3"
API_LOG="$TMP_DIR/api.log"
PORT="${XNATIVE_QA_PORT:-$((18000 + RANDOM % 10000))}"
API_URL="http://127.0.0.1:$PORT"

print_api_log() {
  if [[ -f "$API_LOG" ]]; then
    echo "--- uvicorn log ---" >&2
    cat "$API_LOG" >&2
  fi
}

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT
trap print_api_log ERR

XNATIVE_DB="$DB_PATH" "$ROOT_DIR/.venv/bin/uvicorn" xnative.api.main:app \
  --host 127.0.0.1 \
  --port "$PORT" \
  --log-level warning >"$API_LOG" 2>&1 &
API_PID=$!

API_URL="$API_URL" "$ROOT_DIR/.venv/bin/python" - <<'PY'
import json
import os
import time
import urllib.request

api_url = os.environ["API_URL"]
deadline = time.time() + 10
while time.time() < deadline:
    try:
        with urllib.request.urlopen(f"{api_url}/ready", timeout=1) as response:
            body = json.loads(response.read().decode("utf-8"))
        if body.get("status") == "ready":
            raise SystemExit(0)
    except Exception:
        time.sleep(0.2)
raise SystemExit(f"API did not become ready on {api_url}")
PY

ROOT_DIR="$ROOT_DIR" API_URL="$API_URL" node --input-type=commonjs <<'JS'
const fs = require('fs');
const path = require('path');
const vm = require('vm');

(async () => {
  const root = process.env.ROOT_DIR;
  const backgroundSource = fs.readFileSync(path.join(root, 'extension/background.js'), 'utf8');
  const fixture = JSON.parse(
    fs.readFileSync(path.join(root, 'tests/fixtures/dom_capture_posts.json'), 'utf8')
  );
  const post = fixture.posts[0];

let messageListener = null;
const localStore = {};
const syncStore = { captureEnabled: true };

function selectValues(store, keys) {
  if (typeof keys === 'string') return { [keys]: store[keys] };
  if (Array.isArray(keys)) {
    return Object.fromEntries(keys.map(key => [key, store[key]]));
  }
  if (keys && typeof keys === 'object') {
    return Object.fromEntries(
      Object.entries(keys).map(([key, fallback]) => [key, store[key] ?? fallback])
    );
  }
  return { ...store };
}

const chrome = {
  storage: {
    local: {
      get: async keys => selectValues(localStore, keys),
      set: async value => Object.assign(localStore, value),
    },
    sync: {
      get: (keys, callback) => callback(selectValues(syncStore, keys)),
      set: (value, callback) => {
        Object.assign(syncStore, value);
        if (callback) callback();
      },
    },
  },
  runtime: {
    onMessage: {
      addListener(listener) {
        messageListener = listener;
      },
    },
    onStartup: { addListener() {} },
    onInstalled: { addListener() {} },
  },
  alarms: {
    create() {},
    onAlarm: { addListener() {} },
  },
};

const sandbox = {
  XNATIVE_BACKEND_URL: process.env.API_URL,
  chrome,
  console,
  fetch,
  TextEncoder,
  Set,
  Date,
  Math,
  Error,
  setTimeout,
  clearTimeout,
};
vm.createContext(sandbox);
vm.runInContext(backgroundSource, sandbox, { filename: 'extension/background.js' });

if (!messageListener) throw new Error('background listener was not registered');

const response = await new Promise(resolve => {
  const keepAlive = messageListener(
    { type: 'CAPTURE_POST', data: post },
    {},
    value => resolve(value)
  );
  if (keepAlive !== true) throw new Error('background listener did not keep channel alive');
});

if (!response || response.accepted !== true || response.duplicate !== false) {
  throw new Error(`unexpected background response: ${JSON.stringify(response)}`);
}

const outbox = localStore.xnativeCaptureOutbox || [];
if (outbox.length !== 0) {
  throw new Error(`expected empty outbox after successful delivery: ${JSON.stringify(outbox)}`);
}
console.log('background delivery accepted');
})().catch(error => {
  console.error(error);
  process.exit(1);
});
JS

DB_PATH="$DB_PATH" "$ROOT_DIR/.venv/bin/python" - <<'PY'
import os
import sqlite3

db_path = os.environ["DB_PATH"]
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
post = conn.execute(
    "SELECT canonical_url, selector_version FROM captured_posts"
).fetchone()
job_count = conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"]
inbox_count = conn.execute("SELECT COUNT(*) AS c FROM capture_inbox").fetchone()["c"]
media_count = conn.execute("SELECT COUNT(*) AS c FROM media_assets").fetchone()["c"]

assert post["canonical_url"] == "https://x.com/example/status/1840000000000000300", dict(post)
assert post["selector_version"] == "visible_dom_fixture_v2", dict(post)
assert job_count == 1, job_count
assert inbox_count == 1, inbox_count
assert media_count == 2, media_count
print("background -> API -> DB fixture ok")
PY
