// Background service worker. It forwards visible-page captures to localhost only.
const BACKEND_URL = globalThis.XNATIVE_BACKEND_URL || 'http://localhost:8000';
const OUTBOX_KEY = 'xnativeCaptureOutbox';
const RETRY_ALARM = 'xnativeRetryOutbox';
const MAX_BACKOFF_MS = 5 * 60 * 1000;
const MAX_CAPTURE_BYTES = 512 * 1024;
const MAX_OUTBOX_ITEMS = 500;
const sentCache = new Set();
let flushInProgress = false;

function hashPost(post) {
  const media = post.media && post.media.length ? post.media[0].url : '';
  return `${post.url || ''}::${post.author_handle || ''}::${post.text || ''}::${media}`;
}

async function sendToBackend(post) {
  const response = await fetch(`${BACKEND_URL}/capture`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(post),
  });
  if (!response.ok) throw new Error(`XNative backend status ${response.status}`);
}

function payloadBytes(post) {
  return new TextEncoder().encode(JSON.stringify(post)).length;
}

function getLocal(keys) {
  return chrome.storage.local.get(keys);
}

function setLocal(value) {
  return chrome.storage.local.set(value);
}

async function getOutbox() {
  const result = await getLocal(OUTBOX_KEY);
  return Array.isArray(result[OUTBOX_KEY]) ? result[OUTBOX_KEY] : [];
}

async function saveOutbox(outbox) {
  await setLocal({ [OUTBOX_KEY]: outbox });
}

function nextBackoffMs(attempts) {
  const base = Math.min(MAX_BACKOFF_MS, 2000 * (2 ** Math.max(0, attempts - 1)));
  return Math.floor(base / 2 + Math.random() * (base / 2));
}

async function enqueue(post) {
  if (payloadBytes(post) > MAX_CAPTURE_BYTES) {
    return { accepted: false, reason: 'payload_too_large' };
  }
  const key = hashPost(post);
  if (sentCache.has(key)) return { accepted: true, duplicate: true };
  const outbox = await getOutbox();
  if (outbox.some(item => item.key === key)) return { accepted: true, duplicate: true };
  while (outbox.length >= MAX_OUTBOX_ITEMS) outbox.shift();
  outbox.push({
    key,
    post,
    attempts: 0,
    nextAttemptAt: 0,
    lastError: '',
    createdAt: Date.now(),
  });
  await saveOutbox(outbox);
  return { accepted: true, duplicate: false };
}

async function flushOutbox() {
  if (flushInProgress) return;
  flushInProgress = true;
  try {
    const now = Date.now();
    const outbox = await getOutbox();
    const remaining = [];
    for (const item of outbox) {
      if (sentCache.has(item.key)) continue;
      if (item.nextAttemptAt && item.nextAttemptAt > now) {
        remaining.push(item);
        continue;
      }
      try {
        await sendToBackend(item.post);
        sentCache.add(item.key);
      } catch (err) {
        const attempts = (item.attempts || 0) + 1;
        remaining.push({
          ...item,
          attempts,
          nextAttemptAt: Date.now() + nextBackoffMs(attempts),
          lastError: String(err && err.message ? err.message : err),
        });
      }
    }
    await saveOutbox(remaining);
  } finally {
    flushInProgress = false;
  }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type !== 'CAPTURE_POST') return false;
  const post = message.data;
  chrome.storage.sync.get('captureEnabled', async result => {
    try {
      const enabled = result.captureEnabled !== false;
      if (!enabled) {
        sendResponse({ accepted: false, reason: 'capture_disabled' });
        return;
      }
      const queued = await enqueue(post);
      if (queued.accepted) await flushOutbox();
      sendResponse(queued);
    } catch (err) {
      sendResponse({
        accepted: false,
        reason: String(err && err.message ? err.message : err),
      });
    }
  });
  return true;
});

chrome.alarms.create(RETRY_ALARM, { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === RETRY_ALARM) flushOutbox();
});

chrome.runtime.onStartup.addListener(flushOutbox);
chrome.runtime.onInstalled.addListener(flushOutbox);
