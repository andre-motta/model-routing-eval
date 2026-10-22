/* RHAISTRAT-1527 prototype: multimodal Playground + AI Asset Endpoints (mock data only). */
(function () {
  var MAX_MB = 10;
  var OK_TYPES = { image: ['image/jpeg', 'image/png'], audio: ['audio/wav', 'audio/x-wav', 'audio/mpeg', 'audio/mp3'] };

  function scenarioId() {
    if (window.UxdScenario && window.UxdScenario.get) return window.UxdScenario.get();
    return new URLSearchParams(location.search).get('scenario') || 'default';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function $(id) { return document.getElementById(id); }
  function alertHtml(kind, title, body, id) {
    return '<div class="pf-v6-c-alert pf-m-' + kind + ' pf-m-inline pf-v6-u-mb-md" data-ouia-component-id="' + (id || 'alert') + '"><div class="pf-v6-c-alert__icon"></div>' +
      '<p class="pf-v6-c-alert__title"><span class="pf-v6-screen-reader">' + kind + ' alert:</span>' + esc(title) + '</p>' +
      (body ? '<div class="pf-v6-c-alert__description">' + body + '</div>' : '') + '</div>';
  }
  function label(text, color) {
    return '<span class="pf-v6-c-label' + (color ? ' pf-m-' + color : '') + ' pf-m-compact"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + esc(text) + '</span></span></span>';
  }

  /* ---------- Mock data keyed by scenario ---------- */
  var MODELS = {
    'granite-3.3-8b-instruct': { name: 'granite-3.3-8b-instruct', tags: ['text'] },
    'qwen2.5-vl-7b': { name: 'qwen2.5-vl-7b', tags: ['text', 'image-inferencing'] },
    'granite-speech-3.3': { name: 'granite-speech-3.3', tags: ['text', 'audio-asr'] }
  };
  var ASR_ASSETS = [{ id: 'whisper-large', name: 'whisper-large-v3 (ASR)' }, { id: 'openai-whisper', name: 'openai-whisper-1 (custom endpoint)' }];

  var IMG_USER = { role: 'user', text: 'What is shown in this diagram?', image: { name: 'architecture.png', size: '1.2 MB' } };
  var IMG_REPLY = { role: 'assistant', text: 'The diagram shows a browser calling a gateway, which forwards to a backend service and then to a model server. Three boxes are connected by arrows left to right.' };
  var AUD_USER = { role: 'user', text: 'Summarize this recording.', audio: { name: 'standup-notes.wav', size: '3.4 MB' } };

  var SCENARIOS = {
    'default': { model: 'granite-3.3-8b-instruct', asr: ASR_ASSETS, messages: [
      { role: 'user', text: 'Explain what a vector store is in two sentences.' },
      { role: 'assistant', text: 'A vector store keeps embeddings so you can search by meaning instead of exact words. It returns the stored items closest to a query embedding.' }] },
    'vision-ready': { model: 'qwen2.5-vl-7b', asr: ASR_ASSETS, messages: [] },
    'image-response': { model: 'qwen2.5-vl-7b', asr: ASR_ASSETS, messages: [IMG_USER, IMG_REPLY], limitUsed: 'image',
      alerts: [['info', 'One image or audio file per conversation', 'This conversation already has an image. Start a new chat to add another file.', 'limit-info']] },
    'file-too-large': { model: 'qwen2.5-vl-7b', asr: ASR_ASSETS, messages: [],
      alerts: [['danger', 'File is too large', '<strong>holiday-scan.png</strong> is 18.6 MB. The limit is 10 MB. Nothing was uploaded.', 'size-error']] },
    'audio-no-asr': { model: 'granite-speech-3.3', asr: [], messages: [], blockSend: true,
      alerts: [['warning', 'No transcription model registered', 'Audio is transcribed before it reaches the model. <a href="ai-assets.html">Register a transcription model as an AI asset</a> and flag it as ASR to send audio.', 'no-asr']] },
    'audio-ready': { model: 'granite-speech-3.3', asr: ASR_ASSETS, asrSelected: 'whisper-large', messages: [],
      chip: { kind: 'audio', name: 'standup-notes.wav', size: '3.4 MB' }, prompt: 'Summarize this recording.' },
    'audio-result': { model: 'granite-speech-3.3', asr: ASR_ASSETS, asrSelected: 'whisper-large', limitUsed: 'audio', messages: [
      AUD_USER,
      { role: 'assistant', transcript: 'Yesterday I finished the upload endpoint. Today I will wire the file size checks. No blockers except the storage volume question.',
        text: 'Summary: upload endpoint done, size validation next, and the open question is which storage volume to use for temporary files.' }],
      alerts: [['info', 'One image or audio file per conversation', 'Start a new chat to add another file.', 'limit-info']] },
    'asr-failure': { model: 'granite-speech-3.3', asr: ASR_ASSETS, asrSelected: 'whisper-large', limitUsed: 'audio', messages: [AUD_USER],
      alerts: [['danger', 'Transcription failed', 'whisper-large-v3 could not be reached. No message was sent to the model. Check the endpoint in <a href="ai-assets.html">AI asset endpoints</a> and try again.', 'asr-error']] }
  };

  /* ---------- Playground ---------- */
  function initPlayground() {
    var sid = scenarioId();
    var st = JSON.parse(JSON.stringify(SCENARIOS[sid] || SCENARIOS['default']));
    st.alerts = st.alerts || [];
    var pendingKind = null;

    var sel = $('model-select');
    sel.innerHTML = Object.keys(MODELS).map(function (k) { return '<option value="' + k + '">' + k + '</option>'; }).join('');
    sel.value = st.model;
    sel.onchange = function () { st.model = sel.value; st.alerts = st.alerts.filter(function (a) { return a[3] !== 'x'; }); renderControls(); };
    $('prompt').value = st.prompt || '';

    function caps() { var t = MODELS[st.model].tags; return { image: t.indexOf('image-inferencing') > -1, audio: t.indexOf('audio-asr') > -1 }; }

    function renderControls() {
      var c = caps();
      $('model-tags').innerHTML = MODELS[st.model].tags.map(function (t) { return label(t, t === 'text' ? '' : 'blue'); }).join(' ');
      $('btn-image').hidden = !c.image;
      $('btn-audio').hidden = !c.audio;
      $('limit-hint').hidden = !(c.image || c.audio);
      $('asr-wrap').hidden = !c.audio || !st.asr.length;
      $('asr-select').innerHTML = st.asr.map(function (a) { return '<option value="' + a.id + '">' + esc(a.name) + '</option>'; }).join('');
      if (st.asrSelected) $('asr-select').value = st.asrSelected;
      var blocked = st.limitUsed ? true : false;
      $('btn-image').disabled = blocked; $('btn-audio').disabled = blocked;
      $('alerts').innerHTML = st.alerts.map(function (a) { return alertHtml(a[0], a[1], a[2], a[3]); }).join('');
      renderChips();
      renderTranscript();
      var audioBlocked = c.audio && st.chip && st.chip.kind === 'audio' && !st.asr.length;
      $('btn-send').disabled = !!(st.blockSend && c.audio && !st.asr.length) || audioBlocked;
    }
    function renderChips() {
      $('chips').innerHTML = st.chip ? '<span class="pf-v6-c-label pf-m-outline"><span class="pf-v6-c-label__content"><span class="pf-v6-c-label__text">' + esc(st.chip.name) + ' (' + esc(st.chip.size) + ')</span></span></span> <button class="pf-v6-c-button pf-m-link pf-m-inline" type="button" id="chip-remove">Remove</button>' : '';
      var rm = $('chip-remove'); if (rm) rm.onclick = function () { st.chip = null; renderChips(); };
    }
    function renderTranscript() {
      if (!st.messages.length) { $('transcript').innerHTML = '<div class="pf-v6-c-empty-state pf-m-sm"><div class="pf-v6-c-empty-state__content"><h2 class="pf-v6-c-title pf-m-lg">Start a conversation</h2><div class="pf-v6-c-empty-state__body">Type a message' + (caps().image || caps().audio ? ' or attach a file the selected model can read.' : '. This model accepts text only.') + '</div></div></div>'; return; }
      $('transcript').innerHTML = st.messages.map(function (m) {
        var h = '<div class="pg-msg ' + m.role + '">';
        if (m.image) h += '<svg class="pg-img" role="img" aria-label="Uploaded image ' + esc(m.image.name) + '" viewBox="0 0 220 150"><rect width="220" height="150" fill="#e0e0e0"/><rect x="15" y="55" width="40" height="40" fill="#0066cc"/><rect x="90" y="55" width="40" height="40" fill="#3d7317"/><rect x="165" y="55" width="40" height="40" fill="#c9190b"/></svg><div class="pf-v6-u-font-size-sm pf-v6-u-mb-sm">' + esc(m.image.name) + ' (' + esc(m.image.size) + ')</div>';
        if (m.audio) h += '<div class="pg-audio"><audio controls aria-label="Uploaded audio ' + esc(m.audio.name) + '"></audio><span class="pf-v6-u-font-size-sm">' + esc(m.audio.name) + ' (' + esc(m.audio.size) + ')</span></div>';
        if (m.transcript) h += '<div class="pg-transcript"><strong>Transcript (whisper-large-v3):</strong> ' + esc(m.transcript) + '</div>';
        if (m.text) h += '<div>' + esc(m.text) + '</div>';
        return h + '</div>';
      }).join('');
    }
    function showProgress(steps, done) {
      var p = $('progress'); p.hidden = false;
      var i = 0;
      (function next() {
        if (i >= steps.length) { p.hidden = true; done(); return; }
        p.innerHTML = '<span class="pf-v6-c-spinner pf-m-md" role="progressbar" aria-label="' + steps[i] + '"></span> ' + steps[i];
        i++; setTimeout(next, 900);
      })();
    }

    function attach(kind) { pendingKind = kind; var f = $('file-input'); f.accept = kind === 'image' ? '.jpg,.jpeg,.png' : '.wav,.mp3'; f.value = ''; f.click(); }
    $('btn-image').onclick = function () { attach('image'); };
    $('btn-audio').onclick = function () { attach('audio'); };
    $('file-input').onchange = function () {
      var f = this.files[0]; if (!f) return;
      var err = null;
      if (f.size === 0) err = ['File is empty', esc(f.name) + ' has no content.'];
      else if (f.size > MAX_MB * 1048576) err = ['File is too large', esc(f.name) + ' exceeds the ' + MAX_MB + ' MB limit. Nothing was uploaded.'];
      else if (OK_TYPES[pendingKind].indexOf(f.type) < 0) err = ['Unsupported file type', 'Use ' + (pendingKind === 'image' ? 'JPG or PNG.' : 'WAV or MP3.')];
      if (err) { st.alerts = [['danger', err[0], err[1], 'file-error']]; }
      else { st.alerts = []; st.chip = { kind: pendingKind, name: f.name, size: (f.size / 1048576).toFixed(1) + ' MB' }; }
      renderControls();
    };

    $('btn-send').onclick = function () {
      var text = $('prompt').value.trim(); if (!text && !st.chip) return;
      var c = st.chip; st.alerts = []; $('prompt').value = '';
      var um = { role: 'user', text: text };
      if (c && c.kind === 'image') um.image = { name: c.name, size: c.size };
      if (c && c.kind === 'audio') um.audio = { name: c.name, size: c.size };
      st.messages.push(um); st.chip = null; if (c) st.limitUsed = c.kind; renderControls();
      var steps = c && c.kind === 'audio' ? ['Uploading audio...', 'Transcribing audio...', 'Waiting for model...'] : ['Waiting for model...'];
      showProgress(steps, function () {
        var r = { role: 'assistant', text: c && c.kind === 'image' ? 'This is a mock description of the uploaded image.' : 'This is a mock model reply.' };
        if (c && c.kind === 'audio') r.transcript = 'Mock transcript of the uploaded recording.';
        st.messages.push(r);
        if (c) st.alerts = [['info', 'One image or audio file per conversation', 'Start a new chat to add another file.', 'limit-info']];
        renderControls();
      });
    };
    renderControls();
  }

  /* ---------- AI asset endpoints ---------- */
  var ASSETS = [
    { id: 'qwen-vl', name: 'qwen2.5-vl-7b', type: 'Model deployment', endpoint: 'https://qwen-vl.ai-ns.svc/v1', asr: false },
    { id: 'granite-speech', name: 'granite-speech-3.3', type: 'Model deployment', endpoint: 'https://granite-speech.ai-ns.svc/v1', asr: false },
    { id: 'whisper-large', name: 'whisper-large-v3', type: 'Model deployment', endpoint: 'https://whisper.ai-ns.svc/v1', asr: true },
    { id: 'openai-custom', name: 'openai-whisper-1', type: 'Custom endpoint', endpoint: 'https://api.openai.com/v1', asr: false }
  ];
  function initAssets() {
    var sid = scenarioId();
    var root = $('assets-root');
    if (sid === 'load-error') {
      root.innerHTML = '<div class="pf-v6-c-empty-state"><div class="pf-v6-c-empty-state__content"><h2 class="pf-v6-c-title pf-m-lg">Unable to load AI asset endpoints</h2><div class="pf-v6-c-empty-state__body">The request failed. Check your connection and try again.</div><div class="pf-v6-c-empty-state__footer"><button class="pf-v6-c-button pf-m-primary" type="button" onclick="location.reload()">Retry</button></div></div></div>';
      return;
    }
    var data = JSON.parse(JSON.stringify(ASSETS));
    if (sid === 'no-asr') data.forEach(function (a) { a.asr = false; });
    function render() {
      var any = data.some(function (a) { return a.asr; });
      $('alerts').innerHTML = any ? '' : alertHtml('info', 'No ASR endpoints flagged', 'Playground audio input needs at least one endpoint flagged as ASR. Use <strong>Mark as ASR</strong> on a transcription model.', 'no-asr-info');
      root.innerHTML = '<table class="pf-v6-c-table pf-m-grid-md" role="grid" aria-label="AI asset endpoints"><thead class="pf-v6-c-table__thead"><tr class="pf-v6-c-table__tr"><th class="pf-v6-c-table__th">Name</th><th class="pf-v6-c-table__th">Type</th><th class="pf-v6-c-table__th">Endpoint</th><th class="pf-v6-c-table__th">Capability</th><th class="pf-v6-c-table__th"></th></tr></thead><tbody class="pf-v6-c-table__tbody">' +
        data.map(function (a) {
          return '<tr class="pf-v6-c-table__tr"><td class="pf-v6-c-table__td">' + esc(a.name) + '</td><td class="pf-v6-c-table__td">' + esc(a.type) + '</td><td class="pf-v6-c-table__td">' + esc(a.endpoint) + '</td><td class="pf-v6-c-table__td">' + (a.asr ? label('ASR / transcription', 'green') : label('Chat')) + '</td><td class="pf-v6-c-table__td">' +
            '<button class="pf-v6-c-button pf-m-link" type="button" data-ouia-component-id="mark-asr-' + a.id + '" data-id="' + a.id + '">' + (a.asr ? 'Remove ASR flag' : 'Mark as ASR') + '</button></td></tr>';
        }).join('') + '</tbody></table>';
      Array.prototype.forEach.call(root.querySelectorAll('button[data-id]'), function (b) { b.onclick = function () { openModal(b.getAttribute('data-id')); }; });
    }
    function openModal(id) {
      var a = data.filter(function (x) { return x.id === id; })[0];
      $('modal-root').innerHTML = '<div class="pf-v6-c-backdrop"><div class="pf-v6-l-bullseye"><div class="pf-v6-c-modal-box pf-m-sm" role="dialog" aria-modal="true" aria-labelledby="mt"><div class="pf-v6-c-modal-box__header"><h2 class="pf-v6-c-modal-box__title" id="mt"><span class="pf-v6-c-modal-box__title-text">' + (a.asr ? 'Remove ASR flag?' : 'Mark as ASR endpoint?') + '</span></h2></div><div class="pf-v6-c-modal-box__body">' +
        (a.asr ? esc(a.name) + ' will no longer appear in the Playground transcription model list.' : esc(a.name) + ' must expose <code>/v1/audio/transcriptions</code>. It will appear in the Playground transcription model list.') +
        '</div><div class="pf-v6-c-modal-box__footer"><button class="pf-v6-c-button pf-m-primary" id="m-ok" data-ouia-component-id="confirm-asr">' + (a.asr ? 'Remove flag' : 'Mark as ASR') + '</button><button class="pf-v6-c-button pf-m-link" id="m-cancel">Cancel</button></div></div></div></div>';
      $('m-cancel').onclick = function () { $('modal-root').innerHTML = ''; };
      $('m-ok').onclick = function () { a.asr = !a.asr; $('modal-root').innerHTML = ''; render(); };
    }
    render();
  }

  var page = document.body.getAttribute('data-page');
  if (page === 'playground') initPlayground(); else if (page === 'assets') initAssets();
})();
