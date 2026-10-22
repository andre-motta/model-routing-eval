(function () {
  var MAX_BYTES = 10 * 1024 * 1024;
  var IMAGE_TYPES = ['image/jpeg', 'image/png'];
  var AUDIO_TYPES = ['audio/wav', 'audio/x-wav', 'audio/mpeg'];
  var SAMPLE_IMG = 'data:image/svg+xml;utf8,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><rect width="240" height="150" fill="#cfe7fa"/><rect x="20" y="70" width="90" height="60" fill="#0066cc"/><circle cx="180" cy="50" r="28" fill="#f0ab00"/><text x="20" y="30" font-family="sans-serif" font-size="14">warehouse-shelf.png</text></svg>');

  // Capability tags as they would come from the model-metadata-collection catalog (supported_modalities)
  var MODELS = [
    { id: 'qwen2-5-vl', name: 'Qwen2.5-VL-7B-Instruct', modalities: ['text', 'image'] },
    { id: 'qwen2-audio', name: 'Qwen2-Audio-7B-Instruct', modalities: ['text', 'audio'] },
    { id: 'granite-3-3', name: 'granite-3.3-8b-instruct', modalities: ['text'] }
  ];
  var ASR_ASSETS = {
    registered: [{ id: 'whisper-large-v3', name: 'whisper-large-v3 (InferenceService)' }, { id: 'whisper-ext', name: 'openai-whisper-1 (Custom endpoint)' }],
    none: []
  };

  var scenario = (window.UxdScenario && window.UxdScenario.get()) || new URLSearchParams(location.search).get('scenario') || 'default';
  var SEEDS = {
    'default': { model: 'qwen2-5-vl' },
    'text-only': { model: 'granite-3-3' },
    'image-response': { model: 'qwen2-5-vl', messages: 'image' },
    'audio-transcribed': { model: 'qwen2-audio', messages: 'audio' },
    'audio-no-asr': { model: 'qwen2-audio', asr: 'none', alert: 'no-asr' },
    'file-too-large': { model: 'qwen2-5-vl', alert: 'too-large' },
    'asr-error': { model: 'qwen2-audio', messages: 'asr-error' },
    'limit-reached': { model: 'qwen2-5-vl', messages: 'image', alert: 'limit' }
  };
  var seed = SEEDS[scenario] || SEEDS['default'];

  var state = { model: seed.model, asrList: ASR_ASSETS[seed.asr || 'registered'], asr: 'whisper-large-v3', attachment: null, used: false, messages: [] };

  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function model() { return MODELS.filter(function (m) { return m.id === state.model; })[0]; }
  function has(mod) { return model().modalities.indexOf(mod) !== -1; }

  function alertHtml(variant, title, body, ouia) {
    var icon = { danger: 'exclamation-circle', warning: 'exclamation-triangle', info: 'info-circle', success: 'check-circle' }[variant];
    return '<div class="pf-v6-c-alert pf-m-inline pf-m-' + variant + ' pf-v6-u-mb-sm" data-ouia-component-id="' + ouia + '">' +
      '<div class="pf-v6-c-alert__icon"><i class="fas fa-' + icon + '" aria-hidden="true"></i></div>' +
      '<p class="pf-v6-c-alert__title"><span class="pf-v6-screen-reader">' + variant + ' alert:</span>' + title + '</p>' +
      (body ? '<div class="pf-v6-c-alert__description">' + body + '</div>' : '') + '</div>';
  }

  function setAlert(kind, detail) {
    var html = '';
    if (kind === 'no-asr') html = alertHtml('warning', 'No transcription model available',
      'Audio must be transcribed before it can be sent. Register a transcription model as an AI asset and flag it as ASR. <a href="./ai-asset-endpoints.html?scenario=no-asr">Go to AI asset endpoints</a>', 'alert-no-asr');
    if (kind === 'too-large') html = alertHtml('danger', 'File is too large', esc(detail || 'shelf-photo-raw.png (14.2 MB)') + ' exceeds the 10 MB limit. The file was not uploaded.', 'alert-too-large');
    if (kind === 'zero') html = alertHtml('danger', 'File is empty', esc(detail) + ' is 0 bytes. Choose a different file.', 'alert-zero');
    if (kind === 'type') html = alertHtml('danger', 'Unsupported file type', esc(detail) + ' is not supported. Use JPG or PNG for images, WAV or MP3 for audio.', 'alert-type');
    if (kind === 'limit') html = alertHtml('info', 'One file per conversation', 'This conversation already includes a file. Start a new conversation to attach another image or audio file.', 'alert-limit');
    $('alerts').innerHTML = html;
  }

  function renderModels() {
    $('model-group').innerHTML = MODELS.map(function (m) {
      var sel = m.id === state.model;
      return '<div class="pf-v6-c-toggle-group__item"><button type="button" role="radio" aria-checked="' + sel + '" class="pf-v6-c-toggle-group__button' + (sel ? ' pf-m-selected' : '') + '" data-model="' + m.id + '" data-ouia-component-id="model-option-' + m.id + '"><span class="pf-v6-c-toggle-group__text">' + esc(m.name) + '</span></button></div>';
    }).join('');
    $('model-caps').innerHTML = '<div class="pf-v6-c-label-group"><div class="pf-v6-c-label-group__main"><ul class="pf-v6-c-label-group__list" role="list" aria-label="Supported inputs">' +
      model().modalities.map(function (t) {
        var label = { text: 'Text', image: 'Image (image-inferencing)', audio: 'Audio (audio-asr)' }[t];
        return '<li class="pf-v6-c-label-group__list-item"><span class="pf-v6-c-label pf-m-compact ' + (t === 'text' ? '' : 'pf-m-blue') + '"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + label + '</span></span></span></li>';
      }).join('') + '</ul></div></div>';
  }

  function renderControls() {
    var html = '';
    var disabled = state.used || state.attachment ? ' disabled aria-disabled="true"' : '';
    if (has('image')) html += '<button class="pf-v6-c-button pf-m-plain" type="button" id="btn-image" aria-label="Attach image (JPG or PNG)" title="Attach image" data-ouia-component-id="attach-image"' + disabled + '><i class="fas fa-image" aria-hidden="true"></i></button>' +
      '<button class="pf-v6-c-button pf-m-link pf-m-small" type="button" id="btn-sample" data-ouia-component-id="attach-sample-image"' + disabled + '>Use sample image</button>';
    if (has('audio')) html += '<button class="pf-v6-c-button pf-m-plain" type="button" id="btn-audio" aria-label="Attach audio (WAV or MP3)" title="Attach audio" data-ouia-component-id="attach-audio"' + disabled + '><i class="fas fa-file-audio" aria-hidden="true"></i></button>' +
      '<button class="pf-v6-c-button pf-m-link pf-m-small" type="button" id="btn-sample-audio" data-ouia-component-id="attach-sample-audio"' + disabled + '>Use sample audio</button>';
    $('modality-controls').innerHTML = html;
    $('asr-region').hidden = !has('audio');
    if (has('audio')) {
      $('asr-select').innerHTML = state.asrList.length
        ? state.asrList.map(function (a) { return '<option value="' + a.id + '"' + (a.id === state.asr ? ' selected' : '') + '>' + esc(a.name) + '</option>'; }).join('')
        : '<option value="">No ASR endpoints registered</option>';
      $('asr-select').disabled = !state.asrList.length;
    }
    if (has('audio') && !state.asrList.length) setAlert('no-asr');
  }

  function renderChips() {
    var a = state.attachment;
    $('chips').innerHTML = !a ? '' :
      '<span class="pf-v6-c-label pf-m-outline" data-ouia-component-id="attachment-chip"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__icon"><i class="fas fa-' + (a.kind === 'image' ? 'image' : 'file-audio') + '" aria-hidden="true"></i></span><span class="pf-v6-c-label__text">' + esc(a.name) + ' (' + a.size + ')</span></span>' +
      '<span class="pf-v6-c-label__actions"><button class="pf-v6-c-button pf-m-plain pf-m-no-padding" type="button" aria-label="Remove ' + esc(a.name) + '" id="remove-chip"><i class="fas fa-times" aria-hidden="true"></i></button></span></span>';
  }

  function renderTranscript() {
    var t = $('transcript');
    if (!state.messages.length) {
      t.innerHTML = '<div class="empty-chat"><i class="fas fa-comments fa-2x" aria-hidden="true"></i><p class="pf-v6-u-mt-sm">Send a message to start. ' +
        (has('image') ? 'You can attach one image.' : has('audio') ? 'You can attach one audio file.' : 'This model supports text only.') + '</p></div>';
      return;
    }
    t.innerHTML = state.messages.map(function (m) {
      if (m.role === 'user') {
        var body = '';
        if (m.image) body += '<img src="' + m.image + '" alt="Uploaded image: ' + esc(m.fileName) + '" />';
        if (m.audio) body += '<div class="audio-chip"><i class="fas fa-file-audio" aria-hidden="true"></i><audio controls aria-label="Uploaded audio: ' + esc(m.fileName) + '"></audio></div><div class="msg-meta">' + esc(m.fileName) + '</div>';
        if (m.transcription) body += '<div class="transcription" aria-label="Transcription">"' + esc(m.transcription) + '"</div><div class="msg-meta">Transcribed by ' + esc(m.asrName) + '</div>';
        if (m.text) body += '<div>' + esc(m.text) + '</div>';
        return '<div class="msg msg-user" data-ouia-component-id="user-message"><div class="msg-meta">You</div>' + body + '</div>';
      }
      if (m.role === 'status') return '<div class="msg msg-bot" role="status"><span class="pf-v6-c-spinner pf-m-sm" role="progressbar" aria-label="' + esc(m.text) + '"><span class="pf-v6-c-spinner__path"></span></span> ' + esc(m.text) + '</div>';
      if (m.role === 'error') return '<div class="msg" style="max-width:100%">' + alertHtml('danger', m.title, m.text, 'alert-asr-error') + '</div>';
      return '<div class="msg msg-bot" data-ouia-component-id="assistant-message"><div class="msg-meta">' + esc(model().name) + '</div>' + esc(m.text) + '</div>';
    }).join('');
    t.scrollTop = t.scrollHeight;
  }

  function renderAll() { renderModels(); renderControls(); renderChips(); renderTranscript(); }

  function validate(file, kind) {
    var allowed = kind === 'image' ? IMAGE_TYPES : AUDIO_TYPES;
    if (allowed.indexOf(file.type) === -1) return setAlert('type', file.name), false;
    if (file.size === 0) return setAlert('zero', file.name), false;
    if (file.size > MAX_BYTES) return setAlert('too-large', file.name + ' (' + (file.size / 1048576).toFixed(1) + ' MB)'), false;
    return true;
  }

  function attach(kind, name, size, src) {
    if (state.used) { setAlert('limit'); return; }
    $('alerts').innerHTML = '';
    state.attachment = { kind: kind, name: name, size: size, src: src };
    renderControls(); renderChips();
  }

  function send() {
    var text = $('prompt').value.trim();
    var a = state.attachment;
    if (!text && !a) return;
    if (a && a.kind === 'audio' && !state.asrList.length) { setAlert('no-asr'); return; }
    var msg = { role: 'user', text: text };
    if (a && a.kind === 'image') { msg.image = a.src; msg.fileName = a.name; }
    if (a && a.kind === 'audio') { msg.audio = true; msg.fileName = a.name; }
    state.messages.push(msg);
    if (a) state.used = true;
    state.attachment = null; $('prompt').value = '';
    var steps = a && a.kind === 'audio' ? ['Uploading...', 'Transcribing audio...', 'Generating response...'] : a ? ['Uploading...', 'Generating response...'] : ['Generating response...'];
    var status = { role: 'status', text: steps[0] }; state.messages.push(status);
    renderControls(); renderChips(); renderTranscript();
    var i = 0;
    var timer = setInterval(function () {
      i++;
      if (i < steps.length) { status.text = steps[i]; renderTranscript(); return; }
      clearInterval(timer);
      state.messages.pop();
      if (a && a.kind === 'audio') msg.transcription = 'What are the main risks of rolling out the new inventory system next quarter?', msg.asrName = $('asr-select').selectedOptions[0].text;
      state.messages.push({ role: 'bot', text: a && a.kind === 'image'
        ? 'The image shows a warehouse shelf with a blue storage bin on the lower left and a yellow round object in the upper right.'
        : a ? 'Key risks include data migration errors, staff training gaps, and integration delays with existing supplier systems.'
        : 'Here is a response to your message: "' + text + '".' });
      renderTranscript();
    }, 700);
  }

  // Seed scenario end-state
  if (seed.messages === 'image') {
    state.messages = [{ role: 'user', image: SAMPLE_IMG, fileName: 'warehouse-shelf.png', text: 'What objects are on this shelf?' },
      { role: 'bot', text: 'The image shows a warehouse shelf with a blue storage bin on the lower left and a yellow round object in the upper right. No labels are visible.' }];
    state.used = true;
  } else if (seed.messages === 'audio') {
    state.messages = [{ role: 'user', audio: true, fileName: 'standup-question.wav', transcription: 'What are the main risks of rolling out the new inventory system next quarter?', asrName: 'whisper-large-v3 (InferenceService)' },
      { role: 'bot', text: 'Key risks include data migration errors, staff training gaps, and integration delays with existing supplier systems.' }];
    state.used = true;
  } else if (seed.messages === 'asr-error') {
    state.messages = [{ role: 'user', audio: true, fileName: 'meeting-notes.mp3' },
      { role: 'error', title: 'Transcription failed', text: 'The ASR endpoint whisper-large-v3 could not be reached (503). No request was sent to the model. Try again or choose a different ASR model.' }];
  }
  renderAll();
  if (seed.alert) setAlert(seed.alert);

  // Events
  $('model-group').addEventListener('click', function (e) {
    var b = e.target.closest('[data-model]'); if (!b) return;
    state.model = b.getAttribute('data-model');
    if (state.attachment && !has(state.attachment.kind)) state.attachment = null;
    $('alerts').innerHTML = '';
    renderAll();
  });
  $('modality-controls').addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    if (b.id === 'btn-image') $('file-image').click();
    if (b.id === 'btn-audio') $('file-audio').click();
    if (b.id === 'btn-sample') attach('image', 'warehouse-shelf.png', '1.2 MB', SAMPLE_IMG);
    if (b.id === 'btn-sample-audio') attach('audio', 'standup-question.wav', '2.4 MB');
  });
  $('file-image').addEventListener('change', function (e) {
    var f = e.target.files[0]; if (!f) return;
    if (validate(f, 'image')) attach('image', f.name, (f.size / 1048576).toFixed(1) + ' MB', URL.createObjectURL(f));
    e.target.value = '';
  });
  $('file-audio').addEventListener('change', function (e) {
    var f = e.target.files[0]; if (!f) return;
    if (validate(f, 'audio')) attach('audio', f.name, (f.size / 1048576).toFixed(1) + ' MB');
    e.target.value = '';
  });
  $('chips').addEventListener('click', function (e) { if (e.target.closest('#remove-chip')) { state.attachment = null; renderControls(); renderChips(); } });
  $('asr-select').addEventListener('change', function (e) { state.asr = e.target.value; });
  $('send').addEventListener('click', send);
  $('prompt').addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } });
  $('new-chat').addEventListener('click', function () { state.messages = []; state.used = false; state.attachment = null; $('alerts').innerHTML = ''; renderAll(); });
})();
