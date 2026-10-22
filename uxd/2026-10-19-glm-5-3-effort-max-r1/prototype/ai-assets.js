(function () {
  'use strict';

  var ASSETS = [
    {
      id: 'whisper-aas',
      name: 'Whisper AAS',
      type: 'Custom endpoint',
      endpoint: 'https://whisper-aas.example/v1/audio/transcriptions',
      asrCapable: true
    },
    {
      id: 'whisper-micro',
      name: 'Whisper Micro',
      type: 'InferenceService',
      endpoint: 'https://whisper-micro.example/v1/audio/transcriptions',
      asrCapable: false
    },
    {
      id: 'granite-text',
      name: 'Granite Text',
      type: 'Model as a Service',
      endpoint: 'https://granite-text.example/v1/responses',
      asrCapable: false
    }
  ];

  var state = {
    assets: ASSETS.map(function (asset) {
      return Object.assign({}, asset);
    }),
    alert: null,
    mode: 'table'
  };

  function scenarioId() {
    if (window.UxdScenario && typeof window.UxdScenario.get === 'function') {
      return window.UxdScenario.get();
    }
    return 'default';
  }

  function seedScenario(id) {
    state.alert = null;
    state.mode = 'table';
    state.assets = ASSETS.map(function (asset) {
      return Object.assign({}, asset);
    });

    if (id === 'empty') {
      state.assets = [];
      state.mode = 'empty';
    } else if (id === 'asr-unregistered') {
      state.assets.forEach(function (asset) {
        asset.asrCapable = false;
      });
      state.alert = {
        type: 'warning',
        title: 'No ASR-capable AI Asset',
        body: 'Mark an endpoint that exposes /v1/audio/transcriptions so it can appear in the Playground dropdown.'
      };
    } else if (id === 'save-success') {
      state.assets.forEach(function (asset) {
        if (asset.id === 'whisper-micro') asset.asrCapable = true;
      });
      state.alert = {
        type: 'success',
        title: 'ASR capability saved',
        body: 'Whisper Micro is now available in the Playground audio model dropdown.'
      };
    } else if (id === 'load-error') {
      state.mode = 'error';
      state.alert = {
        type: 'danger',
        title: 'Unable to load AI Asset Endpoints',
        body: 'The request to the AI Asset Endpoints API failed. Retry, or verify your connection and permissions.'
      };
    }
  }

  function alertMarkup(alert) {
    if (!alert) return '';
    return (
      '<div class="pf-v6-c-alert pf-m-' +
      alert.type +
      '" role="alert" data-ouia-component-id="asset-alert">' +
      '<div class="pf-v6-c-alert__icon"><i class="fas fa-exclamation-circle" aria-hidden="true"></i></div>' +
      '<h3 class="pf-v6-c-alert__title">' +
      alert.title +
      '</h3><div class="pf-v6-c-alert__description"><p>' +
      alert.body +
      '</p></div></div>'
    );
  }

  function tableMarkup() {
    if (state.mode === 'error') {
      return (
        '<div class="pf-v6-c-empty-state"><h3 class="pf-v6-c-empty-state__title">AI Assets unavailable</h3>' +
        '<p class="pf-v6-c-empty-state__body">The endpoint list could not be loaded.</p></div>'
      );
    }
    if (!state.assets.length) {
      return (
        '<div class="pf-v6-c-empty-state"><h3 class="pf-v6-c-empty-state__title">No AI Assets registered</h3>' +
        '<p class="pf-v6-c-empty-state__body">Register an OpenAI-compatible model deployment, then mark it ASR-capable if it transcribes audio.</p></div>'
      );
    }

    var rows = state.assets
      .map(function (asset) {
        var checked = asset.asrCapable ? ' checked' : '';
        return (
          '<tr data-asset-row="' +
          asset.id +
          '"><td><strong>' +
          asset.name +
          '</strong></td><td>' +
          asset.type +
          '</td><td><code>' +
          asset.endpoint +
          '</code></td><td>' +
          (asset.asrCapable
            ? '<span class="pf-v6-c-label pf-m-green"><span class="pf-v6-c-label__content">ASR-capable</span></span>'
            : '<span class="pf-v6-c-label pf-m-outline"><span class="pf-v6-c-label__content">Not ASR</span></span>') +
          '</td><td><input type="checkbox" role="switch" aria-label="Mark ' +
          asset.name +
          ' as ASR-capable" data-ouia-component-id="asr-toggle-' +
          asset.id +
          '"' +
          checked +
          ' /></td></tr>'
        );
      })
      .join('');

    return (
      '<table class="pf-v6-c-table pf-m-grid-md prototype-table" aria-label="AI Asset Endpoints">' +
      '<thead><tr><th>Asset</th><th>Type</th><th>Endpoint</th><th>Capability</th><th>ASR</th></tr></thead><tbody>' +
      rows +
      '</tbody></table>'
    );
  }

  function render() {
    document.getElementById('asset-status').innerHTML = alertMarkup(state.alert);
    document.getElementById('asset-table').innerHTML = tableMarkup();
    state.assets.forEach(function (asset) {
      var input = document.querySelector('[data-ouia-component-id="asr-toggle-' + asset.id + '"]');
      if (input) input.checked = asset.asrCapable;
    });
  }

  function bindEvents() {
    document.getElementById('asset-table').addEventListener('change', function (event) {
      var input = event.target;
      var match = input.getAttribute('data-ouia-component-id', '').match(/^asr-toggle-(.+)$/);
      if (!match) return;
      var asset = state.assets.find(function (candidate) {
        return candidate.id === match[1];
      });
      if (asset) asset.asrCapable = input.checked;
    });

    document.querySelector('[data-ouia-component-id="save-asr-capability"]').addEventListener('click', function () {
      var changed = state.assets.filter(function (asset) {
        var source = ASSETS.find(function (candidate) {
          return candidate.id === asset.id;
        });
        return source && source.asrCapable !== asset.asrCapable;
      });
      if (!changed.length) {
        state.alert = {
          type: 'info',
          title: 'No capability changes',
          body: 'Toggle one or more assets before saving.'
        };
      } else {
        state.alert = {
          type: 'success',
          title: 'ASR capability saved',
          body: changed.map(function (asset) { return asset.name; }).join(', ') + ' availability was updated.'
        };
      }
      render();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    seedScenario(scenarioId());
    bindEvents();
    render();
  });
})();
