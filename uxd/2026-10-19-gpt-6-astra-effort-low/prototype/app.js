/* All operations are local mock interactions. No inference or upload API is called. */
'use strict';
const $ = id => document.getElementById(id);
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const initialAssets = [{name:'vision-demo',url:'https://vision.example.test/v1',asr:false},{name:'whisper-transcription',url:'https://asr.example.test/v1',asr:true}];
let assets;
try { assets = JSON.parse(sessionStorage.getItem('uxd-assets')) || initialAssets; } catch { assets = initialAssets; }
function saveAssets(){sessionStorage.setItem('uxd-assets',JSON.stringify(assets));}
const scenarioId = window.UxdScenario ? window.UxdScenario.get() : new URLSearchParams(location.search).get('scenario') || 'default';
const isAssets = location.pathname.endsWith('assets.html');
const allowed = isAssets ? ['default','empty','load-error','unflagged'] : ['default','vision-result','audio-result','text-only','vision-only','no-asr','processing','asr-error','empty-transcription','invalid-file','unsupported'];
const scenario = allowed.includes(scenarioId) ? scenarioId : 'default';
document.body.dataset.scenario = scenario;
if(isAssets){
  if(scenario==='empty') assets=[];
  if(scenario==='unflagged') assets=initialAssets.map(a=>({...a,asr:false}));
  function renderAssets(){
    $('asset-list').innerHTML = assets.length ? `<table class="pf-v6-c-table"><thead><tr><th>Name</th><th>Endpoint</th><th>Capabilities</th><th>Action</th></tr></thead><tbody>${assets.map((a,i)=>`<tr><td>${escapeHtml(a.name)}</td><td>${escapeHtml(a.url)}</td><td><span class="tag">${a.asr?'Audio transcription (ASR)':'Model endpoint'}</span></td><td><button data-toggle-asr="${i}" aria-label="${a.asr?'Disable':'Enable'} transcription for ${escapeHtml(a.name)}">${a.asr?'Disable':'Enable'} transcription</button></td></tr>`).join('')}</tbody></table>` : '<div class="empty"><h2>No endpoints registered</h2><p>Register your deployed transcription model to use audio in the Playground.</p></div>';
    document.querySelectorAll('[data-toggle-asr]').forEach(b=>b.onclick=()=>{assets[b.dataset.toggleAsr].asr=!assets[b.dataset.toggleAsr].asr;saveAssets();renderAssets();$('asset-alert').textContent='Endpoint updated. The Playground audio model selector reflects this change.';});
  }
  $('register').onclick=()=>{$('register-dialog').showModal();$('endpoint-name').focus();};
  $('cancel').onclick=()=>$('register-dialog').close();
  $('endpoint-form').onsubmit=e=>{e.preventDefault();assets.push({name:$('endpoint-name').value.trim(),url:$('endpoint-url').value,asr:$('asr-flag').checked});saveAssets();renderAssets();$('register-dialog').close();$('asset-alert').textContent='Endpoint registered. Open Playground to select your transcription model.';};
  if(scenario==='load-error'){$('asset-list').innerHTML='<div class="alert">Unable to load endpoints. Check the connection and retry.</div><button id="retry-assets">Retry</button>';$('retry-assets').onclick=renderAssets;} else renderAssets();
} else {
  let file=null, used=false, busy=false, messages=[], generation=0;
  const imageFixture='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="360" height="220"><rect width="360" height="220" fill="#d9edf7"/><path d="M0 190L110 60L190 160L270 90L360 190V220H0" fill="#4e7868"/><circle cx="290" cy="45" r="22" fill="#f4c145"/></svg>');
  function audioFixture(){const bytes=new Uint8Array(8044);const view=new DataView(bytes.buffer);function word(offset,text){[...text].forEach((c,i)=>view.setUint8(offset+i,c.charCodeAt(0)));}word(0,'RIFF');view.setUint32(4,8036,true);word(8,'WAVE');word(12,'fmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,8000,true);view.setUint32(28,8000,true);view.setUint16(32,1,true);view.setUint16(34,8,true);word(36,'data');view.setUint32(40,8000,true);for(let i=44;i<bytes.length;i++)bytes[i]=128+Math.round(18*Math.sin(i*0.35));return URL.createObjectURL(new Blob([bytes],{type:'audio/wav'}));}
  function alert(message,kind='error'){const el=$('alert');el.hidden=!message;el.className='alert '+(kind==='error'?'':kind);el.innerHTML=message;}
  function preview(f){return `<div class="attachment"><strong>${escapeHtml(f.name)}</strong>${f.kind==='image'?`<img src="${f.url}" alt="${f.sample?'Sample landscape with mountains and sun':'Uploaded image preview'}">`:`<audio controls src="${f.url}" aria-label="Uploaded audio preview"></audio>`}<span class="note">${f.sample?'Sample fixture':'Local file preview'} · ${f.kind==='image'?'Image':'Audio'}</span></div>`;}
  function renderChat(){ $('chat').innerHTML=messages.length ? messages.map(m=>`<article class="message ${m.role}"><strong>${m.role==='assistant'?'Model response':'You'}</strong>${m.file?preview(m.file):''}${m.transcription?`<p><b>Transcription</b>: ${escapeHtml(m.transcription)}</p>`:''}<p ${m.role==='assistant'?'id="assistant-response"':''}>${escapeHtml(m.text)}</p></article>`).join('') : '<div class="empty"><div class="symbol" aria-hidden="true">✦</div><h2>What would you like to explore?</h2><p>Add an image to ask about visual content, or upload audio to work with a transcription.</p><p>Start with your own file or use a sample below.</p></div>'; }
  function controls(){
    const model=$('model').value;
    const image=model!=='text';const audio=model==='multimodal'||model==='unknown';
    $('capability').textContent=({text:'Text only',vision:'Text · Image input',multimodal:'Text · Image · Audio input',unknown:'Capabilities unknown'})[model];
    $('modality-controls').innerHTML=(image?'<label class="button">Attach image<input id="image-file" type="file" accept="image/jpeg,image/png" aria-label="Choose JPG or PNG image"></label><button id="sample-image" class="link">Use sample image</button>':'')+(audio?'<label class="button">Attach audio<input id="audio-file" type="file" accept="audio/wav,audio/x-wav,audio/mpeg" aria-label="Choose WAV or MP3 audio"></label><button id="sample-audio" class="link">Use sample audio</button>':'');
    for(const kind of ['image','audio']){if($(kind+'-file')){$(kind+'-file').disabled=used||busy||!!file;$(kind+'-file').onchange=e=>selectFile(e.target.files[0],kind);$('sample-'+kind).disabled=used||busy||!!file;$('sample-'+kind).onclick=()=>attach({name:kind==='image'?'mountains.png':'meeting-notes.wav',kind,url:kind==='image'?imageFixture:audioFixture(),sample:true});}}
    $('audio-settings').hidden=!audio;
    const selected=$('asr').value;const list=scenario==='no-asr'?[]:assets.filter(a=>a.asr);
    $('asr').innerHTML=list.length?'<option value="">Select a transcription model</option>'+list.map(a=>`<option value="${escapeHtml(a.name)}">${escapeHtml(a.name)}</option>`).join(''):'<option value="">No transcription endpoints available</option>';
    if(list.some(a=>a.name===selected)) $('asr').value=selected;
    else if(list.length) $('asr').value=list[0].name;
    $('asr-help').innerHTML=list.length?'Audio is transcribed before your message is sent to the selected model.':'<a href="assets.html?scenario=empty">Register a transcription model as an AI Asset</a> and enable audio transcription to submit audio.';
    $('attachment').innerHTML=file?preview(file)+(used?'':'<button id="remove">Remove attachment</button>'):'';
    if($('remove'))$('remove').onclick=()=>{if(file&&!file.sample)URL.revokeObjectURL(file.url);file=null;alert('');controls();};
    $('limit').textContent=used?'This conversation already contains a file. Continue with text, or start a new conversation to attach another file.':'One image or audio file per conversation. JPG, PNG, WAV, MP3. Maximum 10 MB per file.';
    $('send').disabled=busy||(file?.kind==='audio'&&!$('asr').value);
    $('model').disabled=busy; $('asr').disabled=busy||used;
  }
  function selectFile(raw,kind){if(!raw)return;if(used||file){alert('Only one image or audio file is allowed per conversation. Start a new conversation to attach another.');return;}if(raw.size===0){alert('This file is empty (0 bytes). Choose a non-empty file.');return;}if(raw.size>10*1024*1024){alert('File exceeds the 10 MB limit. Choose a smaller file. Nothing was uploaded.');return;}const types=kind==='image'?['image/jpeg','image/png']:['audio/wav','audio/x-wav','audio/mpeg'];if(!types.includes(raw.type)){alert('Unsupported file type. Use JPG or PNG for images, WAV or MP3 for audio. PDFs use the separate Upload files workflow.');return;}attach({name:raw.name,kind,url:URL.createObjectURL(raw),sample:false});}
  function attach(f){if(used||file){alert('Only one file per conversation. Start a new conversation to attach another.');return;}file=f;alert('');controls();}
  function progress(text){$('progress').hidden=!text;$('progress').className='steps';$('progress').textContent=text;}
  function complete(){
    const question=$('prompt').value.trim()||'Describe this attachment.';
    messages.push({role:'user',text:question,file:used?null:file,transcription:file?.kind==='audio'&&!used?'Discuss the launch timeline and assign owners for the next milestone.':null});
    messages.push({role:'assistant',text:file?.kind==='audio'&&!used?'Sample response: The recording discusses launch planning. Next steps are to confirm the timeline and assign milestone owners.':file?.kind==='image'&&!used?'Sample response: This image can be analyzed for visible objects, composition, and context. The sample landscape contains mountains beneath a bright sky.':'Sample text response: I can help explore that question. This prototype uses simulated responses.'});
    used=used||!!file;file=null;busy=false;progress('');$('prompt').value='';renderChat();controls();
  }
  $('send').onclick=()=>{
    if(busy)return;if(!$('prompt').value.trim()&&!file){alert('Enter a message or attach a file.');$('prompt').focus();return;}
    if(file?.kind==='audio'&&!$('asr').value){alert('Register and select a transcription model before sending audio.');return;}
    if(file&&$('model').value==='unknown'){alert('This model rejected the image or audio input. Select a model with supported capabilities, or remove the attachment and send text.');return;}
    alert('');busy=true;controls();const turn=++generation;progress(file?'1. Uploading file…':'Generating response…');
    setTimeout(()=>{if(turn!==generation)return;progress(file?.kind==='audio'?'2. Transcribing audio…':'Generating response…');setTimeout(()=>{if(turn!==generation)return;complete();},700);},400);
  };
  $('asr').onchange=()=>{$('send').disabled=busy||(file?.kind==='audio'&&!$('asr').value);};
  $('model').onchange=()=>{if(file&&($('model').value==='text'||(file.kind==='audio'&&$('model').value==='vision'))){alert('The selected model does not support this attachment. It was removed; your message is preserved.','info');file=null;}else alert('');controls();};
  $('new-chat').onclick=()=>{generation++;file=null;used=false;busy=false;messages=[];$('prompt').value='';alert('');progress('');renderChat();controls();};
  if(scenario==='text-only')$('model').value='text';
  if(scenario==='vision-only')$('model').value='vision';
  if(scenario==='unsupported')$('model').value='unknown';
  renderChat();controls();
  if(['vision-result','unsupported'].includes(scenario))attach({name:'mountains.png',kind:'image',url:imageFixture,sample:true});
  if(['audio-result','processing','asr-error','empty-transcription'].includes(scenario))attach({name:'meeting-notes.wav',kind:'audio',url:audioFixture(),sample:true});
  if(scenario==='vision-result'||scenario==='audio-result')complete();
  if(scenario==='no-asr')alert('Audio needs a registered transcription model. Register an AI Asset with audio transcription enabled.','info');
  if(scenario==='invalid-file')alert('File exceeds the 10 MB limit. Choose a smaller file. Nothing was uploaded.');
  if(scenario==='unsupported')alert('The custom model rejected image input. Select a vision-capable model and retry, or remove the attachment.');
  if(scenario==='processing'){busy=true;progress('2. Transcribing audio… Waiting for the transcription model.');controls();}
  if(scenario==='asr-error')alert('Transcription failed: the selected endpoint is unreachable. Check your endpoint or select another audio model, then retry. Your file and prompt are preserved.');
  if(scenario==='empty-transcription')alert('No speech was detected. No message was sent to the model. Remove this recording and upload audio containing speech.');
  if(scenario==='asr-error')$('send').textContent='Retry transcription';
}
