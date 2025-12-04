/**
 * PEA RE Forecast Platform - Service Worker
 * Provides offline caching and background sync capabilities.
 * Part of v1.1.0 Mobile-Responsive Dashboard (PWA) feature.
 */

const CACHE_NAME = "pea-forecast-v1.1.0";
const STATIC_CACHE = "pea-static-v1.1.0";
const DATA_CACHE = "pea-data-v1.1.0";

// Static assets to cache on install
const STATIC_ASSETS = ["/", "/manifest.json", "/icons/icon.svg", "/offline.html"];

// API routes to cache with network-first strategy
const API_ROUTES = ["/api/v1/forecast/", "/api/v1/alerts/", "/api/v1/data/"];

// Install event - cache static assets
self.addEventListener("install", (event) => {
  console.log("[SW] Installing service worker...");
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => {
      console.log("[SW] Caching static assets");
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
  console.log("[SW] Activating service worker...");
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => {
            return name !== CACHE_NAME && name !== STATIC_CACHE && name !== DATA_CACHE;
          })
          .map((name) => {
            console.log("[SW] Deleting old cache:", name);
            return caches.delete(name);
          })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - handle requests
self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== "GET") {
    return;
  }

  // Skip chrome-extension and other non-http(s) requests
  if (!url.protocol.startsWith("http")) {
    return;
  }

  // API requests - network first, fallback to cache
  if (isApiRequest(url)) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // Static assets - cache first, fallback to network
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirstStrategy(request));
    return;
  }

  // Navigation requests - network first with offline fallback
  if (request.mode === "navigate") {
    event.respondWith(navigationStrategy(request));
    return;
  }

  // Default - network first
  event.respondWith(networkFirstStrategy(request));
});

// Check if request is for API
function isApiRequest(url) {
  return API_ROUTES.some((route) => url.pathname.startsWith(route));
}

// Check if request is for static asset
function isStaticAsset(url) {
  const staticExtensions = [
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
  ];
  return staticExtensions.some((ext) => url.pathname.endsWith(ext));
}

// Cache-first strategy
async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log("[SW] Cache-first fetch failed:", error);
    return new Response("Offline", { status: 503 });
  }
}

// Network-first strategy
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(DATA_CACHE);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log("[SW] Network-first fetch failed, trying cache:", error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    return new Response(JSON.stringify({ error: "Offline", cached: false }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}

// Navigation strategy with offline fallback
async function navigationStrategy(request) {
  try {
    const preloadResponse = await event.preloadResponse;
    if (preloadResponse) {
      return preloadResponse;
    }

    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (_error) {
    console.log("[SW] Navigation failed, showing offline page");
    const cachedResponse = await caches.match("/offline.html");
    if (cachedResponse) {
      return cachedResponse;
    }
    return caches.match("/");
  }
}

// Background sync for offline form submissions
self.addEventListener("sync", (event) => {
  console.log("[SW] Background sync:", event.tag);
  if (event.tag === "sync-alerts") {
    event.waitUntil(syncAlerts());
  }
});

async function syncAlerts() {
  // Sync any queued alert acknowledgments
  console.log("[SW] Syncing alerts...");
}

// Push notifications
self.addEventListener("push", (event) => {
  console.log("[SW] Push notification received");

  let data = { title: "PEA Alert", body: "New notification" };

  if (event.data) {
    try {
      data = event.data.json();
    } catch (_e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: "/icons/icon-192x192.png",
    badge: "/icons/icon-72x72.png",
    vibrate: [100, 50, 100],
    data: {
      url: data.url || "/",
      dateOfArrival: Date.now(),
    },
    actions: [
      { action: "view", title: "View" },
      { action: "dismiss", title: "Dismiss" },
    ],
    tag: data.tag || "pea-notification",
    renotify: true,
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

// Notification click handler
self.addEventListener("notificationclick", (event) => {
  console.log("[SW] Notification clicked:", event.action);
  event.notification.close();

  if (event.action === "dismiss") {
    return;
  }

  const url = event.notification.data?.url || "/";

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      // Focus existing window if available
      for (const client of clientList) {
        if (client.url === url && "focus" in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// Message handler for cache management
self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }

  if (event.data && event.data.type === "CLEAR_CACHE") {
    event.waitUntil(
      caches.keys().then((names) => {
        return Promise.all(names.map((name) => caches.delete(name)));
      })
    );
  }
});
