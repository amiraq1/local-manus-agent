// Self-destructing service worker — clears all caches and unregisters itself.
// This replaces a buggy SW that was intercepting /_next/* assets causing 500 errors.
// Once all clients have loaded this version, the SW is permanently removed.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // Clear ALL caches
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));

      // Claim all clients so they get the new (empty) SW immediately
      await self.clients.claim();

      // Unregister this service worker
      await self.registration.unregister();

      // Force reload all clients to get fresh assets
      const clients = await self.clients.matchAll({ type: "window" });
      clients.forEach((client) => {
        client.navigate(client.url);
      });
    })()
  );
});

// Do NOT intercept any fetch events — let everything pass through to the network
