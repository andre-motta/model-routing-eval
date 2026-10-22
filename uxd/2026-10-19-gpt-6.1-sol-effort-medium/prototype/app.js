/* Standalone UX simulation. No files or prompts are sent to a service. */
'use strict';
const $ = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const scenarioId = window.UxdScenario ? window.UxdScenario.get() : new URLSearchParams(location.search).get('scenario') || 'default';
const page = document.body.dataset.page;
const defaultAssets = [
  {name:'qwen2.5-vl',url:'https://vision.example.test/v1',asr:false},
  {name:'whisper-large-v3',url:'https://whisper.example.test/v1',asr:true}
];
function storedAssets() {
  try { return JSON.parse(localStorage.getItem('uxd-1527-assets')) || defaultAssets; } catch { return defaultAssets; }
}
function alertHtml(text, kind='error') { return `<div class="alert ${kind==='info'?'info-alert':kind==='success'?'success':''}">${text}</div>`; }
if (page === 'assets') {
  let assets = scenarioId==='empty' ? [] : storedAssets();
  let failed = scenarioId==='load-error';
  function renderAssets() {
    const matches = assets.filter((a)=>a.name.toLowerCase().includes($('search').value.toLowerCase()));
    $('count').textContent = `${matches.length} endpoints`;
    $('asset-list').innerHTML = failed ? `<div class="empty"><h2>Unable to load endpoints</h2><p>Check your connection and try again.</p><button id="retry-assets">Retry</button></div>` : !matches.length ? `<div class="empty"><h2>${assets.length?'No matching endpoints':'No AI asset endpoints yet'}</h2><p>${assets.length?'Try a different search.':'Register an existing endpoint to start experimenting.'}</p><button id="empty-register">Register endpoint</button></div>` : `<table class="pf-v6-c-table"><caption class="sr-only">Registered AI asset endpoints</caption><thead><tr><th scope="col">Name</th><th scope="col">Endpoint type</th><th scope="col">Status</th><th scope="col">Audio transcription (ASR)</th></tr></thead><tbody>${matches.map(a=>`<tr><td><strong>${escapeHtml(a.name)}</strong><span class="muted">${escapeHtml(a.url)}</span></td><td>Registered model</td><td><span class="tag">● Available</span></td><td><label><input type="checkbox" data-name="${escapeHtml(a.name)}" aria-label="Audio transcription for ${escapeHtml(a.name)}" ${a.asr?'checked':''}> ASR capable</label></td></tr>`).join('')}</tbody></table>`;
    document.querySelectorAll('[data-name]').forEach(input=>input.onchange=()=>{
      assets.find(a=>a.name===input.dataset.name).asr=input.checked; persist();
      $('asset-notice').innerHTML=alertHtml('Endpoint capability updated. The Playground audio selector now reflects this change.','success');
    });
    if ($('retry-assets')) $('retry-assets').onclick=()=>{failed=false;renderAssets();};
    if ($('empty-register')) $('empty-register').onclick=openDialog;
  }
  function persist(){try{localStorage.setItem('uxd-1527-assets',JSON.stringify(assets));}catch{ $('asset-notice').innerHTML=alertHtml('Browser storage is unavailable. Changes apply only on this page.'); }}
  function openDialog(){ $('endpoint-dialog').showModal(); $('endpoint-name').focus(); }
  $('register').onclick=openDialog;
  $('cancel-endpoint').onclick=()=> $('endpoint-dialog').close();
  $('search').oninput=renderAssets;
  $('endpoint-form').onsubmit=(event)=>{
    event.preventDefault();
    if (assets.some(a=>a.name===$('endpoint-name').value.trim())) { $('endpoint-name').setCustomValidity('Choose a unique endpoint name.'); $('endpoint-name').reportValidity(); return; }
    assets.push({name:$('endpoint-name').value.trim(),url:$('endpoint-url').value,asr:$('asr-flag').checked});
    persist(); failed=false; $('search').value=''; $('endpoint-dialog').close(); $('endpoint-form').reset();
    $('asset-notice').innerHTML=alertHtml('Endpoint registered. ASR-capable endpoints are available in the Playground audio selector.','success'); renderAssets();
  };
  $('endpoint-name').oninput=()=> $('endpoint-name').setCustomValidity('');
  renderAssets();
} else {
  const valid = ['default','image-complete','audio-complete','no-asr','text-only','upload-error','asr-error'];
  const scenario = valid.includes(scenarioId) ? scenarioId : 'default';
  const capabilities = {vision:['text','image'],audio:['text','audio'],text:['text'],unknown:['text','image','audio']};
  let attachment=null, mediaUsed=false, busy=false, epoch=0;
  // Deterministic no-ASR landing; the endpoints page links back to the registered audio workflow.
  let assets=storedAssets();
  if(scenario==='no-asr') assets=[];
  let messages=[];
  function notice(text,kind='error'){$('notice').innerHTML=text?alertHtml(escapeHtml(text),kind):'';}
  function emptyChat(){ $('transcript').innerHTML=`<div class="empty"><div class="symbol" aria-hidden="true">✧</div><h2>What would you like to explore?</h2><p>Add an image, upload audio, or start with a question.</p><button id="suggest-image" class="suggestion">Describe an image</button><p class="muted">Responses are simulated in this prototype.</p></div>`; $('suggest-image').onclick=()=>{$('prompt').value='Describe the key details in this image.';$('prompt').focus();}; }
  function renderMessages(){
    if(!messages.length){emptyChat();return;}
    $('transcript').innerHTML=messages.map(m=>`<div class="message ${m.role}"><strong>${m.role==='user'?'You':'Assistant'}</strong>${m.file?`<span class="tag">${m.file.type==='image'?'Image':'Audio'} · ${escapeHtml(m.file.name)}</span>${m.file.type==='image'?`<img src="${escapeHtml(m.file.url)}" alt="${escapeHtml(m.file.name)} uploaded for visual analysis">`:`<p class="muted">Audio input · ${escapeHtml(m.file.name)}</p>`}`:''}${m.transcription?`<p><strong>Transcription</strong>${escapeHtml(m.transcription)}</p>`:''}<p>${escapeHtml(m.text)}</p></div>`).join('');
    $('transcript').scrollTop=$('transcript').scrollHeight;
  }
  function drawAttachment(){ $('attachment').innerHTML=attachment?`<div class="attachment-chip"><span>${attachment.type==='image'?'▧':'♫'} ${escapeHtml(attachment.name)} <small>· Ready</small></span><button id="remove-file" aria-label="Remove attached file">×</button></div>${attachment.type==='image'?`<img class="attachment-preview" src="${escapeHtml(attachment.url)}" alt="Preview of ${escapeHtml(attachment.name)}">`:''}`:''; if($('remove-file'))$('remove-file').onclick=()=>{if(attachment.url?.startsWith('blob:'))URL.revokeObjectURL(attachment.url);attachment=null;drawAttachment();updateControls();}; }
  function updateControls(){
    const caps=capabilities[$('model').value];
    $('capabilities').innerHTML=caps.map(c=>`<span class="tag">${c==='audio'?'Audio via transcription':c[0].toUpperCase()+c.slice(1)}</span>`).join('');
    $('modality-controls').innerHTML=['image','audio'].filter(type=>caps.includes(type)).map(type=>`<button class="input-button" id="add-${type}" ${mediaUsed||busy?'disabled':''}>${type==='image'?'▧ Add image':'♫ Add audio'}</button><input hidden id="file-${type}" type="file" accept="${type==='image'?'image/jpeg,image/png':'audio/wav,audio/x-wav,audio/mpeg'}" aria-label="Upload ${type}">`).join('');
    ['image','audio'].forEach(type=>{if($('add-'+type)){ $('add-'+type).onclick=()=> $('file-'+type).click(); $('file-'+type).onchange=e=>chooseFile(e.target.files[0],type); }});
    const old=$('asr-model')?.value;
    const asr=assets.filter(a=>a.asr);
    $('asr-control').innerHTML=caps.includes('audio')?`<label for="asr-model">Audio transcription model</label><select id="asr-model" ${!asr.length?'disabled':''}><option value="">Select a registered ASR endpoint</option>${asr.map(a=>`<option value="${escapeHtml(a.name)}">${escapeHtml(a.name)}</option>`).join('')}</select>${!asr.length?alertHtml('No transcription model registered. <a href="assets.html?scenario=empty">Register a transcription model as an AI asset</a>, and mark it as ASR capable.','info'):''}`:'';
    if($('asr-model')&&asr.some(a=>a.name===old))$('asr-model').value=old;
    $('file-hint').textContent=mediaUsed?'One file used. Start a new conversation to add another.':caps.length===1?'Text input':`One image or audio per conversation · 10 MB max`;
    if($('remove-file'))$('remove-file').disabled=busy;
    if($('asr-model'))$('asr-model').disabled=busy || !asr.length;
    $('send').disabled=busy;
    $('new-chat').disabled=busy;
    $('model').disabled=busy;
  }
  function chooseFile(file,type){
    if(!file)return;
    if(mediaUsed){notice('Only one image or audio file is allowed per conversation. Start a new conversation.');return;}
    if(attachment){notice('Remove the current attachment before choosing another file.');return;}
    if(!file.size){notice('The selected file is empty. Choose a file larger than 0 bytes.');return;}
    if(file.size>10*1024*1024){notice('File exceeds the 10 MB limit. Choose a smaller file. Nothing was uploaded.');return;}
    const allow=type==='image'?['image/jpeg','image/png']:['audio/wav','audio/x-wav','audio/mpeg'];
    if(!allow.includes(file.type)){notice(`Unsupported file type. Choose ${type==='image'?'JPG or PNG. PDF is not supported as image input.':'WAV or MP3.'} Nothing was uploaded.`);return;}
    attachment={name:file.name,type,url:type==='image'?URL.createObjectURL(file):null,fileId:'mock-file-'+Date.now()};
    notice('File ready. Upload will be simulated when you send.','info'); drawAttachment();
  }
  $('model').onchange=()=>{notice('');if(attachment && !capabilities[$('model').value].includes(attachment.type)){attachment=null;drawAttachment();notice('Attachment removed because the selected model does not support this input.','info');}updateControls();if($('model').value==='unknown')notice('Capability tags are unavailable. You can try a file; unsupported inputs will return a clear model error.','info');};
  $('new-chat').onclick=()=>{epoch++;attachment=null;mediaUsed=false;messages=[];$('prompt').value='';$('progress').textContent='';notice('');drawAttachment();renderMessages();updateControls();};
  const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
  $('send').onclick=async()=>{
    const text=$('prompt').value.trim(), file=attachment;
    if(!text&&!file){notice('Enter a message or attach a file.');return;}
    if(file?.type==='audio'&&!$('asr-model')?.value){notice('Select a registered audio transcription model before submitting audio.');return;}
    const token=++epoch;busy=true;notice('');updateControls();
    const outcome=$('outcome').value;
    const stage=async label=>{$('progress').textContent=label;await pause(650);return token===epoch;};
    const stop=(message)=>{busy=false;$('progress').textContent='';notice(message);updateControls();};
    if(file){if(!await stage('Uploading file…'))return;if(outcome==='upload-error'){stop('Upload failed. Your file is still attached. Try sending again.');return;}}
    let transcription='';
    if(file?.type==='audio'){
      if(!await stage('Transcribing audio…'))return;
      if(outcome==='asr-error'){stop('Transcription service is unavailable. No message was sent to the response model. Check the endpoint and retry.');return;}
      if(outcome==='silent'){stop('No speech detected. No message was sent to the response model. Remove the file and choose audio with speech.');return;}
      transcription='Please summarize the customer feedback and list the next steps.';
    }
    if(!await stage('Generating response…'))return;
    if(outcome==='inference-error'||($('model').value==='unknown'&&file)){stop('This model rejected the input modality. Select a model with the matching capability and retry.');return;}
    messages.push({role:'user',text,file,transcription});
    messages.push({role:'assistant',text:file?.type==='image'?'The image shows a mountain landscape beside a lake. The calm water reflects the surrounding peaks. This is a simulated vision response.':file?.type==='audio'?'The feedback highlights the need for clearer onboarding. Next steps: simplify setup, improve guidance, and validate changes with customers. This is a simulated response to the transcription.':'I can help explore that question. This is a simulated text response.'});
    if(file)mediaUsed=true;
    attachment=null;busy=false;$('prompt').value='';$('progress').textContent='Response complete';drawAttachment();renderMessages();updateControls();
  };
  const sample={name:'mountain-lake.png',type:'image',url:'sample-landscape.svg',fileId:'mock-file-image'};
  if(scenario==='text-only')$('model').value='text';
  if(['audio-complete','no-asr','asr-error'].includes(scenario) || new URLSearchParams(location.search).get('input')==='audio')$('model').value='audio';
  if(scenario==='image-complete'){mediaUsed=true;messages=[{role:'user',text:'Describe this landscape.',file:sample},{role:'assistant',text:'A mountain range rises above a blue lake, with trees along the shore. The water reflects the peaks. This is a simulated vision response.'}];}
  if(scenario==='audio-complete'){mediaUsed=true;messages=[{role:'user',text:'Summarize this recording.',file:{name:'customer-feedback.wav',type:'audio'},transcription:'The product is useful, but onboarding needs clearer instructions.'},{role:'assistant',text:'The customer values the product and requests clearer onboarding. Next step: improve the setup instructions. This is a simulated text response.'}];}
  if(scenario==='asr-error'){attachment={name:'customer-feedback.mp3',type:'audio',fileId:'mock-file-audio'};notice('Transcription service is unavailable. No message was sent to the response model. Check the endpoint and retry.');}
  if(scenario==='upload-error')notice('File exceeds the 10 MB limit. Choose a smaller JPG, PNG, WAV, or MP3 file. Nothing was uploaded.');
  drawAttachment();renderMessages();updateControls();
  if(scenario==='asr-error'&&$('asr-model'))$('asr-model').value=assets.find(a=>a.asr)?.name||'';
}
