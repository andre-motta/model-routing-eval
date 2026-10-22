/* Mock data for RHAISTRAT-1527: multimodal input in the Gen AI studio Playground.
 * Model capability tags mirror the proposed model-metadata-collection catalog
 * `supported_modalities` / tags (`image-inferencing`, `audio-asr`). */
(function (global) {
  'use strict';

  var MAX_FILE_BYTES = 10 * 1024 * 1024; // proposed 10 MB default (matches /api/v1/files/upload)

  var MODELS = [
    {
      id: 'qwen2-5-vl-7b',
      name: 'Qwen2.5-VL-7B-Instruct',
      deployment: 'InferenceService',
      tags: ['image-inferencing'],
      modalities: ['text', 'image'],
    },
    {
      id: 'qwen2-5-omni-7b',
      name: 'Qwen2.5-Omni-7B',
      deployment: 'InferenceService',
      tags: ['image-inferencing', 'audio-asr'],
      modalities: ['text', 'image', 'audio'],
    },
    {
      id: 'granite-3-3-8b',
      name: 'granite-3.3-8b-instruct',
      deployment: 'InferenceService',
      tags: [],
      modalities: ['text'],
    },
    {
      id: 'gemma-3-4b-it',
      name: 'gemma-3-4b-it',
      deployment: 'MaaS model',
      tags: ['image-inferencing'],
      modalities: ['text', 'image'],
    },
  ];

  /* AI asset endpoints. `asr: true` = flagged as a transcription (ASR) endpoint. */
  var ASSETS = [
    {
      id: 'qwen2-5-vl-7b',
      name: 'Qwen2.5-VL-7B-Instruct',
      type: 'InferenceService',
      endpoint: 'https://qwen25-vl.genai-team.svc.cluster.local/v1',
      catalogTags: ['image-inferencing'],
      asr: false,
      asrEligible: false,
    },
    {
      id: 'qwen2-5-omni-7b',
      name: 'Qwen2.5-Omni-7B',
      type: 'InferenceService',
      endpoint: 'https://qwen25-omni.genai-team.svc.cluster.local/v1',
      catalogTags: ['image-inferencing', 'audio-asr'],
      asr: false,
      asrEligible: false,
    },
    {
      id: 'granite-3-3-8b',
      name: 'granite-3.3-8b-instruct',
      type: 'InferenceService',
      endpoint: 'https://granite-33.genai-team.svc.cluster.local/v1',
      catalogTags: [],
      asr: false,
      asrEligible: false,
    },
    {
      id: 'gemma-3-4b-it',
      name: 'gemma-3-4b-it',
      type: 'MaaS model',
      endpoint: 'https://maas.apps.example.com/gemma-3-4b-it/v1',
      catalogTags: ['image-inferencing'],
      asr: false,
      asrEligible: false,
    },
    {
      id: 'whisper-large-v3',
      name: 'whisper-large-v3',
      type: 'InferenceService',
      endpoint: 'https://whisper-large-v3.genai-team.svc.cluster.local/v1',
      catalogTags: [],
      asr: true,
      asrEligible: true,
    },
    {
      id: 'openai-whisper-1',
      name: 'whisper-1 (OpenAI)',
      type: 'Custom endpoint',
      endpoint: 'https://api.openai.com/v1',
      catalogTags: [],
      asr: true,
      asrEligible: true,
    },
  ];

  var ALLOWED = {
    image: { mimes: ['image/jpeg', 'image/png'], exts: ['jpg', 'jpeg', 'png'], label: 'JPG or PNG' },
    audio: { mimes: ['audio/wav', 'audio/x-wav', 'audio/wave', 'audio/mpeg', 'audio/mp3'], exts: ['wav', 'mp3'], label: 'WAV or MP3' },
  };

  /* Mock "uploaded" image used by seeded scenarios (bar chart screenshot). */
  var SAMPLE_IMAGE_SVG =
    '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="300" viewBox="0 0 480 300">' +
    '<rect width="480" height="300" fill="#ffffff"/>' +
    '<text x="24" y="36" font-family="Red Hat Text, sans-serif" font-size="18" font-weight="600" fill="#151515">GPU utilization by quarter</text>' +
    '<line x1="48" y1="260" x2="456" y2="260" stroke="#8a8d90"/>' +
    '<line x1="48" y1="60" x2="48" y2="260" stroke="#8a8d90"/>' +
    '<rect x="80" y="170" width="60" height="90" fill="#0066cc"/>' +
    '<rect x="170" y="130" width="60" height="130" fill="#0066cc"/>' +
    '<rect x="260" y="100" width="60" height="160" fill="#0066cc"/>' +
    '<rect x="350" y="75" width="60" height="185" fill="#f0561d"/>' +
    '<g font-family="Red Hat Text, sans-serif" font-size="13" fill="#4d4d4d">' +
    '<text x="98" y="280">Q1</text><text x="188" y="280">Q2</text><text x="278" y="280">Q3</text><text x="368" y="280">Q4</text>' +
    '<text x="92" y="162">45%</text><text x="182" y="122">65%</text><text x="272" y="92">80%</text><text x="362" y="67">93%</text>' +
    '</g></svg>';
  var SAMPLE_IMAGE = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(SAMPLE_IMAGE_SVG);

  /* Generate a short WAV tone so seeded audio messages have a playable source. */
  function makeToneWavUrl(seconds, freq) {
    var rate = 8000;
    var n = Math.floor(rate * seconds);
    var buf = new ArrayBuffer(44 + n * 2);
    var v = new DataView(buf);
    function str(o, s) { for (var i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i)); }
    str(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); str(8, 'WAVE'); str(12, 'fmt ');
    v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true);
    v.setUint16(34, 16, true); str(36, 'data'); v.setUint32(40, n * 2, true);
    for (var i = 0; i < n; i++) {
      var env = Math.min(1, i / 400, (n - i) / 400);
      v.setInt16(44 + i * 2, Math.sin((2 * Math.PI * freq * i) / rate) * 6000 * env, true);
    }
    try {
      return URL.createObjectURL(new Blob([buf], { type: 'audio/wav' }));
    } catch (e) {
      return '';
    }
  }

  function formatBytes(b) {
    if (b === 0) return '0 bytes';
    if (b < 1024) return b + ' bytes';
    if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
    return (b / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function getScenario() {
    if (global.UxdScenario && typeof global.UxdScenario.get === 'function') return global.UxdScenario.get();
    try {
      return new URLSearchParams(global.location.search).get('scenario') || 'default';
    } catch (e) {
      return 'default';
    }
  }

  function escapeHtml(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  global.MM = {
    MAX_FILE_BYTES: MAX_FILE_BYTES,
    MODELS: MODELS,
    ASSETS: ASSETS,
    ALLOWED: ALLOWED,
    SAMPLE_IMAGE: SAMPLE_IMAGE,
    makeToneWavUrl: makeToneWavUrl,
    formatBytes: formatBytes,
    getScenario: getScenario,
    escapeHtml: escapeHtml,
  };
})(window);
