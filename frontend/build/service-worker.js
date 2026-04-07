// CineWorld Studio's - Pro Service Worker
const CACHE_VERSION = 'cw-v3';
const STATIC_CACHE = `cw-static-${CACHE_VERSION}`;
const SHELL_CACHE = `cw-shell-${CACHE_VERSION}`;

// App shell - precache for instant open
const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Static asset extensions to cache aggressively (Cache-First)
const STATIC_EXTENSIONS = ['.js', '.css', '.woff', '.woff2', '.ttf', '.eot', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico', '.gif'];

function isStaticAsset(url) {
  return STATIC_EXTENSIONS.some(ext => url.pathname.endsWith(ext));
}

function isAPIRequest(url) {
  return url.pathname.startsWith('/api/') || url.pathname.startsWith('/api');
}

function isNavigationRequest(request) {
  return request.mode === 'navigate';
}

// INSTALL: Precache app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

// ACTIVATE: Clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== STATIC_CACHE && k !== SHELL_CACHE)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// FETCH: Strategy router
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET, socket, chrome-extension etc
  if (event.request.method !== 'GET') return;
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;
  if (url.pathname.includes('/socket.io/')) return;

  // API requests: Network-First, cache as offline fallback ONLY
  if (isAPIRequest(url)) {
    event.respondWith(networkFirstAPI(event.request));
    return;
  }

  // Static assets (JS/CSS/images/fonts): Cache-First for speed
  if (isStaticAsset(url)) {
    event.respondWith(cacheFirstStatic(event.request));
    return;
  }

  // Navigation (HTML pages): Network-First, fallback to app shell
  if (isNavigationRequest(event.request)) {
    event.respondWith(networkFirstNavigation(event.request));
    return;
  }

  // Everything else: Network with cache fallback
  event.respondWith(networkFirstGeneric(event.request));
});

// --- Strategies ---

// API: Always go to network. Cache response ONLY as offline fallback.
async function networkFirstAPI(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      // Store in a volatile API cache (not static)
      const apiCache = await caches.open('cw-api-fallback');
      apiCache.put(request, response.clone());
    }
    return response;
  } catch {
    // Offline: try cached version
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ error: 'Offline', detail: 'Connessione non disponibile' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Static: Cache-First. Fetch and cache if not found.
async function cacheFirstStatic(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    return new Response('', { status: 503 });
  }
}

// Navigation: Network-First, fallback to cached index.html (SPA)
async function networkFirstNavigation(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch {
    const cached = await caches.match('/index.html') || await caches.match('/');
    if (cached) return cached;
    return new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/html' } });
  }
}

// Generic: Network with cache fallback
async function networkFirstGeneric(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('', { status: 503 });
  }
}

// Listen for skip waiting message
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
