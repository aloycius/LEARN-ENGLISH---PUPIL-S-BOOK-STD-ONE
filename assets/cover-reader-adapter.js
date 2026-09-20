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
