/* Shared helpers for the RHAISTRAT-1527 standalone prototype. */
(function () {
  'use strict';

  var ICONS = {
    caretDown: '<path d="M3 6l5 5 5-5z"/>',
    check: '<circle cx="8" cy="8" r="8"/><path d="M4.4 8.3l2.4 2.4 4.9-5.2" stroke="#fff" stroke-width="1.8" fill="none"/>',
    error: '<circle cx="8" cy="8" r="8"/><rect x="7" y="3.5" width="2" height="6" fill="#fff"/><rect x="7" y="10.8" width="2" height="2" fill="#fff"/>',
    warning: '<path d="M8 .8L15.6 14.8H.4z"/><rect x="7.1" y="5.2" width="1.8" height="5" fill="#fff"/><rect x="7.1" y="11.4" width="1.8" height="1.8" fill="#fff"/>',
    info: '<circle cx="8" cy="8" r="8"/><rect x="7" y="6.8" width="2" height="5.7" fill="#fff"/><rect x="7" y="3.6" width="2" height="2" fill="#fff"/>',
    times: '<path d="M3 3l10 10M13 3L3 13" stroke="currentColor" stroke-width="2" fill="none"/>',
    image: '<path d="M1 2h14v12H1zM2.5 3.5v9h11v-9z"/><circle cx="5.5" cy="6" r="1.4"/><path d="M3.5 11.5l3-3.5 2 2.2 1.7-1.7 2.3 3z"/>',
    audio: '<rect x="1" y="6" width="1.8" height="4" rx=".9"/><rect x="4.2" y="3.5" width="1.8" height="9" rx=".9"/><rect x="7.4" y="1" width="1.8" height="14" rx=".9"/><rect x="10.6" y="4" width="1.8" height="8" rx=".9"/><rect x="13.8" y="6.5" width="1.8" height="3" rx=".9"/>',
    send: '<path d="M.8 1.2L15.5 8 .8 14.8l1.9-5.9L10 8 2.7 7.1z"/>',
    kebab: '<circle cx="8" cy="2.5" r="1.6"/><circle cx="8" cy="8" r="1.6"/><circle cx="8" cy="13.5" r="1.6"/>',
    plus: '<path d="M7 1h2v6h6v2H9v6H7V9H1V7h6z"/>',
    cube: '<path d="M8 .5l7 3.5v8L8 15.5 1 12V4zm0 1.7L3 4.6 8 7l5-2.4zM2.5 5.8v5.3l4.8 2.4V8.2zm11 0L8.7 8.2v5.3l4.8-2.4z"/>',
    upload: '<path d="M7 11V4.4L4.6 6.8 3.2 5.4 8 .6l4.8 4.8-1.4 1.4L9 4.4V11zM1 13h14v2H1z"/>',
    redo: '<path d="M13.6 2.4V6H10l1.5-1.5A4.6 4.6 0 1 0 12.6 9h1.9A6.5 6.5 0 1 1 12.8 3.2z"/>',
    paperclip: '<path d="M10.8 3.4L5 9.2a1.2 1.2 0 0 0 1.7 1.7l5.6-5.6a2.5 2.5 0 0 0-3.5-3.5L3.2 7.4a3.7 3.7 0 0 0 5.3 5.3l4.6-4.6 1.1 1.1-4.6 4.6a5.3 5.3 0 1 1-7.5-7.5L7.7.7a4.1 4.1 0 0 1 5.8 5.8L7.9 12a2.8 2.8 0 0 1-4-4L9.7 2.3z"/>'
  };

  function icon(name, cls) {
    return '<svg class="app-icon' + (cls ? ' ' + cls : '') + '" viewBox="0 0 16 16" aria-hidden="true" focusable="false">' + (ICONS[name] || '') + '</svg>';
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function getScenario() {
    if (window.UxdScenario && typeof window.UxdScenario.get === 'function') {
      return window.UxdScenario.get() || 'default';
    }
    var p = new URLSearchParams(window.location.search);
    return p.get('scenario') || 'default';
  }

  var ALERT_ICON = { success: 'check', danger: 'error', warning: 'warning', info: 'info', custom: 'info' };
  var ALERT_SR = { success: 'Success alert:', danger: 'Danger alert:', warning: 'Warning alert:', info: 'Info alert:', custom: 'Alert:' };

  /** PF6 inline alert. opts: {variant, title, body, ouia, actions:[{label, ouia, action}], closeAction} */
  function alertHtml(opts) {
    var v = opts.variant || 'info';
    var actions = (opts.actions || []).map(function (a) {
      return '<div class="pf-v6-c-alert__action-group-item"><button type="button" class="pf-v6-c-button pf-m-link pf-m-inline" data-action="' + esc(a.action) + '"' +
        (a.ouia ? ' data-ouia-component-id="' + esc(a.ouia) + '"' : '') + '><span class="pf-v6-c-button__text">' + esc(a.label) + '</span></button></div>';
    }).join('');
    var close = opts.closeAction
      ? '<div class="pf-v6-c-alert__action"><button type="button" class="pf-v6-c-button pf-m-plain" aria-label="Close alert" data-action="' + esc(opts.closeAction) + '"><span class="pf-v6-c-button__icon">' + icon('times') + '</span></button></div>'
      : '';
    return '<div class="pf-v6-c-alert pf-m-inline pf-m-' + v + '" role="' + (v === 'danger' || v === 'warning' ? 'alert' : 'status') + '"' +
      (opts.ouia ? ' data-ouia-component-id="' + esc(opts.ouia) + '"' : '') + '>' +
      '<div class="pf-v6-c-alert__icon">' + icon(ALERT_ICON[v]) + '</div>' +
      '<p class="pf-v6-c-alert__title"><span class="pf-v6-screen-reader">' + ALERT_SR[v] + '</span>' + esc(opts.title) + '</p>' +
      close +
      (opts.body ? '<div class="pf-v6-c-alert__description"><p>' + opts.body + '</p></div>' : '') +
      (actions ? '<div class="pf-v6-c-alert__action-group">' + actions + '</div>' : '') +
      '</div>';
  }

  function labelHtml(text, color, extra) {
    return '<span class="pf-v6-c-label pf-m-compact' + (color ? ' pf-m-' + color : '') + '"' + (extra || '') + '>' +
      '<span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + esc(text) + '</span></span></span>';
  }

  function spinnerHtml(label, size) {
    return '<svg class="pf-v6-c-spinner pf-m-' + (size || 'md') + '" role="progressbar" viewBox="0 0 100 100" aria-label="' + esc(label) + '">' +
      '<circle class="pf-v6-c-spinner__path" cx="50" cy="50" r="45" fill="none"></circle></svg>';
  }

  function helperTextHtml(variant, text, ouia) {
    var ic = variant === 'error' ? icon('error') : variant === 'warning' ? icon('warning') : variant === 'success' ? icon('check') : '';
    return '<div class="pf-v6-c-helper-text" aria-live="polite"' + (ouia ? ' data-ouia-component-id="' + esc(ouia) + '"' : '') + '>' +
      '<div class="pf-v6-c-helper-text__item' + (variant && variant !== 'default' ? ' pf-m-' + variant : '') + '">' +
      (ic ? '<span class="pf-v6-c-helper-text__item-icon">' + ic + '</span>' : '') +
      '<span class="pf-v6-c-helper-text__item-text">' + text + '</span></div></div>';
  }

  /* ---------- Dropdown / select menus ---------- */
  var openMenu = null;

  function closeMenus() {
    if (!openMenu) return;
    openMenu.menu.hidden = true;
    openMenu.toggle.setAttribute('aria-expanded', 'false');
    openMenu.toggle.classList.remove('pf-m-expanded');
    openMenu = null;
  }

  function openDropdown(toggle, menu) {
    closeMenus();
    menu.hidden = false;
    toggle.setAttribute('aria-expanded', 'true');
    toggle.classList.add('pf-m-expanded');
    openMenu = { toggle: toggle, menu: menu };
    var first = menu.querySelector('.pf-v6-c-menu__item:not([disabled]):not([aria-disabled="true"]), a[href]');
    if (first) first.focus();
  }

  function toggleDropdown(toggle, menu) {
    if (openMenu && openMenu.menu === menu) { closeMenus(); toggle.focus(); return; }
    openDropdown(toggle, menu);
  }

  document.addEventListener('click', function (e) {
    if (!openMenu) return;
    if (openMenu.menu.contains(e.target) || openMenu.toggle.contains(e.target)) return;
    closeMenus();
  });

  document.addEventListener('keydown', function (e) {
    if (!openMenu) return;
    if (e.key === 'Escape') {
      var t = openMenu.toggle;
      closeMenus();
      t.focus();
      return;
    }
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      var items = Array.prototype.slice.call(openMenu.menu.querySelectorAll('.pf-v6-c-menu__item:not([disabled]), a[href]'));
      if (!items.length) return;
      var i = items.indexOf(document.activeElement);
      i = e.key === 'ArrowDown' ? (i + 1) % items.length : (i - 1 + items.length) % items.length;
      items[i].focus();
      e.preventDefault();
    }
  });

  function menuToggleHtml(opts) {
    return '<button type="button" class="pf-v6-c-menu-toggle' + (opts.fullWidth ? ' pf-m-full-width' : '') + (opts.plain ? ' pf-m-plain' : '') + '"' +
      ' aria-expanded="false" aria-haspopup="listbox"' +
      (opts.id ? ' id="' + esc(opts.id) + '"' : '') +
      (opts.ouia ? ' data-ouia-component-id="' + esc(opts.ouia) + '"' : '') +
      (opts.ariaLabel ? ' aria-label="' + esc(opts.ariaLabel) + '"' : '') +
      (opts.labelledBy ? ' aria-labelledby="' + esc(opts.labelledBy) + '"' : '') + '>' +
      (opts.plain ? '<span class="pf-v6-c-menu-toggle__icon">' + icon('kebab') + '</span>'
        : '<span class="pf-v6-c-menu-toggle__text">' + opts.text + '</span>' +
          '<span class="pf-v6-c-menu-toggle__controls"><span class="pf-v6-c-menu-toggle__toggle-icon">' + icon('caretDown') + '</span></span>') +
      '</button>';
  }

  /** items: [{label, description, value, ouia, selected, disabled, group}] or {divider:true} or {html} */
  function menuHtml(items, opts) {
    opts = opts || {};
    var body = items.map(function (it) {
      if (it.divider) return '<li class="pf-v6-c-divider" role="separator"></li>';
      if (it.groupTitle) return '<li role="presentation"><h3 class="pf-v6-c-menu__group-title" style="padding: var(--pf-t--global--spacer--sm) var(--pf-t--global--spacer--md) 0">' + esc(it.groupTitle) + '</h3></li>';
      if (it.html) return '<li class="pf-v6-c-menu__list-item" role="none" style="padding: var(--pf-t--global--spacer--sm) var(--pf-t--global--spacer--md)">' + it.html + '</li>';
      return '<li class="pf-v6-c-menu__list-item' + (it.selected ? ' pf-m-selected' : '') + (it.disabled ? ' pf-m-aria-disabled' : '') + '" role="none">' +
        '<button type="button" class="pf-v6-c-menu__item" role="' + (opts.role === 'menu' ? 'menuitem' : 'option') + '"' +
        (opts.role === 'menu' ? '' : ' aria-selected="' + (it.selected ? 'true' : 'false') + '"') +
        (it.disabled ? ' aria-disabled="true" disabled' : '') +
        ' data-value="' + esc(it.value) + '"' +
        (it.ouia ? ' data-ouia-component-id="' + esc(it.ouia) + '"' : '') + '>' +
        '<span class="pf-v6-c-menu__item-main">' +
        (it.icon ? '<span class="pf-v6-c-menu__item-icon">' + icon(it.icon) + '</span>' : '') +
        '<span class="pf-v6-c-menu__item-text">' + esc(it.label) + '</span>' +
        (it.selected ? '<span class="pf-v6-c-menu__item-select-icon">' + icon('check') + '</span>' : '') +
        '</span>' +
        (it.description ? '<span class="pf-v6-c-menu__item-description">' + it.description + '</span>' : '') +
        '</button></li>';
    }).join('');
    return '<div class="pf-v6-c-menu' + (opts.cls ? ' ' + opts.cls : '') + '" hidden' +
      (opts.ouia ? ' data-ouia-component-id="' + esc(opts.ouia) + '"' : '') + '>' +
      '<div class="pf-v6-c-menu__content"><ul class="pf-v6-c-menu__list" role="' + (opts.role || 'listbox') + '"' +
      (opts.ariaLabel ? ' aria-label="' + esc(opts.ariaLabel) + '"' : '') + '>' + body + '</ul></div></div>';
  }

  /** Wire a rendered .app-dropdown container: toggle + menu; onSelect(value, item) */
  function wireDropdown(container, onSelect) {
    if (!container) return;
    var toggle = container.querySelector('.pf-v6-c-menu-toggle');
    var menu = container.querySelector('.pf-v6-c-menu');
    if (!toggle || !menu) return;
    toggle.addEventListener('click', function (e) {
      e.stopPropagation();
      toggleDropdown(toggle, menu);
    });
    menu.addEventListener('click', function (e) {
      var item = e.target.closest('.pf-v6-c-menu__item');
      if (!item || item.disabled) return;
      closeMenus();
      onSelect(item.getAttribute('data-value'), item);
    });
  }

  /* ---------- Mock catalog (model-metadata-collection supported_modalities + AI asset endpoints) ---------- */
  var MODELS = [
    {
      id: 'qwen2.5-vl-7b-instruct', name: 'Qwen2.5-VL-7B-Instruct', source: 'InferenceService',
      modalities: ['text', 'image'], tags: ['image-inferencing'],
      endpoint: 'https://qwen25-vl-7b.multimodal-demo.svc.cluster.local/v1'
    },
    {
      id: 'granite-3.3-8b-instruct', name: 'Granite-3.3-8B-Instruct', source: 'MaaS',
      modalities: ['text'], tags: [],
      endpoint: 'https://maas.apps.example.com/granite-3-3-8b-instruct/v1'
    },
    {
      id: 'gemma-3-12b-it', name: 'Gemma-3-12B-IT', source: 'InferenceService',
      modalities: ['text', 'image', 'audio'], tags: ['image-inferencing', 'audio-asr'],
      endpoint: 'https://gemma-3-12b.multimodal-demo.svc.cluster.local/v1'
    },
    {
      id: 'llama-3.3-70b-instruct', name: 'Llama-3.3-70B-Instruct', source: 'MaaS',
      modalities: ['text', 'audio'], tags: ['audio-asr'],
      endpoint: 'https://maas.apps.example.com/llama-3-3-70b-instruct/v1'
    }
  ];

  var ASR_ASSETS = [
    {
      id: 'whisper-large-v3', name: 'whisper-large-v3', source: 'InferenceService',
      endpoint: 'https://whisper-large-v3.multimodal-demo.svc.cluster.local/v1'
    },
    {
      id: 'whisper-1', name: 'whisper-1 (OpenAI)', source: 'Custom endpoint',
      endpoint: 'https://api.openai.com/v1'
    }
  ];

  window.App = {
    icon: icon,
    esc: esc,
    getScenario: getScenario,
    alertHtml: alertHtml,
    labelHtml: labelHtml,
    spinnerHtml: spinnerHtml,
    helperTextHtml: helperTextHtml,
    menuToggleHtml: menuToggleHtml,
    menuHtml: menuHtml,
    wireDropdown: wireDropdown,
    toggleDropdown: toggleDropdown,
    closeMenus: closeMenus,
    MODELS: MODELS,
    ASR_ASSETS: ASR_ASSETS,
    MAX_BYTES: 10 * 1024 * 1024,
    PROJECT: 'multimodal-demo'
  };
})();
