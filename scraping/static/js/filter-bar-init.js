/* filter-bar-init.js
   Detecta si cada .filter-bar contiene .filter-container y añade clases
   .filter-bar--has-container o .filter-bar--no-container
   Usa MutationObserver para manejar cambios dinámicos en el DOM.
*/
(function () {
  'use strict';

  function updateSingle(bar) {
    if (!bar) return;
    if (bar.querySelector('.filter-container')) {
      bar.classList.add('filter-bar--has-container');
      bar.classList.remove('filter-bar--no-container');
    } else {
      bar.classList.add('filter-bar--no-container');
      bar.classList.remove('filter-bar--has-container');
    }
  }

  function updateAll() {
    document.querySelectorAll('.filter-bar').forEach(updateSingle);
  }

  function initObserver() {
    // Observa cambios en el body y actualiza filter-bars afectadas
    const observer = new MutationObserver(function (mutations) {
      const touched = new Set();
      mutations.forEach(function (m) {
        if (m.type === 'childList') {
          m.addedNodes && m.addedNodes.forEach(function (n) {
            if (n.nodeType === 1) {
              const fb = n.closest ? n.closest('.filter-bar') : null;
              if (fb) touched.add(fb);
            }
          });
          m.removedNodes && m.removedNodes.forEach(function (n) {
            if (n.nodeType === 1) {
              const fb = n.closest ? n.closest('.filter-bar') : null;
              if (fb) touched.add(fb);
            }
          });
          if (m.target && m.target.nodeType === 1) {
            const fb = m.target.closest ? m.target.closest('.filter-bar') : null;
            if (fb) touched.add(fb);
          }
        }
        // También podríamos reaccionar a atributos si fuera necesario
      });

      touched.forEach(function (bar) {
        if (bar) updateSingle(bar);
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      updateAll();
      initObserver();
    });
  } else {
    updateAll();
    initObserver();
  }
})();
