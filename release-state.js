// Release time is midnight Eastern, independent of the visitor's timezone.
(function () {
  'use strict';
  var releaseAt = Date.parse('2026-10-07T00:00:00-04:00');
  window.SelenaRelease = {
    releaseAt: releaseAt,
    isLive: function () { return Date.now() >= releaseAt; },
    book: function (book) {
      if (book.id !== 'what-the-night-keeps' || !this.isLive()) return book;
      return Object.assign({}, book, {
        status: 'out-now', status_label: 'Available Now', homepage_group: 'available',
        release_label: 'Available Now',
        links: (book.links || []).map(function (link) {
          return link.primary ? Object.assign({}, link, { label: 'Read on Amazon' }) : link;
        })
      });
    }
  };
  var applied = false;
  function applyRelease() {
    if (applied || !window.SelenaRelease.isLive()) return;
    applied = true;
    document.querySelectorAll('[data-release-text]').forEach(function (el) {
      el.textContent = el.getAttribute('data-release-text');
    });
    document.querySelectorAll('[data-release-href]').forEach(function (el) {
      el.href = el.getAttribute('data-release-href');
    });
    document.querySelectorAll('[data-release-hide]').forEach(function (el) { el.hidden = true; el.style.display = 'none'; });
    var banner = document.getElementById('launchBanner');
    if (banner) banner.innerHTML = '<span>&#10022; <strong>What the Night Keeps</strong> is available now</span><a href="https://www.amazon.com/dp/B0HC9W1MDW" target="_blank" rel="noopener">Read now &rarr;</a>';
    var feature = document.querySelector('[data-release-feature]');
    if (feature) {
      feature.href = 'https://www.amazon.com/dp/B0HC9W1MDW';
      feature.querySelector('img').src = 'What_the_Night_Keeps_home.jpg';
      feature.querySelector('img').alt = 'What the Night Keeps';
      feature.querySelector('.featured-title').textContent = 'What the Night Keeps';
      feature.querySelector('.featured-sub').textContent = 'A journalist, a vampire, and the buried records the Registry hoped no one would find.';
    }
    window.dispatchEvent(new Event('selena-release'));
  }
  function applyOmnibusReleases() {
    var pending = false;
    document.querySelectorAll('[data-omnibus-release-at]').forEach(function (card) {
      if (card.getAttribute('data-omnibus-live') === 'true') return;
      if (Date.now() < Date.parse(card.getAttribute('data-omnibus-release-at'))) {
        pending = true;
        return;
      }
      card.querySelectorAll('[data-omnibus-text]').forEach(function (el) {
        el.textContent = el.getAttribute('data-omnibus-text');
      });
      card.setAttribute('data-omnibus-live', 'true');
    });
    return pending;
  }
  applyRelease();
  var pendingOmnibuses = applyOmnibusReleases();
  if (!applied || pendingOmnibuses) {
    var timer = setInterval(function () {
      applyRelease();
      pendingOmnibuses = applyOmnibusReleases();
      if (applied && !pendingOmnibuses) clearInterval(timer);
    }, 1000);
  }
}());
