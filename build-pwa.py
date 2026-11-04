#!/usr/bin/env python3
"""Turn planner.html into an installable, offline-capable PWA in dist/."""
import json, hashlib, pathlib, datetime

here = pathlib.Path(__file__).parent
dist = here / "dist"
dist.mkdir(exist_ok=True)

src = (here / "planner.html").read_text(encoding="utf-8")
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M")
build = f"{stamp}-{hashlib.sha256(src.encode()).hexdigest()[:8]}"

HEAD = """<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,minimum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="description" content="Shamanigans — schedule, habits, time blocking, tasks and rewards.">
<meta name="application-name" content="Shamanigans">
<meta name="apple-mobile-web-app-title" content="Shamanigans">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="format-detection" content="telephone=no">
<meta name="theme-color" content="#F2F5F4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#101614" media="(prefers-color-scheme: dark)">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
"""

SW_REG = """<script>
/* service worker: the app shell is cached, so it opens with no signal */
if('serviceWorker' in navigator){
  window.addEventListener('load',function(){
    navigator.serviceWorker.register('sw.js').catch(function(){});
  });
  var reloading=false;
  navigator.serviceWorker.addEventListener('controllerchange',function(){
    if(reloading) return; reloading=true; location.reload();
  });
}
</script>
"""

# planner.html opens with <title>; drop the artifact-only viewport hint.
out = src.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
anchor = "<title>Shamanigans</title>\n"
assert out.count(anchor) == 1, "title anchor missing"
out = out.replace(anchor, anchor + HEAD)
out = out.rstrip() + "\n" + SW_REG
(dist / "index.html").write_text(out, encoding="utf-8")

manifest = {
    "name": "Shamanigans",
    "short_name": "Shamanigans",
    "description": "Schedule, habits, time blocking, tasks and rewards.",
    "start_url": "./index.html",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait-primary",
    "background_color": "#F2F5F4",
    "theme_color": "#0E6B62",
    "categories": ["productivity", "lifestyle"],
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(dist / "manifest.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

SW = """/* Shamanigans service worker — build %BUILD% */
var BUILD = '%BUILD%';
var SHELL = 'shell-' + BUILD;
var RUNTIME = 'runtime-' + BUILD;
var ASSETS = ['./','./index.html','./manifest.webmanifest','./apple-touch-icon.png',
  './icon-192.png','./icon-512.png','./icon-maskable-512.png','./favicon-32.png'];

self.addEventListener('install', function(e){
  e.waitUntil(caches.open(SHELL).then(function(c){
    return c.addAll(ASSETS);
  }).then(function(){ return self.skipWaiting() }));
});

self.addEventListener('activate', function(e){
  e.waitUntil(caches.keys().then(function(keys){
    return Promise.all(keys.map(function(k){
      if(k !== SHELL && k !== RUNTIME) return caches.delete(k);
    }));
  }).then(function(){ return self.clients.claim() }));
});

self.addEventListener('fetch', function(e){
  var req = e.request;
  if(req.method !== 'GET') return;
  var url = new URL(req.url);

  /* every navigation gets the app shell, online or not */
  if(req.mode === 'navigate'){
    e.respondWith(
      fetch(req).then(function(res){
        var copy = res.clone();
        caches.open(SHELL).then(function(c){ c.put('./index.html', copy) });
        return res;
      }).catch(function(){
        return caches.match('./index.html', {ignoreSearch:true}).then(function(m){
          return m || new Response('<h1>Offline</h1>', {headers:{'Content-Type':'text/html'}});
        });
      })
    );
    return;
  }

  /* fonts and our own files: serve from cache, refill in the background */
  var sameOrigin = url.origin === self.location.origin;
  var isFont = /fonts\\.(googleapis|gstatic)\\.com$/.test(url.hostname);
  if(!sameOrigin && !isFont) return;

  e.respondWith(
    caches.match(req).then(function(hit){
      if(hit) return hit;
      return fetch(req).then(function(res){
        if(res && (res.status === 200 || res.type === 'opaque')){
          var copy = res.clone();
          caches.open(RUNTIME).then(function(c){ c.put(req, copy) });
        }
        return res;
      }).catch(function(){ return hit });
    })
  );
});
"""
(dist / "sw.js").write_text(SW.replace("%BUILD%", build), encoding="utf-8")

# Netlify/Cloudflare: never let the HTML or the worker go stale behind a CDN cache.
(dist / "_headers").write_text(
    "/sw.js\n  Cache-Control: no-cache\n"
    "/index.html\n  Cache-Control: no-cache\n"
    "/manifest.webmanifest\n  Cache-Control: no-cache\n",
    encoding="utf-8",
)

print("build", build)
for f in sorted(dist.iterdir()):
    print(f"  {f.name:28} {f.stat().st_size:>8,} bytes")
