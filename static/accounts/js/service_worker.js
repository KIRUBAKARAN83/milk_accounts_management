const CACHE_NAME = "milk-billing-v2";
const CORE_ASSETS = [
  "/static/accounts/offline.html",
  "/static/accounts/css/offline.css",
  "/static/accounts/js/offline.js",
  "/static/accounts/js/pwa.js"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.addAll(CORE_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys
          .filter(function (key) { return key.indexOf("milk-billing-") === 0 && key !== CACHE_NAME; })
          .map(function (key) { return caches.delete(key); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("fetch", function (event) {
  if (event.request.method !== "GET" || new URL(event.request.url).origin !== self.location.origin) return;

  var requestUrl = new URL(event.request.url);
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(function () {
        return caches.match("/static/accounts/offline.html").then(function (cached) {
          return cached || Response.error();
        });
      })
    );
    return;
  }

  if (requestUrl.pathname.indexOf("/static/accounts/") === 0) {
    event.respondWith(
      caches.match(event.request).then(function (cached) {
        if (cached) return cached;
        return fetch(event.request).then(function (response) {
          if (response && response.status === 200 && response.type === "basic") {
            var copy = response.clone();
            caches.open(CACHE_NAME).then(function (cache) {
              cache.put(event.request, copy);
            });
          }
          return response;
        });
      })
    );
  }
});
