/* Playground with per-modality (image / audio) input controls. */
(function () {
  'use strict';

  var MM = window.MM;
  var esc = MM.escapeHtml;
  var toneUrl = null;
  function tone() {
    if (!toneUrl) toneUrl = MM.makeToneWavUrl(2.5, 330);
    return toneUrl;
  }

  function modelById(id) {
    for (var i = 0; i < MM.MODELS.length; i++) if (MM.MODELS[i].id === id) return MM.MODELS[i];
    return MM.MODELS[0];
  }
  function asrAssets(state) {
    return state.assets.filter(function (a) { return a.asr; });
  }
  function supports(model, kind) {
    return model.modalities.indexOf(kind) !== -1;
  }

  var IMAGE_MSG = {
    role: 'user',
    text: 'What trend does this chart show, and which quarter needs attention?',
    attachment: { kind: 'image', name: 'gpu-utilization-q1-q4.png', size: 248320, src: MM.SAMPLE_IMAGE, alt: 'Uploaded image: bar chart titled GPU utilization by quarter' },
  };
  var IMAGE_REPLY = {
    role: 'assistant',
    text: 'The chart shows GPU utilization rising every quarter: 45% in Q1, 65% in Q2, 80% in Q3 and 93% in Q4. Q4 needs attention: at 93% the cluster is close to saturation, so new workloads are likely to queue. Consider adding capacity or rebalancing workloads before next quarter.',
  };
  var AUDIO_MSG = {
    role: 'user',
    text: '',
    attachment: {
      kind: 'audio', name: 'standup-notes.wav', size: 1835008, alt: 'Uploaded audio: standup-notes.wav',
      transcript: 'Summarize the action items from today\'s standup: Priya is finishing the storage spike by Thursday, Marco needs a test namespace with a Whisper deployment, and we still need PM sign-off on the 10 megabyte file limit.',
      asr: 'whisper-large-v3',
    },
  };
  var AUDIO_REPLY = {
    role: 'assistant',
    text: 'Action items from the standup:\n1. Priya: finish the storage spike by Thursday.\n2. Marco: set up a test namespace with a Whisper deployment.\n3. Team: get PM sign-off on the 10 MB file size limit.',
  };

  function baseState() {
    return {
      modelId: 'qwen2-5-vl-7b',
      assets: MM.ASSETS.map(function (a) { return Object.assign({}, a); }),
      asrId: 'whisper-large-v3',
      messages: [],
      pending: null, // attachment staged in the composer
      composerAlert: null, // { variant, title, body, action }
      progress: null, // { steps: [{label, status}] }
      notice: null, // info notice in settings (e.g. attachment removed after model switch)
      draft: '',
      busy: false,
    };
  }

  var SCENARIOS = {
    default: function (s) { return s; },
    'text-only-model': function (s) {
      s.modelId = 'granite-3-3-8b';
      s.messages = [
        { role: 'user', text: 'Give me three tips for writing a good system prompt.' },
        { role: 'assistant', text: '1. State the role and goal up front.\n2. Specify the output format you expect.\n3. Add constraints and one short example.' },
      ];
      return s;
    },
    'image-response': function (s) {
      s.messages = [IMAGE_MSG, IMAGE_REPLY];
      return s;
    },
    'image-processing': function (s) {
      s.messages = [IMAGE_MSG];
      s.busy = true;
      s.progress = { steps: [
        { label: 'Image uploaded', status: 'done' },
        { label: 'Waiting for model response…', status: 'active' },
      ] };
      return s;
    },
    'audio-ready': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.pending = { kind: 'audio', name: 'standup-notes.wav', size: 1835008, src: tone(), demo: true };
      s.draft = '';
      return s;
    },
    'audio-transcribing': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.messages = [{ role: 'user', text: '', attachment: Object.assign({}, AUDIO_MSG.attachment, { transcript: null }) }];
      s.busy = true;
      s.progress = { steps: [
        { label: 'Audio uploaded', status: 'done' },
        { label: 'Transcribing audio with whisper-large-v3…', status: 'active' },
        { label: 'Waiting for model response', status: 'todo' },
      ] };
      return s;
    },
    'audio-response': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.messages = [AUDIO_MSG, AUDIO_REPLY];
      return s;
    },
    'no-asr-asset': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.assets.forEach(function (a) { a.asr = false; });
      s.asrId = '';
      s.pending = { kind: 'audio', name: 'customer-call.mp3', size: 3460300, src: tone(), demo: true };
      return s;
    },
    'file-too-large': function (s) {
      s.composerAlert = {
        variant: 'danger',
        title: 'File not attached: site-survey-photo.png is too large',
        body: 'The file is 14.2 MB. Images and audio files must be 10 MB or smaller. Compress or resize the file and try again.',
      };
      return s;
    },
    'unsupported-file-type': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.composerAlert = {
        variant: 'danger',
        title: 'File not attached: quarterly-report.pdf is not a supported image type',
        body: 'Attach a JPG or PNG image. To chat with PDF content, use Upload files in the Knowledge section instead.',
      };
      return s;
    },
    'empty-file': function (s) {
      s.composerAlert = {
        variant: 'danger',
        title: 'File not attached: screenshot.png is empty',
        body: 'The selected file is 0 bytes. Choose a different file.',
      };
      return s;
    },
    'conversation-limit': function (s) {
      s.messages = [IMAGE_MSG, IMAGE_REPLY];
      s.composerAlert = {
        variant: 'warning',
        title: 'Only one image or audio file per conversation',
        body: 'This conversation already includes gpu-utilization-q1-q4.png. Start a new chat to attach another file.',
        action: 'new-chat',
      };
      return s;
    },
    'asr-error': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.messages = [
        { role: 'user', text: '', attachment: Object.assign({}, AUDIO_MSG.attachment, { transcript: null }) },
        { role: 'error', variant: 'danger', title: 'Audio transcription failed',
          text: 'whisper-large-v3 could not be reached (503 Service Unavailable). The message was not sent to Qwen2.5-Omni-7B. Check that the transcription endpoint is running, or choose a different transcription model, then try again.' },
      ];
      return s;
    },
    'empty-transcription': function (s) {
      s.modelId = 'qwen2-5-omni-7b';
      s.messages = [
        { role: 'user', text: '', attachment: Object.assign({}, AUDIO_MSG.attachment, { name: 'meeting-room-mic.wav', transcript: '' }) },
        { role: 'error', variant: 'warning', title: 'No speech detected',
          text: 'whisper-large-v3 returned an empty transcription for meeting-room-mic.wav, so nothing was sent to the model. Check that the recording contains speech and try a different file.' },
      ];
      return s;
    },
    'model-rejected-input': function (s) {
      s.modelId = 'gemma-3-4b-it';
      s.messages = [
        Object.assign({}, IMAGE_MSG),
        { role: 'error', variant: 'danger', title: 'gemma-3-4b-it could not process the image',
          text: 'The model returned 400 Bad Request: "image content parts are not supported by this deployment". The model catalog lists this model as image-capable, but this endpoint rejected the image. Choose another model with Image input, or remove the image and send text only.' },
      ];
      return s;
    },
  };

  var scenarioId = MM.getScenario();
  var state = (SCENARIOS[scenarioId] || SCENARIOS.default)(baseState());

  /* ---------- rendering ---------- */

  var el = {};

  function icon(name) {
    var paths = {
      image: 'M2 3h12v10H2z M4 11l3-4 2 2.5L11 7l2 4z',
      audio: 'M6 3v7.3A2 2 0 1 0 7 12V6h5V3z',
      x: 'M4 4l8 8M12 4l-8 8',
    };
    var fill = name === 'x' ? 'none' : 'currentColor';
    var stroke = name === 'x' ? 'currentColor' : 'none';
    return '<svg class="mm-icon" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="' + fill + '" stroke="' + stroke + '" stroke-width="1.6" fill-rule="evenodd"><path d="' + paths[name] + '"/></svg>';
  }

  function fileUsedInConversation() {
    return state.messages.some(function (m) { return m.attachment; }) ? state.messages.filter(function (m) { return m.attachment; })[0].attachment : null;
  }

  function alertHtml(variant, title, body, actionHtml, live) {
    return (
      '<div class="pf-v6-c-alert pf-m-inline pf-m-' + variant + '"' + (live ? ' role="alert"' : '') + '>' +
      '<div class="pf-v6-c-alert__icon">' + alertIcon(variant) + '</div>' +
      '<p class="pf-v6-c-alert__title"><span class="pf-v6-screen-reader">' + variant + ' alert:</span>' + esc(title) + '</p>' +
      (body ? '<div class="pf-v6-c-alert__description"><p>' + body + '</p></div>' : '') +
      (actionHtml ? '<div class="pf-v6-c-alert__action-group">' + actionHtml + '</div>' : '') +
      '</div>'
    );
  }
  function alertIcon(variant) {
    var glyph = { danger: '!', warning: '!', success: '✓', info: 'i', custom: '•' }[variant] || 'i';
    return '<span class="mm-alert-glyph mm-alert-glyph--' + variant + '" aria-hidden="true">' + glyph + '</span>';
  }

  function renderSettings() {
    var model = modelById(state.modelId);
    var opts = MM.MODELS.map(function (m) {
      return '<option value="' + m.id + '"' + (m.id === model.id ? ' selected' : '') + '>' + esc(m.name) + '</option>';
    }).join('');

    var labels = model.modalities.map(function (k) {
      var color = { text: '', image: ' pf-m-blue', audio: ' pf-m-purple' }[k];
      var name = { text: 'Text', image: 'Image input', audio: 'Audio input' }[k];
      return '<span class="pf-v6-c-label pf-m-compact' + color + '" data-modality-label="' + k + '"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + name + '</span></span></span>';
    }).join(' ');

    var html =
      '<div class="pf-v6-c-form__group">' +
      '<div class="pf-v6-c-form__group-label"><label class="pf-v6-c-form__label" for="model-select"><span class="pf-v6-c-form__label-text">Model</span></label></div>' +
      '<div class="pf-v6-c-form__group-control">' +
      '<span class="pf-v6-c-form-control"><select id="model-select" data-ouia-component-id="model-select" aria-describedby="model-modalities">' + opts + '</select>' +
      '<span class="pf-v6-c-form-control__utilities"><span class="pf-v6-c-form-control__toggle-icon">▾</span></span></span>' +
      '<div class="mm-modalities" id="model-modalities"><span class="mm-modalities__label">Accepts:</span> ' + labels + '</div>' +
      (model.modalities.length === 1
        ? '<div class="pf-v6-c-helper-text"><div class="pf-v6-c-helper-text__item"><span class="pf-v6-c-helper-text__item-text">This model accepts text only. Choose a model labeled Image input or Audio input to attach files.</span></div></div>'
        : '') +
      '</div></div>';

    if (supports(model, 'audio')) {
      var asr = asrAssets(state);
      if (asr.length) {
        var asrOpts = asr.map(function (a) {
          return '<option value="' + a.id + '"' + (a.id === state.asrId ? ' selected' : '') + '>' + esc(a.name) + ' · ' + esc(a.type) + '</option>';
        }).join('');
        html +=
          '<div class="pf-v6-c-form__group" data-testid="asr-group">' +
          '<div class="pf-v6-c-form__group-label"><label class="pf-v6-c-form__label" for="asr-select"><span class="pf-v6-c-form__label-text">Audio transcription model</span></label></div>' +
          '<div class="pf-v6-c-form__group-control">' +
          '<span class="pf-v6-c-form-control"><select id="asr-select" data-ouia-component-id="asr-select" aria-describedby="asr-help">' + asrOpts + '</select>' +
          '<span class="pf-v6-c-form-control__utilities"><span class="pf-v6-c-form-control__toggle-icon">▾</span></span></span>' +
          '<div class="pf-v6-c-helper-text" id="asr-help"><div class="pf-v6-c-helper-text__item"><span class="pf-v6-c-helper-text__item-text">Audio files are transcribed with this model, then the text is sent to ' + esc(model.name) + '. Lists AI asset endpoints marked as transcription (ASR).</span></div></div>' +
          '</div></div>';
      } else {
        html +=
          '<div class="pf-v6-c-form__group" data-testid="asr-group">' +
          '<div class="pf-v6-c-form__group-label"><label class="pf-v6-c-form__label" for="asr-select"><span class="pf-v6-c-form__label-text">Audio transcription model</span></label></div>' +
          '<div class="pf-v6-c-form__group-control">' +
          '<span class="pf-v6-c-form-control pf-m-disabled"><select id="asr-select" disabled aria-describedby="asr-help"><option>No transcription models available</option></select></span>' +
          '<div class="pf-v6-c-helper-text" id="asr-help"><div class="pf-v6-c-helper-text__item pf-m-warning"><span class="pf-v6-c-helper-text__item-text">No AI asset is marked as a transcription (ASR) endpoint. <a href="ai-asset-endpoints.html?scenario=no-asr-flagged" data-ouia-component-id="register-asr-link">Go to AI asset endpoints</a> to mark one.</span></div></div>' +
          '</div></div>';
      }
    }

    if (state.notice) {
      html += '<div class="mm-settings-notice">' + alertHtml('info', state.notice, '', '', true) + '</div>';
    }

    el.settings.innerHTML = html;
    el.settings.querySelector('#model-select').addEventListener('change', onModelChange);
    var asrSel = el.settings.querySelector('#asr-select:not([disabled])');
    if (asrSel) asrSel.addEventListener('change', function (e) { state.asrId = e.target.value; render(); });
  }

  function attachmentHtml(att, inTranscript) {
    if (att.kind === 'image') {
      return '<figure class="mm-attachment mm-attachment--image"><img src="' + att.src + '" alt="' + esc(att.alt || ('Uploaded image: ' + att.name)) + '" />' +
        '<figcaption>' + icon('image') + ' ' + esc(att.name) + ' · ' + MM.formatBytes(att.size) + '</figcaption></figure>';
    }
    var t = '';
    if (inTranscript) {
      if (att.transcript === null || att.transcript === undefined) {
        t = '<p class="mm-transcript mm-transcript--pending">Transcription not available</p>';
      } else if (att.transcript === '') {
        t = '<p class="mm-transcript mm-transcript--pending">Empty transcription</p>';
      } else {
        t = '<details class="mm-transcript" open><summary>Transcription · ' + esc(att.asr || state.asrId) + '</summary><p>' + esc(att.transcript) + '</p></details>';
      }
    }
    return '<figure class="mm-attachment mm-attachment--audio">' +
      '<figcaption>' + icon('audio') + ' ' + esc(att.name) + ' · ' + MM.formatBytes(att.size) + '</figcaption>' +
      '<audio controls preload="none" src="' + (att.src || tone()) + '" aria-label="' + esc(att.alt || ('Uploaded audio: ' + att.name)) + '"></audio>' + t + '</figure>';
  }

  function renderTranscript() {
    var model = modelById(state.modelId);
    var html = '';
    if (!state.messages.length && !state.progress) {
      html =
        '<div class="pf-v6-c-empty-state pf-m-sm"><div class="pf-v6-c-empty-state__content">' +
        '<div class="pf-v6-c-empty-state__header"><div class="pf-v6-c-empty-state__title"><h2 class="pf-v6-c-empty-state__title-text">Start a conversation with ' + esc(model.name) + '</h2></div></div>' +
        '<div class="pf-v6-c-empty-state__body">' +
        (model.modalities.length > 1
          ? 'Type a message' + (supports(model, 'image') ? ', attach a JPG or PNG image' : '') + (supports(model, 'audio') ? ', or attach a WAV or MP3 audio file' : '') + '. You can include one image or audio file per conversation.'
          : 'Type a message to begin. This model accepts text only.') +
        '</div></div></div>';
    }
    state.messages.forEach(function (m) {
      if (m.role === 'error') {
        html += '<div class="mm-msg mm-msg--system" data-testid="transcript-alert">' + alertHtml(m.variant, m.title, esc(m.text), '', true) + '</div>';
        return;
      }
      var who = m.role === 'user' ? 'You' : modelById(state.modelId).name;
      html += '<div class="mm-msg mm-msg--' + m.role + '"><div class="mm-msg__author">' + esc(who) + '</div><div class="mm-msg__bubble">' +
        (m.attachment ? attachmentHtml(m.attachment, true) : '') +
        (m.text ? '<p class="mm-msg__text">' + esc(m.text).replace(/\n/g, '<br/>') + '</p>' : '') +
        '</div></div>';
    });
    if (state.progress) {
      html += '<div class="mm-progress" role="status" aria-live="polite" data-testid="processing-status">' +
        state.progress.steps.map(function (st) {
          var mark = st.status === 'done' ? '<span class="mm-step-done" aria-hidden="true">✓</span>'
            : st.status === 'active' ? '<svg class="pf-v6-c-spinner" role="progressbar" viewBox="0 0 100 100" aria-label="In progress" style="--pf-v6-c-spinner--diameter: 1rem"><circle class="pf-v6-c-spinner__path" cx="50" cy="50" r="45" fill="none"></circle></svg>'
            : '<span class="mm-step-todo" aria-hidden="true">○</span>';
          return '<div class="mm-progress__step mm-progress__step--' + st.status + '">' + mark + '<span>' + esc(st.label) + '</span></div>';
        }).join('') + '</div>';
    }
    el.transcript.innerHTML = html;
    el.transcript.scrollTop = el.transcript.scrollHeight;
  }

  function renderComposer() {
    var model = modelById(state.modelId);
    var used = fileUsedInConversation();
    var limitReached = !!used || !!state.pending;
    var noAsr = supports(model, 'audio') && !asrAssets(state).length;

    // Composer alert
    var alerts = '';
    if (state.composerAlert) {
      var a = state.composerAlert;
      var action = a.action === 'new-chat'
        ? '<div class="pf-v6-c-alert__action"><button class="pf-v6-c-button pf-m-link pf-m-inline" type="button" data-action="new-chat"><span class="pf-v6-c-button__text">Start new chat</span></button></div>'
        : '';
      alerts += alertHtml(a.variant, a.title, esc(a.body), action, true);
    }
    if (state.pending && state.pending.kind === 'audio' && noAsr) {
      alerts += alertHtml('warning', 'Audio can\'t be sent: no transcription model is registered',
        'Audio is transcribed before it reaches the model. Mark a deployed transcription model (for example, Whisper) as an ASR endpoint in AI asset endpoints, then return here.',
        '<div class="pf-v6-c-alert__action"><a class="pf-v6-c-button pf-m-link pf-m-inline" href="ai-asset-endpoints.html?scenario=no-asr-flagged" data-ouia-component-id="no-asr-register"><span class="pf-v6-c-button__text">Go to AI asset endpoints</span></a></div>', true);
    }
    el.alerts.innerHTML = alerts;
    var na = el.alerts.querySelector('[data-action="new-chat"]');
    if (na) na.addEventListener('click', newChat);

    // Pending attachment chip
    el.pending.innerHTML = state.pending
      ? '<div class="mm-pending" data-testid="pending-attachment">' + (state.pending.kind === 'image' && state.pending.src
          ? '<img class="mm-pending__thumb" src="' + state.pending.src + '" alt="" />'
          : '<span class="mm-pending__icon">' + icon(state.pending.kind) + '</span>') +
        '<span class="mm-pending__name">' + esc(state.pending.name) + '<small>' + MM.formatBytes(state.pending.size) + ' · ' + (state.pending.kind === 'image' ? 'Image' : 'Audio') + ' ready to send</small></span>' +
        '<button class="pf-v6-c-button pf-m-plain" type="button" aria-label="Remove ' + esc(state.pending.name) + '" data-action="remove-pending">' + icon('x') + '</button></div>'
      : '';
    var rp = el.pending.querySelector('[data-action="remove-pending"]');
    if (rp) rp.addEventListener('click', function () { state.pending = null; state.composerAlert = null; render(); });

    // Per-modality controls
    var controls = '';
    if (supports(model, 'image')) {
      controls += '<button class="pf-v6-c-button pf-m-secondary pf-m-small' + (limitReached ? ' pf-m-aria-disabled' : '') + '" type="button" data-ouia-component-id="attach-image" data-modality-control="image"' + (limitReached ? ' aria-disabled="true"' : '') + ' aria-describedby="attach-help"><span class="pf-v6-c-button__icon pf-m-start">' + icon('image') + '</span><span class="pf-v6-c-button__text">Attach image</span></button>';
    }
    if (supports(model, 'audio')) {
      controls += '<button class="pf-v6-c-button pf-m-secondary pf-m-small' + (limitReached ? ' pf-m-aria-disabled' : '') + '" type="button" data-ouia-component-id="attach-audio" data-modality-control="audio"' + (limitReached ? ' aria-disabled="true"' : '') + ' aria-describedby="attach-help"><span class="pf-v6-c-button__icon pf-m-start">' + icon('audio') + '</span><span class="pf-v6-c-button__text">Attach audio</span></button>';
    }
    var help = '';
    if (controls) {
      var kinds = [];
      if (supports(model, 'image')) kinds.push('JPG, PNG');
      if (supports(model, 'audio')) kinds.push('WAV, MP3');
      help = limitReached
        ? (used ? '1 of 1 file used in this conversation. Start a new chat to attach another file.' : 'One file per conversation. Remove the attached file to choose a different one.')
        : kinds.join(' · ') + ' · up to 10 MB · 1 file per conversation';
      controls += '<span class="pf-v6-c-helper-text mm-attach-help" id="attach-help"><span class="pf-v6-c-helper-text__item' + (used ? ' pf-m-indeterminate' : '') + '"><span class="pf-v6-c-helper-text__item-text">' + help + '</span></span></span>';
    }
    el.controls.innerHTML = controls;
    el.controls.querySelectorAll('[data-modality-control]').forEach(function (b) {
      b.addEventListener('click', function () { onAttachClick(b.getAttribute('data-modality-control')); });
    });

    // Send
    var blocked = state.busy || (state.pending && state.pending.kind === 'audio' && noAsr);
    el.send.disabled = !!blocked;
    el.send.classList.toggle('pf-m-disabled', !!blocked);
    if (el.input.value !== state.draft) el.input.value = state.draft;
    el.input.disabled = state.busy;
  }

  function render() {
    renderSettings();
    renderTranscript();
    renderComposer();
  }

  /* ---------- behavior ---------- */

  function onModelChange(e) {
    var prev = modelById(state.modelId);
    state.modelId = e.target.value;
    var next = modelById(state.modelId);
    state.notice = null;
    if (state.pending && !supports(next, state.pending.kind)) {
      state.notice = state.pending.name + ' was removed because ' + next.name + ' doesn\'t accept ' + state.pending.kind + ' input.';
      state.pending = null;
    }
    if (prev.id !== next.id) state.composerAlert = null;
    render();
  }

  function onAttachClick(kind) {
    if (fileUsedInConversation()) {
      state.composerAlert = {
        variant: 'warning',
        title: 'Only one image or audio file per conversation',
        body: 'This conversation already includes ' + fileUsedInConversation().name + '. Start a new chat to attach another file.',
        action: 'new-chat',
      };
      render();
      return;
    }
    if (state.pending) {
      state.composerAlert = {
        variant: 'warning',
        title: 'Only one image or audio file per conversation',
        body: 'Remove ' + state.pending.name + ' to attach a different file.',
      };
      render();
      return;
    }
    (kind === 'image' ? el.imageInput : el.audioInput).click();
  }

  function validate(file, kind) {
    var rule = MM.ALLOWED[kind];
    var ext = (file.name.split('.').pop() || '').toLowerCase();
    var mimeOk = file.type ? rule.mimes.indexOf(file.type) !== -1 : rule.exts.indexOf(ext) !== -1;
    if (file.size === 0) {
      return { title: 'File not attached: ' + file.name + ' is empty', body: 'The selected file is 0 bytes. Choose a different file.' };
    }
    if (!mimeOk) {
      return { title: 'File not attached: ' + file.name + ' is not a supported ' + kind + ' type',
        body: 'Attach a ' + rule.label + ' file.' + (ext === 'pdf' ? ' To chat with PDF content, use Upload files in the Knowledge section instead.' : '') };
    }
    if (file.size > MM.MAX_FILE_BYTES) {
      return { title: 'File not attached: ' + file.name + ' is too large',
        body: 'The file is ' + MM.formatBytes(file.size) + '. Images and audio files must be 10 MB or smaller. Compress or resize the file and try again.' };
    }
    return null;
  }

  function onFilePicked(kind, input) {
    var file = input.files && input.files[0];
    input.value = '';
    if (!file) return;
    var err = validate(file, kind);
    if (err) {
      // Client-side validation: nothing is uploaded to the BFF.
      state.composerAlert = { variant: 'danger', title: err.title, body: err.body };
      render();
      return;
    }
    state.composerAlert = null;
    state.pending = { kind: kind, name: file.name, size: file.size, src: URL.createObjectURL(file) };
    render();
  }

  function newChat() {
    var keepModel = state.modelId;
    var keepAssets = state.assets;
    var keepAsr = state.asrId;
    state = baseState();
    state.modelId = keepModel;
    state.assets = keepAssets;
    state.asrId = keepAsr;
    render();
    el.input.focus();
  }

  function step(steps, i, delay, done) {
    state.progress = { steps: steps.map(function (s, j) { return { label: s, status: j < i ? 'done' : j === i ? 'active' : 'todo' }; }) };
    render();
    setTimeout(function () {
      if (i + 1 < steps.length) step(steps, i + 1, delay, done);
      else done();
    }, delay);
  }

  function send() {
    var model = modelById(state.modelId);
    var text = el.input.value.trim();
    if (state.busy) return;
    if (!text && !state.pending) {
      el.input.focus();
      return;
    }
    var att = state.pending;
    var msg = { role: 'user', text: text, attachment: att ? Object.assign({}, att) : null };
    state.messages.push(msg);
    state.pending = null;
    state.composerAlert = null;
    state.notice = null;
    state.draft = '';
    state.busy = true;

    var finish = function (reply) {
      state.busy = false;
      state.progress = null;
      state.messages.push(reply);
      render();
    };

    if (att && att.kind === 'audio') {
      var asr = state.asrId;
      step(['Uploading audio…', 'Transcribing audio with ' + asr + '…', 'Waiting for model response…'], 0, 900, function () {
        var silent = /silent|silence/i.test(att.name);
        if (silent) {
          msg.attachment.transcript = '';
          finish({ role: 'error', variant: 'warning', title: 'No speech detected',
            text: asr + ' returned an empty transcription for ' + att.name + ', so nothing was sent to the model. Check that the recording contains speech and try a different file.' });
          return;
        }
        msg.attachment.transcript = att.demo ? AUDIO_MSG.attachment.transcript : '(Simulated transcription of ' + att.name + ')';
        msg.attachment.asr = asr;
        finish(att.demo ? AUDIO_REPLY : { role: 'assistant', text: 'Here is a response based on the transcription of ' + att.name + '. (Simulated response from ' + model.name + '.)' });
      });
    } else if (att && att.kind === 'image') {
      step(['Uploading image…', 'Waiting for model response…'], 0, 900, function () {
        finish({ role: 'assistant', text: 'I can see the image you attached (' + att.name + '). ' + (text ? 'In answer to your question: ' : '') + 'This is a simulated response from ' + model.name + ' describing the visual content.' });
      });
    } else {
      step(['Waiting for model response…'], 0, 800, function () {
        finish({ role: 'assistant', text: 'This is a simulated text response from ' + model.name + '.' });
      });
    }
  }

  function init() {
    el.settings = document.getElementById('playground-settings');
    el.transcript = document.getElementById('chat-transcript');
    el.alerts = document.getElementById('composer-alerts');
    el.pending = document.getElementById('composer-pending');
    el.controls = document.getElementById('modality-controls');
    el.input = document.getElementById('chat-input');
    el.send = document.getElementById('send-button');
    el.imageInput = document.getElementById('image-file-input');
    el.audioInput = document.getElementById('audio-file-input');

    el.imageInput.addEventListener('change', function () { onFilePicked('image', el.imageInput); });
    el.audioInput.addEventListener('change', function () { onFilePicked('audio', el.audioInput); });
    el.send.addEventListener('click', send);
    el.input.addEventListener('input', function () { state.draft = el.input.value; });
    el.input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
    });
    document.getElementById('new-chat-button').addEventListener('click', newChat);
    render();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
