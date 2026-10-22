'use strict';
window.addEventListener('DOMContentLoaded', () => {
const $ = s => document.querySelector(s);
const escape = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const scenario = window.UxdScenario.get();
const assetPage = location.pathname.endsWith('assets.html');
const key = 'uxd-rhaistrat-1527-assets';
const defaults = [{name:'Whisper large v3',url:'https://whisper.example.test/v1',asr:true}];
let assets; try {assets=JSON.parse(sessionStorage.getItem(key)) || defaults;} catch {assets=defaults;}
if(new URLSearchParams(location.search).has('scenario')) assets=defaults.map(a=>({...a}));
if(['no-asr','empty'].includes(scenario)) assets=[];
const notice = (text, type='error') => {$('#notice').className='alert '+type; $('#notice').textContent=text; $('#notice').hidden=false;};
if(assetPage){
 const render = () => {
 $('#rows').innerHTML=assets.map((a,i)=>`<tr><td>${escape(a.name)}</td><td>${escape(a.url)}</td><td><label><input type="checkbox" data-asr="${i}" ${a.asr?'checked':''}> Audio transcription (ASR)</label></td></tr>`).join('');
 $('#empty-assets').hidden=assets.length>0; $('#asset-table').hidden=!assets.length;
 document.querySelectorAll('[data-asr]').forEach(c=>c.onchange=()=>{assets[Number(c.dataset.asr)].asr=c.checked;sessionStorage.setItem(key,JSON.stringify(assets));notice('Capability updated. The Playground audio model list now reflects this endpoint.','success');});
 };
 if(scenario==='unmarked')assets=[{...defaults[0],asr:false}];
 render();
 if(scenario==='load-error'){ $('#asset-table').hidden=true;$('#empty-assets').hidden=true;notice('AI Asset Endpoints could not be loaded. Try again.');$('#retry-assets').hidden=false; }
 if(scenario==='registered')notice('Transcription endpoint registered. It is available in the Playground audio model list.','success');
 $('#retry-assets').onclick=()=>{render();$('#retry-assets').hidden=true;notice('AI Asset Endpoints loaded.','success');};
 $('#register').onclick=()=>{$('#register-dialog').showModal();$('#asset-name').focus();};
 $('#cancel').onclick=()=>$('#register-dialog').close();
 $('#register-form').onsubmit=e=>{e.preventDefault();assets.push({name:$('#asset-name').value.trim(),url:$('#asset-url').value,asr:$('#asset-asr').checked});sessionStorage.setItem(key,JSON.stringify(assets));render();$('#register-dialog').close();notice('Endpoint registered. ASR-marked assets are available in the Playground audio model list.','success');};
 return;
}
// Catalog fixtures are illustrative, not a production capability fallback list.
const models={vision:{name:'Qwen2.5-VL',image:true,audio:false},audio:{name:'Audio workflow model',image:false,audio:true},text:{name:'Text-only model',image:false,audio:false},unknown:{name:'Custom model • metadata unavailable',image:true,audio:true}};
let attachment=null,used=false,busy=false,epoch=0;
const asrAssets=assets.filter(a=>a.asr);
$('#asr').innerHTML='<option value="">Select an audio model</option>'+asrAssets.map((a,i)=>`<option value="${i}">${escape(a.name)}</option>`).join('');
const update = () => {
 const model=models[$('#model').value];
 $('#capabilities').textContent=$('#model').value==='unknown'?'Capabilities unknown':`Text${model.image?' · Image':''}${model.audio?' · Audio via transcription':''}`;
 $('#modalities').innerHTML='';
 for(const [type,enabled] of [['image',model.image],['audio',model.audio]])if(enabled){const b=document.createElement('button');b.type='button';b.textContent=type==='image'?'Attach image':'Attach audio';b.dataset.ouiaComponentId='attach-'+type;b.disabled=used||busy;b.onclick=()=>choose(type);$('#modalities').appendChild(b);}
 $('#audio-settings').hidden=!model.audio;
 $('#no-asr').hidden=!model.audio||asrAssets.length>0;
 $('#limit').textContent=used?'This conversation already contains a file. Start a new chat to attach another.':'One image or one audio file per conversation, including previous messages.';
 $('#model').disabled=busy;
 $('#send').disabled=busy||(!$('#prompt').value.trim()&&!attachment)||(attachment?.type==='audio'&&!$('#asr').value)||(attachment&&!model[attachment.type]);
 $('#new-chat').disabled=busy;
};
const choose=type=>{if(used)return notice('Only one file is allowed in the entire conversation. Start a new chat.');if(type==='audio'&&!asrAssets.length)return notice('Register a transcription model in AI Asset Endpoints before submitting audio.');const f=$('#file');f.accept=type==='image'?'image/jpeg,image/png':'.wav,.mp3,audio/wav,audio/mpeg';f.dataset.type=type;f.value='';f.click();};
const showAttachment=()=>{$('#attachment').hidden=!attachment;$('#attachment').innerHTML=attachment?`<button id="remove-file" type="button" aria-label="Remove attachment">Remove</button><strong>${escape(attachment.name)}</strong><div>${attachment.type==='image'?`<img src="${attachment.url}" alt="Selected image preview">`:`<audio controls src="${attachment.url}" aria-label="Uploaded audio preview"></audio>`}</div><span class="help">Ready to send</span>`:'';if(attachment)$('#remove-file').onclick=()=>{URL.revokeObjectURL(attachment.url);attachment=null;showAttachment();update();};};
$('#file').onchange=()=>{const f=$('#file').files[0];if(!f)return;if(used)return notice('Only one file is allowed per conversation. Start a new chat.');const type=$('#file').dataset.type;const allowed=type==='image'?['image/jpeg','image/png']:['audio/wav','audio/x-wav','audio/wave','audio/mpeg','audio/mp3'];if(f.size===0)return notice('This file is empty. Choose a non-empty file.');if(f.size>10*1024*1024)return notice('This file exceeds the 10 MB prototype limit. Choose a smaller file.');if(!allowed.includes(f.type))return notice('Unsupported file type. Use JPG or PNG for images, WAV or MP3 for audio.');if(attachment)URL.revokeObjectURL(attachment.url);attachment={type,name:f.name,url:URL.createObjectURL(f)};$('#notice').hidden=true;$('#status').textContent='Upload complete (simulated).';showAttachment();update();};
const message=(who,text,media='')=>{$('#empty-chat')?.remove();$('#transcript').insertAdjacentHTML('beforeend',`<article class="message ${who==='Model'?'assistant':''}"><strong>${who}</strong>${media}<p>${escape(text)}</p></article>`);$('#transcript').scrollTop=$('#transcript').scrollHeight;};
$('#prompt').oninput=update;$('#asr').onchange=update;
$('#model').onchange=()=>{if(attachment&&!models[$('#model').value][attachment.type])notice('The selected model does not support this attachment. Remove it or choose a compatible model.');else $('#notice').hidden=true;update();};
$('#new-chat').onclick=()=>{epoch++;attachment=null;used=false;$('#transcript').innerHTML='<div id="empty-chat" class="empty"><div class="symbol">✦</div><h2>Start a conversation</h2><p class="muted">Explore your model with a prompt and an image or audio file.</p></div>';$('#prompt').value='';$('#status').textContent='';$('#notice').hidden=true;showAttachment();update();$('#prompt').focus();};
$('#composer').onsubmit=e=>{e.preventDefault();if($('#send').disabled)return;const prompt=$('#prompt').value.trim();const file=attachment;const current=++epoch;busy=true;update();$('#status').textContent=file?.type==='audio'?'Transcribing audio…':file?'Processing image…':'Generating response…';setTimeout(()=>{if(current!==epoch)return;busy=false;if(file&&$('#model').value==='unknown'){notice('This model rejected the attachment. Select a model with supported image or audio capabilities, then retry.');$('#status').textContent='Request failed.';update();return;}message('You',prompt||'Describe this file.',file?(file.type==='image'?`<img src="${file.url}" alt="${escape(file.name)}">`:`<p>Audio: ${escape(file.name)}</p><audio controls src="${file.url}"></audio>`):'');if(file?.type==='audio')message('Transcription','Please summarize the project update and identify the next steps.');message('Model',file?.type==='image'?'Sample response: The uploaded image is ready for visual analysis. In the connected product, the model would describe its contents.':file?.type==='audio'?'Sample response: The project update asks for a summary and next steps. Confirm the owner and schedule a follow-up.':'Sample response: I can help explore your prompt. This prototype returns illustrative text.');if(file)used=true;attachment=null;$('#prompt').value='';$('#status').textContent='Response complete · Simulated inference';showAttachment();update();},900);};
if(['audio-complete','no-asr','asr-error','silent-audio'].includes(scenario))$('#model').value='audio';
if(scenario==='text-only')$('#model').value='text';
if(scenario==='unsupported-model')$('#model').value='unknown';
if(scenario==='image-complete'){used=true;message('You','What does this chart show?','<img src="sample-image.svg" alt="Sample bar chart with sales increasing from January to March">');message('Model','Sales increased each month, from 24 in January to 61 in March. March has the highest sales.');}
if(scenario==='audio-complete'){used=true;message('You','Summarize the uploaded meeting audio.','<p>Audio: project-update.wav · Silent placeholder; transcription below is sample data.</p><audio controls src="sample-audio.wav" aria-label="Uploaded meeting audio"></audio>');message('Transcription','The prototype is ready. Next, schedule a design review.');message('Model','The prototype is ready for review. The next step is to schedule a design review.');$('#asr').value=asrAssets.length?'0':'';}
if(scenario==='oversize')notice('landscape.png exceeds the 10 MB prototype limit. No file was uploaded. Choose a smaller file.');
if(scenario==='asr-error')notice('Transcription failed: the audio model is unavailable. No prompt was sent. Choose another audio model or upload again.');
if(scenario==='silent-audio')notice('No speech was detected. No prompt was sent. Upload a recording with audible speech.');
if(scenario==='unsupported-model')notice('This model rejected image input. Choose a vision-enabled model and retry.');
if(scenario==='text-only')notice('This model supports text only. Choose a different model to use image or audio input.','info');
update();
});
