// preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  startProctor: () => ipcRenderer.send('start-proctor'),
  stopProctor: () => ipcRenderer.send('stop-proctor'),
  requestReport: () => ipcRenderer.invoke('request-report'),
  onPythonEvent: (cb) => ipcRenderer.on('python-event', (e, msg) => cb(msg))
});

