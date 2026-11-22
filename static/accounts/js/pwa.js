(function () {
  "use strict";

  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/service-worker.js").catch(function (error) {
        console.warn("PWA service worker registration failed:", error);
      });
    });
  }

  var deferredPrompt = null;
  var installButton = null;

  function createInstallButton() {
    if (installButton) return installButton;

    installButton = document.createElement("button");
    installButton.type = "button";
    installButton.id = "pwa-install-button";
    installButton.textContent = "Install App";
    installButton.setAttribute("aria-label", "Install Milk Billing app");
    installButton.style.cssText =
      "position:fixed;right:20px;bottom:20px;z-index:9999;display:none;" +
      "border:0;border-radius:999px;padding:12px 18px;color:#fff;" +
      "background:linear-gradient(135deg,#1e3c72,#2a5298);font-weight:700;" +
      "box-shadow:0 8px 24px rgba(30,60,114,.35);cursor:pointer";
    document.body.appendChild(installButton);

    installButton.addEventListener("click", async function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      installButton.style.display = "none";
    });
    return installButton;
  }

  window.addEventListener("DOMContentLoaded", createInstallButton);

  window.addEventListener("beforeinstallprompt", function (event) {
    event.preventDefault();
    deferredPrompt = event;
    var button = createInstallButton();
    button.style.display = "block";
  });

  window.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    if (installButton) installButton.style.display = "none";
  });
})();

