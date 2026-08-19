/* Service worker de las apps TK.
   Único propósito: que la app abra sin red una vez visitada.
   No cachea nada del ESP32 — el BLE no pasa por aquí.
   Al cambiar cualquier HTML, sube CACHE para forzar la actualización. */

const CACHE = "tk-termostato-v4";

const ASSETS = [
  "./",
  "./index.html",
  "./termostato-1-rele.html",
  "./termostato-1-rele.webmanifest",
  "./icono-app-oscuro.svg",
  "./icono-app-redondeado.svg"
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE)
      // addAll aborta entero si un archivo falta; así un 404 no rompe la instalación
      .then((c) => Promise.allSettled(ASSETS.map((a) => c.add(a))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Red primero para el HTML: si hay señal ves la versión nueva,
  // si no la cacheada. Evita quedarte con una app vieja pegada.
  if (req.mode === "navigate" || req.destination === "document") {
    e.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then((hit) => hit || caches.match("./termostato-1-rele.html")))
    );
    return;
  }

  // El resto (iconos, manifest): cache primero, es estático.
  e.respondWith(
    caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    }))
  );
});
