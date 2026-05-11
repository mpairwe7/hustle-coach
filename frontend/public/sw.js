// HustleScale Service Worker v4 — Enhanced offline-first PWA
const CACHE_VERSION = "hustle-scale-v4";
const STATIC_ASSETS = [
  "/",
  "/chat",
  "/dashboard",
  "/leaderboard",
  "/auth",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/offline.html",
];

// API paths that should never be cached
const API_PATHS = ["/v1/", "/api/"];

// Install — pre-cache app shell
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activate — purge old caches
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_VERSION)
            .map((key) => caches.delete(key))
        )
      )
  );
  self.clients.claim();
});

// Fetch — strategy per request type
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET
  if (request.method !== "GET") return;

  // Skip API requests — always network
  if (API_PATHS.some((p) => url.pathname.startsWith(p))) return;

  // Static assets (JS/CSS/images) — stale-while-revalidate
  if (
    url.pathname.match(
      /\.(js|css|png|jpg|jpeg|svg|ico|woff2?|ttf|eot)(\?.*)?$/
    )
  ) {
    event.respondWith(
      caches.open(CACHE_VERSION).then((cache) =>
        cache.match(request).then((cached) => {
          const networkFetch = fetch(request)
            .then((response) => {
              if (response.ok) cache.put(request, response.clone());
              return response;
            })
            .catch(() => cached || new Response("", { status: 503 }));

          return cached || networkFetch;
        })
      )
    );
    return;
  }

  // Navigation — network-first with cache fallback
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
          }
          return response;
        })
        .catch(() =>
          caches
            .match(request)
            .then((cached) => cached || caches.match("/"))
            .then(
              (fallback) =>
                fallback ||
                caches.match("/offline.html").then(
                  (offline) => offline || new Response("Offline", { status: 503, headers: { "Content-Type": "text/plain" } })
                )
            )
        )
    );
    return;
  }

  // Default — network-first with cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_VERSION).then((cache) => cache.put(request, clone));
        }
        return response;
      })
      .catch(() =>
        caches.match(request).then(
          (cached) => cached || new Response("", { status: 503 })
        )
      )
  );
});

// Background sync — queue failed API calls for retry
self.addEventListener("sync", (event) => {
  if (event.tag === "retry-feedback") {
    event.waitUntil(retryQueuedRequests());
  }
});

async function retryQueuedRequests() {
  try {
    const cache = await caches.open("hustle-scale-queue");
    const requests = await cache.keys();
    for (const request of requests) {
      try {
        const cached = await cache.match(request);
        if (cached) {
          const body = await cached.text();
          await fetch(request, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body,
          });
          await cache.delete(request);
        }
      } catch {
        // Will retry on next sync
      }
    }
  } catch {}
}
