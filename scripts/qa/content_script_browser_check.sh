#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
PWCLI="${PWCLI:-$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh}"
PORT="${XNATIVE_QA_HTTP_PORT:-8765}"
FIXTURE_URL="http://127.0.0.1:$PORT/tests/fixtures/content_script_dom_fixture.html"

SERVER_LOG="$(mktemp -t xnative-content-script-server.XXXXXX)"
"$ROOT_DIR/.venv/bin/python" -m http.server "$PORT" --bind 127.0.0.1 \
  --directory "$ROOT_DIR" >"$SERVER_LOG" 2>&1 &
SERVER_PID=$!
trap '"$PWCLI" close >/dev/null 2>&1 || true; kill "$SERVER_PID" >/dev/null 2>&1 || true' EXIT
sleep 0.5

"$PWCLI" open "$FIXTURE_URL" --json >/dev/null

RESULT="$("$PWCLI" eval 'async () => {
  await new Promise(resolve => setTimeout(resolve, 200));
  const messages = window.__xnativeMessages || [];
  const article = document.querySelector("article[role=\"article\"]");
  return {
    messageCount: messages.length,
    captured: article ? article.dataset.xnativeCaptured === "true" : false,
    pending: article ? Boolean(article.dataset.xnativePending) : true,
    first: messages[0] || null
  };
}' --raw)"

RESULT_JSON="$RESULT" "$ROOT_DIR/.venv/bin/python" - <<'PY'
import json
import os

result = json.loads(os.environ["RESULT_JSON"])
assert result["messageCount"] == 1, result
assert result["captured"] is True, result
assert result["pending"] is False, result
message = result["first"]
assert message["type"] == "CAPTURE_POST", message
data = message["data"]
assert data["url"] == "https://x.com/example/status/1840000000000000400", data
assert data["author_handle"] == "Example", data
assert data["quoted_text"], data
assert data["quoted_url"] == "https://x.com/analyst/status/1840000000000000200", data
assert len(data["media"]) == 2, data
assert [item["media_scope"] for item in data["media"]] == ["post", "quote"], data
assert all("profile_images" not in item["url"] for item in data["media"]), data
assert data["parse_quality"]["has_url"] is True, data
assert data["parse_quality"]["has_author"] is True, data
assert data["parse_quality"]["has_quote"] is True, data
assert data["parse_quality"]["media_count"] == 2, data
print("content-script browser fixture ok")
PY
