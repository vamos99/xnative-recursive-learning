// Local-first X visible-page capture. No X API, no credentials, no public actions.
(() => {
  const POST_SELECTOR = 'article[role="article"]';
  const POST_LIMIT_PER_SESSION = 100;
  let sentCount = 0;

  function textOf(el) { return el ? (el.innerText || '').trim() : ''; }

  function extractPostUrl(postEl) {
    const links = [...postEl.querySelectorAll('a[href*="/status/"]')];
    const href = links.map(a => a.href).find(Boolean) || '';
    return href.split('?')[0];
  }

  function extractAuthor(postEl) {
    const handleEl = [...postEl.querySelectorAll('a[href^="/"] span')]
      .find(s => (s.innerText || '').startsWith('@'));
    return handleEl ? handleEl.innerText.replace('@', '').trim() : 'unknown';
  }

  function extractQuoted(postEl) {
    const quoted = [...postEl.querySelectorAll('div[role="link"]')]
      .find(el => el.querySelector('time') || (el.innerText || '').includes('@'));
    return {
      quoted_text: quoted ? textOf(quoted) : '',
      quoted_author: quoted ? extractAuthor(quoted) : '',
      quoted_url: quoted ? extractPostUrl(quoted) : ''
    };
  }

  function extractMedia(postEl) {
    const media = [];
    postEl.querySelectorAll('img, video').forEach(el => {
      const url = el.currentSrc || el.src || '';
      if (!url || url.startsWith('data:')) return;
      media.push({
        type: el.tagName.toLowerCase() === 'video' ? 'video' : 'image',
        url,
        alt_text: el.getAttribute('alt') || '',
      });
    });
    return media;
  }

  function extractMetrics(postEl) {
    const metrics = {};
    postEl.querySelectorAll('[aria-label]').forEach(el => {
      const label = el.getAttribute('aria-label') || '';
      if (/like|repost|reply|view|beğeni|yanıt|görüntülenme/i.test(label)) {
        metrics[label] = textOf(el);
      }
    });
    return metrics;
  }

  function extractPost(postEl) {
    if (postEl.dataset.xnativeCaptured || postEl.dataset.xnativePending) return null;
    if (sentCount >= POST_LIMIT_PER_SESSION) return null;
    const textEl = postEl.querySelector('[data-testid="tweetText"]') || postEl.querySelector('[lang]');
    const url = extractPostUrl(postEl);
    const quoted = extractQuoted(postEl);
    const media = extractMedia(postEl);
    const text = textOf(textEl);
    const author = extractAuthor(postEl);
    const parseQuality = {
      has_url: Boolean(url),
      has_author: Boolean(author && author !== 'unknown'),
      has_text: Boolean(text),
      has_quote: Boolean(quoted.quoted_text),
      media_count: media.length,
      selector_version: 'visible_dom_v1'
    };
    return {
      text,
      url,
      author_handle: author,
      display_name: textOf(postEl.querySelector('[data-testid="User-Name"]')),
      timestamp: (postEl.querySelector('time') || {}).dateTime || '',
      visible_metrics: extractMetrics(postEl),
      media,
      ...quoted,
      parse_quality: parseQuality,
      raw_capture_version: 'visible_dom_v1'
    };
  }

  function sendPost(postEl, postData) {
    postEl.dataset.xnativePending = 'true';
    chrome.runtime.sendMessage({ type: 'CAPTURE_POST', data: postData }, response => {
      delete postEl.dataset.xnativePending;
      if (chrome.runtime.lastError) return;
      if (response && response.accepted) {
        postEl.dataset.xnativeCaptured = 'true';
        sentCount += 1;
      }
    });
  }

  function scanVisiblePosts() {
    document.querySelectorAll(POST_SELECTOR).forEach(postEl => {
      const post = extractPost(postEl);
      if (post && (post.text || post.media.length || post.quoted_text)) sendPost(postEl, post);
    });
  }

  let timer = null;
  const observer = new MutationObserver(() => {
    if (timer) return;
    timer = setTimeout(() => { timer = null; scanVisiblePosts(); }, 1500);
  });

  function initialise() {
    observer.observe(document.body, { childList: true, subtree: true });
    scanVisiblePosts();
  }

  if (document.readyState === 'complete' || document.readyState === 'interactive') initialise();
  else window.addEventListener('DOMContentLoaded', initialise);
})();
