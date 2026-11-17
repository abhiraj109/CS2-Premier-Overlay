# Security and privacy

Report vulnerabilities privately using **Security → Report a vulnerability** after the maintainer enables private vulnerability reporting on GitHub. Include affected version, conditions, impact and a minimal example with fictional data. Avoid sharing credentials or personal files. For a local candidate, contact the maintainer directly.

- The HTTP server binds to `127.0.0.1:3000` and checks Host, Origin and browser cross-site request metadata. Keep it on loopback. Local processes with access to this user's network session can still read or change overlay data. The GSI token shipped in the config distinguishes packets and is public.
- The overlay reads account identifiers and persona names from Steam's active registry entry, its recent-login config and GSI. No Steam credentials are needed. The Browser Source can display the selected account's identifier, name and public avatar.
- In normal mode Leetify receives the chosen SteamID64, typical HTTPS connection metadata, and the optional user-provided API key. Public avatars may cause a browser request to the avatar host. Use `run_overlay.bat --offline` to disable provider requests and avatar data for the session.
- `%LOCALAPPDATA%\CS2PremierOverlay` can contain a SteamID64 override and match history with timestamps and stats. The overlay logs to its console. Provider data stays in memory. Redact identifiers, passwords, paths and credentials in screenshots or diagnostic output.
- Keep `LEETIFY_API_KEY` in your Windows user environment. If a key leaks, revoke or rotate it at the provider first. If it entered Git, remove it from the affected history and coordinate with anyone holding copies before publishing or rewriting shared branches. Never rely on ignore rules to erase past commits.
