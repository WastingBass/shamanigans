# Shamanigans

A personal life planner — schedule, habits, time blocking, tasks, rewards and
tracking — built as a single self-contained page that installs to an iPhone
Home Screen and runs with no signal.

Not distributed, not multi-user. One person, two devices.

## What's here

| Path | What it is |
|---|---|
| `planner.html` | **The app.** One file: markup, styles and script. This is the only file to edit. |
| `build-pwa.py` | Wraps `planner.html` into `dist/` — adds the manifest, iOS meta tags and a versioned service worker. |
| `mkicons.js` | Regenerates the app icons from the wave mark. Only needed if the icon changes. |
| `dist/` | **The built site. Netlify serves this folder.** Committed on purpose, so no build runs on deploy. |
| `netlify.toml` | Tells Netlify to publish `dist/` and never to cache the shell or the worker. |

## Making a change

```bash
# edit planner.html, then:
python3 build-pwa.py        # rewrites dist/ with a fresh build stamp
git add -A && git commit -m "what changed" && git push
```

Netlify rebuilds within a minute of the push. The phone picks it up the next
time the app is opened: the service worker re-checks `sw.js` (served
`no-cache`), installs the new build, claims the page and reloads it once.

Nothing needs re-adding to the Home Screen, and no data is lost on an update.

## Where the data lives

In the browser's local storage, keyed to the domain. It never leaves the
device and is not in this repo. Settings → Backup writes a JSON file and
reads one back; that is the only way data moves between devices today.

**Never commit a backup file.** They contain real tasks, habits and notes.
`.gitignore` already excludes `seed*.json` and anything matching `*backup*`.

## Checking a change before pushing

The app is plain ES5 in one `<script>`, so a syntax check is cheap:

```bash
node -e 'const h=require("fs").readFileSync("planner.html","utf8");
  new Function(h.split("<script>")[1].split("</script>")[0]);console.log("ok")'
```

Layout and touch behaviour are verified against headless Chromium at phone
sizes — the drags in particular need real touch events, because mouse
emulation does not exercise the long-press path.

## Known limits

- Phone and laptop hold separate data until a sync backend exists. The backup
  file is the bridge.
- Week view on a phone is seven columns in under 400px, so task titles
  truncate. Day view is the comfortable one.
- Calendar sync is not built. The target is Microsoft Graph, against the
  Outlook account, which can run entirely client-side.
