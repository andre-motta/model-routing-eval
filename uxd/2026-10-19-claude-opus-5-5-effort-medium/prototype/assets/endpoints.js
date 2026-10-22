/* AI asset endpoints table with the transcription (ASR) endpoint flag. */
(function () {
  'use strict';

  var MM = window.MM;
  var esc = MM.escapeHtml;

  function clone() { return MM.ASSETS.map(function (a) { return Object.assign({}, a); }); }

  var state = { assets: clone(), alert: null, loadError: false, filter: 'all', editing: null, highlight: null };

  var SCENARIOS = {
    default: function (s) { return s; },
    'no-asr-flagged': function (s) {
      s.assets.forEach(function (a) { a.asr = false; });
      s.highlight = 'whisper-large-v3';
      s.alert = { variant: 'info', title: 'No transcription (ASR) endpoints',
        body: 'Audio input in the Playground needs a transcription model. whisper-large-v3 is deployed in this project but is not marked as a transcription endpoint. Select <b>Edit capabilities</b> on its row to mark it.' };
      return s;
    },
    'asr-flag-saved': function (s) {
      s.assets.forEach(function (a) { if (a.id === 'openai-whisper-1') a.asr = false; });
      s.highlight = 'whisper-large-v3';
      s.alert = { variant: 'success', title: 'whisper-large-v3 is now a transcription (ASR) endpoint',
        body: 'It appears in the Playground\'s Audio transcription model dropdown. <a href="playground.html?scenario=audio-ready">Open Playground</a>' };
      return s;
    },
    'asr-filter': function (s) {
      s.filter = 'asr';
      return s;
    },
    empty: function (s) { s.assets = []; return s; },
    'load-error': function (s) { s.loadError = true; return s; },
  };

  state = (SCENARIOS[MM.getScenario()] || SCENARIOS.default)(state);

  var el = {};

  function label(text, color) {
    return '<span class="pf-v6-c-label pf-m-compact' + (color ? ' pf-m-' + color : '') + '"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + esc(text) + '</span></span></span>';
  }

  function alertHtml(a) {
    var glyph = { danger: '!', warning: '!', success: '✓', info: 'i' }[a.variant];
    return '<div class="pf-v6-c-alert pf-m-inline pf-m-' + a.variant + '" role="alert">' +
      '<div class="pf-v6-c-alert__icon"><span class="mm-alert-glyph mm-alert-glyph--' + a.variant + '" aria-hidden="true">' + glyph + '</span></div>' +
      '<p class="pf-v6-c-alert__title"><span class="pf-v6-screen-reader">' + a.variant + ' alert:</span>' + esc(a.title) + '</p>' +
      (a.body ? '<div class="pf-v6-c-alert__description"><p>' + a.body + '</p></div>' : '') + '</div>';
  }

  function render() {
    el.alerts.innerHTML = state.alert ? alertHtml(state.alert) : '';

    if (state.loadError) {
      el.toolbar.hidden = true;
      el.content.innerHTML =
        '<div class="pf-v6-c-empty-state"><div class="pf-v6-c-empty-state__content"><div class="pf-v6-c-empty-state__header">' +
        '<div class="pf-v6-c-empty-state__icon"><span class="mm-alert-glyph mm-alert-glyph--danger" style="width:2.5rem;height:2.5rem;font-size:1.25rem">!</span></div>' +
        '<div class="pf-v6-c-empty-state__title"><h2 class="pf-v6-c-empty-state__title-text">Unable to load AI asset endpoints</h2></div></div>' +
        '<div class="pf-v6-c-empty-state__body">The request to list AI assets in genai-team failed (502 Bad Gateway). The Playground audio transcription dropdown will also be empty until this resolves.</div>' +
        '<div class="pf-v6-c-empty-state__footer"><div class="pf-v6-c-empty-state__actions"><a class="pf-v6-c-button pf-m-primary" href="ai-asset-endpoints.html"><span class="pf-v6-c-button__text">Retry</span></a></div></div></div></div>';
      return;
    }

    if (!state.assets.length) {
      el.toolbar.hidden = true;
      el.content.innerHTML =
        '<div class="pf-v6-c-empty-state"><div class="pf-v6-c-empty-state__content"><div class="pf-v6-c-empty-state__header">' +
        '<div class="pf-v6-c-empty-state__title"><h2 class="pf-v6-c-empty-state__title-text">No AI asset endpoints</h2></div></div>' +
        '<div class="pf-v6-c-empty-state__body">Deploy a model or add a custom endpoint to use it in the Playground. To enable audio input, deploy a transcription model such as Whisper and mark it as a transcription (ASR) endpoint.</div>' +
        '<div class="pf-v6-c-empty-state__footer"><div class="pf-v6-c-empty-state__actions"><button class="pf-v6-c-button pf-m-primary" type="button"><span class="pf-v6-c-button__text">Add custom endpoint</span></button></div></div></div></div>';
      return;
    }

    el.toolbar.hidden = false;
    el.filter.value = state.filter;
    // Mirror into the attribute so exports / serialized DOM keep the selection.
    Array.prototype.forEach.call(el.filter.options, function (o) { o.toggleAttribute('selected', o.value === state.filter); });
    var rows = state.assets.filter(function (a) { return state.filter === 'all' || a.asr; });
    var body = rows.map(function (a) {
      var caps = [];
      if (a.catalogTags.indexOf('image-inferencing') !== -1) caps.push(label('Image input', 'blue'));
      if (a.catalogTags.indexOf('audio-asr') !== -1) caps.push(label('Audio input', 'purple'));
      if (a.asr) caps.push(label('Transcription (ASR)', 'teal'));
      if (!caps.length) caps.push('<span class="pf-v6-u-color-200">Text</span>');
      return '<tr class="pf-v6-c-table__tr' + (state.highlight === a.id ? ' mm-row-highlight' : '') + '" data-asset="' + a.id + '">' +
        '<td class="pf-v6-c-table__td" data-label="Name"><b>' + esc(a.name) + '</b></td>' +
        '<td class="pf-v6-c-table__td" data-label="Type">' + esc(a.type) + '</td>' +
        '<td class="pf-v6-c-table__td" data-label="Endpoint"><span class="mm-mono">' + esc(a.endpoint) + '</span></td>' +
        '<td class="pf-v6-c-table__td" data-label="Capabilities"><div class="mm-labels">' + caps.join('') + '</div></td>' +
        '<td class="pf-v6-c-table__td pf-v6-c-table__action"><button class="pf-v6-c-button pf-m-link pf-m-inline" type="button" data-edit="' + a.id + '" data-ouia-component-id="edit-capabilities-' + a.id + '"><span class="pf-v6-c-button__text">Edit capabilities</span></button></td></tr>';
    }).join('');
    if (!rows.length) {
      body = '<tr class="pf-v6-c-table__tr"><td class="pf-v6-c-table__td" colspan="5"><div class="pf-v6-c-empty-state pf-m-xs"><div class="pf-v6-c-empty-state__content"><div class="pf-v6-c-empty-state__body">No AI assets are marked as transcription (ASR) endpoints.</div></div></div></td></tr>';
    }
    el.content.innerHTML =
      '<table class="pf-v6-c-table pf-m-grid-md" role="grid" aria-label="AI asset endpoints">' +
      '<thead class="pf-v6-c-table__thead"><tr class="pf-v6-c-table__tr">' +
      '<th class="pf-v6-c-table__th" scope="col">Name</th><th class="pf-v6-c-table__th" scope="col">Type</th><th class="pf-v6-c-table__th" scope="col">Endpoint</th>' +
      '<th class="pf-v6-c-table__th" scope="col">Capabilities</th><td class="pf-v6-c-table__td"></td></tr></thead>' +
      '<tbody class="pf-v6-c-table__tbody">' + body + '</tbody></table>';
    el.content.querySelectorAll('[data-edit]').forEach(function (b) {
      b.addEventListener('click', function () { openModal(b.getAttribute('data-edit')); });
    });
  }

  function find(id) { for (var i = 0; i < state.assets.length; i++) if (state.assets[i].id === id) return state.assets[i]; return null; }

  function openModal(id) {
    var a = find(id);
    if (!a) return;
    state.editing = id;
    el.modalTitle.textContent = 'Edit capabilities: ' + a.name;
    var cat = [];
    if (a.catalogTags.indexOf('image-inferencing') !== -1) cat.push('Image input');
    if (a.catalogTags.indexOf('audio-asr') !== -1) cat.push('Audio input');
    el.catalogCaps.textContent = cat.length ? cat.join(', ') : 'Text only (no modality tags in the model catalog)';
    el.asrCheck.checked = !!a.asr;
    el.backdrop.hidden = false;
    el.asrCheck.focus();
  }
  function closeModal() {
    el.backdrop.hidden = true;
    var btn = state.editing && el.content.querySelector('[data-edit="' + state.editing + '"]');
    state.editing = null;
    if (btn) btn.focus();
  }
  function saveModal() {
    var a = find(state.editing);
    if (a) {
      var was = a.asr;
      a.asr = el.asrCheck.checked;
      state.highlight = a.id;
      if (a.asr && !was) {
        state.alert = { variant: 'success', title: a.name + ' is now a transcription (ASR) endpoint',
          body: 'It appears in the Playground\'s Audio transcription model dropdown. <a href="playground.html?scenario=audio-ready">Open Playground</a>' };
      } else if (!a.asr && was) {
        state.alert = { variant: 'info', title: a.name + ' is no longer a transcription (ASR) endpoint', body: 'It was removed from the Playground\'s Audio transcription model dropdown.' };
      } else {
        state.alert = null;
      }
    }
    closeModal();
    render();
  }

  function init() {
    el.alerts = document.getElementById('page-alerts');
    el.content = document.getElementById('assets-content');
    el.toolbar = document.getElementById('assets-toolbar');
    el.filter = document.getElementById('asset-filter');
    el.backdrop = document.getElementById('capabilities-modal');
    el.modalTitle = document.getElementById('capabilities-modal-title');
    el.catalogCaps = document.getElementById('catalog-capabilities');
    el.asrCheck = document.getElementById('asr-flag');
    el.filter.addEventListener('change', function () { state.filter = el.filter.value; render(); });
    document.getElementById('capabilities-save').addEventListener('click', saveModal);
    document.querySelectorAll('[data-modal-close]').forEach(function (b) { b.addEventListener('click', closeModal); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !el.backdrop.hidden) closeModal(); });
    render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
