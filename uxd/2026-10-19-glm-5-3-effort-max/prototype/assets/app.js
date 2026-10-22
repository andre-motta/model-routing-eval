"use strict";

const scenarioFromUrl = new URLSearchParams(window.location.search).get("scenario") || "default";
const activeScenario = window.UxdScenario && window.UxdScenario.get ? window.UxdScenario.get() : scenarioFromUrl;

const models = [
  { id: "qwen3-omni", name: "Qwen3 Omni", capabilities: ["image-inferencing", "audio-asr"] },
  { id: "qwen25-vl", name: "Qwen2.5-VL", capabilities: ["image-inferencing"] },
  { id: "granite-audio", name: "Granite Audio", capabilities: ["audio-asr"] },
  { id: "granite-text", name: "Granite 3.3 Text", capabilities: [] }
];

const playgroundStates = {
  default: {
    model: models[0],
    asr: "Whisper Production",
    messages: [],
    alert: null
  },
  "image-complete": {
    model: models[1],
    asr: null,
    messages: [
      { role: "user", title: "Image prompt", body: "Identify the safety issue in this equipment photo.", media: "image" },
      { role: "model", title: "Vision response", body: "The extension cable is frayed near the connector and should be removed from service.", id: "image-response-message" }
    ],
    alert: null
  },
  "audio-transcribed": {
    model: models[0],
    asr: "Whisper Production",
    messages: [
      { role: "user", title: "Audio prompt", body: "Summarize the recorded incident report.", media: "audio", transcript: "The coolant pump leaked during the overnight run and maintenance replaced the hose." },
      { role: "model", title: "Model response", body: "The overnight incident involved a coolant pump leak. Maintenance replaced the hose; no production impact was reported.", id: "audio-response-message" }
    ],
    alert: null
  },
  "text-only-model": {
    model: models[3],
    asr: null,
    messages: [
      { role: "user", title: "Text prompt", body: "Draft a one-line incident summary." },
      { role: "model", title: "Text response", body: "Coolant pump leaked overnight; maintenance replaced the hose." }
    ],
    alert: null
  },
  "no-asr-asset": {
    model: models[2],
    asr: null,
    messages: [],
    alert: { type: "warning", title: "No ASR-capable AI Asset registered", body: "Register a transcription model as an AI Asset before submitting audio." }
  },
  "upload-too-large": {
    model: models[1],
    asr: null,
    messages: [],
    alert: { type: "error", title: "File exceeds 10 MB limit", body: "equipment-inspection.tiff is 18.4 MB. Choose a JPG or PNG smaller than 10 MB. No upload request was sent." }
  },
  "one-file-limit": {
    model: models[0],
    asr: "Whisper Production",
    messages: [
      { role: "user", title: "First media prompt", body: "Describe the equipment.", media: "image" },
      { role: "model", title: "Vision response", body: "The image shows a portable generator with a fuel cap and control panel." }
    ],
    alert: { type: "warning", title: "One media file per conversation", body: "This conversation already contains one image or audio file. Start a new conversation to attach different media." }
  },
  "transcription-error": {
    model: models[0],
    asr: "Whisper Production",
    messages: [
      { role: "user", title: "Audio prompt", body: "Summarize the recording.", media: "audio" }
    ],
    alert: { type: "error", title: "ASR endpoint unavailable", body: "The selected AI Asset returned 503. No transcription or model response was generated." }
  }
};

const assetStates = {
  default: {
    assets: [
      { name: "Whisper Production", type: "OpenAI-compatible", capabilities: ["audio-asr"], status: "Ready", updated: "Oct 18, 2026" },
      { name: "Granite Inference", type: "InferenceService", capabilities: ["text"], status: "Ready", updated: "Oct 17, 2026" },
      { name: "Custom Vision", type: "Custom endpoint", capabilities: ["image-inferencing"], status: "Ready", updated: "Oct 16, 2026" }
    ],
    alert: null
  },
  empty: {
    assets: [],
    alert: null
  },
  "asr-registered": {
    assets: [
      { name: "Whisper Production", type: "OpenAI-compatible", capabilities: ["audio-asr"], status: "Ready", updated: "Just now", saved: true },
      { name: "Granite Inference", type: "InferenceService", capabilities: ["text"], status: "Ready", updated: "Oct 17, 2026" }
    ],
    alert: { type: "success", title: "AI Asset registered", body: "Whisper Production is now available in the Playground ASR model dropdown." }
  },
  "load-error": {
    assets: [],
    alert: { type: "error", title: "Unable to load AI Asset Endpoints", body: "The Gen AI Studio BFF returned 503. Retry after the endpoint service recovers." }
  },
  "capability-metadata-pending": {
    assets: [
      { name: "Vision Preview", type: "InferenceService", capabilities: [], status: "Metadata pending", updated: "Oct 18, 2026" },
      { name: "Audio Preview", type: "InferenceService", capabilities: [], status: "Metadata pending", updated: "Oct 18, 2026" }
    ],
    alert: { type: "warning", title: "Capability metadata unavailable", body: "The model catalog does not include supported modalities. The static YAML fallback will be used until the catalog ships." }
  }
};

function scenarioName(id) {
  return id === "default" ? "default" : id;
}

function alertMarkup(alert) {
  if (!alert) return "";
  const variant = alert.type === "error" ? "" : `uxd-${alert.type}`;
  return `<div class="uxd-inline-alert ${variant}" role="alert">
    <strong>${alert.title}</strong><span>${alert.body}</span></div>`;
}

function mediaMarkup(message) {
  if (message.media === "image") {
    return `<div class="uxd-media"><div class="uxd-image-preview" role="img" aria-label="Uploaded JPG image of equipment">equipment-photo.jpg</div><small>2.1 MB · JPG · stored with BFF file ID</small></div>`;
  }
  if (message.media === "audio") {
    return `<div class="uxd-media"><div class="uxd-audio">🎙️ incident-report.wav <audio controls src="#"></audio></div><small>1.4 MB · WAV · stored with BFF file ID</small>${message.transcript ? `<div><strong>Transcript:</strong> ${message.transcript}</div>` : ""}</div>`;
  }
  return "";
}

function renderPlayground() {
  const state = playgroundStates[activeScenario] || playgroundStates.default;
  document.querySelector("#scenario-label").textContent = `Scenario: ${scenarioName(activeScenario)}`;
  document.querySelector("#model-select").innerHTML = models.map((model) => `<option value="${model.id}" ${model.id === state.model.id ? "selected" : ""}>${model.name}</option>`).join("");
  const asrSelect = document.querySelector("#asr-model-select");
  const showAsr = state.model.capabilities.includes("audio-asr");
  asrSelect.closest(".pf-v6-c-form__group").hidden = !showAsr;
  asrSelect.innerHTML = state.asr ? `<option>${state.asr}</option>` : `<option value="">No ASR AI Assets registered</option>`;

  document.querySelector("#capability-badges").innerHTML = state.model.capabilities.length
    ? state.model.capabilities.map((capability) => `<span class="pf-v6-c-label pf-m-green">${capability}</span>`).join("")
    : `<span class="pf-v6-c-label pf-m-gray">text only</span>`;

  document.querySelector("#alert-slot").innerHTML = alertMarkup(state.alert);
  document.querySelector("#transcript").innerHTML = state.messages.map((message) => `
    <article class="uxd-message ${message.role === "user" ? "uxd-message-user" : "uxd-message-model"}" ${message.id ? `data-ouia-component-id="${message.id}"` : ""}>
      <h3>${message.title}</h3>${mediaMarkup(message)}<p>${message.body}</p>
    </article>`).join("") || `<div class="uxd-empty"><strong>No messages yet</strong><span>Attach an image or audio file, or enter a text prompt.</span></div>`;

  const controls = document.querySelector("#input-controls");
  const showImage = state.model.capabilities.includes("image-inferencing");
  const showAudio = state.model.capabilities.includes("audio-asr");
  controls.innerHTML = "";
  if (showImage) {
    controls.insertAdjacentHTML("beforeend", `<div class="uxd-input-row">
      <strong>Image input</strong><small>JPG or PNG · 10 MB maximum · one media file per conversation</small>
      <button class="pf-v6-c-button pf-m-secondary" type="button" data-ouia-component-id="attach-sample-image">Attach sample image</button>
    </div>`);
  }
  if (showAudio) {
    controls.insertAdjacentHTML("beforeend", `<div class="uxd-input-row">
      <strong>Audio input</strong><small>WAV or MP3 · 10 MB maximum · file upload only</small>
      <button class="pf-v6-c-button pf-m-secondary" type="button" data-ouia-component-id="attach-sample-audio">Attach sample audio</button>
    </div>`);
  }
  if (!showImage && !showAudio) {
    controls.insertAdjacentHTML("beforeend", `<p class="uxd-scenario-note">This model supports text input only, so image and audio controls are not rendered.</p>`);
  }

  controls.querySelector("[data-ouia-component-id=\"attach-sample-image\"]")?.addEventListener("click", () => {
    window.location.search = "?scenario=image-complete";
  });
  controls.querySelector("[data-ouia-component-id=\"attach-sample-audio\"]")?.addEventListener("click", () => {
    window.location.search = "?scenario=audio-transcribed";
  });
}

function assetRow(asset) {
  return `<tr ${asset.saved ? "data-ouia-component-id=\"asr-asset-row\"" : ""}>
    <td><strong>${asset.name}</strong></td><td>${asset.type}</td>
    <td>${asset.capabilities.length ? asset.capabilities.map((capability) => `<span class="pf-v6-c-label pf-m-blue">${capability}</span>`).join(" ") : `<span class="uxd-scenario-note">Unknown</span>`}</td>
    <td><span class="pf-v6-c-label ${asset.status === "Ready" ? "pf-m-green" : "pf-m-orange"}">${asset.status}</span></td><td>${asset.updated}</td>
  </tr>`;
}

function renderAssets() {
  const state = assetStates[activeScenario] || assetStates.default;
  document.querySelector("#scenario-label")?.remove();
  document.querySelector("#alert-slot").innerHTML = alertMarkup(state.alert);
  document.querySelector("#asset-content").innerHTML = state.assets.length
    ? `<table class="uxd-table"><thead><tr><th>Endpoint</th><th>Type</th><th>Capabilities</th><th>Status</th><th>Updated</th></tr></thead><tbody>${state.assets.map(assetRow).join("")}</tbody></table>`
    : `<div class="uxd-empty"><strong>No AI Asset Endpoints registered</strong><span>Register an OpenAI-compatible endpoint and mark it Audio/ASR capable to use it in the Playground.</span></div>`;

  const dialog = document.querySelector("#register-dialog");
  document.querySelector("[data-ouia-component-id=\"register-ai-asset\"]").addEventListener("click", () => dialog.showModal());
  document.querySelector("[data-ouia-component-id=\"cancel-ai-asset\"]").addEventListener("click", () => dialog.close());
  document.querySelector("[data-ouia-component-id=\"save-ai-asset\"]").addEventListener("click", () => {
    dialog.close();
    window.location.search = "?scenario=asr-registered";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.dataset.page === "playground") {
    renderPlayground();
  } else if (document.body.dataset.page === "ai-assets") {
    renderAssets();
  }
});
