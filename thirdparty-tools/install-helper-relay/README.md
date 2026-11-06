# Freedom Arrow install helper relay

Keeps the DeepSeek API key off players' PCs. The launcher talks to this Worker; only the Worker talks to DeepSeek.

## Set up (one time, by the key owner)
1. Make a free Cloudflare account and install Node.js.
2. In this folder:
   ```
   npx wrangler login
   npx wrangler secret put DEEPSEEK_API_KEY     # paste the key when asked; it is stored encrypted
   npx wrangler deploy
   ```
3. Wrangler prints the address, for example `https://fa-install-helper.<name>.workers.dev`.
   Give that address (not the key) to BA Codex to build into the launcher.

## Limits
- 5 questions per minute per IP, 12 KB per request, last 8 messages, answers up to 600 tokens.
- Nothing is stored. Set a monthly spending limit in the DeepSeek dashboard as well.

## Turn it off
`npx wrangler delete` or remove the secret: `npx wrangler secret delete DEEPSEEK_API_KEY`.
