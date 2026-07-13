(function () {
  var chips = document.querySelectorAll('.chip[href^="#"]');
  var sections = Array.from(chips)
    .map(function (chip) { return document.querySelector(chip.getAttribute('href')); })
    .filter(Boolean);
  var chipsById = new Map();

  chips.forEach(function (chip) {
    chipsById.set(chip.getAttribute('href').slice(1), chip);
  });

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        chips.forEach(function (chip) { chip.classList.remove('is-active'); });
        var active = chipsById.get(entry.target.id);
        if (active) {
          active.classList.add('is-active');
          active.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });

    sections.forEach(function (section) { observer.observe(section); });
  }

  document.querySelectorAll('.video-embed__thumb[data-video-id]').forEach(function (thumbnail) {
    thumbnail.addEventListener('click', function () {
      var id = thumbnail.getAttribute('data-video-id');
      if (!/^[A-Za-z0-9_-]{6,20}$/.test(id || '')) return;

      var iframe = document.createElement('iframe');
      iframe.setAttribute('src', 'https://www.youtube.com/embed/' + id + '?autoplay=1&rel=0');
      iframe.setAttribute('allow', 'autoplay; encrypted-media');
      iframe.setAttribute('allowfullscreen', '');
      iframe.setAttribute('title', 'YouTube video');
      thumbnail.parentNode.replaceChild(iframe, thumbnail);
    });
  });

  document.querySelectorAll('[data-deep-dive]').forEach(function (link) {
    link.addEventListener('click', function (event) {
      event.preventDefault();
      var targetId = link.getAttribute('data-deep-dive');
      if (!targetId) return;
      var target = document.getElementById(targetId);
      if (target) {
        target.open = true;
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  });

  window.addEventListener('beforeprint', function () {
    document.querySelectorAll('details').forEach(function (details) { details.open = true; });
  });

  window.addEventListener('afterprint', function () {
    document.querySelectorAll('details').forEach(function (details) { details.open = false; });
  });
})();
