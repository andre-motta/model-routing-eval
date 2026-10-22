(function () {
  'use strict';

  var MODELS = {
    'qwen3-vl': {
      label: 'Qwen3 VL',
      capabilities: ['image-inferencing'],
      modality: 'image'
    },
    'granite-audio': {
      label: 'Granite Audio',
      capabilities: ['audio-asr'],
      modality: 'audio'
    },
    'granite-text': {
      label: 'Granite Text',
      capabilities: [],
      modality: null
    }
  };

  var ASR_ASSETS = [
    { id: 'whisper-aas', label: 'Whisper AAS' },
    { id: 'whisper-platform', label: 'Whisper Platform' }
  ];

  var SAMPLE_IMAGE =
    'data:image/svg+xml;utf8,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="360" role="img" aria-label="Warehouse image">' +
        '<rect width="560" height="360" fill="#d9e8fb" /><rect x="60" y="120" width="440" height="180" fill="#7cb0e8" />' +
        '<rect x="110" y="180" width="100" height="120" fill="#fff" /><rect x="270" y="180" width="100" height="120" fill="#fff" />' +
        '<rect x="160" y="55" width="260" height="70" fill="#e5e5e5" /><text x="150" y="45" font-family="sans-serif" font-size="24" fill="#204363">warehouse-safety.jpg</text>' +
        '<circle cx="420" cy="105" r="22" fill="#f5c518" /></svg>'
    );

  var SAMPLE_AUDIO =
    'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=';

  var state = {
    modelId: 'qwen3-vl',
    asrAssetId: 'whisper-aas',
    assets: ASR_ASSETS.slice(),
    attachment: null,
    messages: [],
    alert: null,
    prompt: ''
  };

  function scenarioId() {
    if (window.UxdScenario && typeof window.UxdScenario.get === 'function') {
      return window.UxdScenario.get();
    }
    return 'default';
  }

  function clearMessages() {
    state.messages = [];
    state.attachment = null;
    state.alert = null;
  }

  function seedScenario(id) {
    clearMessages();
    state.prompt = '';
    state.assets = ASR_ASSETS.slice();
    state.asrAssetId = 'whisper-aas';

    if (id === 'text-only-model') {
      state.modelId = 'granite-text';
    } else if (id === 'audio-no-asr') {
      state.modelId = 'granite-audio';
      state.assets = [];
      state.asrAssetId = '';
      state.alert = {
        type: 'warning',
        title: 'No ASR-capable AI Asset is registered',
        body: 'Register a transcription-capable model in AI Asset Endpoints before submitting audio.'
      };
    } else if (id === 'image-ready') {
      state.modelId = 'qwen3-vl';
      state.prompt = 'What safety issues are visible in this image?';
      state.attachment = {
        type: 'image',
        name: 'warehouse-safety.jpg',
        size: '2.1 MB',
        src: SAMPLE_IMAGE
      };
      state.messages.push(
        { role: 'user', attachment: state.attachment, text: state.prompt },
        {
          role: 'assistant',
          text: 'The forklift aisle has an open cabinet and an unmarked spill. Move the obstruction, contain the spill, and post a temporary warning before traffic resumes.'
        }
      );
    } else if (id === 'audio-ready') {
      state.modelId = 'granite-audio';
      state.prompt = 'Summarize the customer issue and next step.';
      state.attachment = {
        type: 'audio',
        name: 'customer-call.mp3',
        size: '1.4 MB',
        src: SAMPLE_AUDIO,
        transcription:
          'The cluster upgrade stalled at 60% and the dashboard shows two schedulers in a crash loop.'
      };
      state.messages.push(
        { role: 'user', attachment: state.attachment, text: state.prompt },
        {
          role: 'assistant',
          text: 'The upgrade is blocked by two crash-looping schedulers. Roll back the scheduler deployment, inspect its events and logs, then resume the upgrade after both pods stabilize.'
        }
      );
    } else if (id === 'upload-error') {
      state.modelId = 'qwen3-vl';
      state.prompt = 'Inspect this image.';
      state.alert = {
        type: 'danger',
        title: 'Image exceeds the 10 MB limit',
        body: 'warehouse-layout.png is 12.4 MB. Choose a JPG or PNG under 10 MB. No upload request was sent.'
      };
    } else if (id === 'modality-limit') {
      state.modelId = 'qwen3-vl';
      state.prompt = 'Compare the second image.';
      state.attachment = {
        type: 'image',
        name: 'warehouse-safety.jpg',
        size: '2.1 MB',
        src: SAMPLE_IMAGE
      };
      state.messages.push({
        role: 'user',
        attachment: state.attachment,
        text: 'What safety issues are visible?'
      });
      state.alert = {
        type: 'warning',
        title: 'One image or audio file per conversation history',
        body: 'This conversation already contains warehouse-safety.jpg. Start a new conversation to use a different image or audio file.'
      };
    } else {
      state.modelId = 'qwen3-vl';
    }
  }

  function capabilityBadges(model) {
    if (!model.capabilities.length) {
      return '<span class="prototype-badge prototype-badge--text">Text only</span>';
    }
    return model.capabilities
      .map(function (capability) {
        var kind = capability === 'image-inferencing' ? 'vision' : 'audio';
        return '<span class="prototype-badge prototype-badge--' + kind + '">' + capability + '</span>';
      })
      .join('');
  }

  function attachmentMarkup(attachment) {
    if (!attachment) return '';
    if (attachment.type === 'image') {
      return (
        '<figure class="prototype-message__attachment">' +
        '<img class="prototype-image-preview" src="' +
        attachment.src +
        '" alt="Uploaded ' +
        attachment.name +
        '" data-ouia-component-id="image-thumbnail" />' +
        '<figcaption class="prototype-hint">' +
        attachment.name +
        ' • ' +
        attachment.size +
        '</figcaption></figure>'
      );
    }
    return (
      '<figure class="prototype-message__attachment" data-ouia-component-id="audio-attachment">' +
      '<audio class="prototype-audio" controls src="' +
      attachment.src +
      '" aria-label="Uploaded ' +
      attachment.name +
      '"></audio>' +
      '<figcaption class="prototype-hint">' +
      attachment.name +
      ' • ' +
      attachment.size +
      '</figcaption></figure>'
    );
  }

  function messageMarkup(message, index) {
    var heading = message.role === 'user' ? 'You' : 'Model response';
    var responseId = message.role === 'assistant' ? ' data-ouia-component-id="assistant-response"' : '';
    return (
      '<article class="prototype-message" data-message-index="' +
      index +
      '"' +
      responseId +
      '><div class="prototype-message__header"><strong>' +
      heading +
      '</strong></div>' +
      attachmentMarkup(message.attachment) +
      (message.attachment && message.attachment.transcription
        ? '<p><strong>ASR transcription:</strong> ' + message.attachment.transcription + '</p>'
        : '') +
      '<p>' +
      message.text +
      '</p></article>'
    );
  }

  function alertMarkup(alert) {
    if (!alert) return '';
    return (
      '<div class="pf-v6-c-alert pf-m-' +
      alert.type +
      '" role="alert" data-ouia-component-id="playground-alert">' +
      '<div class="pf-v6-c-alert__icon"><i class="fas fa-exclamation-circle" aria-hidden="true"></i></div>' +
      '<h3 class="pf-v6-c-alert__title">' +
      alert.title +
      '</h3><div class="pf-v6-c-alert__description"><p>' +
      alert.body +
      '</p></div></div>'
    );
  }

  function render() {
    var model = MODELS[state.modelId];
    var modelSelector = document.getElementById('model-selector');
    var imageControl = document.getElementById('image-upload-control');
    var audioControl = document.getElementById('audio-upload-control');
    var asrControl = document.getElementById('asr-control');
    var asrSelector = document.getElementById('asr-model-selector');
    var capabilities = document.getElementById('model-capabilities');
    var status = document.getElementById('status-region');
    var transcript = document.getElementById('transcript');
    var prompt = document.getElementById('prompt-input');

    modelSelector.value = state.modelId;
    capabilities.innerHTML = capabilityBadges(model);
    imageControl.hidden = !model.capabilities.includes('image-inferencing');
    audioControl.hidden = !model.capabilities.includes('audio-asr');
    asrControl.hidden = !model.capabilities.includes('audio-asr');
    prompt.value = state.prompt;

    if (model.capabilities.includes('audio-asr')) {
      if (!state.assets.length) {
        asrSelector.innerHTML = '<option value="">No ASR-capable AI Asset registered</option>';
        asrSelector.disabled = true;
      } else {
        asrSelector.disabled = false;
        asrSelector.innerHTML = state.assets
          .map(function (asset) {
            return '<option value="' + asset.id + '" data-ouia-component-id="option-' + asset.id + '">' + asset.label + '</option>';
          })
          .join('');
        asrSelector.value = state.asrAssetId || state.assets[0].id;
      }
    }

    status.innerHTML = alertMarkup(state.alert);
    transcript.innerHTML = state.messages.length
      ? state.messages.map(messageMarkup).join('')
      : '<div class="pf-v6-c-empty-state"><h3 class="pf-v6-c-empty-state__title">Start a conversation</h3>' +
        '<p class="pf-v6-c-empty-state__body">Select a model, add an allowed attachment, and submit your prompt.</p></div>';
  }

  function setAlert(type, title, body) {
    state.alert = { type: type, title: title, body: body };
    render();
  }

  function addAttachment(attachment, promptText) {
    if (state.attachment) {
      setAlert(
        'warning',
        'One image or audio file per conversation history',
        'This conversation already contains ' +
          state.attachment.name +
          '. Start a new conversation to use a different image or audio file.'
      );
      return;
    }

    state.attachment = attachment;
    state.messages.push({ role: 'user', attachment: attachment, text: promptText });
    state.messages.push({ role: 'assistant', text: responseFor(attachment) });
    state.alert = {
      type: 'success',
      title: attachment.type === 'image' ? 'Vision response returned' : 'Audio transcribed and response returned',
      body:
        attachment.type === 'image'
          ? 'The image was stored temporarily, encoded by the BFF, and sent through OGX Responses API.'
          : 'The audio was transcribed by ' + selectedAssetLabel() + ', then sent to OGX Responses API as text.'
    };
    render();
  }

  function responseFor(attachment) {
    if (attachment.type === 'image') {
      return 'The image shows an obstructed forklift aisle and a possible spill. Clear the obstruction, isolate the spill, and warn traffic before work resumes.';
    }
    return 'The recording describes an upgrade stalled by two schedulers in a crash loop. Roll back that deployment, review scheduler events, and resume the upgrade after stability returns.';
  }

  function selectedAssetLabel() {
    var selected = state.assets.find(function (asset) {
      return asset.id === state.asrAssetId;
    });
    return selected ? selected.label : 'the selected ASR AI Asset';
  }

  function validateFile(file, expected) {
    if (file.size === 0) {
      return 'The selected file is empty.';
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'The selected file is larger than 10 MB.';
    }
    if (expected === 'image' && !['image/jpeg', 'image/png'].includes(file.type)) {
      return 'Images must be JPG or PNG.';
    }
    if (expected === 'audio' && !['audio/wav', 'audio/mpeg', 'audio/x-mpeg', 'audio/mp3'].includes(file.type)) {
      return 'Audio must be WAV or MP3.';
    }
    return null;
  }

  function bindEvents() {
    document.getElementById('model-selector').addEventListener('change', function (event) {
      state.modelId = event.target.value;
      state.prompt = '';
      state.alert = null;
      render();
    });

    document.getElementById('asr-model-selector').addEventListener('change', function (event) {
      state.asrAssetId = event.target.value;
    });

    document.getElementById('use-sample-image').addEventListener('click', function () {
      addAttachment(
        {
          type: 'image',
          name: 'warehouse-safety.jpg',
          size: '2.1 MB',
          src: SAMPLE_IMAGE
        },
        'What safety issues are visible in this image?'
      );
    });

    document.getElementById('use-sample-audio').addEventListener('click', function () {
      if (!state.assets.length) {
        setAlert(
          'warning',
          'No ASR-capable AI Asset is registered',
          'Register a transcription model in AI Asset Endpoints before submitting audio.'
        );
        return;
      }
      addAttachment(
        {
          type: 'audio',
          name: 'customer-call.mp3',
          size: '1.4 MB',
          src: SAMPLE_AUDIO,
          transcription:
            'The cluster upgrade stalled at 60% and two schedulers are in a crash loop.'
        },
        'Summarize the customer issue and next step.'
      );
    });

    document.getElementById('image-file-input').addEventListener('change', function (event) {
      var file = event.target.files && event.target.files[0];
      if (!file) return;
      var error = validateFile(file, 'image');
      if (error) {
        setAlert('danger', 'Image validation failed', error + ' No upload request was sent.');
        return;
      }
      addAttachment(
        { type: 'image', name: file.name, size: (file.size / 1048576).toFixed(1) + ' MB', src: SAMPLE_IMAGE },
        'What is in this image?'
      );
    });

    document.getElementById('audio-file-input').addEventListener('change', function (event) {
      var file = event.target.files && event.target.files[0];
      if (!file) return;
      var error = validateFile(file, 'audio');
      if (error) {
        setAlert('danger', 'Audio validation failed', error + ' No upload request was sent.');
        return;
      }
      if (!state.assets.length) {
        setAlert('warning', 'No ASR-capable AI Asset is registered', 'Register an ASR AI Asset before submitting audio.');
        return;
      }
      addAttachment(
        {
          type: 'audio',
          name: file.name,
          size: (file.size / 1048576).toFixed(1) + ' MB',
          src: SAMPLE_AUDIO,
          transcription: 'This mocked transcription represents the selected ASR AI Asset result.'
        },
        'Summarize the audio.'
      );
    });

    document.getElementById('submit-prompt').addEventListener('click', function () {
      var promptText = document.getElementById('prompt-input').value.trim();
      var model = MODELS[state.modelId];
      if (!promptText) {
        setAlert('danger', 'Prompt required', 'Enter a prompt before submitting.');
        return;
      }
      if (model.modality === 'audio' && !state.assets.length) {
        setAlert('warning', 'Audio submission blocked', 'Register an ASR-capable AI Asset before submitting audio.');
        return;
      }
      state.messages.push({ role: 'user', text: promptText, attachment: state.attachment });
      state.messages.push({
        role: 'assistant',
        text:
          model.modality === 'image'
            ? 'Vision analysis completed for the attached image.'
            : model.modality === 'audio'
              ? 'Audio transcription and response completed.'
              : 'Text response completed.'
      });
      state.alert = {
        type: 'success',
        title: 'Response returned',
        body: 'Processing completed within the 120-second timeout.'
      };
      render();
    });

    document.getElementById('new-conversation').addEventListener('click', function () {
      seedScenario('default');
      render();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    seedScenario(scenarioId());
    bindEvents();
    render();
  });
})();
