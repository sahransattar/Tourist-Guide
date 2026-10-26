/* =========================================================
   Tourist Guide PWA - Service Worker (service-worker.js)
   Cache API & Offline Caching Strategies
   ========================================================= */

const CACHE_NAME = 'tourist-guide-v1.0';
const STATIC_ASSETS = [
  '/',
  '/places',
  '/favorites',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/js/favorites.js',
  '/static/js/pwa.js',
  '/static/manifest.json',
  '/static/offline.html',
  '/static/images/default_place.jpg',
  '/static/images/taj_mahal.jpg',
  '/static/images/jaipur_palace.jpg',
  '/static/images/goa_beach.jpg',
  '/static/images/kerala_backwaters.jpg',
  '/static/images/varanasi_ghats.jpg',
  '/static/images/pangong_lake.jpg',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png'
];

// 1. Install Event: Cache Core Static Resources
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching Core App Shell...');
      return cache.addAll(STATIC_ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate Event: Clean up outdated caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating Service Worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            console.log('[ServiceWorker] Removing Old Cache:', cache);
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch Event: Serve cached content or fetch from network with offline fallbacks
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Skip non-GET requests or browser extension requests
  if (request.method !== 'GET' || !url.protocol.startsWith('http')) {
    return;
  }

  // Strategy A: Static Assets (CSS, JS, Images, Manifest) -> Cache First, Network Fallback
  if (
    request.destination === 'style' ||
    request.destination === 'script' ||
    request.destination === 'image' ||
    url.pathname.startsWith('/static/')
  ) {
    event.respondWith(
      caches.match(request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => {
          // If image request fails offline, return default placeholder
          if (request.destination === 'image') {
            return caches.match('/static/images/default_place.jpg');
          }
        });
      })
    );
    return;
  }

  // Strategy B: HTML Pages & Navigation -> Network First, Cache Fallback, Offline HTML Page
  if (request.mode === 'navigate' || request.headers.get('accept').includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          // Dynamic Cache visited HTML pages
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => {
          return caches.match(request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            return caches.match('/static/offline.html');
          });
        })
    );
    return;
  }

  // Strategy C: API Endpoints (/api/places) -> Network First with Cache Fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => caches.match(request))
    );
    return;
  }

  // Default Stale-While-Revalidate
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, networkResponse.clone());
          });
        }
        return networkResponse;
      }).catch(() => cachedResponse);
      return cachedResponse || fetchPromise;
    })
  );
});
