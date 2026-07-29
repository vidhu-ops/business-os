// @ts-nocheck
// PWA Setup Utility
// Adds necessary meta tags and registers service worker for PWA functionality

export function setupPWA() {
  // Add meta tags for PWA
  const metaTags = [
    { name: 'application-name', content: 'BI Checklist' },
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'default' },
    { name: 'apple-mobile-web-app-title', content: 'BI Checklist' },
    { name: 'mobile-web-app-capable', content: 'yes' },
    { name: 'theme-color', content: '#9333ea' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes' },
  ];

  metaTags.forEach(({ name, content }) => {
    let meta = document.querySelector(`meta[name="${name}"]`);
    if (!meta) {
      meta = document.createElement('meta');
      meta.setAttribute('name', name);
      document.head.appendChild(meta);
    }
    meta.setAttribute('content', content);
  });

  // Add link for manifest
  let manifestLink = document.querySelector('link[rel="manifest"]');
  if (!manifestLink) {
    manifestLink = document.createElement('link');
    manifestLink.setAttribute('rel', 'manifest');
    document.head.appendChild(manifestLink);
  }
  manifestLink.setAttribute('href', '/manifest.json');

  // Register service worker if supported
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {
        // Service worker registration failed, but app still works
        console.log('Service worker registration not available');
      });
    });
  }
}

// Detect if app is running as PWA
export function isPWA(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches ||
         (window.navigator as any).standalone === true ||
         document.referrer.includes('android-app://');
}

// Prompt user to install PWA
export function promptPWAInstall(): Promise<boolean> {
  return new Promise((resolve) => {
    let deferredPrompt: any;

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
    });

    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then((choiceResult: any) => {
        resolve(choiceResult.outcome === 'accepted');
        deferredPrompt = null;
      });
    } else {
      resolve(false);
    }
  });
}