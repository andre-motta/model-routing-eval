/* Playground: per-modality input controls, ASR transcription model, one file per conversation. */
(function () {
  'use strict';
  var A = window.App;
  var esc = A.esc;

  var IMAGE_TYPES = ['image/jpeg', 'image/png'];
  var AUDIO_TYPES = ['audio/wav', 'audio/x-wav', 'audio/wave', 'audio/vnd.wave', 'audio/mpeg', 'audio/mp3'];
  var STEP_DELAY = 1600;

  var SAMPLE_IMAGE_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 200">' +
    '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4a261"/><stop offset="1" stop-color="#2a3d66"/></linearGradient></defs>' +
    '<rect width="320" height="200" fill="url(#sky)"/>' +
    '<rect x="10" y="40" width="70" height="110" fill="#3a3a52"/><rect x="230" y="25" width="80" height="125" fill="#30304a"/>' +
    '<g fill="#ffd166"><rect x="20" y="55" width="10" height="10"/><rect x="45" y="55" width="10" height="10"/><rect x="20" y="85" width="10" height="10"/><rect x="245" y="45" width="10" height="10"/><rect x="275" y="70" width="10" height="10"/><rect x="245" y="100" width="10" height="10"/></g>' +
    '<rect y="150" width="320" height="50" fill="#444"/><rect x="0" y="172" width="320" height="4" fill="#ddd" stroke-dasharray="20 14"/>' +
    '<rect x="60" y="150" width="90" height="26" rx="8" fill="#d62828"/><rect x="78" y="138" width="50" height="18" rx="5" fill="#b51f1f"/><circle cx="80" cy="178" r="9" fill="#111"/><circle cx="132" cy="178" r="9" fill="#111"/>' +
    '<rect x="185" y="152" width="56" height="16" rx="5" fill="#277da1"/><circle cx="197" cy="169" r="6" fill="#111"/><circle cx="230" cy="169" r="6" fill="#111"/>' +
    '<rect x="205" y="70" width="6" height="80" fill="#222"/><rect x="198" y="52" width="20" height="44" rx="4" fill="#222"/>' +
    '<circle cx="208" cy="61" r="5" fill="#552"/><circle cx="208" cy="74" r="5" fill="#553"/><circle cx="208" cy="87" r="5" fill="#2dc653"/>' +
    '</svg>';
  var SAMPLE_IMAGE_URL = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(SAMPLE_IMAGE_SVG);
  var SAMPLE_IMAGE_ALT = 'City street at dusk with a red car, a blue car, a green traffic light, and two lit buildings';

  var SAMPLES = {
    image: [
      { id: 'sample-image', name: 'street-scene.png', type: 'image/png', size: 2.1 * 1024 * 1024, desc: 'PNG, 2.1 MB' },
      { id: 'sample-image-large', name: 'aerial-survey.png', type: 'image/png', size: 14.2 * 1024 * 1024, desc: 'PNG, 14.2 MB (exceeds limit)' },
      { id: 'sample-image-pdf', name: 'invoice-scan.pdf', type: 'application/pdf', size: 0.8 * 1024 * 1024, desc: 'PDF, not an allowed image type' }
    ],
    audio: [
      { id: 'sample-audio', name: 'planning-meeting.wav', type: 'audio/wav', size: 1.4 * 1024 * 1024, desc: 'WAV, 1.4 MB' },
      { id: 'sample-audio-silent', name: 'silence.mp3', type: 'audio/mpeg', size: 0.3 * 1024 * 1024, desc: 'MP3, 0.3 MB (no speech)', silent: true },
      { id: 'sample-audio-empty', name: 'recording.wav', type: 'audio/wav', size: 0, desc: 'WAV, 0 bytes' }
    ]
  };

  var TRANSCRIPTION = 'Can you summarize the three action items from today\'s planning meeting? First, finish the storage spike by Friday. Second, confirm the 10 megabyte upload limit with product. Third, schedule the accessibility review.';
  var IMAGE_ANSWER = 'The image shows a city street at dusk. In the foreground there is a red car in the near lane, with a smaller blue car further back. On the right, a traffic light is showing green. Two buildings frame the street, both with several lit windows, and the sky fades from orange to dark blue, suggesting early evening.';
  var AUDIO_ANSWER = 'Here are the three action items from the meeting:\n1. Finish the storage spike by Friday.\n2. Confirm the 10 MB upload limit with product management.\n3. Schedule the accessibility review.';
  var TEXT_ANSWER = 'Sure. Ask me anything, or attach a supported file if you want me to look at an image or listen to audio.';

  var audioUrlCache = null;
  function sampleAudioUrl() {
    if (audioUrlCache) return audioUrlCache;
    var rate = 8000, secs = 2, n = rate * secs;
    var buf = new ArrayBuffer(44 + n * 2);
    var v = new DataView(buf);
    function str(o, s) { for (var i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); }
    str(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
    str(36, 'data'); v.setUint32(40, n * 2, true);
    for (var i = 0; i < n; i++) {
      var env = Math.sin(Math.PI * i / n);
      v.setInt16(44 + i * 2, Math.sin(2 * Math.PI * 330 * i / rate) * 3000 * env, true);
    }
    audioUrlCache = URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }));
    return audioUrlCache;
  }

  function fmtSize(bytes) {
    if (bytes === 0) return '0 bytes';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function fileId() { return 'file-' + Math.random().toString(36).slice(2, 10); }

  /* ---------- State ---------- */
  var state;
  var timers = [];

  function freshState() {
    return {
      modelId: 'qwen2.5-vl-7b-instruct',
      asrAssets: A.ASR_ASSETS.slice(),
      asrId: null,
      messages: [],
      attachment: null,      // {kind, name, size, type, status: 'uploading'|'ready', url, fileId, silent}
      fileUsed: false,       // a file was already sent in this conversation
      composerAlert: null,   // alert opts
      validationError: null, // string (html-safe)
      busy: false
    };
  }

  function clearTimers() { timers.forEach(clearTimeout); timers = []; }
  function later(fn, ms) { timers.push(setTimeout(fn, ms)); }

  function model() {
    return A.MODELS.filter(function (m) { return m.id === state.modelId; })[0] || A.MODELS[0];
  }
  function supports(kind) { return model().modalities.indexOf(kind) !== -1; }
  function asr() {
    return state.asrAssets.filter(function (a) { return a.id === state.asrId; })[0] || null;
  }

  /* ---------- Rendering ---------- */
  function renderModelSelect() {
    var el = document.getElementById('model-dropdown');
    var m = model();
    var items = A.MODELS.map(function (x) {
      var caps = x.modalities.map(function (k) { return k.charAt(0).toUpperCase() + k.slice(1); }).join(', ');
      return { label: x.name, value: x.id, selected: x.id === m.id, ouia: 'model-option-' + x.id, description: esc(x.source + ' · ' + caps) };
    });
    el.innerHTML = A.menuToggleHtml({ text: esc(m.name), fullWidth: true, ouia: 'model-select', labelledBy: 'model-select-label model-select-toggle', id: 'model-select-toggle' }) +
      A.menuHtml(items, { ouia: 'model-select-menu', ariaLabel: 'Models' });
    A.wireDropdown(el, selectModel);
  }

  function renderCapabilities() {
    var m = model();
    var html = '<span role="listitem">' + A.labelHtml('Text', 'grey') + '</span>';
    if (supports('image')) html += '<span role="listitem">' + A.labelHtml('Image', 'blue', ' data-ouia-component-id="cap-image"') + '</span>';
    if (supports('audio')) html += '<span role="listitem">' + A.labelHtml('Audio (via transcription)', 'purple', ' data-ouia-component-id="cap-audio"') + '</span>';
    document.getElementById('capability-labels').innerHTML = html;
    var hint = [];
    if (supports('image')) hint.push('Images: JPG or PNG up to 10 MB');
    if (supports('audio')) hint.push('Audio: WAV or MP3 up to 10 MB');
    if (hint.length) hint.push('One image or audio file per conversation');
    else hint.push(esc(m.name) + ' accepts text only');
    document.getElementById('limits-hint').innerHTML = hint.join(' · ');
  }

  function attachMenuItems(kind) {
    var items = [{ label: 'Upload from computer', value: 'upload', icon: 'upload', ouia: 'upload-' + kind,
      description: kind === 'image' ? 'JPG or PNG, up to 10 MB' : 'WAV or MP3, up to 10 MB' }];
    items.push({ divider: true });
    items.push({ groupTitle: 'Prototype sample files' });
    SAMPLES[kind].forEach(function (s) {
      items.push({ label: s.name, value: s.id, ouia: s.id, description: esc(s.desc) });
    });
    return items;
  }

  function renderModalityControls() {
    var el = document.getElementById('modality-controls');
    var html = '';
    var used = state.fileUsed || !!state.attachment;
    if (supports('image')) {
      html += '<div class="app-dropdown app-dropdown--up" id="image-dropdown">' +
        '<button type="button" class="pf-v6-c-menu-toggle" aria-expanded="false" aria-haspopup="menu" data-ouia-component-id="attach-image" id="attach-image" aria-label="Attach image">' +
        '<span class="pf-v6-c-menu-toggle__icon">' + A.icon('image') + '</span><span class="pf-v6-c-menu-toggle__text">Image</span>' +
        '<span class="pf-v6-c-menu-toggle__controls"><span class="pf-v6-c-menu-toggle__toggle-icon">' + A.icon('caretDown') + '</span></span></button>' +
        A.menuHtml(attachMenuItems('image'), { ouia: 'attach-image-menu', role: 'menu', ariaLabel: 'Attach image', cls: 'app-menu-wide' }) +
        '</div>';
    }
    if (supports('audio')) {
      html += '<div class="app-dropdown app-dropdown--up" id="audio-dropdown">' +
        '<button type="button" class="pf-v6-c-menu-toggle" aria-expanded="false" aria-haspopup="menu" data-ouia-component-id="attach-audio" id="attach-audio" aria-label="Attach audio file">' +
        '<span class="pf-v6-c-menu-toggle__icon">' + A.icon('audio') + '</span><span class="pf-v6-c-menu-toggle__text">Audio</span>' +
        '<span class="pf-v6-c-menu-toggle__controls"><span class="pf-v6-c-menu-toggle__toggle-icon">' + A.icon('caretDown') + '</span></span></button>' +
        A.menuHtml(attachMenuItems('audio'), { ouia: 'attach-audio-menu', role: 'menu', ariaLabel: 'Attach audio', cls: 'app-menu-wide' }) +
        '</div>';
      html += '<span class="pg-divider-v" aria-hidden="true"></span>' + asrSelectHtml();
    }
    if (supports('image') || supports('audio')) {
      html += '<span class="pg-hint" data-ouia-component-id="file-usage">' + (used ? '1 of 1 file used in this conversation' : '0 of 1 file used') + '</span>';
    }
    el.innerHTML = html;
    el.hidden = !html;

    ['image', 'audio'].forEach(function (kind) {
      var dd = document.getElementById(kind + '-dropdown');
      if (!dd) return;
      var toggle = dd.querySelector('.pf-v6-c-menu-toggle');
      var menu = dd.querySelector('.pf-v6-c-menu');
      toggle.addEventListener('click', function (e) {
        e.stopPropagation();
        if (state.fileUsed || state.attachment) {
          A.closeMenus();
          showFileLimit();
          return;
        }
        A.toggleDropdown(toggle, menu);
      });
      menu.addEventListener('click', function (e) {
        var item = e.target.closest('.pf-v6-c-menu__item');
        if (!item) return;
        A.closeMenus();
        var value = item.getAttribute('data-value');
        if (value === 'upload') {
          document.getElementById('file-input-' + kind).click();
        } else {
          var s = SAMPLES[kind].filter(function (x) { return x.id === value; })[0];
          if (s) acceptFile(kind, { name: s.name, type: s.type, size: s.size, silent: !!s.silent, sample: true });
        }
      });
    });

    var asrEl = document.getElementById('asr-dropdown');
    if (asrEl) {
      A.wireDropdown(asrEl, function (value) {
        if (value === 'register') { window.location.href = './ai-asset-endpoints.html'; return; }
        state.asrId = value;
        render();
      });
    }
  }

  function asrSelectHtml() {
    var assets = state.asrAssets;
    var cur = asr();
    var items;
    if (!assets.length) {
      items = [{ html: '<div class="pf-v6-u-font-size-sm" data-ouia-component-id="asr-empty"><strong>No transcription models available</strong><br/>Mark an AI asset endpoint as a transcription (ASR) endpoint to use audio.</div>' },
        { divider: true },
        { label: 'Go to AI asset endpoints', value: 'register', ouia: 'asr-register-link' }];
    } else {
      items = assets.map(function (a) {
        return { label: a.name, value: a.id, selected: cur && cur.id === a.id, ouia: 'asr-option-' + a.id, description: esc(a.source) };
      });
    }
    var text = cur ? esc(cur.name) : assets.length ? 'Select a transcription model' : 'No transcription models';
    return '<span class="pg-asr"><span class="pg-asr__label" id="asr-label">Transcription model</span>' +
      '<span class="app-dropdown app-dropdown--up" id="asr-dropdown">' +
      A.menuToggleHtml({ text: text, ouia: 'asr-select', labelledBy: 'asr-label asr-select-toggle', id: 'asr-select-toggle' }) +
      A.menuHtml(items, { ouia: 'asr-select-menu', ariaLabel: 'Transcription models', cls: 'app-menu-wide' }) +
      '</span></span>';
  }

  function renderAttachment() {
    var el = document.getElementById('attachment-area');
    var a = state.attachment;
    if (!a) { el.innerHTML = ''; return; }
    var thumb = a.kind === 'image'
      ? '<img class="pg-attachment__thumb" src="' + esc(a.url) + '" alt="' + esc(a.alt || ('Preview of ' + a.name)) + '"/>'
      : '<span class="pg-attachment__thumb">' + A.icon('audio', 'app-icon--lg') + '</span>';
    var status = a.status === 'uploading'
      ? '<span class="pf-v6-l-flex pf-m-gap-sm pf-m-align-items-center">' + A.spinnerHtml('Uploading', 'sm') + '<span class="pg-hint">Uploading...</span></span>'
      : '<span class="pg-hint" data-ouia-component-id="attachment-ready">' + A.icon('check') + ' Uploaded · ' + esc(fmtSize(a.size)) + '</span>';
    el.innerHTML = '<div class="pg-attachment" data-ouia-component-id="attachment-chip">' + thumb +
      '<div class="pg-attachment__info"><div class="pg-attachment__name">' + esc(a.name) + '</div>' + status + '</div>' +
      '<button type="button" class="pf-v6-c-button pf-m-plain" aria-label="Remove ' + esc(a.name) + '" data-ouia-component-id="remove-attachment" id="remove-attachment">' +
      '<span class="pf-v6-c-button__icon">' + A.icon('times') + '</span></button></div>';
    document.getElementById('remove-attachment').addEventListener('click', function () {
      state.attachment = null;
      state.composerAlert = null;
      render();
    });
  }

  function audioBlockedReason() {
    var a = state.attachment;
    if (!a || a.kind !== 'audio') return null;
    if (!state.asrAssets.length) return 'no-asr';
    if (!asr()) return 'no-selection';
    return null;
  }

  function renderComposerAlerts() {
    var el = document.getElementById('composer-alerts');
    var html = '';
    if (state.composerAlert) html += A.alertHtml(state.composerAlert);
    if (audioBlockedReason() === 'no-asr') {
      html += A.alertHtml({
        variant: 'warning', ouia: 'no-asr-alert',
        title: 'Audio cannot be submitted: no transcription model available',
        body: 'Audio is transcribed to text before it is sent to ' + esc(model().name) + '. Deploy a transcription model (for example, Whisper) and mark it as a <strong>Transcription (ASR)</strong> endpoint in AI asset endpoints.',
        actions: [{ label: 'Go to AI asset endpoints', action: 'go-assets', ouia: 'go-ai-asset-endpoints' }]
      });
    }
    el.innerHTML = html;
    el.style.display = html ? '' : 'none';
  }

  function renderHelper() {
    var el = document.getElementById('composer-helper');
    if (state.validationError) {
      el.innerHTML = A.helperTextHtml('error', state.validationError, 'file-validation-error');
    } else if (audioBlockedReason() === 'no-selection') {
      el.innerHTML = A.helperTextHtml('warning', 'Select a transcription model to send this audio file.', 'asr-required');
    } else if (supports('audio') && !state.asrAssets.length && !state.attachment) {
      el.innerHTML = A.helperTextHtml('default', 'No transcription models available. Audio files can be attached, but cannot be sent until a transcription (ASR) endpoint is registered.', 'asr-missing-hint');
    } else {
      el.innerHTML = '';
    }
  }

  function renderSend() {
    var btn = document.getElementById('send-message');
    var text = document.getElementById('prompt-input').value.trim();
    var a = state.attachment;
    var disabled = state.busy || (a && a.status !== 'ready') || !!audioBlockedReason() || (!text && !a);
    btn.disabled = !!disabled;
    btn.classList.toggle('pf-m-disabled', !!disabled);
  }

  function stepperHtml(steps) {
    var ICON = { success: A.icon('check'), current: A.spinnerHtml('In progress', 'sm'), pending: '', danger: A.icon('error'), warning: A.icon('warning') };
    return '<ol class="pf-v6-c-progress-stepper pf-m-compact pf-m-horizontal" aria-label="Request progress" data-ouia-component-id="request-progress">' +
      steps.map(function (s) {
        var cls = s.status === 'success' ? 'pf-m-success' : s.status === 'current' ? 'pf-m-current pf-m-info' : s.status === 'danger' ? 'pf-m-danger' : s.status === 'warning' ? 'pf-m-warning' : 'pf-m-pending';
        return '<li class="pf-v6-c-progress-stepper__step ' + cls + '"' + (s.status === 'current' ? ' aria-current="step"' : '') + '>' +
          '<div class="pf-v6-c-progress-stepper__step-connector"><span class="pf-v6-c-progress-stepper__step-icon">' + (ICON[s.status] || '') + '</span></div>' +
          '<div class="pf-v6-c-progress-stepper__step-main"><div class="pf-v6-c-progress-stepper__step-title">' + esc(s.title) + '</div></div></li>';
      }).join('') + '</ol>';
  }

  function messageHtml(msg) {
    if (msg.role === 'user') {
      var parts = '';
      if (msg.image) parts += '<img class="pg-msg__image" src="' + esc(msg.image.url) + '" alt="' + esc(msg.image.alt) + '"/><span class="pg-msg__meta">' + esc(msg.image.name) + '</span>';
      if (msg.audio) {
        parts += '<audio controls src="' + esc(msg.audio.url) + '" aria-label="Uploaded audio: ' + esc(msg.audio.name) + '"></audio>' +
          '<span class="pg-msg__meta">' + esc(msg.audio.name) + (msg.audio.asrName ? ' · Transcribed with ' + esc(msg.audio.asrName) : '') + '</span>';
        if (msg.audio.transcription) {
          parts += '<div class="pg-transcription" data-ouia-component-id="transcription-text"><span class="pg-msg__meta">Transcription</span><br/>' + esc(msg.audio.transcription) + '</div>';
        }
      }
      if (msg.text) parts += '<div>' + esc(msg.text) + '</div>';
      return '<div class="pg-msg pg-msg--user" data-ouia-component-id="user-message"><span class="pg-msg__avatar" aria-hidden="true">You</span><div class="pg-msg__body">' + parts + '</div></div>';
    }
    var inner;
    if (msg.status === 'processing') {
      inner = (msg.steps ? stepperHtml(msg.steps) : '') +
        '<div class="pg-processing" data-ouia-component-id="processing-indicator">' + A.spinnerHtml(msg.label || 'Generating response', 'md') +
        '<span>' + esc(msg.label || 'Generating response...') + '</span></div>' +
        '<span class="pg-msg__meta">Responses can take up to 2 minutes for image and audio inputs.</span>';
    } else if (msg.status === 'error') {
      inner = (msg.steps ? stepperHtml(msg.steps) : '') + A.alertHtml(msg.alert);
    } else {
      inner = '<div data-ouia-component-id="assistant-response" style="white-space: pre-line">' + esc(msg.text) + '</div>';
    }
    return '<div class="pg-msg pg-msg--assistant"><span class="pg-msg__avatar" aria-hidden="true">AI</span><div class="pg-msg__body">' +
      '<span class="pg-msg__meta">' + esc(msg.modelName || model().name) + '</span>' + inner + '</div></div>';
  }

  function renderTranscript() {
    var el = document.getElementById('transcript');
    if (!state.messages.length) {
      var caps = supports('image') && supports('audio') ? 'text, images, and audio (transcribed)' : supports('image') ? 'text and images' : supports('audio') ? 'text and audio (transcribed)' : 'text only';
      el.innerHTML = '<div class="pf-v6-c-empty-state" data-ouia-component-id="chat-empty-state"><div class="pf-v6-c-empty-state__content">' +
        '<div class="pf-v6-c-empty-state__header"><div class="pf-v6-c-empty-state__icon">' + A.icon('cube', 'app-icon--lg') + '</div>' +
        '<div class="pf-v6-c-empty-state__title"><h2 class="pf-v6-c-empty-state__title-text">Start a conversation</h2></div></div>' +
        '<div class="pf-v6-c-empty-state__body">' + esc(model().name) + ' accepts ' + caps + '.</div></div></div>';
      return;
    }
    el.innerHTML = state.messages.map(messageHtml).join('');
    var scroller = document.getElementById('transcript-scroll');
    scroller.scrollTop = scroller.scrollHeight;
  }

  function render() {
    renderModelSelect();
    renderCapabilities();
    renderModalityControls();
    renderAttachment();
    renderComposerAlerts();
    renderHelper();
    renderTranscript();
    renderSend();
  }

  /* ---------- Behaviour ---------- */
  function selectModel(id) {
    if (state.busy) return;
    var prev = model();
    state.modelId = id;
    var m = model();
    state.validationError = null;
    if (state.attachment && !supports(state.attachment.kind)) {
      var removed = state.attachment.name;
      state.attachment = null;
      state.composerAlert = {
        variant: 'info', ouia: 'attachment-removed-alert', closeAction: 'dismiss-alert',
        title: removed + ' was removed',
        body: esc(m.name) + ' does not support ' + (prev.modalities.indexOf('image') !== -1 && m.modalities.indexOf('image') === -1 ? 'image' : 'audio') + ' input.'
      };
    } else if (state.composerAlert && state.composerAlert.ouia === 'attachment-removed-alert') {
      state.composerAlert = null;
    }
    render();
  }

  function showFileLimit() {
    state.composerAlert = {
      variant: 'warning', ouia: 'file-limit-alert', closeAction: 'dismiss-alert',
      title: 'Only one image or audio file per conversation',
      body: state.attachment && !state.fileUsed
        ? 'Remove ' + esc(state.attachment.name) + ' to choose a different file.'
        : 'This conversation already includes a file. Start a new chat to attach another image or audio file.',
      actions: state.fileUsed ? [{ label: 'Start new chat', action: 'new-chat', ouia: 'alert-new-chat' }] : []
    };
    render();
  }

  function validate(kind, f) {
    var allowed = kind === 'image' ? IMAGE_TYPES : AUDIO_TYPES;
    var label = kind === 'image' ? 'JPG or PNG' : 'WAV or MP3';
    if (f.size === 0) return esc(f.name) + ' is empty (0 bytes). Choose a ' + label + ' file that contains data.';
    if (allowed.indexOf(f.type) === -1) return esc(f.name) + ' is not a supported ' + kind + ' type. Use ' + label + '.' + (f.type === 'application/pdf' ? ' To use PDF content, add it with Upload files instead.' : '');
    if (f.size > A.MAX_BYTES) return esc(f.name) + ' is ' + fmtSize(f.size) + '. The limit is 10 MB.';
    return null;
  }

  function acceptFile(kind, f) {
    state.composerAlert = null;
    var err = validate(kind, f);
    if (err) {
      state.validationError = err; // no upload request is made
      render();
      return;
    }
    state.validationError = null;
    var url = f.objectUrl || (kind === 'image' ? SAMPLE_IMAGE_URL : sampleAudioUrl());
    state.attachment = { kind: kind, name: f.name, size: f.size, type: f.type, status: 'uploading', url: url, silent: !!f.silent,
      alt: f.sample ? SAMPLE_IMAGE_ALT : 'Uploaded image ' + f.name };
    render();
    later(function () {
      if (!state.attachment) return;
      state.attachment.status = 'ready';
      state.attachment.fileId = fileId();
      render();
    }, 700);
  }

  function onFileChosen(kind, input) {
    var file = input.files && input.files[0];
    input.value = '';
    if (!file) return;
    acceptFile(kind, { name: file.name, type: file.type, size: file.size, objectUrl: file.size ? URL.createObjectURL(file) : null });
  }

  function send() {
    var input = document.getElementById('prompt-input');
    var text = input.value.trim();
    var a = state.attachment;
    if (state.busy || (a && a.status !== 'ready') || audioBlockedReason() || (!text && !a)) return;
    var m = model();
    var userMsg = { role: 'user', text: text };
    if (a && a.kind === 'image') userMsg.image = { url: a.url, alt: a.alt, name: a.name };
    if (a && a.kind === 'audio') userMsg.audio = { url: a.url, name: a.name, asrName: asr().name };
    state.messages.push(userMsg);
    if (a) state.fileUsed = true;
    state.attachment = null;
    state.composerAlert = null;
    input.value = '';
    state.busy = true;

    var reply = { role: 'assistant', modelName: m.name, status: 'processing' };
    state.messages.push(reply);

    if (a && a.kind === 'audio') {
      var asrName = asr().name;
      reply.label = 'Transcribing audio...';
      reply.steps = [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribing audio', status: 'current' }, { title: 'Generating response', status: 'pending' }];
      render();
      later(function () {
        if (a.silent) {
          reply.status = 'error';
          reply.steps = [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribing audio', status: 'warning' }, { title: 'Generating response', status: 'pending' }];
          reply.alert = emptyTranscriptionAlert(a.name, asrName);
          state.busy = false;
          render();
          return;
        }
        userMsg.audio.transcription = TRANSCRIPTION;
        reply.label = 'Generating response...';
        reply.steps = [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribed', status: 'success' }, { title: 'Generating response', status: 'current' }];
        render();
        later(function () {
          reply.status = 'done';
          reply.text = AUDIO_ANSWER;
          state.busy = false;
          render();
        }, STEP_DELAY);
      }, STEP_DELAY);
      return;
    }

    reply.label = 'Generating response...';
    render();
    later(function () {
      reply.status = 'done';
      reply.text = a ? IMAGE_ANSWER : TEXT_ANSWER;
      state.busy = false;
      render();
    }, a ? STEP_DELAY + 300 : 900);
  }

  function emptyTranscriptionAlert(name, asrName) {
    return {
      variant: 'warning', ouia: 'empty-transcription-alert',
      title: 'No speech detected',
      body: esc(asrName) + ' returned an empty transcription for ' + esc(name) + '. Nothing was sent to the model. Try a different recording.',
      actions: [{ label: 'Start new chat', action: 'new-chat', ouia: 'alert-new-chat' }]
    };
  }

  function asrErrorAlert(name, asrName) {
    return {
      variant: 'danger', ouia: 'asr-error-alert',
      title: 'Transcription failed',
      body: esc(asrName) + ' could not be reached (503 Service Unavailable). ' + esc(name) + ' was not transcribed, and nothing was sent to the model.',
      actions: [{ label: 'Retry transcription', action: 'retry-asr', ouia: 'retry-transcription' }, { label: 'View AI asset endpoints', action: 'go-assets', ouia: 'alert-go-assets' }]
    };
  }

  function newChat() {
    clearTimers();
    var keepModel = state.modelId;
    var keepAsr = state.asrId;
    var keepAssets = state.asrAssets;
    state = freshState();
    state.modelId = keepModel;
    state.asrId = keepAsr;
    state.asrAssets = keepAssets;
    document.getElementById('prompt-input').value = '';
    render();
    document.getElementById('prompt-input').focus();
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-action]');
    if (!btn) return;
    var action = btn.getAttribute('data-action');
    if (action === 'dismiss-alert') { state.composerAlert = null; render(); }
    else if (action === 'new-chat') newChat();
    else if (action === 'go-assets') window.location.href = './ai-asset-endpoints.html';
    else if (action === 'retry-asr') retryAsr();
  });

  function retryAsr() {
    var reply = state.messages[state.messages.length - 1];
    var userMsg = state.messages[state.messages.length - 2];
    if (!reply || reply.status !== 'error' || !userMsg || !userMsg.audio) return;
    state.busy = true;
    reply.status = 'processing';
    reply.label = 'Transcribing audio...';
    reply.steps = [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribing audio', status: 'current' }, { title: 'Generating response', status: 'pending' }];
    render();
    later(function () {
      userMsg.audio.transcription = TRANSCRIPTION;
      reply.label = 'Generating response...';
      reply.steps = [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribed', status: 'success' }, { title: 'Generating response', status: 'current' }];
      render();
      later(function () { reply.status = 'done'; reply.text = AUDIO_ANSWER; state.busy = false; render(); }, STEP_DELAY);
    }, STEP_DELAY);
  }

  /* ---------- Scenario seeds (on-load end states) ---------- */
  function imageUserMsg(text) {
    return { role: 'user', text: text || 'What objects are in this image?', image: { url: SAMPLE_IMAGE_URL, alt: SAMPLE_IMAGE_ALT, name: 'street-scene.png' } };
  }
  function audioUserMsg(withTranscript) {
    var m = { role: 'user', text: '', audio: { url: sampleAudioUrl(), name: 'planning-meeting.wav', asrName: 'whisper-large-v3' } };
    if (withTranscript) m.audio.transcription = TRANSCRIPTION;
    return m;
  }

  var SEEDS = {
    'default': function () {},
    'text-only': function (s) { s.modelId = 'granite-3.3-8b-instruct'; },
    'file-too-large': function (s) {
      s.validationError = 'aerial-survey.png is 14.2 MB. The limit is 10 MB.';
    },
    'image-processing': function (s) {
      s.messages = [imageUserMsg(), { role: 'assistant', status: 'processing', label: 'Generating response...', modelName: 'Qwen2.5-VL-7B-Instruct' }];
      s.fileUsed = true; s.busy = true;
    },
    'image-response': function (s) {
      s.messages = [imageUserMsg(), { role: 'assistant', status: 'done', text: IMAGE_ANSWER, modelName: 'Qwen2.5-VL-7B-Instruct' }];
      s.fileUsed = true;
    },
    'model-rejected': function (s) {
      s.messages = [imageUserMsg('Describe this image.'), {
        role: 'assistant', status: 'error', modelName: 'Qwen2.5-VL-7B-Instruct',
        alert: {
          variant: 'danger', ouia: 'model-rejected-alert',
          title: 'The model rejected the image input',
          body: 'Qwen2.5-VL-7B-Instruct returned <code>400: image input is not enabled for this deployment</code>. The model catalog lists image support, but this deployment does not accept it. Choose another model with Image support, or start a new chat without an image.',
          actions: [{ label: 'Start new chat', action: 'new-chat', ouia: 'alert-new-chat' }]
        }
      }];
      s.fileUsed = true;
    },
    'one-file-limit': function (s) {
      SEEDS['image-response'](s);
      s.composerAlert = {
        variant: 'warning', ouia: 'file-limit-alert', closeAction: 'dismiss-alert',
        title: 'Only one image or audio file per conversation',
        body: 'This conversation already includes a file. Start a new chat to attach another image or audio file.',
        actions: [{ label: 'Start new chat', action: 'new-chat', ouia: 'alert-new-chat' }]
      };
    },
    'audio-no-asr': function (s) {
      s.modelId = 'gemma-3-12b-it';
      s.asrAssets = [];
      s.attachment = { kind: 'audio', name: 'planning-meeting.wav', size: 1.4 * 1024 * 1024, type: 'audio/wav', status: 'ready', url: sampleAudioUrl(), fileId: 'file-7f3a9c21' };
    },
    'audio-transcribing': function (s) {
      s.modelId = 'gemma-3-12b-it'; s.asrId = 'whisper-large-v3';
      s.messages = [audioUserMsg(false), {
        role: 'assistant', status: 'processing', label: 'Transcribing audio...', modelName: 'Gemma-3-12B-IT',
        steps: [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribing audio', status: 'current' }, { title: 'Generating response', status: 'pending' }]
      }];
      s.fileUsed = true; s.busy = true;
    },
    'audio-response': function (s) {
      s.modelId = 'gemma-3-12b-it'; s.asrId = 'whisper-large-v3';
      s.messages = [audioUserMsg(true), { role: 'assistant', status: 'done', text: AUDIO_ANSWER, modelName: 'Gemma-3-12B-IT' }];
      s.fileUsed = true;
    },
    'asr-error': function (s) {
      s.modelId = 'gemma-3-12b-it'; s.asrId = 'whisper-large-v3';
      s.messages = [audioUserMsg(false), {
        role: 'assistant', status: 'error', modelName: 'Gemma-3-12B-IT',
        steps: [{ title: 'Uploaded', status: 'success' }, { title: 'Transcription failed', status: 'danger' }, { title: 'Generating response', status: 'pending' }],
        alert: asrErrorAlert('planning-meeting.wav', 'whisper-large-v3')
      }];
      s.fileUsed = true;
    },
    'empty-transcription': function (s) {
      s.modelId = 'gemma-3-12b-it'; s.asrId = 'whisper-large-v3';
      var u = audioUserMsg(false); u.audio.name = 'silence.mp3';
      s.messages = [u, {
        role: 'assistant', status: 'error', modelName: 'Gemma-3-12B-IT',
        steps: [{ title: 'Uploaded', status: 'success' }, { title: 'Transcribing audio', status: 'warning' }, { title: 'Generating response', status: 'pending' }],
        alert: emptyTranscriptionAlert('silence.mp3', 'whisper-large-v3')
      }];
      s.fileUsed = true;
    }
  };

  function init() {
    state = freshState();
    var id = A.getScenario();
    (SEEDS[id] || SEEDS['default'])(state);
    document.getElementById('new-chat-icon').innerHTML = A.icon('plus');
    document.getElementById('send-icon').innerHTML = A.icon('send');
    document.getElementById('new-chat').addEventListener('click', newChat);
    document.getElementById('send-message').addEventListener('click', send);
    var prompt = document.getElementById('prompt-input');
    prompt.addEventListener('input', renderSend);
    prompt.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    document.getElementById('file-input-image').addEventListener('change', function (e) { onFileChosen('image', e.target); });
    document.getElementById('file-input-audio').addEventListener('change', function (e) { onFileChosen('audio', e.target); });
    if (id === 'audio-no-asr') prompt.value = 'Summarize this recording.';
    if (id === 'file-too-large') prompt.value = 'What does this aerial photo show?';
    render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
