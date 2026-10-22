/* Local UX mocks only. No inference, upload, or endpoint network requests. */
const $ = id => document.getElementById(id);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const requested = window.UxdScenario?.get() || new URLSearchParams(location.search).get('scenario') || 'default';
const isAssets = location.pathname.endsWith('assets.html');
const allowed = isAssets ? ['default','empty','unmarked','load-error'] : ['default','image-complete','audio-complete','no-asr','text-only','file-too-large','transcription-error'];
const scenario = allowed.includes(requested) ? requested : 'default';
const initialAssets = [{name:'Whisper demo',url:'https://asr.example.com/v1',asr:true}];
let assets;
try { assets = JSON.parse(sessionStorage.getItem('uxd-assets')) || initialAssets; } catch { assets = initialAssets; }
if (scenario === 'empty' || scenario === 'no-asr') assets = [];
if (scenario === 'unmarked') assets = [{name:'Whisper demo',url:'https://asr.example.com/v1',asr:false}];
function saveAssets(){sessionStorage.setItem('uxd-assets',JSON.stringify(assets));}
if (isAssets) {
  const render = () => {
    $('asset-table').innerHTML = assets.length ? '<table class="pf-v6-c-table"><thead><tr><th>Name</th><th>Endpoint</th><th>Audio transcription</th></tr></thead><tbody>'+assets.map((a,i)=>`<tr><td>${esc(a.name)}</td><td>${esc(a.url)}</td><td><label><input type="checkbox" data-asset="${i}" ${a.asr?'checked':''}> ASR-capable</label></td></tr>`).join('')+'</tbody></table>' : '<div class="empty"><h2>No AI Asset Endpoints</h2><p>Register a transcription model to enable audio input in the Playground.</p></div>';
    document.querySelectorAll('[data-asset]').forEach(input=>input.onchange=()=>{assets[+input.dataset.asset].asr=input.checked;saveAssets();$('asset-status').textContent='Capabilities updated. The Playground audio dropdown will reflect this change.';});
  };
  $('register').onclick=()=>$('endpoint-dialog').showModal();
  $('cancel').onclick=()=>$('endpoint-dialog').close();
  $('endpoint-form').onsubmit=e=>{e.preventDefault();assets.push({name:$('endpoint-name').value.trim(),url:$('endpoint-url').value,asr:$('endpoint-asr').checked});saveAssets();render();$('endpoint-dialog').close();$('asset-status').textContent='Endpoint registered. Return to Playground to select it.';};
  if(scenario==='load-error'){
    $('asset-table').innerHTML='<div class="notice error"><h2>Unable to load endpoints</h2><p>Your assets could not be retrieved.</p><button id="retry-assets">Retry</button></div>';
    $('retry-assets').onclick=render;
  } else render();
} else {
  let attachment=null, used=false, busy=false, timer;
  const notify=(message,error=false)=>{$('status').className=message?'notice'+(error?' error':''):'';$('status').textContent=message;};
  const empty=()=>{$('transcript').innerHTML='<div class="empty"><h2>Start exploring</h2><p>Ask a question, attach an image, or transcribe an audio file.</p></div>';};
  const append=(role,text,media='')=>{if($('transcript').querySelector('.empty'))$('transcript').innerHTML='';$('transcript').insertAdjacentHTML('beforeend',`<article class="message ${role==='Model'?'assistant':''}"><strong>${role}</strong><p>${esc(text)}</p>${media}</article>`);};
  const media=a=>a?.url ? a.kind==='image'?`<img src="${a.url}" alt="Attached image: ${esc(a.name)}">`:`<audio controls src="${a.url}" aria-label="Uploaded audio: ${esc(a.name)}"></audio>` : '';
  function controls(){
    const model=$('model').value, audio=model==='multi';
    $('capabilities').textContent=model==='text'?'Text input':model==='vision'?'Text and image input':'Text, image, and audio input';
    $('asr-region').hidden=!audio;
    $('modalities').innerHTML=(model!=='text'?'<button type="button" id="image-input">Attach image</button><input hidden id="image-file" type="file" accept="image/jpeg,image/png">':'')+(audio?'<button type="button" id="audio-input">Attach audio</button><input hidden id="audio-file" type="file" accept="audio/wav,audio/x-wav,audio/mpeg">':'');
    for(const kind of ['image','audio']) if($(kind+'-input')){
      $(kind+'-input').disabled=busy||used||!!attachment;
      $(kind+'-input').onclick=()=>$(kind+'-file').click();
      $(kind+'-file').onchange=e=>choose(e.target.files[0],kind);
    }
    $('limit').textContent=used?'This conversation already contains a file. Start a new chat to attach another.':'';
    $('send').disabled=busy || (attachment?.kind==='audio'&&!$('asr').value);
    $('model').disabled=busy||used||!!attachment;
  }
  function choose(file,kind){
    if(!file)return;
    if(used||attachment){notify('Only one file is allowed per conversation. Start a new chat.',true);return;}
    if(!file.size){notify('This file is empty. Choose a non-empty file.',true);return;}
    if(file.size>10*1024*1024){notify('File exceeds the 10 MB demo limit. Choose a smaller file.',true);return;}
    const types=kind==='image'?['image/jpeg','image/png']:['audio/wav','audio/x-wav','audio/mpeg'];
    if(!types.includes(file.type)){notify('Unsupported format. Choose '+(kind==='image'?'JPG or PNG. PDFs belong in Upload files.':'WAV or MP3.'),true);return;}
    attachment={name:file.name,kind,url:URL.createObjectURL(file)};
    $('attachment').innerHTML=`<div class="message">${esc(file.name)}${media(attachment)} <button type="button" id="remove-file">Remove attachment</button></div>`;
    $('remove-file').onclick=()=>{URL.revokeObjectURL(attachment.url);attachment=null;$('attachment').innerHTML='';notify('');controls();};
    notify(kind==='audio'&&!$('asr').value?'Register an ASR-capable AI Asset Endpoint before sending audio.':'Attachment ready.');controls();
  }
  $('asr').innerHTML='<option value="">Select transcription model</option>'+assets.filter(a=>a.asr).map(a=>`<option value="${esc(a.name)}">${esc(a.name)}</option>`).join('');
  $('asr').onchange=()=>{notify('');controls();};
  $('model').onchange=()=>{notify('');controls();};
  $('composer').onsubmit=e=>{
    e.preventDefault();if(busy)return;
    const prompt=$('prompt').value.trim();
    if(!prompt&&!attachment){notify('Enter a message or attach a file.',true);return;}
    if(attachment?.kind==='audio'&&!$('asr').value){notify('Select a registered transcription model before sending audio.',true);return;}
    append('You',prompt||attachment.name,media(attachment));
    const kind=attachment?.kind;used=used||!!attachment;busy=true;controls();notify(kind?'Uploading file…':'Generating response…');
    $('prompt').value='';$('attachment').innerHTML='';attachment=null;
    timer=setTimeout(()=>{notify(kind==='audio'?'Transcribing audio…':'Generating response…');timer=setTimeout(()=>{
      if(kind==='audio')append('Transcription','Demo transcript: Please summarize the quarterly planning discussion.');
      append('Model',kind==='image'?'Demo vision response: The uploaded image has been received. A connected model would describe its contents here.':kind==='audio'?'Demo response: The discussion requests a summary of quarterly planning.':'Demo response: I can help explore this question. Connect a model for a real answer.');busy=false;notify('Response complete.');controls();
    },900);},600);
  };
  $('new-chat').onclick=()=>{clearTimeout(timer);attachment=null;used=false;busy=false;$('prompt').value='';$('attachment').innerHTML='';notify('');empty();controls();};
  empty();
  if(scenario==='text-only')$('model').value='text';
  if(scenario==='image-complete'){
    $('model').value='vision';used=true;append('You','Describe this sample landscape.','<svg role="img" aria-label="Sample landscape image" viewBox="0 0 240 100" width="240"><rect width="240" height="100" fill="#d9effc"/><path d="M0 100L70 20L140 100L190 45L240 100" fill="#669c75"/></svg>');append('Model','The image shows green mountains beneath a clear blue sky.');
  }
  if(scenario==='audio-complete'){used=true;$('asr').selectedIndex=assets.some(a=>a.asr)?1:0;append('You','Summarize planning.wav.');append('Transcription','We plan to complete the project review on Friday.');append('Model','The project review is planned for Friday.');}
  if(scenario==='no-asr')notify('No transcription model registered. Register an ASR-capable AI Asset Endpoint to send audio.');
  if(scenario==='file-too-large')notify('photo.png is 14 MB and exceeds the 10 MB demo limit. No file was uploaded. Choose a smaller file.',true);
  if(scenario==='transcription-error'){notify('Transcription failed: the endpoint is unavailable. No model response was requested. Start a new chat to retry with another endpoint.',true);append('You','Transcribe meeting.wav.');used=true;}
  controls();
}
