(function () {
  initAllProductCarousels();

  var body = document.body;
  var manifestUrl = safeUrl(body.getAttribute('data-research-manifest')) || '/manifest.json';
  var siteTitle = body.getAttribute('data-research-title') || 'Research library';
  var siteSubtitle = body.getAttribute('data-research-subtitle') || 'Published product research.';
  var homeUrl = safeUrl(body.getAttribute('data-research-home')) || '/';
  var locale = body.getAttribute('data-research-locale') || 'en-US';

  fetch(manifestUrl)
    .then(function (response) {
      if (!response.ok) throw new Error('Manifest request failed with ' + response.status);
      return response.json();
    })
    .then(function (items) {
      if (!Array.isArray(items)) throw new Error('Research manifest must be an array');
      buildNavigation(items);
    })
    .catch(function () {
      // The article remains usable without sidebar navigation.
    });

  function buildNavigation(items) {
    var path = normalizePath(window.location.pathname);
    var sidebar = document.createElement('nav');
    sidebar.className = 'sidebar';
    sidebar.setAttribute('aria-label', 'Published research');

    var header = document.createElement('div');
    header.className = 'sidebar__header';

    var title = document.createElement('a');
    title.href = homeUrl;
    title.className = 'sidebar__title';
    title.textContent = siteTitle;

    var subtitle = document.createElement('div');
    subtitle.className = 'sidebar__subtitle';
    subtitle.textContent = siteSubtitle;

    header.appendChild(title);
    header.appendChild(subtitle);
    sidebar.appendChild(header);

    var list = document.createElement('ul');
    list.className = 'sidebar__items';

    items.forEach(function (item) {
      if (!item || typeof item.url !== 'string') return;
      var itemUrl = safeUrl(item.url);
      if (!itemUrl) return;

      var itemPath = normalizePath(new URL(itemUrl, window.location.origin).pathname);
      var entry = document.createElement('li');
      entry.className = 'sidebar__item' + (path === itemPath ? ' sidebar__item--active' : '');

      var link = document.createElement('a');
      link.href = itemUrl;

      var emoji = document.createElement('span');
      emoji.className = 'sidebar__emoji';
      emoji.textContent = typeof item.emoji === 'string' ? item.emoji : '';

      var info = document.createElement('span');
      info.className = 'sidebar__item-info';

      var itemTitle = document.createElement('span');
      itemTitle.className = 'sidebar__item-title';
      itemTitle.textContent = typeof item.title === 'string' ? item.title : item.url;

      var date = document.createElement('span');
      date.className = 'sidebar__item-date';
      date.textContent = formatDate(item.date);

      info.appendChild(itemTitle);
      if (date.textContent) info.appendChild(date);
      link.appendChild(emoji);
      link.appendChild(info);
      entry.appendChild(link);
      list.appendChild(entry);
    });

    sidebar.appendChild(list);

    var overlay = document.createElement('div');
    overlay.className = 'sidebar__overlay';

    var toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'sidebar-toggle';
    toggle.setAttribute('aria-label', 'Toggle navigation');
    toggle.innerHTML = '&#9776;';

    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('sidebar--open');
    });
    overlay.addEventListener('click', function () {
      sidebar.classList.remove('sidebar--open');
    });

    document.body.prepend(overlay);
    document.body.prepend(sidebar);
    document.body.prepend(toggle);
  }

  function initAllProductCarousels() {
    document.querySelectorAll('.allp').forEach(function (carousel) {
      if (carousel.dataset.enhanced === 'true') return;
      carousel.dataset.enhanced = 'true';

      var controls = document.createElement('div');
      controls.className = 'allp__controls';

      var previous = document.createElement('button');
      previous.type = 'button';
      previous.className = 'allp__arrow';
      previous.setAttribute('aria-label', 'Scroll products left');
      previous.innerHTML = '&larr;';

      var next = document.createElement('button');
      next.type = 'button';
      next.className = 'allp__arrow';
      next.setAttribute('aria-label', 'Scroll products right');
      next.innerHTML = '&rarr;';

      controls.appendChild(previous);
      controls.appendChild(next);
      carousel.insertAdjacentElement('afterend', controls);

      function scrollCards(direction) {
        var amount = Math.min(carousel.clientWidth * 0.85, 520);
        carousel.scrollBy({ left: direction * amount, behavior: 'smooth' });
      }

      function updateButtons() {
        var track = carousel.querySelector('.allp__track');
        var trackPadding = track ? parseInt(window.getComputedStyle(track).paddingLeft, 10) : 0;
        var maxScroll = carousel.scrollWidth - carousel.clientWidth;
        var hasOverflow = maxScroll > 4;

        controls.hidden = !hasOverflow;
        previous.disabled = !hasOverflow || carousel.scrollLeft <= trackPadding + 4;
        next.disabled = !hasOverflow || carousel.scrollLeft >= maxScroll - 4;
      }

      previous.addEventListener('click', function () { scrollCards(-1); });
      next.addEventListener('click', function () { scrollCards(1); });
      carousel.addEventListener('scroll', updateButtons, { passive: true });
      window.addEventListener('resize', updateButtons);
      setTimeout(updateButtons, 0);
    });
  }

  function safeUrl(value) {
    if (typeof value !== 'string' || !value) return null;
    if (value.charAt(0) === '/' && value.charAt(1) !== '/') return value;
    try {
      var url = new URL(value);
      if (url.protocol !== 'http:' && url.protocol !== 'https:') return null;
      return isPublicHost(url.hostname) ? value : null;
    } catch (_) {
      return null;
    }
  }

  function isPublicHost(hostname) {
    var host = hostname.toLowerCase().replace(/^\[|\]$/g, '');
    if (host === 'localhost' || host.endsWith('.localhost') || host === '::1') return false;
    if (host.includes(':') && (host.startsWith('fc') || host.startsWith('fd') || host.startsWith('fe8') || host.startsWith('fe9') || host.startsWith('fea') || host.startsWith('feb'))) return false;

    var parts = host.split('.').map(Number);
    if (parts.length !== 4 || parts.some(Number.isNaN)) return true;
    return !(
      parts[0] === 10 ||
      parts[0] === 127 ||
      (parts[0] === 169 && parts[1] === 254) ||
      (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) ||
      (parts[0] === 192 && parts[1] === 168)
    );
  }

  function normalizePath(value) {
    return value.replace(/\/+$/, '') || '/';
  }

  function formatDate(dateString) {
    if (typeof dateString !== 'string' || !dateString) return '';
    var date = new Date(dateString + 'T00:00:00');
    if (Number.isNaN(date.getTime())) return dateString;
    return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' });
  }
})();
