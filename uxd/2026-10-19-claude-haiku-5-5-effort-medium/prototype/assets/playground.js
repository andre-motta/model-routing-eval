/*
 * Playground page wiring for the RHAISTRAT-1527 prototype.
 * Renders the scenario end-state on load; interactions re-render the same state.
 */
(function (global) {
  'use strict';

  var M = global.UxdMocks;
  var state = M.pickScenario(M.pages.playground, M.scenarioId());

  var modelSelect = document.getElementById('model-select');
  var toggleGroup = document.getElementById('input-type-group');
  var modalityBanner = document.getElementById('modality-banner');
  var limitContainer = document.getElementById('conversation-limit');
  var alertContainer = document.getElementById('composer-alert');
  var audioControls = document.getElementById('audio-controls');
  var attachmentSlot = document.getElementById('attachment-slot');
  var attachmentCard = document.getElementById('attachment');
  var transcript = document.getElementById('transcript');
  var capabilityTags = document.getElementById('capability-tags');
  var sendButton = document.getElementById('send');

  function currentModel() {
    return M.modelById(state.model);
  }

  function renderModelSelect() {
    modelSelect.innerHTML = M.models.map(function (m) {
      return '<option value="' + m.id + '"' + (m.id === state.model ? ' selected' : '') + '>' + m.label + '</option>';
    }).join('');
  }

  function renderToggles() {
    var model = currentModel();
    var modes = ['text'].concat(['image', 'audio'].filter(function (mod) {
      return M.supports(model, mod);
    }));
    toggleGroup.innerHTML = modes.map(function (mod) {
      var on = state.inputType === mod;
      var label = mod.charAt(0).toUpperCase() + mod.slice(1);
      return '<div class="pf-v6-c-toggle-group__item">' +
        '<button type="button" class="pf-v6-c-toggle-group__button' + (on ? ' pf-m-selected' : '') + '"' +
        ' data-testid="input-type-' + mod + '" data-input-type="' + mod + '" aria-pressed="' + on + '">' +
        '<span class="pf-v6-c-toggle-group__text">' + label + '</span></button></div>';
    }).join('');
  }

  function renderBanner() {
    var model = currentModel();
    var textOnly = !M.supports(model, 'image') && !M.supports(model, 'audio');
    modalityBanner.innerHTML = textOnly
      ? M.alertHtml(M.note('info', 'Text-only model',
          'This model accepts text input. Image and audio inputs are unavailable.'))
      : '';
  }

  function renderAudio() {
    if (state.inputType !== 'audio' || !M.supports(currentModel(), 'audio')) {
      audioControls.innerHTML = '';
      return;
    }
    var asrOptions = M.assetsFlagged(state.asrFlagged).filter(function (a) { return a.asrCapable; });
    var options = asrOptions.length
      ? asrOptions.map(function (a) {
          return '<option value="' + a.id + '"' + (a.id === state.asrAssetId ? ' selected' : '') + '>' +
            a.name + ' (' + a.endpointType + ')</option>';
        }).join('')
      : '<option value="" disabled selected>No ASR-capable AI Asset registered</option>';
    audioControls.innerHTML =
      '<div class="pf-v6-c-form__group">' +
      '<label class="pf-v6-c-form__label" for="asr-select"><span class="pf-v6-c-form__label-text">' +
      'Transcription model (ASR AI Asset)</span></label>' +
      '<select id="asr-select" class="pf-v6-c-form-control" data-testid="asr-model-select">' + options + '</select>' +
      '</div>';
  }

  function renderAttachSlot() {
    if (state.inputType === 'text') {
      attachmentSlot.innerHTML = '';
      return;
    }
    var kind = state.inputType;
    var disabled = state.limitNotice ? ' disabled' : '';
    var accept = kind === 'image' ? 'image/jpeg,image/png' : 'audio/wav,audio/mpeg';
    attachmentSlot.innerHTML =
      '<button type="button" class="pf-v6-c-button pf-m-secondary" data-testid="attach"' + disabled + '>' +
      'Attach ' + kind + '</button>' +
      '<input type="file" id="file" hidden accept="' + accept + '" />';
  }

  function renderAttachment() {
    if (!state.attachment) {
      attachmentCard.innerHTML = '';
      return;
    }
    var a = state.attachment;
    attachmentCard.innerHTML =
      '<div class="pf-v6-c-card pf-m-compact"><div class="pf-v6-c-card__body">' +
      '<strong>' + a.name + '</strong> &middot; ' + a.size + ' &middot; ' + a.status +
      '</div></div>';
  }

  function renderTranscript() {
    if (!state.transcript.length) {
      transcript.innerHTML = '<p class="uxd-empty">Start a conversation by choosing an input type and sending a message.</p>';
      return;
    }
    transcript.innerHTML = state.transcript.map(function (m) {
      var thumb = m.image
        ? '<div class="uxd-thumb" role="img" aria-label="Uploaded image: ' + m.image + '">' + m.image + '</div>'
        : '';
      return '<article class="uxd-message uxd-message--' + m.role + '">' + thumb + '<p>' + m.text + '</p></article>';
    }).join('');
  }

  function renderCapabilities() {
    var tags = currentModel().tags;
    var labels = tags.length ? tags : ['text only'];
    capabilityTags.innerHTML = labels.map(function (t) {
      return '<span class="pf-v6-c-label pf-m-compact"><span class="pf-v6-c-label__content">' + t + '</span></span>';
    }).join(' ');
  }

  function render() {
    renderModelSelect();
    renderToggles();
    renderBanner();
    renderAudio();
    renderAttachSlot();
    limitContainer.innerHTML = M.alertHtml(state.limitNotice);
    alertContainer.innerHTML = M.alertHtml(state.alert);
    renderAttachment();
    renderTranscript();
    renderCapabilities();
    sendButton.disabled = !state.sendEnabled;
  }

  modelSelect.addEventListener('change', function () {
    state.model = modelSelect.value;
    if (state.inputType !== 'text' && !M.supports(currentModel(), state.inputType)) {
      state.inputType = 'text';
    }
    state.attachment = null;
    render();
  });

  toggleGroup.addEventListener('click', function (event) {
    var button = event.target.closest('[data-input-type]');
    if (!button) return;
    state.inputType = button.getAttribute('data-input-type');
    state.attachment = null;
    render();
  });

  audioControls.addEventListener('change', function (event) {
    if (event.target.id !== 'asr-select') return;
    state.asrAssetId = event.target.value;
    render();
  });

  attachmentSlot.addEventListener('click', function (event) {
    var attach = event.target.closest('[data-testid="attach"]');
    if (!attach || attach.disabled) return;
    attachmentSlot.querySelector('input[type="file"]').click();
  });

  render();
})(window);
