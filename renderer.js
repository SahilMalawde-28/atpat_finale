// renderer.js (adapted)

const startBtn = document.getElementById('start');
const endBtn = document.getElementById('end');
const downloadBtn = document.getElementById('download');
const linkInput = document.getElementById('link');
const warnings = document.getElementById('warnings');
const preview = document.getElementById('preview');
const webwrap = document.getElementById('webwrap');
const thankyou = document.getElementById('thankyou');

let webview = null;
let parsed = null;

function addWarning(txt){
  if(warnings.innerText==="No warnings yet.") warnings.innerText="";
  const div = document.createElement('div');
  div.innerText = `[${new Date().toLocaleTimeString()}] ${txt}`;
  warnings.appendChild(div);
  warnings.scrollTop = warnings.scrollHeight;
}

// Start Test
startBtn.addEventListener('click', async ()=>{
  const raw = linkInput.value.trim();
  const parts = raw.split(':ATPAT=');
  if(parts.length !== 2){ alert("Invalid format"); return; }
  parsed = { parent: parts[0].startsWith("http")? parts[0] : "https://"+parts[0], id: parts[1] };

  // start python proctor (which will start Flask stream)
  window.electronAPI.startProctor();

  // set preview to python stream
  preview.src = "http://127.0.0.1:5000/video_feed";

  webwrap.innerHTML = "";
  webview = document.createElement('webview');
  webview.src = parsed.parent;
  webwrap.appendChild(webview);

  startBtn.disabled = true;
  endBtn.disabled = false;
  addWarning("Test started");
});




// End Test
endBtn.addEventListener('click', ()=>{
  window.electronAPI.stopProctor();
  endBtn.disabled = true;
  downloadBtn.disabled = false;
  webwrap.style.display="none";
  preview.style.display="none";
  thankyou.style.display="flex";
  addWarning("Test ended");
});

// Download Report
downloadBtn.addEventListener('click', async ()=>{
  const res = await window.electronAPI.requestReport();
  if(res && res.ok) alert("Report saved: "+res.path);
  else alert("Report not ready yet.");
});

// Focus / tab switching
window.addEventListener('blur', ()=> {
  addWarning("Focus lost (possible tab switch)");
  // optional: trigger screenshot command to python via ipc if implemented
});
document.addEventListener('visibilitychange', ()=> {
  if(document.visibilityState!=='visible'){
    addWarning("Window hidden / tab switch");
  }
});

// Python events
window.electronAPI.onPythonEvent((msg)=>{
  if(msg.type==='flag' && msg.flag){
    addWarning(msg.flag.type+" - "+msg.flag.detail);
  } else if(msg.type==='info'){
    addWarning("INFO: "+msg.msg);
  } else {
    // log arbitrary messages
    addWarning(JSON.stringify(msg));
  }
});

