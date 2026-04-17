// CineWorld Studio's - Pro Service Worker v4
// FIXED: No API caching (prevents cross-user data leaks)
const CACHE_VERSION = 'cw-v4';
const STATIC_CACHE = `cw-static-${CACHE_VERSION}`;
const SHELL_CACHE = `cw-shell-${CACHE_VERSION}`;

const APP_SHELL = ['/', '/index.html', '/manifest.json'];
const STATIC_EXTENSIONS = ['.js', '.css', '.woff', '.woff2', '.ttf', '.eot', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico', '.gif'];

function isStaticAsset(url) { return STATIC_EXTENSIONS.some(ext => url.pathname.endsWith(ext)); }
function isAPIRequest(url) { return url.pathname.startsWith('/api/') || url.pathname.startsWith('/api'); }
function isNavigationRequest(request) { return request.mode === 'navigate'; }

// INSTALL
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

// ACTIVATE: Clean ALL old caches including stale API cache
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

// FETCH
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET') return;
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;
  if (url.pathname.includes('/socket.io/')) return;

  // API: ALWAYS network, NEVER cache (prevents cross-user data leaks)
  if (isAPIRequest(url)) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ error: 'Offline', detail: 'Connessione non disponibile' }), {
          status: 503, headers: { 'Content-Type': 'application/json' }
        })
      )
    );
    return;
  }

  if (isStaticAsset(url)) {
    event.respondWith(cacheFirstStatic(event.request));
    return;
  }

  if (isNavigationRequest(event.request)) {
    event.respondWith(networkFirstNavigation(event.request));
    return;
  }

  event.respondWith(networkFirstGeneric(event.request));
});

async function cacheFirstStatic(request) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    if (response.ok) { const cache = await caches.open(STATIC_CACHE); cache.put(request, response.clone()); }
    return response;
  } catch { return new Response('', { status: 503 }); }
}

async function networkFirstNavigation(request) {
  try { return await fetch(request); }
  catch {
    const cached = await caches.match('/index.html') || await caches.match('/');
    return cached || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/html' } });
  }
}

async function networkFirstGeneric(request) {
  try {
    const response = await fetch(request);
    if (response.ok) { const cache = await caches.open(STATIC_CACHE); cache.put(request, response.clone()); }
    return response;
  } catch {
    const cached = await caches.match(request);
    return cached || new Response('', { status: 503 });
  }
}

// Messages: skip waiting + clear caches on logout
self.addEventListener('message', (event) => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CLEAR_API_CACHE') {
    caches.delete('cw-api-fallback').catch(() => {});
  }
  if (event.data?.type === 'LOGOUT') {
    caches.keys().then(keys => keys.filter(k => k.includes('api')).forEach(k => caches.delete(k)));
  }
});
