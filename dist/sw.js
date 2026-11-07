/* Shamanigans service worker — build 20261107-0912-17591d06 */
var BUILD = '20261107-0912-17591d06';
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
  var isFont = /fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
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
