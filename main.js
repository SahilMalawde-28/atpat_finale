// main.js
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const fetch = require('node-fetch'); 



let proctorInfo = {mis_id:"612303156",parenturl:"https://moodle.coeptech.ac.in/my/"};

//ipcMain.on('set-proctor-info', (event, data) => {
//  proctorInfo = data;
//  console.log('Received proctor info:', proctorInfo);
//});





let win;
let pyProc = null;
let pyStdoutBuffer = "";

async function sendReportToServer(reportData) {
  try {
    const response = await fetch("http://localhost:5000/api/flag_routes/postflags", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(reportData),
    });

    const result = await response.json();
    console.log("✅ Report uploaded successfully:", result);
    if (win) win.webContents.send("python-event", { type: "info", msg: "Report uploaded to server." });
  } catch (err) {
    console.error("❌ Error uploading report:", err);
    if (win) win.webContents.send("python-event", { type: "error", msg: `Upload failed: ${err.message}` });
  }
}

function createWindow(){
  win = new BrowserWindow({
    width: 1200, height: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webviewTag: true
    }
  });
  win.loadFile('index.html');
}

app.whenReady().then(createWindow);

ipcMain.on('start-proctor', (e, arg) => {
  if (pyProc) return;
  const pyPath = path.join(__dirname, 'python', 'proctor.py');
  pyProc = spawn('python3', [pyPath], { cwd: __dirname });

  pyProc.stdout.on('data', (data) => {
    const text = data.toString();
    // split by newline and try parse JSON lines
    pyStdoutBuffer += text;
    let idx;
    while ((idx = pyStdoutBuffer.indexOf('\n')) >= 0) {
      const line = pyStdoutBuffer.slice(0, idx).trim();
      pyStdoutBuffer = pyStdoutBuffer.slice(idx+1);
      if (!line) continue;
      try {
  const obj = JSON.parse(line);

  // ✅ Detect final report and send to backend
  if (obj.type === "final_report") {
    console.log("📤 Sending final report to backend...");
    sendReportToServer({...obj.data,
    mis_id:proctorInfo.mis_id,
    parenturl:proctorInfo.parenturl
    });
  }

  win.webContents.send('python-event', obj);
} catch (err) {
  win.webContents.send('python-event', { type: 'log', msg: line });
}
    }
  });

  pyProc.stderr.on('data', (d) => {
    win.webContents.send('python-event', { type: 'stderr', msg: d.toString() });
  });

  pyProc.on('exit', (code) => {
    win.webContents.send('python-event', { type: 'info', msg: `Python exited (${code})`});
    pyProc = null;
  });

  win.webContents.send('python-event', { type:'info', msg:'Python proctor started' });
});

ipcMain.on('stop-proctor', (e, arg) => {
  if (!pyProc) return;
  try {
    // ask python to stop politely via stdin "stop\n"
    pyProc.stdin.write(JSON.stringify({cmd:'stop'}) + "\n");
  } catch (err) {
    // fallback kill
    pyProc.kill();
  }
});

ipcMain.handle('request-report', async (e) => {
  const reportPath = path.join(__dirname, 'out', 'report.pdf');
  if (fs.existsSync(reportPath)) {
    const { canceled, filePath } = await dialog.showSaveDialog(win, { defaultPath: "proctor_report.pdf" });
    if (!canceled && filePath) {
      fs.copyFileSync(reportPath, filePath);
      return { ok: true, path: filePath };
    }
    return { ok:false };
  } else {
    return { ok:false, msg: "Report not found yet." };
  }
});


