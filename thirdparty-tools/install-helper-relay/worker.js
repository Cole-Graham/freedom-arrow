// Freedom Arrow install helper relay (Cloudflare Worker).
// The DeepSeek key lives only here, as the secret DEEPSEEK_API_KEY. The launcher never has it.
// The launcher sends { report, messages:[{role,content}] }. Nothing is stored.

const MAX_BODY = 12000;      // bytes per request
const MAX_TURNS = 8;         // player + helper messages kept per request
const MAX_TOKENS = 600;      // answer length cap

const SYSTEM = `You help players install the Freedom Arrow mod for the game Broken Arrow.
You only help with installing and starting the mod: the Freedom Arrow Mod Launcher, MelonLoader,
the .bamod file, Steam launch options, Proton on Linux, and turning other mods off.
Answer in short numbered steps in plain words for people who are not technical.
You can only see the install report and the messages below. You cannot see or change the player's PC.
Never ask for passwords, Steam login or personal details. If the question is not about installing
Freedom Arrow, say you can only help with installing it and point to the Freedom Arrow Discord.
Facts:
- The Mod Launcher's PLAY button installs MelonLoader and the mod pack, then starts the game (Windows).
- On Linux, install with the launcher under Proton, then start the game from Steam with launch options
  WINEDLLOVERRIDES="version=n,b" %command% and choose "Play Anti-Cheat Disabled". The launcher's PLAY
  button starts the game without mods on Linux.
- Only one mod pack may be on: turn ActualArrow and other gameplay mods off.
- Everyone in a lobby needs the same Freedom Arrow version, or the game says "Not all players have the scenario".
- If files are damaged, drop the .bamod file on the launcher to install it again, then fully restart the game.
- Never use mods in ranked or quick match.`;

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return json({ error: "POST only" }, 405);
    const ip = request.headers.get("cf-connecting-ip") || "unknown";
    const { success } = await env.LIMITER.limit({ key: ip });
    if (!success) return json({ error: "Too many questions. Wait a minute and try again." }, 429);

    const raw = await request.text();
    if (raw.length > MAX_BODY) return json({ error: "Message too long." }, 413);
    let body;
    try { body = JSON.parse(raw); } catch { return json({ error: "Bad request." }, 400); }
    const report = String(body.report || "").slice(0, 6000);
    const turns = (Array.isArray(body.messages) ? body.messages : [])
      .filter(m => (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
      .slice(-MAX_TURNS)
      .map(m => ({ role: m.role, content: m.content.slice(0, 2000) }));
    if (!turns.length || turns[turns.length - 1].role !== "user") return json({ error: "No question." }, 400);

    const r = await fetch("https://api.deepseek.com/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Authorization": `Bearer ${env.DEEPSEEK_API_KEY}` },
      body: JSON.stringify({
        model: "deepseek-chat",
        max_tokens: MAX_TOKENS,
        temperature: 0.2,
        messages: [{ role: "system", content: SYSTEM }, { role: "user", content: "Install report:\n" + report }, ...turns],
      }),
    });
    if (!r.ok) return json({ error: "The helper is busy. Try again later." }, 502);
    const data = await r.json();
    return json({ answer: data?.choices?.[0]?.message?.content || "" });
  },
};

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });
}
