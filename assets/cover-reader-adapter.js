(function () {
  "use strict";

  var kindMeta = document.querySelector('meta[name="cover-kind"]');
  if (!kindMeta) return;

  var kind = kindMeta.getAttribute("content");
  var isFront = kind === "front";
  var label = isFront ? "Front cover" : "Back cover";
  var activeControlLabel = isFront ? "Next page" : "Previous page";
  var destination = isFront ? "pg001_sec001.html" : "pg088_sec002.html";
  var videoKeyMeta = document.querySelector('meta[name="cover-video-key"]');

  window.__adtCoverContext = Object.freeze({
    kind: kind,
    numbered: false,
    signVideoKey: videoKeyMeta ? videoKeyMeta.getAttribute("content") : "cover-" + kind
  });

  function replaceCounter(nav) {
    var pageNavButton = nav.querySelector('[aria-label="Next page"], [aria-label="Previous page"]');
    var counter = pageNavButton && pageNavButton.parentElement
      ? pageNavButton.parentElement.querySelector(".order-3")
      : null;
    if (counter) {
      if (counter.textContent !== label) counter.textContent = label;
      counter.setAttribute("aria-label", label + ". This cover is not included in the numbered pages.");
      return;
    }

    var walker = document.createTreeWalker(nav, NodeFilter.SHOW_TEXT);
    var node;
    while ((node = walker.nextNode())) {
      if (/^\s*\d*\s*\/\s*\d+\s*$/.test(node.nodeValue || "")) {
        node.nodeValue = label;
        return;
      }
    }
  }

  function activateCoverNavigation(nav) {
    var button = nav.querySelector('[aria-label="' + activeControlLabel + '"]');
    if (!button || button.getAttribute("data-cover-navigation") === destination) return;

    button.disabled = false;
    button.removeAttribute("disabled");
    button.setAttribute("aria-disabled", "false");
    button.setAttribute("data-cover-navigation", destination);
    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      window.location.href = destination;
    }, true);
  }

  function ensureCoverSignSlot() {
    Array.from(document.querySelectorAll("button")).forEach(function (languageControl) {
      var controlText = languageControl.querySelector("span");
      var isLanguageControl = languageControl.getAttribute("aria-label") === "Language" ||
        (controlText && controlText.textContent.trim() === "Language");
      if (!isLanguageControl || !languageControl.parentElement) return;

      var controls = languageControl.parentElement;
      var alreadyPresent = Array.from(controls.querySelectorAll("button")).some(function (button) {
        var textLabel = button.querySelector("span");
        return button.hasAttribute("data-cover-sign-slot") ||
          button.getAttribute("aria-label") === "Sign language" ||
          (textLabel && textLabel.textContent.trim() === "Sign language");
      });
      if (alreadyPresent) return;

      var signControl = languageControl.cloneNode(true);
      signControl.removeAttribute("id");
      signControl.querySelectorAll("[id]").forEach(function (element) {
        element.removeAttribute("id");
      });
      signControl.setAttribute("aria-label", "Sign language");
      signControl.setAttribute("title", "Sign language");
      signControl.setAttribute("data-cover-sign-slot", window.__adtCoverContext.signVideoKey);
      signControl.setAttribute("aria-pressed", "false");
      signControl.removeAttribute("aria-checked");

      var signText = signControl.querySelector("span");
      if (signText) signText.textContent = "Sign language";

      var icon = signControl.querySelector("svg");
      if (icon) {
        var iconClass = icon.getAttribute("class") || "";
        icon.setAttribute("class", "lucide lucide-hand" + (iconClass.includes("size-6") ? " size-6" : ""));
        icon.innerHTML = '<path d="M18 11V6a2 2 0 0 0-4 0v5"></path>' +
          '<path d="M14 10V4a2 2 0 0 0-4 0v7"></path>' +
          '<path d="M10 10.5V6a2 2 0 0 0-4 0v8"></path>' +
          '<path d="M18 8a2 2 0 1 1 4 0v6a8 8 0 0 1-8 8h-2c-2.8 0-4.5-.86-6-2L2.5 16.5a2.12 2.12 0 0 1 3-3L7 15"></path>';
      }

      signControl.addEventListener("click", function (event) {
        event.preventDefault();
        event.stopImmediatePropagation();
        var status = document.getElementById("cover-sign-language-status");
        if (!status) {
          status = document.createElement("div");
          status.id = "cover-sign-language-status";
          status.className = "sr-only";
          status.setAttribute("role", "status");
          status.setAttribute("aria-live", "polite");
          document.body.appendChild(status);
        }
        status.textContent = "The sign language video for this cover has not been added yet.";
      }, true);

      controls.insertBefore(signControl, languageControl);
    });
  }

  var scheduled = false;
  function patchReaderDock() {
    scheduled = false;
    var nav = document.getElementById("nav-container");
    if (!nav) return;
    replaceCounter(nav);
    activateCoverNavigation(nav);
    ensureCoverSignSlot();
  }

  function schedulePatch() {
    if (scheduled) return;
    scheduled = true;
    window.requestAnimationFrame(patchReaderDock);
  }

  new MutationObserver(schedulePatch).observe(document.documentElement, {
    childList: true,
    subtree: true
  });
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedulePatch, { once: true });
  } else {
    schedulePatch();
  }
})();
