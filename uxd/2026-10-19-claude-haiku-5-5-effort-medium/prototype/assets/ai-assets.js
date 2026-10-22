/*
 * AI Asset Endpoints page wiring for the RHAISTRAT-1527 prototype.
 * Renders the scenario end-state on load; the Edit dialog flags an asset as ASR / transcription.
 */
(function (global) {
  'use strict';

  var M = global.UxdMocks;
  var state = M.pickScenario(M.pages.aiAssets, M.scenarioId());

  var bannerContainer = document.getElementById('endpoints-banner');
  var content = document.getElementById('endpoints-content');
  var dialog = document.getElementById('asset-dialog');
  var dialogTitle = document.getElementById('asset-dialog-title');
  var asrFlag = document.getElementById('asr-flag');
  var saveButton = document.getElementById('asset-save');
  var cancelButton = document.getElementById('asset-cancel');
  var editingId = null;

  function render() {
    bannerContainer.innerHTML = M.alertHtml(state.banner);

    if (state.status === 'error') {
      content.innerHTML = '<button type="button" class="pf-v6-c-button pf-m-secondary" data-testid="retry-load">Retry</button>';
      return;
    }

    if (state.status === 'empty') {
      content.innerHTML =
        '<div class="pf-v6-c-empty-state" data-testid="empty-state">' +
        '<h2 class="pf-v6-c-empty-state__title-text">No AI Assets registered</h2>' +
        '<p>Register a model deployment as an AI Asset to use it in the Playground.</p>' +
        '<button type="button" class="pf-v6-c-button pf-m-primary" data-testid="add-asset">Add AI Asset</button>' +
        '</div>';
      return;
    }

    var rows = M.assetsFlagged(state.flagged).map(function (a) {
      return '<tr data-testid="asset-row-' + a.id + '">' +
        '<th scope="row">' + a.name + '</th>' +
        '<td>' + a.endpointType + '</td>' +
        '<td>' + (a.asrCapable ? 'ASR / transcription' : 'Chat') + '</td>' +
        '<td><button type="button" class="pf-v6-c-button pf-m-secondary pf-m-small"' +
        ' data-testid="edit-asset-' + a.id + '" data-asset-id="' + a.id + '">Edit</button></td>' +
        '</tr>';
    }).join('');

    content.innerHTML =
      '<table class="pf-v6-c-table" aria-label="AI Asset Endpoints" data-testid="endpoints-table">' +
      '<thead><tr><th scope="col">Name</th><th scope="col">Endpoint type</th>' +
      '<th scope="col">Capability</th><th scope="col"><span class="pf-v6-screen-reader">Actions</span></th></tr></thead>' +
      '<tbody>' + rows + '</tbody></table>';
  }

  function openDialog(assetId) {
    var asset = M.assetsFlagged(state.flagged).filter(function (a) { return a.id === assetId; })[0];
    if (!asset) return;
    editingId = assetId;
    dialogTitle.textContent = 'Edit ' + asset.name;
    asrFlag.checked = asset.asrCapable;
    dialog.hidden = false;
    asrFlag.focus();
  }

  function closeDialog() {
    editingId = null;
    dialog.hidden = true;
  }

  content.addEventListener('click', function (event) {
    var edit = event.target.closest('[data-asset-id]');
    if (edit) openDialog(edit.getAttribute('data-asset-id'));
  });

  saveButton.addEventListener('click', function () {
    var index = state.flagged.indexOf(editingId);
    if (asrFlag.checked && index === -1) state.flagged.push(editingId);
    if (!asrFlag.checked && index !== -1) state.flagged.splice(index, 1);
    closeDialog();
    render();
  });

  cancelButton.addEventListener('click', closeDialog);

  render();
})(window);
