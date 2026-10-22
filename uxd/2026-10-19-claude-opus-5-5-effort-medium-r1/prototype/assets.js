/* AI asset endpoints: mark an endpoint as a Transcription (ASR) endpoint for Playground audio input. */
(function () {
  'use strict';
  var A = window.App;
  var esc = A.esc;

  function baseAssets() {
    var rows = A.MODELS.map(function (m) {
      return { id: m.id, name: m.name, modelId: m.id, source: m.source, endpoint: m.endpoint, modalities: m.modalities.slice(), use: 'chat' };
    });
    rows.push({ id: 'whisper-large-v3', name: 'whisper-large-v3', modelId: 'openai/whisper-large-v3', source: 'InferenceService',
      endpoint: 'https://whisper-large-v3.multimodal-demo.svc.cluster.local/v1', modalities: ['audio'], use: 'asr' });
    rows.push({ id: 'whisper-1', name: 'whisper-1 (OpenAI)', modelId: 'whisper-1', source: 'Custom endpoint',
      endpoint: 'https://api.openai.com/v1', modalities: ['audio'], use: 'asr' });
    return rows;
  }

  var state = { assets: [], filter: 'all', alert: null, highlight: null, status: 'loaded', modalFor: null };

  var USE_LABEL = { chat: 'Chat', asr: 'Transcription (ASR)' };

  function capLabels(mods) {
    return '<span class="assets-label-group">' + mods.map(function (k) {
      var color = k === 'image' ? 'blue' : k === 'audio' ? 'purple' : 'grey';
      return A.labelHtml(k.charAt(0).toUpperCase() + k.slice(1), color);
    }).join('') + '</span>';
  }

  function render() {
    var alerts = document.getElementById('page-alerts');
    var html = '';
    var asrCount = state.assets.filter(function (a) { return a.use === 'asr'; }).length;
    if (state.alert) html += A.alertHtml(state.alert);
    if (state.status === 'loaded' && state.assets.length && !asrCount) {
      html += A.alertHtml({
        variant: 'info', ouia: 'no-asr-info',
        title: 'No transcription endpoint',
        body: 'Audio input in the Playground is transcribed to text by a transcription (ASR) endpoint before it reaches the selected model. Choose <strong>Edit endpoint use</strong> on a transcription model, such as Whisper, and set it to <strong>Transcription (ASR)</strong>.'
      });
    }
    alerts.innerHTML = html;
    alerts.style.display = html ? '' : 'none';

    var c = document.getElementById('assets-content');
    if (state.status === 'error') {
      c.innerHTML = emptyState('error', 'Unable to load AI asset endpoints',
        'The AI asset endpoints could not be retrieved (500 Internal Server Error). Try again, or check the Gen AI studio service status.',
        '<button type="button" class="pf-v6-c-button pf-m-primary" data-action="retry" data-ouia-component-id="retry-load"><span class="pf-v6-c-button__text">Retry</span></button>', 'load-error-state');
      return;
    }
    if (!state.assets.length) {
      c.innerHTML = emptyState('cube', 'No AI asset endpoints',
        'Deploy a model in this project, or add a custom endpoint, to make it available to the Playground. To use audio input, also deploy a transcription model such as Whisper and mark it as a Transcription (ASR) endpoint.',
        '<button type="button" class="pf-v6-c-button pf-m-primary" disabled><span class="pf-v6-c-button__text">Deploy model</span></button> ' +
        '<button type="button" class="pf-v6-c-button pf-m-secondary" disabled><span class="pf-v6-c-button__text">Add custom endpoint</span></button>', 'assets-empty-state');
      return;
    }

    var rows = state.assets.filter(function (a) { return state.filter === 'all' || a.use === state.filter; });
    var toolbar = '<div class="pf-v6-c-toolbar"><div class="pf-v6-c-toolbar__content"><div class="pf-v6-c-toolbar__content-section">' +
      '<div class="pf-v6-c-toolbar__item"><div class="pf-v6-c-toggle-group" role="group" aria-label="Filter by endpoint use" data-ouia-component-id="use-filter">' +
      ['all', 'chat', 'asr'].map(function (f) {
        var label = f === 'all' ? 'All' : USE_LABEL[f];
        return '<div class="pf-v6-c-toggle-group__item"><button type="button" class="pf-v6-c-toggle-group__button' + (state.filter === f ? ' pf-m-selected' : '') + '" aria-pressed="' + (state.filter === f) + '" data-filter="' + f + '"><span class="pf-v6-c-toggle-group__text">' + esc(label) + '</span></button></div>';
      }).join('') +
      '</div></div>' +
      '<div class="pf-v6-c-toolbar__item pf-m-align-end"><span class="pg-hint">' + state.assets.length + ' endpoints · ' + asrCount + ' transcription</span></div>' +
      '</div></div></div>';

    var body = rows.map(function (a) {
      var useLabel = a.use === 'asr' ? A.labelHtml(USE_LABEL.asr, 'purple', ' data-ouia-component-id="use-label-' + a.id + '"') : A.labelHtml(USE_LABEL.chat, 'grey', ' data-ouia-component-id="use-label-' + a.id + '"');
      var menu = A.menuHtml([
        { label: 'Edit endpoint use', value: 'edit-use', ouia: 'edit-endpoint-use-' + a.id },
        { label: 'Open in Playground', value: 'playground', ouia: 'open-in-playground-' + a.id, disabled: a.use === 'asr' },
        { divider: true },
        { label: 'Remove from AI assets', value: 'remove', disabled: true }
      ], { role: 'menu', ouia: 'row-actions-menu-' + a.id, ariaLabel: 'Actions for ' + a.name, cls: 'app-menu-wide' });
      return '<tr class="pf-v6-c-table__tr' + (state.highlight === a.id ? ' assets-row--highlight' : '') + '" data-ouia-component-id="asset-row-' + a.id + '">' +
        '<td class="pf-v6-c-table__td" data-label="Name"><strong>' + esc(a.name) + '</strong><div class="pg-hint">' + esc(a.modelId) + '</div></td>' +
        '<td class="pf-v6-c-table__td" data-label="Source">' + esc(a.source) + '</td>' +
        '<td class="pf-v6-c-table__td" data-label="Endpoint"><span class="assets-endpoint">' + esc(a.endpoint) + '</span></td>' +
        '<td class="pf-v6-c-table__td" data-label="Supported inputs">' + capLabels(a.modalities) + '</td>' +
        '<td class="pf-v6-c-table__td" data-label="Use in Playground">' + useLabel + '</td>' +
        '<td class="pf-v6-c-table__td pf-v6-c-table__action"><div class="app-dropdown app-dropdown--right" data-row="' + esc(a.id) + '">' +
        A.menuToggleHtml({ plain: true, ariaLabel: 'Actions for ' + a.name, ouia: 'row-actions-' + a.id }) + menu + '</div></td></tr>';
    }).join('');

    c.innerHTML = toolbar +
      '<table class="pf-v6-c-table pf-m-grid-md" role="grid" aria-label="AI asset endpoints" data-ouia-component-id="assets-table">' +
      '<thead class="pf-v6-c-table__thead"><tr class="pf-v6-c-table__tr">' +
      '<th class="pf-v6-c-table__th" scope="col">Name</th><th class="pf-v6-c-table__th" scope="col">Source</th><th class="pf-v6-c-table__th" scope="col">Endpoint</th>' +
      '<th class="pf-v6-c-table__th" scope="col">Supported inputs</th><th class="pf-v6-c-table__th" scope="col">Use in Playground</th><td class="pf-v6-c-table__td"></td></tr></thead>' +
      '<tbody class="pf-v6-c-table__tbody">' + body + '</tbody></table>';

    Array.prototype.forEach.call(c.querySelectorAll('.app-dropdown[data-row]'), function (dd) {
      var id = dd.getAttribute('data-row');
      A.wireDropdown(dd, function (value) {
        if (value === 'edit-use') openModal(id);
        else if (value === 'playground') window.location.href = './index.html';
      });
    });
  }

  function emptyState(iconName, title, body, actions, ouia) {
    var danger = iconName === 'error';
    return '<div class="pf-v6-c-empty-state' + (danger ? ' pf-m-danger' : '') + '" data-ouia-component-id="' + ouia + '"><div class="pf-v6-c-empty-state__content">' +
      '<div class="pf-v6-c-empty-state__header"><div class="pf-v6-c-empty-state__icon"' + (danger ? ' style="color: var(--pf-t--global--icon--color--status--danger--default)"' : '') + '>' + A.icon(iconName, 'app-icon--lg') + '</div>' +
      '<div class="pf-v6-c-empty-state__title"><h2 class="pf-v6-c-empty-state__title-text">' + esc(title) + '</h2></div></div>' +
      '<div class="pf-v6-c-empty-state__body">' + esc(body) + '</div>' +
      '<div class="pf-v6-c-empty-state__footer"><div class="pf-v6-c-empty-state__actions">' + actions + '</div></div></div></div>';
  }

  var lastFocus = null;
  function openModal(id) {
    var a = state.assets.filter(function (x) { return x.id === id; })[0];
    if (!a) return;
    lastFocus = document.activeElement;
    state.modalFor = id;
    var root = document.getElementById('modal-root');
    function radio(value, label, desc) {
      return '<div class="pf-v6-c-radio"><input class="pf-v6-c-radio__input" type="radio" id="use-' + value + '" name="endpoint-use" value="' + value + '"' + (a.use === value ? ' checked' : '') + ' data-ouia-component-id="use-option-' + value + '"/>' +
        '<label class="pf-v6-c-radio__label" for="use-' + value + '">' + esc(label) + '</label><span class="pf-v6-c-radio__description">' + desc + '</span></div>';
    }
    root.innerHTML = '<div class="pf-v6-c-backdrop"><div class="pf-v6-l-bullseye">' +
      '<div class="pf-v6-c-modal-box pf-m-sm" role="dialog" aria-modal="true" aria-labelledby="edit-use-title" aria-describedby="edit-use-desc" data-ouia-component-id="edit-use-modal">' +
      '<div class="pf-v6-c-modal-box__close"><button type="button" class="pf-v6-c-button pf-m-plain" aria-label="Close" data-modal="cancel"><span class="pf-v6-c-button__icon">' + A.icon('times') + '</span></button></div>' +
      '<header class="pf-v6-c-modal-box__header"><h1 class="pf-v6-c-modal-box__title" id="edit-use-title">Edit endpoint use</h1>' +
      '<div class="pf-v6-c-modal-box__description" id="edit-use-desc">Choose how the Playground uses <strong>' + esc(a.name) + '</strong>.</div></header>' +
      '<div class="pf-v6-c-modal-box__body"><fieldset class="pf-v6-c-form__fieldset" style="border:0;padding:0;margin:0"><legend class="app-sr-only">Endpoint use</legend>' +
      radio('chat', 'Chat', 'Listed in the Playground model selector for text, image, or audio prompts.') +
      '<div class="pf-v6-u-mt-md"></div>' +
      radio('asr', 'Transcription (ASR)', 'Listed in the Playground transcription model dropdown. Audio files are sent to <code>/v1/audio/transcriptions</code> on this endpoint, and the text is forwarded to the selected chat model.') +
      '</fieldset>' +
      '<div class="pf-v6-u-mt-md">' + A.helperTextHtml('default', 'The endpoint must be OpenAI-compatible. Requests use the same credentials as other AI asset calls in this project.') + '</div>' +
      '</div>' +
      '<footer class="pf-v6-c-modal-box__footer">' +
      '<button type="button" class="pf-v6-c-button pf-m-primary" data-modal="save" data-ouia-component-id="save-endpoint-use"><span class="pf-v6-c-button__text">Save</span></button>' +
      '<button type="button" class="pf-v6-c-button pf-m-link" data-modal="cancel"><span class="pf-v6-c-button__text">Cancel</span></button>' +
      '</footer></div></div></div>';
    var checked = root.querySelector('input:checked') || root.querySelector('input');
    checked.focus();
  }

  function closeModal() {
    document.getElementById('modal-root').innerHTML = '';
    state.modalFor = null;
    if (lastFocus && document.body.contains(lastFocus)) lastFocus.focus();
  }

  function saveModal() {
    var root = document.getElementById('modal-root');
    var input = root.querySelector('input[name="endpoint-use"]:checked');
    var a = state.assets.filter(function (x) { return x.id === state.modalFor; })[0];
    if (!a || !input) { closeModal(); return; }
    var prev = a.use;
    a.use = input.value;
    closeModal();
    if (prev === a.use) return;
    state.highlight = a.id;
    state.alert = a.use === 'asr'
      ? { variant: 'success', ouia: 'asr-marked-alert', closeAction: 'dismiss',
          title: a.name + ' is now available as a transcription model in the Playground',
          body: 'Select an audio-capable model in the Playground, then choose ' + esc(a.name) + ' in the Transcription model dropdown.',
          actions: [{ label: 'Open Playground', action: 'open-playground', ouia: 'open-playground' }] }
      : { variant: 'success', ouia: 'chat-marked-alert', closeAction: 'dismiss',
          title: a.name + ' is now a chat endpoint',
          body: 'It no longer appears in the Playground transcription model dropdown.' };
    render();
  }

  document.addEventListener('click', function (e) {
    var f = e.target.closest('[data-filter]');
    if (f) { state.filter = f.getAttribute('data-filter'); render(); return; }
    var m = e.target.closest('[data-modal]');
    if (m) { if (m.getAttribute('data-modal') === 'save') saveModal(); else closeModal(); return; }
    var act = e.target.closest('[data-action]');
    if (!act) return;
    var action = act.getAttribute('data-action');
    if (action === 'dismiss') { state.alert = null; state.highlight = null; render(); }
    else if (action === 'open-playground') window.location.href = './index.html';
    else if (action === 'retry') { state.status = 'loaded'; state.assets = baseAssets(); render(); }
  });

  document.addEventListener('keydown', function (e) {
    if (state.modalFor && e.key === 'Escape') closeModal();
  });

  var SEEDS = {
    'default': function () {},
    'no-asr': function (s) {
      s.assets = s.assets.filter(function (a) { return a.id !== 'whisper-1'; });
      s.assets.forEach(function (a) { a.use = 'chat'; });
    },
    'asr-marked': function (s) {
      s.assets = s.assets.filter(function (a) { return a.id !== 'whisper-1'; });
      s.highlight = 'whisper-large-v3';
      s.alert = { variant: 'success', ouia: 'asr-marked-alert', closeAction: 'dismiss',
        title: 'whisper-large-v3 is now available as a transcription model in the Playground',
        body: 'Select an audio-capable model in the Playground, then choose whisper-large-v3 in the Transcription model dropdown.',
        actions: [{ label: 'Open Playground', action: 'open-playground', ouia: 'open-playground' }] };
    },
    'empty': function (s) { s.assets = []; },
    'load-error': function (s) { s.assets = []; s.status = 'error'; }
  };

  function init() {
    state.assets = baseAssets();
    var id = A.getScenario();
    (SEEDS[id] || SEEDS['default'])(state);
    render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
