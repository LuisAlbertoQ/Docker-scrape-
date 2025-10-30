// sw.js
self.addEventListener('install', event => {
    console.log('Service Worker instalado');
});

self.addEventListener('activate', event => {
    console.log('Service Worker activado');
});

self.addEventListener('fetch', event => {
    console.log('Service Worker interceptando:', event.request.url);
    event.respondWith(fetch(event.request));
});