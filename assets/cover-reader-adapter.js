(function () {
  "use strict";

  var kindMeta = document.querySelector('meta[name="cover-kind"]');
  var kind = kindMeta ? kindMeta.getAttribute("content") : null;
  var isFrontCover = kind === "front";
  var isBackCover = kind === "back";

  function setButtonState(button, enabled, destination) {
    if (!button) return;

    button.disabled = !enabled;
    if (enabled) {
      button.removeAttribute("disabled");
      button.setAttribute("aria-disabled", "false");
    } else {
      button.setAttribute("disabled", "");
      button.setAttribute("aria-disabled", "true");
    }

    if (!destination || button.getAttribute("data-cover-navigation") === destination) return;

    button.setAttribute("data-cover-navigation", destination);
    button.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopImmediatePropagation();
      window.location.href = destination;
    }, true);
  }

  function patchCoverNavigation(nav) {
    if (!isFrontCover && !isBackCover) return;

    var nextButton = nav.querySelector('[aria-label="Next page"]');
    var previousButton = nav.querySelector('[aria-label="Previous page"]');

    if (isFrontCover) {
      setButtonState(previousButton, false, null);
      setButtonState(nextButton, true, "pg001_sec001.html");
    } else {
      setButtonState(previousButton, true, "pg088_sec002.html");
      setButtonState(nextButton, false, null);
    }
  }

  function readSignLanguageMode() {
    try {
      return JSON.parse(window.localStorage.getItem("signLanguageMode") || "false") === true;
    } catch (_error) {
      return false;
    }
  }

  function writeSignLanguageMode(enabled) {
    try {
      window.localStorage.setItem("signLanguageMode", JSON.stringify(enabled));
    } catch (_error) {
      // The reader will fall back to its default if storage is unavailable.
    }
  }

  function updateCoverSignControls(enabled) {
    document.querySelectorAll("[data-cover-sign-language]").forEach(function (button) {
      button.setAttribute("aria-pressed", enabled ? "true" : "false");
      button.setAttribute("title", enabled ? "Deactivate sign language" : "Activate sign language");
    });
  }

  function announceSignLanguageMode(enabled) {
    var status = document.getElementById("cover-sign-language-status");
    if (!status) {
      status = document.createElement("div");
      status.id = "cover-sign-language-status";
      status.className = "sr-only";
      status.setAttribute("role", "status");
      status.setAttribute("aria-live", "polite");
      document.body.appendChild(status);
    }
    status.textContent = enabled
      ? "Sign language is active. The signed video will open on the next available page."
      : "Sign language is inactive.";
  }

  function ensureCoverSignControl() {
    if (!isFrontCover && !isBackCover) return;

    document.querySelectorAll("button").forEach(function (languageControl) {
      var textLabel = languageControl.querySelector("span");
      var isLanguageControl = languageControl.getAttribute("aria-label") === "Language" ||
        (textLabel && textLabel.textContent.trim() === "Language");
      if (!isLanguageControl || !languageControl.parentElement) return;

      var controls = languageControl.parentElement;
      var alreadyPresent = Array.from(controls.querySelectorAll("button")).some(function (button) {
        return button.hasAttribute("data-cover-sign-language") ||
          button.getAttribute("aria-label") === "Sign language";
      });
      if (alreadyPresent) return;

      var signControl = languageControl.cloneNode(true);
      signControl.removeAttribute("id");
      signControl.removeAttribute("aria-controls");
      signControl.removeAttribute("aria-expanded");
      signControl.removeAttribute("aria-haspopup");
      signControl.querySelectorAll("[id]").forEach(function (element) {
        element.removeAttribute("id");
      });
      signControl.setAttribute("aria-label", "Sign language");
      signControl.setAttribute("data-cover-sign-language", "");

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
        var enabled = !readSignLanguageMode();
        writeSignLanguageMode(enabled);
        updateCoverSignControls(enabled);
        announceSignLanguageMode(enabled);
      }, true);

      controls.insertBefore(signControl, languageControl);
      updateCoverSignControls(readSignLanguageMode());
    });
  }

  function removeLegacyCoverListItems() {
    document.querySelectorAll('button[aria-label="Front cover"], button[aria-label="Back cover"]').forEach(function (button) {
      var item = button.closest("li");
      if (item) item.remove();
    });
  }

  var scheduled = false;
  function patchReaderDock() {
    scheduled = false;
    var nav = document.getElementById("nav-container");
    if (!nav) return;

    patchCoverNavigation(nav);
    ensureCoverSignControl();
    removeLegacyCoverListItems();
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
