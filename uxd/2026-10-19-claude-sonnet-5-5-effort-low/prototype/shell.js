/* Shared PF6 page shell: masthead + nav. Call UxdShell.mount(activeHref, renderMain). */
window.UxdShell = {
  mount: function (active, render) {
    var nav = [['Playground', 'index.html'], ['AI asset endpoints', 'ai-assets.html']];
    document.body.innerHTML =
      '<div class="pf-v6-c-page">' +
      '<header class="pf-v6-c-masthead"><div class="pf-v6-c-masthead__main"><span class="pf-v6-c-masthead__brand pf-v6-u-font-weight-bold" style="padding:0 var(--pf-t--global--spacer--md)">Red Hat OpenShift AI &middot; Gen AI Studio</span></div></header>' +
      '<div class="pf-v6-c-page__sidebar pf-m-expanded"><div class="pf-v6-c-page__sidebar-body"><nav class="pf-v6-c-nav" aria-label="Gen AI Studio"><ul class="pf-v6-c-nav__list">' +
      nav.map(function (n) {
        return '<li class="pf-v6-c-nav__item"><a class="pf-v6-c-nav__link' + (n[1] === active ? ' pf-m-current' : '') + '" href="' + n[1] + location.search + '"' + (n[1] === active ? ' aria-current="page"' : '') + '>' + n[0] + '</a></li>';
      }).join('') + '</ul></nav></div></div>' +
      '<main class="pf-v6-c-page__main" id="main"></main></div>';
    render(document.getElementById('main'));
  }
};
