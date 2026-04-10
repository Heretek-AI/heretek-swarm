"""
Heretek Swarm - Desktop Application Entry Point

Electron main process for the Heretek Swarm desktop application.
Handles window management, IPC communication, and data directory management.

Data Directory: ~/.heretek-swarm/
- config.json: Application configuration
- logs/: Application logs
- data/: Runtime data (sessions, states, memories)
- cache/: Temporary cache files
"""

import { app, BrowserWindow, ipcMain, dialog, shell, Menu, Tray, nativeImage } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import log from 'electron-log';

// ============================================================================
// Configuration
// ============================================================================

const HERETEK_DATA_DIR = path.join(app.getPath('home'), '.heretek-swarm');
const HERETEK_CONFIG_FILE = path.join(HERETEK_DATA_DIR, 'config.json');
const HERETEK_LOGS_DIR = path.join(HERETEK_DATA_DIR, 'logs');
const HERETEK_DATA_SUBDIR = path.join(HERETEK_DATA_DIR, 'data');
const HERETEK_CACHE_DIR = path.join(HERETEK_DATA_DIR, 'cache');

// Ensure data directory structure exists
function ensureDataDirectories(): void {
    const dirs = [HERETEK_DATA_DIR, HERETEK_LOGS_DIR, HERETEK_DATA_SUBDIR, HERETEK_CACHE_DIR];
    for (const dir of dirs) {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
            log.info(`Created directory: ${dir}`);
        }
    }
}

// ============================================================================
// Logging Configuration
// ============================================================================

function configureLogging(): void {
    log.transports.file.level = 'info';
    log.transports.file.resolvePathFn = () => path.join(HERETEK_LOGS_DIR, 'heretek-swarm.log');
    log.transports.console.level = 'debug';
    
    // Configure log format
    log.transports.file.format = '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}';
    
    log.info('='.repeat(60));
    log.info('Heretek Swarm Desktop Starting');
    log.info(`Data Directory: ${HERETEK_DATA_DIR}`);
    log.info(`App Version: ${app.getVersion()}`);
    log.info(`Electron: ${process.versions.electron}`);
    log.info(`Chrome: ${process.versions.chrome}`);
    log.info(`Node: ${process.versions.node}`);
    log.info('='.repeat(60));
}

// ============================================================================
// Global State
// ============================================================================

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let isQuitting = false;

// ============================================================================
// Docker Detection
// ============================================================================

interface DockerStatus {
    available: boolean;
    version: string | null;
    error: string | null;
}

async function checkDockerStatus(): Promise<DockerStatus> {
    const { execSync } = require('child_process');
    
    try {
        const version = execSync('docker --version', { encoding: 'utf8' }).trim();
        log.info(`Docker detected: ${version}`);
        return {
            available: true,
            version: version,
            error: null
        };
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        log.warn(`Docker not available: ${errorMessage}`);
        return {
            available: false,
            version: null,
            error: errorMessage
        };
    }
}

// ============================================================================
// Configuration Management
// ============================================================================

interface HeretekConfig {
    version: string;
    theme: 'dark' | 'light' | 'system';
    language: string;
    autoStart: boolean;
    minimizeToTray: boolean;
    dockerEnabled: boolean;
    apiUrl: string;
    prometheusUrl: string;
    lokiUrl: string;
    modelProviders: ModelProviderConfig[];
    lastOpened?: string;
}

interface ModelProviderConfig {
    id: string;
    type: 'openai' | 'ollama' | 'minimax' | 'zai' | 'anthropic';
    name: string;
    baseUrl: string;
    apiKey?: string;
    defaultModel: string;
    isEnabled: boolean;
}

const DEFAULT_CONFIG: HeretekConfig = {
    version: '1.0.0',
    theme: 'dark',
    language: 'en',
    autoStart: false,
    minimizeToTray: true,
    dockerEnabled: true,
    apiUrl: 'http://localhost:8000',
    prometheusUrl: 'http://localhost:9090',
    lokiUrl: 'http://localhost:3100',
    modelProviders: [
        {
            id: 'default-ollama',
            type: 'ollama',
            name: 'Local Ollama',
            baseUrl: 'http://localhost:11434',
            defaultModel: 'llama3.1',
            isEnabled: true
        }
    ]
};

function loadConfig(): HeretekConfig {
    try {
        if (fs.existsSync(HERETEK_CONFIG_FILE)) {
            const data = fs.readFileSync(HERETEK_CONFIG_FILE, 'utf8');
            const config = JSON.parse(data) as Partial<HeretekConfig>;
            log.info('Configuration loaded from file');
            return { ...DEFAULT_CONFIG, ...config };
        }
    } catch (error) {
        log.error('Failed to load configuration:', error);
    }
    
    log.info('Using default configuration');
    return { ...DEFAULT_CONFIG };
}

function saveConfig(config: HeretekConfig): void {
    try {
        fs.writeFileSync(HERETEK_CONFIG_FILE, JSON.stringify(config, null, 2), 'utf8');
        log.info('Configuration saved');
    } catch (error) {
        log.error('Failed to save configuration:', error);
    }
}

// ============================================================================
// Window Management
// ============================================================================

function createWindow(): void {
    log.info('Creating main window...');
    
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        backgroundColor: '#0f172a',
        show: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js'),
            sandbox: true
        },
        titleBarStyle: 'hiddenInset',
        frame: process.platform === 'darwin' ? true : false,
        autoHideMenuBar: false
    });
    
    // Set up application menu
    createApplicationMenu();
    
    // Load the app
    if (process.env.NODE_ENV === 'development' || process.argv.includes('--dev')) {
        mainWindow.loadURL('http://localhost:5173');
        mainWindow.webContents.openDevTools();
        log.info('Running in development mode');
    } else {
        const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
        mainWindow.loadFile(indexPath);
        log.info(`Loading production build: ${indexPath}`);
    }
    
    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        log.info('Main window ready to show');
        mainWindow?.show();
        
        // Update last opened
        const config = loadConfig();
        config.lastOpened = new Date().toISOString();
        saveConfig(config);
    });
    
    // Handle window close
    mainWindow.on('close', (event) => {
        if (!isQuitting && loadConfig().minimizeToTray) {
            event.preventDefault();
            mainWindow?.hide();
            log.info('Window hidden to tray');
        }
    });
    
    mainWindow.on('closed', () => {
        mainWindow = null;
        log.info('Main window closed');
    });
    
    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });
    
    log.info('Main window created successfully');
}

// ============================================================================
// System Tray
// ============================================================================

function createTray(): void {
    // Create a simple 16x16 tray icon
    const iconPath = path.join(__dirname, '..', 'resources', 'tray-icon.png');
    let trayIcon: nativeImage;
    
    if (fs.existsSync(iconPath)) {
        trayIcon = nativeImage.createFromPath(iconPath);
    } else {
        // Create a simple default icon
        trayIcon = nativeImage.createEmpty();
    }
    
    tray = new Tray(trayIcon);
    
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Open Heretek Swarm',
            click: () => {
                mainWindow?.show();
            }
        },
        { type: 'separator' },
        {
            label: 'Start Services',
            click: () => {
                mainWindow?.webContents.send('start-services');
            }
        },
        {
            label: 'Stop Services',
            click: () => {
                mainWindow?.webContents.send('stop-services');
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true;
                app.quit();
            }
        }
    ]);
    
    tray.setToolTip('Heretek Swarm - AI Agent Collective');
    tray.setContextMenu(contextMenu);
    
    tray.on('click', () => {
        mainWindow?.show();
    });
    
    log.info('System tray created');
}

// ============================================================================
// Application Menu
// ============================================================================

function createApplicationMenu(): void {
    const template: Electron.MenuItemConstructorOptions[] = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Open Data Folder',
                    click: () => {
                        shell.openPath(HERETEK_DATA_DIR);
                    }
                },
                { type: 'separator' },
                {
                    label: 'Settings',
                    accelerator: 'CmdOrCtrl+,',
                    click: () => {
                        mainWindow?.webContents.send('open-settings');
                    }
                },
                { type: 'separator' },
                { role: 'quit' }
            ]
        },
        {
            label: 'Edit',
            submenu: [
                { role: 'undo' },
                { role: 'redo' },
                { type: 'separator' },
                { role: 'cut' },
                { role: 'copy' },
                { role: 'paste' },
                { role: 'selectAll' }
            ]
        },
        {
            label: 'View',
            submenu: [
                { role: 'reload' },
                { role: 'forceReload' },
                { role: 'toggleDevTools' },
                { type: 'separator' },
                { role: 'resetZoom' },
                { role: 'zoomIn' },
                { role: 'zoomOut' },
                { type: 'separator' },
                { role: 'togglefullscreen' }
            ]
        },
        {
            label: 'Services',
            submenu: [
                {
                    label: 'Start All Services',
                    click: () => {
                        mainWindow?.webContents.send('start-services');
                    }
                },
                {
                    label: 'Stop All Services',
                    click: () => {
                        mainWindow?.webContents.send('stop-services');
                    }
                },
                { type: 'separator' },
                {
                    label: 'View Logs',
                    click: () => {
                        shell.openPath(HERETEK_LOGS_DIR);
                    }
                },
                {
                    label: 'View Prometheus',
                    click: () => {
                        shell.openExternal('http://localhost:9090');
                    }
                }
            ]
        },
        {
            label: 'Window',
            submenu: [
                { role: 'minimize' },
                { role: 'zoom' },
                { type: 'separator' },
                { role: 'close' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: () => {
                        shell.openExternal('https://github.com/heretek-ai/heretek-swarm');
                    }
                },
                {
                    label: 'Report Issue',
                    click: () => {
                        shell.openExternal('https://github.com/heretek-ai/heretek-swarm/issues');
                    }
                },
                { type: 'separator' },
                {
                    label: 'About',
                    click: () => {
                        dialog.showMessageBox({
                            type: 'info',
                            title: 'About Heretek Swarm',
                            message: 'Heretek Swarm',
                            detail: `Version: ${app.getVersion()}\n\nA 23-agent autonomous AI collective for intelligent task processing.`
                        });
                    }
                }
            ]
        }
    ];
    
    // macOS specific menu adjustments
    if (process.platform === 'darwin') {
        template.unshift({
            label: app.getName(),
            submenu: [
                { role: 'about' },
                { type: 'separator' },
                { role: 'services' },
                { type: 'separator' },
                { role: 'hide' },
                { role: 'hideOthers' },
                { role: 'unhide' },
                { type: 'separator' },
                { role: 'quit' }
            ]
        });
    }
    
    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

// ============================================================================
// IPC Handlers
// ============================================================================

function setupIpcHandlers(): void {
    // Get data directory paths
    ipcMain.handle('get-data-paths', () => {
        return {
            dataDir: HERETEK_DATA_DIR,
            configFile: HERETEK_CONFIG_FILE,
            logsDir: HERETEK_LOGS_DIR,
            dataSubdir: HERETEK_DATA_SUBDIR,
            cacheDir: HERETEK_CACHE_DIR
        };
    });
    
    // Get configuration
    ipcMain.handle('get-config', () => {
        return loadConfig();
    });
    
    // Save configuration
    ipcMain.handle('save-config', (_event, config: Partial<HeretekConfig>) => {
        const currentConfig = loadConfig();
        const newConfig = { ...currentConfig, ...config };
        saveConfig(newConfig);
        return newConfig;
    });
    
    // Check Docker status
    ipcMain.handle('check-docker', async () => {
        return await checkDockerStatus();
    });
    
    // Get app info
    ipcMain.handle('get-app-info', () => {
        return {
            version: app.getVersion(),
            electron: process.versions.electron,
            chrome: process.versions.chrome,
            node: process.versions.node,
            platform: process.platform,
            arch: process.arch
        };
    });
    
    // Read file
    ipcMain.handle('read-file', async (_event, filePath: string) => {
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            return { success: true, content };
        } catch (error) {
            return { success: false, error: String(error) };
        }
    });
    
    // Write file
    ipcMain.handle('write-file', async (_event, filePath: string, content: string) => {
        try {
            fs.writeFileSync(filePath, content, 'utf8');
            return { success: true };
        } catch (error) {
            return { success: false, error: String(error) };
        }
    });
    
    // Open external URL
    ipcMain.handle('open-external', async (_event, url: string) => {
        await shell.openExternal(url);
        return { success: true };
    });
    
    // Show open dialog
    ipcMain.handle('show-open-dialog', async (_event, options: Electron.OpenDialogOptions) => {
        return await dialog.showOpenDialog(mainWindow!, options);
    });
    
    // Show save dialog
    ipcMain.handle('show-save-dialog', async (_event, options: Electron.SaveDialogOptions) => {
        return await dialog.showSaveDialog(mainWindow!, options);
    });
    
    log.info('IPC handlers registered');
}

// ============================================================================
// Application Lifecycle
// ============================================================================

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) {
    app.quit();
}

app.whenReady().then(async () => {
    log.info('App ready event received');
    
    // Initialize data directories
    ensureDataDirectories();
    
    // Configure logging
    configureLogging();
    
    // Check Docker availability
    const dockerStatus = await checkDockerStatus();
    
    // Set up IPC handlers
    setupIpcHandlers();
    
    // Create main window
    createWindow();
    
    // Create system tray
    createTray();
    
    // Log startup complete
    log.info('Application startup complete');
    log.info(`Docker available: ${dockerStatus.available}`);
    
    if (!dockerStatus.available) {
        log.warn('Docker not detected - services will not be available');
    }
    
    // Handle macOS activation
    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        } else {
            mainWindow?.show();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    isQuitting = true;
    log.info('Application shutting down...');
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    log.error('Uncaught exception:', error);
    dialog.showErrorBox('Error', `An unexpected error occurred: ${error.message}`);
});

process.on('unhandledRejection', (reason, promise) => {
    log.error('Unhandled rejection at:', promise, 'reason:', reason);
});

// ============================================================================
// Export for type checking
// ============================================================================

export type { HeretekConfig, ModelProviderConfig, DockerStatus };
