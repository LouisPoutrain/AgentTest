const { downloadArtifact } = require('@electron/get');
const extract = require('extract-zip');
const path = require('path');
const fs = require('fs');

async function downloadAndExtract() {
  try {
    console.log('Downloading Electron binary...');
    const zipPath = await downloadArtifact({
      version: '32.3.3',
      artifactName: 'electron',
      platform: process.platform,
      arch: process.arch
    });

    console.log('Downloaded to:', zipPath);
    
    const distPath = path.join(__dirname, 'node_modules', 'electron', 'dist');
    if (!fs.existsSync(distPath)) {
      fs.mkdirSync(distPath, { recursive: true });
    }

    console.log('Extracting to:', distPath);
    await extract(zipPath, { dir: distPath });
    
    // Write path.txt
    const pathTxt = process.platform === 'darwin' 
      ? 'Electron.app/Contents/MacOS/Electron' 
      : 'electron';
    
    fs.writeFileSync(path.join(__dirname, 'node_modules', 'electron', 'path.txt'), pathTxt);
    
    console.log('Electron successfully installed manually!');
  } catch (error) {
    console.error('Failed to download Electron:', error);
  }
}

downloadAndExtract();
