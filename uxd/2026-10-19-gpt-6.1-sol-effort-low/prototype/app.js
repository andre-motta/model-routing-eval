/* Local UX simulation. No files or credentials leave the browser. */
const $ = id => document.getElementById(id);
const escapeHTML = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const scenario = window.UxdScenario ? window.UxdScenario.get() : new URLSearchParams(location.search).get('scenario') || 'default';
const initialAssets = [{name:'Qwen2.5-VL',url:'https://vision.example.com/v1',asr:false,vision:true},{name:'Llama',url:'https://text.example.com/v1',asr:false},{name:'Whisper',url:'https://whisper.example.com/v1',asr:true}];
let assets;
try { assets = JSON.parse(sessionStorage.getItem('uxd-assets')) || initialAssets; } catch { assets = initialAssets; }
const persist = () => sessionStorage.setItem('uxd-assets', JSON.stringify(assets));
function alertBox(message, kind='warning') { $('alerts').innerHTML = `<div class="alert ${kind}" role="${kind==='error'?'alert':'status'}">${message}</div>`; }
if ($('endpoint-list')) {
  if (scenario==='empty') assets=[];
  if (scenario==='registered' && !assets.some(a=>a.name==='Research ASR')) assets.push({name:'Research ASR',url:'https://research-asr.example.com/v1',asr:true});
  function renderAssets() {
    $('endpoint-list').innerHTML = assets.length ? `<table class="pf-v6-c-table"><thead><tr><th>Name</th><th>Endpoint</th><th>Capabilities</th><th>Audio transcription</th></tr></thead><tbody>${assets.map((a,i)=>`<tr><td><strong>${escapeHTML(a.name)}</strong></td><td>${escapeHTML(a.url)}</td><td><span class="badge">${a.asr?'Audio / ASR':a.vision?'Text + image':'Text'}</span></td><td><label class="check"><input type="checkbox" data-asset="${i}" ${a.asr?'checked':''} aria-label="Audio transcription for ${escapeHTML(a.name)}"> ASR capable</label></td></tr>`).join('')}</tbody></table>` : '<div class="empty"><h2>No AI Asset endpoints</h2><p>Register a deployed transcription model to enable audio in Playground.</p><button id="empty-register">Register endpoint</button></div>';
    $('empty-register')?.addEventListener('click',()=>$('register-dialog').showModal());
    document.querySelectorAll('[data-asset]').forEach(el=>el.onchange=()=>{assets[Number(el.dataset.asset)].asr=el.checked;persist();renderAssets();alertBox('Capability updated. The Playground audio model selector now reflects this endpoint.','success');});
  }
  renderAssets();
  if(scenario==='registered') alertBox('Research ASR registered for audio transcription. <a href="index.html">Open Playground</a>.','success');
  if(scenario==='load-error') {$('endpoint-list').innerHTML='<div class="empty"><h2>Unable to load endpoints</h2><p>Check your connection and try again.</p><button id="retry-load">Retry</button></div>'; $('retry-load').onclick=()=>{$('alerts').innerHTML='';renderAssets();};alertBox('Endpoint service is unavailable.','error');}
  $('register').onclick=()=>$('register-dialog').showModal();
  $('cancel').onclick=()=>$('register-dialog').close();
  $('endpoint-form').onsubmit=e=>{e.preventDefault();assets.push({name:$('endpoint-name').value.trim(),url:$('endpoint-url').value,asr:$('asr-flag').checked});persist();renderAssets();$('register-dialog').close();alertBox('Endpoint registered. <a href="index.html">Open Playground</a> to use it.','success');};
} else {
  let mode='text', attachment=null, used=false, busy=false, failed=false, generation=0;
  const sampleImage='sample-scene.svg';
  const asrAssets=scenario==='no-asr'?[]:assets.filter(a=>a.asr);
  $('asr').innerHTML='<option value="">Select a transcription model</option>'+asrAssets.map((a,i)=>`<option value="${i}">${escapeHTML(a.name)}</option>`).join('');
  if(asrAssets.length) $('asr').value='0';
  function emptyChat() {$('chat').innerHTML='<div class="empty"><div class="icon">✧</div><h2>Start with a question. Add context.</h2><p class="muted">Test how your model understands an image or spoken content.<br>Use a sample below or attach your own file.</p></div>';}
  function controls() {
    const unknown=$('model').value==='unknown';
    $('image-mode').hidden=$('model').value==='text';
    $('sample-image').hidden=$('model').value==='text';
    $('capabilities').textContent=unknown?'Capabilities unknown':$('model').value==='vision'?'Text + image':'Text only';
    $('audio-settings').hidden=mode!=='audio';
    $('upload').hidden=mode==='text';
    $('file').accept=mode==='image'?'.jpg,.jpeg,.png':'.wav,.mp3';
    ['image-mode','audio-mode','sample-image','sample-audio','upload'].forEach(id=>$(id).disabled=used||busy||!!attachment);
    $('send').disabled=busy||failed||(attachment?.type==='audio'&&!$('asr').value);
    ['text','image','audio'].forEach(m=>$(m+'-mode').setAttribute('aria-pressed',String(m===mode)));
    if(mode==='audio'&&!asrAssets.length) alertBox('No transcription endpoint registered. <a href="endpoints.html?scenario=empty">Register an AI Asset</a> and mark it for audio transcription before sending audio.');
    $('limits').textContent=used?'This conversation has used its one attachment. Continue with text or start a new conversation.':'One image or audio file per conversation. JPG, PNG, WAV or MP3. Maximum 10 MB (proposed).';
  }
  function renderAttachment(){
    $('attachment').hidden=!attachment;
    if(attachment) $('attachment').innerHTML=`<strong>${escapeHTML(attachment.name)}</strong> <span class="badge">${attachment.type==='image'?'Image':'Audio'}</span>${attachment.type==='image'?`<img src="${attachment.url}" alt="Attached image preview">`:'<p>Audio file ready for transcription</p>'}<button id="remove">Remove</button>${failed?' <button id="retry-upload">Retry upload</button>':''}`;
    $('remove')?.addEventListener('click',()=>{attachment=null;failed=false;$('alerts').innerHTML='';renderAttachment();controls();});
    $('retry-upload')?.addEventListener('click',()=>{failed=false;alertBox('Upload complete. Ready to send.','success');renderAttachment();controls();});
    controls();
  }
  function attach(type,name,url){if(used||busy||attachment)return;mode=type;attachment={type,name,url};renderAttachment();}
  ['text','image','audio'].forEach(m=>$(m+'-mode').onclick=()=>{mode=m;$('alerts').innerHTML='';controls();});
  $('model').onchange=()=>{if($('model').value==='text'&&mode==='image'&&!attachment)mode='text';controls();};
  $('asr').onchange=controls;
  $('sample-image').onclick=()=>attach('image','storefront.png',sampleImage);
  $('sample-audio').onclick=()=>attach('audio','customer-feedback.wav',null);
  $('upload').onclick=()=>$('file').click();
  $('file').onchange=()=>{
    const f=$('file').files[0]; if(!f)return;
    if(f.size>10*1024*1024){alertBox('File exceeds the proposed 10 MB limit. Choose a smaller file.','error');$('file').value='';return;}
    const allowed=mode==='image'?/\.(jpe?g|png)$/i:/\.(wav|mp3)$/i;
    if(!allowed.test(f.name)){alertBox('Unsupported file format. Choose JPG or PNG for images, WAV or MP3 for audio. PDF uses the separate Upload files capability.','error');$('file').value='';return;}
    attach(mode,f.name,URL.createObjectURL(f));alertBox('Upload complete (simulated). Ready to send.','success');
  };
  function finishResponse(a,prompt){
    busy=false;used=used||!!a;attachment=null;failed=false;
    const transcript=a?.type==='audio'?'<p><strong>Transcription</strong></p><p>“The new checkout is easier to use, but delivery updates could be clearer.”</p>':'';
    $('chat').innerHTML+=`<article class="message" id="assistant-response"><strong>${escapeHTML($('model').selectedOptions[0].text.split(' · ')[0])}</strong>${transcript}<p>${a?.type==='image'?'The sample shows a storefront with a blue awning and a clearly marked entrance. You could improve accessibility by keeping the entrance clear.':a?.type==='audio'?'The speaker likes the checkout experience and wants clearer delivery updates. Consider adding proactive shipment notifications.':'I can help explore that question. Add more detail about your goal to refine the response.'}</p><small class="muted">Simulated text response</small></article>`;
    $('processing-status')?.remove();renderAttachment();controls();
  }
  $('send').onclick=()=>{
    const prompt=$('prompt').value.trim();if(busy||failed||(!prompt&&!attachment))return;
    if(attachment?.type==='audio'&&!$('asr').value){alertBox('Select a registered transcription endpoint before sending audio.');return;}
    if($('model').value==='text'&&attachment?.type==='image'||$('model').value==='unknown'&&attachment){alertBox('This model rejected the input modality. Your file and prompt are retained. <button id="use-vision">Choose a supported model</button>','error');$('use-vision').onclick=()=>{$('model').value='vision';$('alerts').innerHTML='';controls();};return;}
    const a=attachment;const token=generation;busy=true;
    if($('chat').querySelector('.empty'))$('chat').innerHTML='';
    $('chat').innerHTML+=`<article class="message user"><strong>You</strong><p>${escapeHTML(prompt||'Describe this input.')}</p>${a?`<p>${escapeHTML(a.name)}</p>${a.type==='image'?`<img src="${a.url}" alt="Uploaded image in conversation">`:''}`:''}</article><div id="processing-status" class="status" role="status">${a?.type==='audio'?'Transcribing audio with '+escapeHTML($('asr').selectedOptions[0].text)+'…':'Processing input…'}<progress aria-label="Processing"></progress></div>`;
    $('prompt').value='';$('alerts').innerHTML='';controls();
    setTimeout(()=>{if(token===generation)finishResponse(a,prompt);},900);
  };
  $('new-chat').onclick=()=>{generation++;attachment=null;used=false;busy=false;failed=false;mode='text';$('prompt').value='';$('alerts').innerHTML='';$('file').value='';emptyChat();renderAttachment();};
  emptyChat();
  if(['image-result','audio-result','processing','upload-error','unsupported','no-asr'].includes(scenario)) {
    if(scenario==='no-asr') mode='audio';
    else {
      const audio=['audio-result','processing'].includes(scenario);
      attachment={type:audio?'audio':'image',name:audio?'customer-feedback.wav':'storefront.png',url:sampleImage};mode=attachment.type;
      if(scenario.endsWith('-result')){$('chat').innerHTML=`<article class="message user"><strong>You</strong><p>${audio?'Summarize this customer feedback.':'Describe this storefront.'}</p><p>${attachment.name}</p>${audio?'':`<img src="${sampleImage}" alt="Storefront sample">`}</article>`;finishResponse(attachment,'');}
      if(scenario==='processing'){busy=true;$('chat').innerHTML='<div class="status" role="status"><h2>Transcribing customer-feedback.wav</h2><p>Whisper is converting your audio to text before the response model answers.</p><progress aria-label="Transcribing audio"></progress></div>';}
      if(scenario==='upload-error'){failed=true;alertBox('Upload failed. Your file could not be stored. Retry the upload or remove it and choose another file.','error');}
      if(scenario==='unsupported'){$('model').value='unknown';alertBox('The selected model rejected image input. Your prompt and attachment are retained. Select Qwen2.5-VL and send again.','error');$('prompt').value='Describe this storefront.';}
    }
  }
  renderAttachment();controls();
}
