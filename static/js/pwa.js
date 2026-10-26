/* =========================================================
   Tourist Guide PWA - PWA Registration & Install Handler
   ========================================================= */

let deferredInstallPrompt = null;

document.addEventListener('DOMContentLoaded', () => {
  // 1. Register Service Worker
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker
      .register('/static/service-worker.js')
      .then((registration) => {
        console.log('[PWA] ServiceWorker registered with scope:', registration.scope);
      })
      .catch((error) => {
        console.error('[PWA] ServiceWorker registration failed:', error);
      });
  }

  // 2. Track Network Status (Online / Offline indicator)
  function updateNetworkStatus() {
    const badge = document.getElementById('network-status-badge');
    if (!badge) return;

    if (navigator.onLine) {
      badge.textContent = '● Online';
      badge.className = 'status-badge online';
    } else {
      badge.textContent = '⚡ Offline Mode';
      badge.className = 'status-badge offline';
    }
  }

  window.addEventListener('online', updateNetworkStatus);
  window.addEventListener('offline', updateNetworkStatus);
  updateNetworkStatus();

  // 3. Catch PWA Install Prompt ('beforeinstallprompt')
  window.dismissPwaPrompt = function () {
    const banner = document.getElementById('pwa-install-banner');
    if (banner) {
      banner.classList.add('hidden');
    }
    sessionStorage.setItem('pwa_prompt_dismissed', 'true');
  };

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredInstallPrompt = e;
    if (sessionStorage.getItem('pwa_prompt_dismissed') === 'true') {
      return;
    }
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBanner) {
      installBanner.classList.remove('hidden');
    }
  });

  // Handle Install Button Click
  const btnInstall = document.getElementById('btn-pwa-install');
  if (btnInstall) {
    btnInstall.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      const choiceResult = await deferredInstallPrompt.userChoice;
      if (choiceResult.outcome === 'accepted') {
        console.log('[PWA] User accepted the install prompt');
      } else {
        console.log('[PWA] User dismissed the install prompt');
      }
      deferredInstallPrompt = null;
      const installBanner = document.getElementById('pwa-install-banner');
      if (installBanner) installBanner.classList.add('hidden');
    });
  }
});
