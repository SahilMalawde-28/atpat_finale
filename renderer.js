const startBtn = document.getElementById('start');
const endBtn = document.getElementById('end');
const downloadBtn = document.getElementById('download');
const linkInput = document.getElementById('link');
const warnings = document.getElementById('warnings');
const preview = document.getElementById('preview');
const webwrap = document.getElementById('webwrap');
const thankyou = document.getElementById('thankyou');

let webview=null, parsed=null, stream=null;

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
    if(parts.length!==2){ alert("Invalid format"); return; }
    parsed = { parent: parts[0].startsWith("http")? parts[0] : "https://"+parts[0], id: parts[1] };

    webwrap.innerHTML = "";
    webview = document.createElement('webview');
    webview.src = parsed.parent;
    webwrap.appendChild(webview);
    
    // after creating webview
	webview.style.width = "100%";
	webview.style.height = "100%";
	webview.style.border = "none";


    window.electronAPI.sendToPython({ type:'start', ts: Date.now(), meta: parsed });

    startBtn.disabled = true;
    endBtn.disabled = false;
    addWarning("Test started");
});

// End Test
endBtn.addEventListener('click', ()=>{
    window.electronAPI.sendToPython({ type:'end' });
    endBtn.disabled = true;
    downloadBtn.disabled = false;
    webwrap.style.display="none";
    preview.style.display="none";
    thankyou.style.display="flex";
    addWarning("Test ended");
});

// Download Report (dummy pdf for demo)
downloadBtn.addEventListener('click', async ()=>{
    const pdfContent = "%PDF-1.4\n%Dummy PDF content for demo";
    const res = await window.electronAPI.requestReport(pdfContent);
    if(res.ok) alert("Report saved: "+res.path);
});

// Tab / focus
window.addEventListener('blur', ()=> {
    addWarning("Focus lost (possible tab switch)");
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
    }
});

