const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let win;
let pythonProcess = null;

function createWindow() {
   win = new BrowserWindow({
    width: 1200,
    height: 700,
    webPreferences: {
        preload: path.join(__dirname,'preload.js'),
        contextIsolation: true,
        nodeIntegration: false,
        webviewTag: true   // <--- enable webview
    }
});

    win.loadFile('index.html');
}

app.whenReady().then(createWindow);

ipcMain.on('start-proctor', (e, meta) => {
    if (pythonProcess) return;
    pythonProcess = spawn('python3', [path.join(__dirname,'python/proctor.py')]);
    pythonProcess.stdout.on('data', (data)=>{
        try{
            const msg = JSON.parse(data.toString());
            win.webContents.send('python-event', msg);
        }catch{}
    });
    pythonProcess.stderr.on('data', (d)=>console.error('py err:', d.toString()));
});

ipcMain.on('end-proctor', ()=>{
    if(pythonProcess){
        pythonProcess.kill();
        pythonProcess = null;
    }
});

ipcMain.handle('save-report', async (e, report)=>{
    const { filePath } = await dialog.showSaveDialog(win, { 
        title:'Save Report PDF', 
        defaultPath:'report.pdf' 
    });
    if(filePath){
        const fs = require('fs');
        fs.writeFileSync(filePath, report);
        return { ok:true, path:filePath };
    }
    return { ok:false };
});

