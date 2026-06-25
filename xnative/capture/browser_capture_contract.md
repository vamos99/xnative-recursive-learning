# Browser Capture Contract

The MVP does not use X API. Browser capture reads only content visible in the user's own browser tab.

Required payload fields: `text`, `url`, `author_handle`, `timestamp`.
Optional fields: `display_name`, `quoted_text`, `quoted_author`, `quoted_url`, `visible_metrics`, `media[].url`, `media[].alt_text`, `media[].type`.

The extension must not collect passwords, cookies, 2FA codes, tokens, or hidden user data. It must not like, repost, follow, reply, quote, or publish.
