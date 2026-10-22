/*
 * Scenario catalog for the multimodal Playground prototype (RHAISTRAT-1527).
 * Each scenario is the end-state a page renders on load for ?scenario=<id>.
 * Keep the ids in sync with .artifacts/RHAISTRAT-1527/scenarios.json.
 */
(function (global) {
  'use strict';

  var MODELS = [
    { id: 'granite-text', label: 'granite-3.3-8b-instruct', tags: [] },
    { id: 'qwen-vl', label: 'qwen2.5-vl-7b-instruct', tags: ['image-inferencing'] },
    { id: 'omni-audio', label: 'omni-audio-chat-7b', tags: ['image-inferencing', 'audio-asr'] }
  ];

  var AI_ASSETS = [
    { id: 'whisper-large', name: 'whisper-large-v3', endpointType: 'InferenceService' },
    { id: 'granite-maas', name: 'granite-3.3-8b-instruct', endpointType: 'MaaS model' },
    { id: 'custom-gateway', name: 'openai-compatible-gateway', endpointType: 'Custom endpoint' }
  ];

  function note(variant, title, body, link) {
    return { variant: variant, title: title, body: body, link: link || null };
  }

  function assetsFlagged(flagged) {
    return AI_ASSETS.map(function (asset) {
      return Object.assign({}, asset, { asrCapable: flagged.indexOf(asset.id) !== -1 });
    });
  }

  var PAGES = {
    playground: {
      default: {
        model: 'qwen-vl', inputType: 'image', asrFlagged: [], asrAssetId: null,
        attachment: null, limitNotice: null, alert: null, sendEnabled: false, transcript: []
      },
      'text-only-model': {
        model: 'granite-text', inputType: 'text', asrFlagged: [], asrAssetId: null,
        attachment: null, limitNotice: null, alert: null, sendEnabled: false, transcript: []
      },
      'audio-no-asr-asset': {
        model: 'omni-audio', inputType: 'audio', asrFlagged: [], asrAssetId: null,
        attachment: null, limitNotice: null,
        alert: note('warning', 'No transcription model registered',
          'Register an ASR-capable model as an AI Asset to send audio. Text and image input still work.',
          { href: 'ai-asset-endpoints.html', text: 'Open AI Asset Endpoints' }),
        sendEnabled: false, transcript: []
      },
      'audio-ready': {
        model: 'omni-audio', inputType: 'audio', asrFlagged: ['whisper-large'], asrAssetId: 'whisper-large',
        attachment: { name: 'standup-note.wav', kind: 'audio', size: '412 KB', status: 'Ready to transcribe' },
        limitNotice: null, alert: null, sendEnabled: true, transcript: []
      },
      'image-limit-reached': {
        model: 'qwen-vl', inputType: 'image', asrFlagged: [], asrAssetId: null,
        attachment: null,
        limitNotice: note('info', 'One image per conversation',
          'This conversation already has an image. Start a new conversation to attach another.'),
        alert: null, sendEnabled: false,
        transcript: [
          { role: 'user', text: 'Describe the trend in this chart.', image: 'sales-chart.png' },
          { role: 'assistant', text: 'Quarterly revenue rises in each quarter, with the steepest gain in Q3.' }
        ]
      },
      'file-too-large': {
        model: 'qwen-vl', inputType: 'image', asrFlagged: [], asrAssetId: null,
        attachment: null, limitNotice: null,
        alert: note('danger', 'File too large',
          'scan-report.png is 14.2 MB. The limit is 10 MB. No upload was sent.'),
        sendEnabled: false, transcript: []
      },
      'asr-failed': {
        model: 'omni-audio', inputType: 'audio', asrFlagged: ['whisper-large'], asrAssetId: 'whisper-large',
        attachment: { name: 'standup-note.mp3', kind: 'audio', size: '1.1 MB', status: 'Transcription failed' },
        limitNotice: null,
        alert: note('danger', 'Transcription failed',
          'whisper-large-v3 is unreachable. The model was not called.'),
        sendEnabled: false, transcript: []
      }
    },
    aiAssets: {
      default: {
        status: 'table', flagged: ['whisper-large'], banner: null
      },
      'no-asr-flag': {
        status: 'table', flagged: [],
        banner: note('warning', 'No ASR AI Asset',
          'No AI Asset is flagged as ASR / transcription. Playground audio input stays blocked until one is.')
      },
      empty: {
        status: 'empty', flagged: [], banner: null
      },
      'load-error': {
        status: 'error', flagged: [],
        banner: note('danger', 'Could not load AI Asset endpoints', 'Check your connection and try again.')
      }
    }
  };

  function scenarioId() {
    if (global.UxdScenario && typeof global.UxdScenario.get === 'function') {
      return global.UxdScenario.get();
    }
    return new URLSearchParams(global.location.search).get('scenario') || 'default';
  }

  function pickScenario(catalog, id) {
    var entry = Object.prototype.hasOwnProperty.call(catalog, id) ? catalog[id] : catalog.default;
    return JSON.parse(JSON.stringify(entry));
  }

  function modelById(id) {
    return MODELS.filter(function (m) { return m.id === id; })[0] || MODELS[0];
  }

  function supports(model, modality) {
    var tag = modality === 'image' ? 'image-inferencing' : 'audio-asr';
    return model.tags.indexOf(tag) !== -1;
  }

  function alertHtml(n) {
    if (!n) return '';
    var link = n.link
      ? ' <a class="pf-v6-c-button pf-m-link pf-m-inline" href="' + n.link.href + '">' + n.link.text + '</a>'
      : '';
    return '<div class="pf-v6-c-alert pf-m-inline pf-m-' + n.variant + '" aria-live="polite">' +
      '<div class="pf-v6-c-alert__title">' + n.title + '</div>' +
      '<div class="pf-v6-c-alert__description"><p>' + n.body + link + '</p></div></div>';
  }

  global.UxdMocks = {
    models: MODELS,
    pages: PAGES,
    note: note,
    scenarioId: scenarioId,
    pickScenario: pickScenario,
    modelById: modelById,
    supports: supports,
    assetsFlagged: assetsFlagged,
    alertHtml: alertHtml
  };
})(window);
