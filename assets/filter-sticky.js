(() => {
  const initializeStickyFilters = () => {
    const attachObserver = () => {
      const sentinel = document.querySelector(".filter-sticky-sentinel");
      const filterPanel = document.querySelector(".filter-card");

      if (!sentinel || !filterPanel || !("IntersectionObserver" in window)) {
        return false;
      }

      const observer = new IntersectionObserver(
        ([entry]) => {
          const hasReachedStickyOffset = entry.boundingClientRect.top < 12;
          filterPanel.classList.toggle(
            "is-sticky",
            !entry.isIntersecting && hasReachedStickyOffset,
          );
        },
        {
          rootMargin: "-12px 0px 0px 0px",
          threshold: 0,
        },
      );

      observer.observe(sentinel);
      return true;
    };

    if (attachObserver()) {
      return;
    }

    const mountObserver = new MutationObserver(() => {
      if (attachObserver()) {
        mountObserver.disconnect();
      }
    });
    mountObserver.observe(document.documentElement, {
      childList: true,
      subtree: true,
    });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeStickyFilters, {
      once: true,
    });
  } else {
    initializeStickyFilters();
  }
})();
