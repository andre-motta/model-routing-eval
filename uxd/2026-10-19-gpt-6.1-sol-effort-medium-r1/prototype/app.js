/* Local prototype only. File upload, transcription, and inference are simulated. */
'use strict';
const page = document.body.dataset.page;
const scenarioIds = page === 'assets' ? ['default','empty','load-error'] : ['default','image-result','audio-result','no-asr','transcribing','transcription-error','silent-audio','text-only'];
const requested = window.UxdScenario?.get() || new URLSearchParams(location.search).get('scenario') || 'default';
const scenario = scenarioIds.includes(requested) ? requested : 'default';
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const defaults = [{id:'vision',name:'Qwen2.5-VL',url:'https://vision.example.test/v1',asr:false},{id:'whisper',name:'Whisper large-v3',url:'https://whisper.example.test/v1',asr:true}];
let assets;
try { assets = JSON.parse(sessionStorage.getItem('uxd-assets')) || defaults; } catch { assets = defaults; }
if (page === 'assets' && scenario === 'empty') assets = [];
if (page === 'playground' && scenario === 'no-asr') assets = assets.filter(a => !a.asr);
const saveAssets = () => sessionStorage.setItem('uxd-assets',JSON.stringify(assets));
const models = {
  multimodal:{name:'Qwen2.5-VL · multimodal demo',image:true,audio:true,tags:['Text','Image','Audio input']},
  vision:{name:'Gemma 3 · vision demo',image:true,audio:false,tags:['Text','Image']},
  text:{name:'Llama 3.3 · text only',image:false,audio:false,tags:['Text']},
  unknown:{name:'Custom endpoint · tags unavailable',image:true,audio:true,tags:['Capabilities unavailable']}
};
const state = {model:scenario === 'text-only' ? 'text':'multimodal',attachment:null,used:false,busy:false,mode:'text',asr:'',messages:[],error:'',progress:'',generation:0};
const sampleImage = '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="240" viewBox="0 0 480 240"><rect width="480" height="240" fill="#eff5fa"/><text x="28" y="36" font-size="18" font-family="sans-serif" fill="#151515">Quarterly revenue · sample chart</text><path d="M45 65V195H440" stroke="#6a6e73" fill="none"/><g fill="#0066cc"><rect x="75" y="135" width="58" height="60"/><rect x="175" y="110" width="58" height="85"/><rect x="275" y="80" width="58" height="115"/><rect x="375" y="58" width="40" height="137"/></g><g fill="#3c3f42" font-size="13" font-family="sans-serif"><text x="88" y="218">Q1</text><text x="188" y="218">Q2</text><text x="288" y="218">Q3</text><text x="380" y="218">Q4</text></g></svg>';
const imageUrl = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(sampleImage);
const imageFile = () => ({name:'quarterly-revenue.png',size:243712,type:'image/png',kind:'image',url:imageUrl,id:'mock-image-01'});
const audioFile = () => ({name:'customer-feedback.wav',size:782144,type:'audio/wav',kind:'audio',url:'sample-audio.wav',id:'mock-audio-01'});
const imageAnswer = 'Revenue increases each quarter. Q4 is the strongest quarter, at a little over twice the Q1 level. This sample chart suggests consistent growth throughout the year.';
const audioAnswer = 'The customer is asking for clearer onboarding instructions and faster setup. Suggested next steps: simplify the quick-start guide and add an example project.';
function shell(){
  $('#app').innerHTML = `<header><div class="brand"><span class="brand-mark" aria-hidden="true"></span><div><small>RED HAT</small><strong>OpenShift AI</strong></div></div><div class="header-meta"><span>Gen AI Studio</span><span class="avatar">JD</span></div></header><div class="layout"><aside><div class="nav-label">Gen AI Studio</div><nav aria-label="Main navigation"><a href="index.html" class="${page==='playground'?'active':''}" ${page==='playground'?'aria-current="page"':''}>Playground</a><a href="ai-assets.html" class="${page==='assets'?'active':''}" ${page==='assets'?'aria-current="page"':''}>AI Asset Endpoints</a></nav><div class="nav-caption">Project<br><strong>Multimodal exploration</strong></div></aside><main id="main"><div class="breadcrumb">Gen AI Studio / ${page==='assets'?'AI Asset Endpoints':'Playground'}</div><div class="page-heading"><h1>${page==='assets'?'AI Asset Endpoints':'Playground'}</h1>${page==='playground'?'<button class="btn" id="new-chat" data-ouia-component-id="new-chat">New chat</button>':''}</div><p class="subtitle">${page==='assets'?'Connect your models and choose which endpoints can transcribe audio.':'Explore model responses with text, an image, or an audio file.'}</p><div id="content"></div><p class="page-note">Interactive prototype · Sample data and simulated responses · Chats are not saved.</p></main></div>`;
}
function notice(text,type='error'){return text?`<div class="notice ${type}" role="${type==='error'?'alert':'status'}">${text}</div>`:'';}
function playground(){
  $('#content').innerHTML = `<div class="workspace"><section class="card chat" aria-label="Conversation"><div class="chat-top"><strong>New conversation</strong><span class="tag gray">Text responses</span></div><div id="transcript" class="transcript" role="log" aria-label="Chat transcript" aria-live="polite"></div><form id="composer" class="composer"><div id="modality-region" role="region" aria-label="Input controls"></div><div id="feedback"></div><div id="attachment"></div><label for="prompt" class="field"><span>Message</span></label><textarea id="prompt" data-ouia-component-id="prompt" placeholder="Ask a question or describe what you want to explore…" aria-describedby="limit-hint"></textarea><div class="composer-footer"><span id="limit-hint" class="hint">One image or audio file per conversation. Text follow-ups are welcome.</span><button class="btn primary" id="send" data-ouia-component-id="send" type="submit">Send</button></div></form></section><section class="card settings" aria-label="Model configuration"><div><h2>Configuration</h2><label class="field"><span>Model</span><select id="model" data-ouia-component-id="model">${Object.entries(models).map(([id,m])=>`<option value="${id}">${m.name}</option>`).join('')}</select></label><div id="capabilities"></div></div><hr><div><h3>System instructions</h3><label class="field"><span class="muted">Optional</span><textarea id="system" placeholder="You are a helpful assistant."></textarea></label><p class="muted">Model responses are shown as text. Audio files are transcribed before the model responds.</p><a href="ai-assets.html">Manage AI Asset Endpoints</a></div></section></div>`;
  $('#model').value = state.model;
  $('#model').onchange = e => {state.model=e.target.value; if(state.attachment && !models[state.model][state.attachment.kind]){state.error='This model does not support the attached input. Choose a compatible model or remove the file.';} else state.error=''; renderControls();};
  $('#new-chat').onclick = resetChat;
  $('#composer').onsubmit = e => {e.preventDefault();send();};
  if(['image-result','audio-result'].includes(scenario)){
    const image = scenario==='image-result'; const file=image?imageFile():audioFile();
    state.messages=[{role:'user',text:image?'What does this chart tell us?':'Summarize the customer feedback.',file,transcription:image?'':'The setup was confusing. Please add clearer onboarding instructions and an example project.'},{role:'assistant',text:image?imageAnswer:audioAnswer}];state.used=true;state.mode=image?'image':'audio';
  }
  if(['transcribing','transcription-error','silent-audio'].includes(scenario)){
    state.mode='audio';state.attachment=audioFile();state.asr='whisper';
    if(scenario==='transcribing'){state.busy=true;state.progress='Transcribing audio…';}else if(scenario==='silent-audio') state.error='No speech was detected in this audio file. Your message has not been sent to the response model. Remove the file and upload audio containing speech.';else state.error='Transcription failed. Whisper large-v3 is unreachable. Your message has not been sent to the response model. Retry or choose another audio model.';
  }
  if(scenario==='no-asr') state.mode='audio';
  renderTranscript();renderControls();
}
function renderTranscript(){
  $('#transcript').innerHTML = state.messages.length ? state.messages.map(m=>`<article class="message ${m.role}"><div class="icon" aria-hidden="true">${m.role==='user'?'JD':'AI'}</div><div class="message-content"><strong>${m.role==='user'?'You':esc(models[state.model].name.split(' · ')[0])}</strong>${m.file?fileView(m.file):''}<p>${esc(m.text)}</p>${m.transcription?`<details open><summary>Audio transcription</summary><p>${esc(m.transcription)}</p></details>`:''}</div></article>`).join('') : `<div class="empty"><div class="orb" aria-hidden="true">✧</div><h2>Start with a question.<br>Add a new perspective.</h2><p>Explore an image or turn an audio file into insights, all in one conversation.</p><div class="examples"><button type="button" id="example-image" data-ouia-component-id="example-image">Explore a sample image</button><button type="button" id="example-audio" data-ouia-component-id="example-audio">Try sample audio</button></div></div>`;
  if($('#example-image')) $('#example-image').onclick = ()=>attachSample('image');
  if($('#example-audio')) $('#example-audio').onclick = ()=>attachSample('audio');
}
function fileView(f){return `<div class="attachment-name"><span class="tag gray">${f.kind==='image'?'Image':'Audio'}</span> ${esc(f.name)} <span class="muted">${(f.size/1024).toFixed(0)} KB</span></div>${f.kind==='image'?`<img class="preview" src="${esc(f.url)}" alt="${f.url===imageUrl?'Sample quarterly revenue chart showing growth from Q1 to Q4':esc(f.name)}">`:`<audio controls src="${esc(f.url)}" aria-label="Uploaded audio: ${esc(f.name)}"></audio>`}`;}
function renderControls(){
  const m = models[state.model]; const asrs=assets.filter(a=>a.asr);
  if(!asrs.some(a=>a.id===state.asr))state.asr=asrs[0]?.id||'';
  if(!m[state.mode] && state.mode!=='text')state.mode='text';
  $('#capabilities').innerHTML=m.tags.map(t=>`<span class="tag ${state.model==='unknown'?'gray':'green'}">${t}</span>`).join('');
  $('#modality-region').innerHTML=`<div class="composer-tools"><span class="muted">Add input</span>${m.image?'<button type="button" class="btn subtle" id="add-image" data-ouia-component-id="add-image">▧ Image</button>':''}${m.audio?'<button type="button" class="btn subtle" id="add-audio" data-ouia-component-id="add-audio">♫ Audio</button>':''}<span class="tag gray">Text${m.image?' + image':''}${m.audio?' / audio':''}</span></div>${m.image||m.audio?`<p class="hint">${m.image?'JPG, PNG':''}${m.image&&m.audio?' · ':''}${m.audio?'WAV, MP3':''} · Up to 10 MB per file</p>`:''}${m.image?'<input hidden id="image-input" type="file" accept="image/jpeg,image/png" aria-label="Upload image">':''}${m.audio?'<input hidden id="audio-input" type="file" accept="audio/wav,audio/x-wav,audio/mpeg" aria-label="Upload audio">':''}${m.audio&&state.mode==='audio'?`<label class="field"><span>Audio transcription model</span><select id="asr-model" data-ouia-component-id="asr-model" ${!asrs.length?'disabled':''}>${asrs.length?asrs.map(a=>`<option value="${esc(a.id)}">${esc(a.name)}</option>`).join(''):'<option>No transcription models registered</option>'}</select><small>Only AI Asset Endpoints marked for audio transcription are listed.</small></label>${!asrs.length?notice('No audio transcription model is registered. Register an ASR-capable endpoint to send audio. <a href="ai-assets.html?scenario=empty" data-ouia-component-id="register-asr-link">Register a transcription model</a>.','warning'):''}`:''}${state.model==='unknown'?notice('Capability information is unavailable for this endpoint. Unsupported input will return an error when you send.','warning'):''}${state.used?notice('This conversation already contains an image or audio file. You can send text follow-ups, or start a new chat to attach another file.','warning'):''}`;
  if($('#asr-model')){$('#asr-model').value=state.asr;$('#asr-model').onchange=e=>state.asr=e.target.value;}
  for(const kind of ['image','audio'])if($(`#add-${kind}`)){
    $(`#add-${kind}`).disabled=state.busy;
    $(`#add-${kind}`).onclick=()=>{if(state.used||state.attachment){state.error='Only one image or audio file is allowed per conversation. Remove the pending file or start a new chat.';renderFeedback();return;}state.mode=kind;renderControls();$(`#${kind}-input`).click();};
    $(`#${kind}-input`).onchange=e=>{if(e.target.files[0])attachFile(e.target.files[0],kind);};
  }
  renderAttachment();renderFeedback();
}
function renderFeedback(){
  $('#feedback').innerHTML=notice(esc(state.error))+(state.busy?notice(`<span class="spinner" aria-hidden="true"></span><strong>${esc(state.progress)}</strong>${scenario==='transcribing'?'Scenario preview. Select Default in the Prototype Bar to try the full flow.':'Please keep this conversation open.'}`,'info'):'');
  $('#model').disabled=state.busy;
  $('#send').disabled=state.busy || (state.mode==='audio'&&!state.asr);
  $('#prompt').disabled=state.busy;
}
function renderAttachment(){
  $('#attachment').innerHTML=state.attachment?`<div class="attachment"><div>${fileView(state.attachment)}<span class="status-line">${state.busy?esc(state.progress):'Ready to send'}</span></div><button type="button" class="btn link" id="remove-file" aria-label="Remove attachment" ${state.busy?'disabled':''}>Remove</button></div>`:'';
  if($('#remove-file'))$('#remove-file').onclick=()=>{releaseAttachment();state.error='';renderControls();};
}
function releaseAttachment(){if(state.attachment?.url?.startsWith('blob:'))URL.revokeObjectURL(state.attachment.url);state.attachment=null;}
function validateFile(file,kind){
  if(state.used||state.attachment)return 'Only one image or audio file is allowed per conversation. Remove the pending file or start a new chat.';
  if(!models[state.model][kind])return 'Select a model that supports this input type.';
  if(!file.size)return 'This file is empty. Choose a file larger than 0 bytes.';
  if(file.size>10*1024*1024)return 'This file exceeds the 10 MB limit. Choose a smaller file.';
  if(!(kind==='image'?['image/jpeg','image/png']:['audio/wav','audio/x-wav','audio/mpeg']).includes(file.type))return 'Unsupported file type. Use JPG or PNG for images, or WAV or MP3 for audio. PDF files belong in Upload files.';
  return '';
}
async function attachFile(file,kind){
  state.error=validateFile(file,kind);if(state.error){renderFeedback();return;}
  state.mode=kind;state.busy=true;state.progress='Uploading file…';renderControls();const generation=state.generation;
  await new Promise(r=>setTimeout(r,650));if(generation!==state.generation)return;
  state.attachment={name:file.name,size:file.size,type:file.type,kind,url:URL.createObjectURL(file),id:'mock-file-'+Date.now()};state.busy=false;renderControls();
}
function attachSample(kind){
  const file=kind==='image'?imageFile():audioFile();state.error=validateFile(file,kind);if(state.error){renderFeedback();return;}
  state.mode=kind;state.attachment=file;$('#prompt').value=kind==='image'?'What does this chart tell us?':'Summarize the customer feedback.';renderControls();$('#prompt').focus();
}
async function send(){
  if(state.busy)return;
  const text=$('#prompt').value.trim(),file=state.attachment;
  if(!text&&!file){state.error='Enter a message or attach a file to continue.';renderFeedback();return;}
  if(file&&!models[state.model][file.kind]){state.error='This model does not support the attached file. Select a compatible model or remove the file.';renderFeedback();return;}
  if(file?.kind==='audio'&&!state.asr){state.error='Register and select an audio transcription model before sending audio.';renderFeedback();return;}
  if(file&&state.model==='unknown'){state.error='The endpoint rejected this input type. Its capabilities are unavailable. Choose a model labeled Image or Audio input, or send text only.';renderFeedback();return;}
  state.error='';state.busy=true;state.progress=file?.kind==='audio'?'Transcribing audio…':'Generating response…';renderControls();const generation=state.generation;
  await new Promise(r=>setTimeout(r,900));if(generation!==state.generation)return;
  if(file?.kind==='audio'&&scenario==='silent-audio'){state.busy=false;state.error='No speech was detected in this audio file. Your message has not been sent to the response model. Remove the file and upload audio containing speech.';renderControls();return;}
  if(file?.kind==='audio'&&scenario==='transcription-error'){state.busy=false;state.error='Transcription failed. Whisper large-v3 is unreachable. Your message has not been sent to the response model. Choose another audio model or start a new chat.';renderControls();return;}
  const transcription=file?.kind==='audio'?'The setup was confusing. Please add clearer onboarding instructions and an example project.':'';
  if(file?.kind==='audio'){state.progress='Generating response from transcription…';renderFeedback();await new Promise(r=>setTimeout(r,700));if(generation!==state.generation)return;}
  state.messages.push({role:'user',text:text||'Analyze this file.',file,transcription},{role:'assistant',text:file?.kind==='image'?imageAnswer:file?.kind==='audio'?audioAnswer:'This is a simulated text response. I can help explore your question, summarize the conversation, or suggest a next step.'});
  if(file)state.used=true;state.attachment=null;state.busy=false;$('#prompt').value='';renderTranscript();renderControls();$('#transcript').scrollTop=$('#transcript').scrollHeight;
}
function resetChat(){state.generation++;releaseAttachment();state.messages=[];state.used=false;state.busy=false;state.error='';state.mode='text';$('#prompt').value='';renderTranscript();renderControls();$('#prompt').focus();}
function assetsPage(){
  $('#content').innerHTML=`<div id="asset-feedback"></div><section class="card table-card"><div class="table-toolbar"><div><h2>Registered endpoints</h2><span class="muted">${assets.length} endpoints in this project</span></div><button class="btn primary" id="register" data-ouia-component-id="register-endpoint">Register endpoint</button></div><div id="asset-list"></div></section><div class="notice"><strong>Bring your own audio transcription model</strong>Deploy a transcription-capable model, then register its endpoint and select Audio transcription (ASR). It will appear in the Playground audio model menu. <a href="index.html">Open Playground</a></div><dialog id="register-dialog" aria-labelledby="dialog-title"><form id="register-form"><h2 id="dialog-title">Register AI Asset Endpoint</h2><p class="muted">Connect an existing model endpoint in your project.</p><label class="field"><span>Endpoint name</span><input id="endpoint-name" data-ouia-component-id="endpoint-name" required placeholder="e.g. Whisper large-v3"></label><label class="field"><span>Endpoint URL</span><input type="url" id="endpoint-url" required placeholder="https://model.example.test/v1"></label><label class="checkbox"><input id="endpoint-asr" data-ouia-component-id="endpoint-asr" type="checkbox"><span>Audio transcription (ASR)<small>This endpoint supports transcription of audio files and will be listed in Playground.</small></span></label><div class="dialog-actions"><button class="btn primary" type="submit" data-ouia-component-id="save-endpoint">Register</button><button class="btn subtle" type="button" id="cancel-register">Cancel</button></div></form></dialog>`;
  const list=$('#asset-list');
  if(scenario==='load-error'){list.innerHTML=notice('<strong>Unable to load endpoints</strong>Check your connection and try again. <button class="btn" id="retry-assets">Retry</button>');$('#retry-assets').onclick=()=>location.href='ai-assets.html';}
  else if(!assets.length)list.innerHTML='<div class="empty"><div class="orb" aria-hidden="true">+</div><h2>No endpoints registered</h2><p>Register your first endpoint. For audio input, mark a transcription model as ASR-capable.</p></div>';
  else list.innerHTML=`<div class="table-scroll"><table><caption class="muted" style="text-align:left;padding-bottom:12px">AI Asset Endpoints available to this project</caption><thead><tr><th scope="col">Name</th><th scope="col">Capabilities</th><th scope="col">Status</th><th scope="col">Audio transcription</th></tr></thead><tbody>${assets.map(a=>`<tr><td><strong>${esc(a.name)}</strong><small>${esc(a.url)}</small></td><td><span class="tag ${a.asr?'':'gray'}">${a.asr?'Audio transcription (ASR)':'Model inference'}</span></td><td><span class="tag green">Available</span></td><td><label><input type="checkbox" data-asset="${esc(a.id)}" ${a.asr?'checked':''} aria-label="Mark ${esc(a.name)} as audio transcription capable"> ASR-capable</label></td></tr>`).join('')}</tbody></table></div>`;
  $('#register').onclick=()=>$('#register-dialog').showModal();$('#cancel-register').onclick=()=>$('#register-dialog').close();
  document.querySelectorAll('[data-asset]').forEach(el=>el.onchange=()=>{const a=assets.find(a=>a.id===el.dataset.asset);a.asr=el.checked;saveAssets();assetsPage();$('#asset-feedback').innerHTML=notice('Endpoint capability updated. The Playground audio model menu now reflects this change.','success');});
  $('#register-form').onsubmit=e=>{e.preventDefault();const asr=$('#endpoint-asr').checked;assets.push({id:'endpoint-'+Date.now(),name:$('#endpoint-name').value.trim(),url:$('#endpoint-url').value.trim(),asr});saveAssets();$('#register-dialog').close();assetsPage();$('#asset-feedback').innerHTML=notice(`Endpoint registered.${asr?' It is now available as an audio transcription model.':''} <a href="index.html">Return to Playground</a>.`,'success');$('#register').focus();};
}
shell();if(page==='assets')assetsPage();else playground();
