const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    sendToPython: (msg)=>ipcRenderer.send(msg.type==='start'?'start-proctor':'end-proctor', msg.meta),
    requestReport: (data)=>ipcRenderer.invoke('save-report', data),
    onPythonEvent: (cb)=>ipcRenderer.on('python-event',(e,msg)=>cb(msg))
});

