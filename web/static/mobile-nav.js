/* Devlithium — Bottom navigation injector
   Runs on all pages. Injects the mobile nav bar and marks the active item
   based on the current pathname. Skips the login page (no .main element). */

(function () {
  function inject() {
    // Only inject on authenticated pages that have a .main layout
    if (!document.querySelector('.main')) return;

    var path = window.location.pathname;

    var items = [
      {
        href: '/dashboard', label: 'Home', match: '/dashboard',
        svg: '<path d="M1.5 6.5L8 1.5l6.5 5V14a.5.5 0 01-.5.5H10v-4H6v4H2a.5.5 0 01-.5-.5V6.5z"/>',
      },
      {
        href: '/residents', label: 'Expenses', match: '/residents',
        svg: '<path d="M3 2h10a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1zm1 2v2h2V4H4zm4 0v2h2V4H8zm0 4v2h2V8H8zm-4 0v2h2V8H4z"/>',
      },
      {
        href: '/house', label: 'House', match: '/house',
        svg: '<path d="M8 1L2 5v1h1v7h2V9h2v4h2V9h2v4h2V6h1V5L8 1z"/>',
      },
      {
        href: '/my-room', label: 'My Room', match: '/my-room',
        svg: '<path d="M8 1a3.5 3.5 0 100 7A3.5 3.5 0 008 1zM2.5 13c0-2.485 2.46-4.5 5.5-4.5s5.5 2.015 5.5 4.5H2.5z"/>',
      },
    ];

    var nav = document.createElement('nav');
    nav.className = 'mobile-nav';
    nav.setAttribute('aria-label', 'Main navigation');
    nav.setAttribute('role', 'navigation');

    var inner = document.createElement('div');
    inner.className = 'mobile-nav-inner';

    items.forEach(function (item) {
      var a = document.createElement('a');
      a.href = item.href;
      a.className = 'mnav-item' + (path === item.match ? ' active' : '');
      a.setAttribute('aria-label', item.label);
      if (path === item.match) a.setAttribute('aria-current', 'page');

      a.innerHTML =
        '<svg viewBox="0 0 16 16" fill="currentColor">' + item.svg + '</svg>' +
        '<span>' + item.label + '</span>';

      inner.appendChild(a);
    });

    nav.appendChild(inner);
    document.body.appendChild(nav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
