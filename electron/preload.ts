/**
 * Heretek Swarm - Preload Script
 * 
 * Exposes safe, limited APIs to the renderer process via contextBridge.
 * All IPC communication goes through here to maintain security.
 */

import { contextBridge, ipcRenderer } from 'electron';

// Type definitions for exposed API
export interface DataPaths {
    dataDir: string;
    configFile: string;
    logsDir: string;
    dataSubdir: string;
    cacheDir: string;
}

export interface HeretekConfig {
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

export interface ModelProviderConfig {
    id: string;
    type: 'openai' | 'ollama' | 'minimax' | 'zai' | 'anthropic';
    name: string;
    baseUrl: string;
    apiKey?: string;
    defaultModel: string;
    isEnabled: boolean;
}

export interface DockerStatus {
    available: boolean;
    version: string | null;
    error: string | null;
}

export interface AppInfo {
    version: string;
    electron: string;
    chrome: string;
    node: string;
    platform: string;
    arch: string;
}

export interface FileResult {
    success: boolean;
    content?: string;
    error?: string;
}

export interface DialogResult {
    canceled: boolean;
    filePaths?: string[];
    filePath?: string;
}

// Define the API exposed to renderer
const heretekAPI = {
    // Data paths
    getDataPaths: (): Promise<DataPaths> => 
        ipcRenderer.invoke('get-data-paths'),
    
    // Configuration
    getConfig: (): Promise<HeretekConfig> => 
        ipcRenderer.invoke('get-config'),
    
    saveConfig: (config: Partial<HeretekConfig>): Promise<HeretekConfig> => 
        ipcRenderer.invoke('save-config', config),
    
    // Docker
    checkDocker: (): Promise<DockerStatus> => 
        ipcRenderer.invoke('check-docker'),
    
    // App info
    getAppInfo: (): Promise<AppInfo> => 
        ipcRenderer.invoke('get-app-info'),
    
    // File operations
    readFile: (filePath: string): Promise<FileResult> => 
        ipcRenderer.invoke('read-file', filePath),
    
    writeFile: (filePath: string, content: string): Promise<FileResult> => 
        ipcRenderer.invoke('write-file', filePath, content),
    
    // External links
    openExternal: (url: string): Promise<{ success: boolean }> => 
        ipcRenderer.invoke('open-external', url),
    
    // Dialogs
    showOpenDialog: (options: Electron.OpenDialogOptions): Promise<DialogResult> => 
        ipcRenderer.invoke('show-open-dialog', options),
    
    showSaveDialog: (options: Electron.SaveDialogOptions): Promise<DialogResult> => 
        ipcRenderer.invoke('show-save-dialog', options),
    
    // Event listeners for main process messages
    onStartServices: (callback: () => void) => {
        const handler = () => callback();
        ipcRenderer.on('start-services', handler);
        return () => ipcRenderer.removeListener('start-services', handler);
    },
    
    onStopServices: (callback: () => void) => {
        const handler = () => callback();
        ipcRenderer.on('stop-services', handler);
        return () => ipcRenderer.removeListener('stop-services', handler);
    },
    
    onOpenSettings: (callback: () => void) => {
        const handler = () => callback();
        ipcRenderer.on('open-settings', handler);
        return () => ipcRenderer.removeListener('open-settings', handler);
    }
};

// Expose API to renderer via contextBridge
contextBridge.exposeInMainWorld('heretek', heretekAPI);

// Type declaration for renderer
declare global {
    interface Window {
        heretek: typeof heretekAPI;
    }
}
