/* Shared mock data + helpers for RHAISTRAT-1527 standalone prototype */
window.MM = (function () {
  var MODELS = [
    { id: 'granite-3.3-8b-instruct', name: 'granite-3.3-8b-instruct', modalities: ['text'] },
    { id: 'qwen2.5-vl-7b-instruct', name: 'qwen2.5-vl-7b-instruct', modalities: ['text', 'image'] },
    { id: 'gemma-3-12b-it', name: 'gemma-3-12b-it', modalities: ['text', 'image', 'audio'] }
  ];
  var ASSETS = [
    { name: 'whisper-large-v3', type: 'InferenceService', endpoint: 'https://whisper-large-v3.my-project.svc/v1', asr: true, status: 'Ready' },
    { name: 'granite-3.3-8b-instruct', type: 'InferenceService', endpoint: 'https://granite.my-project.svc/v1', asr: false, status: 'Ready' },
    { name: 'qwen2.5-vl-7b-instruct', type: 'InferenceService', endpoint: 'https://qwen-vl.my-project.svc/v1', asr: false, status: 'Ready' },
    { name: 'openai-whisper-1', type: 'Custom endpoint', endpoint: 'https://api.openai.com/v1', asr: true, status: 'Ready' },
    { name: 'gemma-3-12b-it', type: 'MaaS model', endpoint: 'https://maas.example.com/gemma-3/v1', asr: false, status: 'Ready' }
  ];
  function scenario() {
    return (window.UxdScenario && window.UxdScenario.get()) ||
      new URLSearchParams(location.search).get('scenario') || 'default';
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function sampleImage() {
    return 'data:image/svg+xml;utf8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="240" height="150"><rect width="240" height="150" fill="#e0f0ff"/><rect x="20" y="60" width="90" height="70" fill="#73bcf7"/><circle cx="180" cy="45" r="25" fill="#f4c145"/><polygon points="120,130 170,70 220,130" fill="#3e8635"/><text x="10" y="20" font-size="12" font-family="sans-serif">warehouse-shelf.png</text></svg>');
  }
  return { MODELS: MODELS, ASSETS: ASSETS, scenario: scenario, esc: esc, sampleImage: sampleImage, MAX_MB: 10 };
})();
