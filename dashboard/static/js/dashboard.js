// CinePi Dashboard - Main JavaScript
class CinePiDashboard {
    constructor() {
        this.ws = null;
        this.statusInterval = null;
        this.isConnected = false;
        this.currentSession = null;
        this.cameraStatus = null;
        this.systemStatus = null;
        this.streamActive = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.connectWebSocket();
        this.startStatusPolling();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Capture controls
        document.getElementById('startCapture')?.addEventListener('click', () => this.startCapture());
        document.getElementById('stopCapture')?.addEventListener('click', () => this.stopCapture());
        document.getElementById('takeSnapshot')?.addEventListener('click', () => this.takeSnapshot());
        
        // Settings controls
        document.getElementById('updateSettings')?.addEventListener('click', () => this.updateSettings());
        document.getElementById('refreshSettings')?.addEventListener('click', () => this.loadSettings());
        document.getElementById('resetSettings')?.addEventListener('click', () => this.resetSettings());
        
        // Interval slider
        const intervalSlider = document.getElementById('intervalSlider');
        if (intervalSlider) {
            intervalSlider.addEventListener('input', (e) => {
                this.updateIntervalDisplay(e.target.value);
            });
            intervalSlider.addEventListener('change', (e) => {
                this.updateInterval(e.target.value);
            });
        }

        // Settings form
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.updateSettings();
            });
        }

        // Camera settings sliders and controls
        this.setupSettingsControls();

        // Real-time toggle
        const realtimeToggle = document.getElementById('realtimeToggle');
        if (realtimeToggle) {
            realtimeToggle.addEventListener('change', (e) => {
                this.toggleRealtime(e.target.checked);
            });
        }
    }

    setupSettingsControls() {
        // ISO slider
        const isoSlider = document.getElementById('isoSlider');
        if (isoSlider) {
            isoSlider.addEventListener('input', (e) => {
                this.updateIsoDisplay(e.target.value);
            });
        }

        // Gain slider
        const gainSlider = document.getElementById('gainSlider');
        if (gainSlider) {
            gainSlider.addEventListener('input', (e) => {
                this.updateGainDisplay(e.target.value);
            });
        }

        // Exposure toggle
        const exposureToggle = document.getElementById('exposure');
        if (exposureToggle) {
            exposureToggle.addEventListener('change', (e) => {
                this.updateExposureLabel(e.target.checked);
            });
        }
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadStatus(),
                this.loadSettings(),
                this.loadRecentCaptures()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading dashboard data', 'error');
        }
    }

    async loadStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Failed to load status');
            
            const data = await response.json();
            this.updateStatusDisplay(data);
        } catch (error) {
            console.error('Error loading status:', error);
            this.updateStatusDisplay({ error: 'Failed to load status' });
        }
    }

    async loadSettings() {
        try {
            this.updateSettingsStatus('loading', 'Loading settings...');
            
            const [settingsResponse, parametersResponse] = await Promise.all([
                fetch('/api/camera/settings'),
                fetch('/api/camera/parameters')
            ]);
            
            if (!settingsResponse.ok) throw new Error('Failed to load settings');
            if (!parametersResponse.ok) throw new Error('Failed to load parameters');
            
            const settings = await settingsResponse.json();
            const parameters = await parametersResponse.json();
            
            this.updateSettingsDisplay(settings, parameters);
            this.updateSettingsStatus('ready', 'Settings loaded');
        } catch (error) {
            console.error('Error loading settings:', error);
            this.showNotification('Error loading camera settings', 'error');
            this.updateSettingsStatus('error', 'Failed to load settings');
        }
    }

    async loadRecentCaptures() {
        try {
            const response = await fetch('/api/capture/list?limit=10');
            if (!response.ok) throw new Error('Failed to load captures');
            
            const data = await response.json();
            this.updateCapturesDisplay(data.captures || []);
        } catch (error) {
            console.error('Error loading captures:', error);
        }
    }

    updateStatusDisplay(data) {
        // Update camera status
        if (data.camera) {
            this.cameraStatus = data.camera;
            this.updateCameraStatusCard(data.camera);
        }

        // Update session status
        if (data.session) {
            this.currentSession = data.session;
            this.updateSessionStatusCard(data.session);
            this.updateCaptureStatusIndicators(data.session);
            this.updateProgressBar(data.session);
        }

        // Update system status
        if (data.system) {
            this.systemStatus = data.system;
            this.updateSystemStatusCard(data.system);
        }

        // Update connection status
        this.updateConnectionStatus();
    }

    updateCameraStatusCard(camera) {
        const card = document.getElementById('cameraStatusCard');
        if (!card) return;

        const statusIndicator = card.querySelector('.status-indicator');
        const statusText = card.querySelector('.status-text');
        const connectedText = card.querySelector('.connected-text');
        const errorText = card.querySelector('.error-text');

        if (statusIndicator) {
            statusIndicator.className = `status-indicator ${camera.connected ? 'online' : 'offline'}`;
        }

        if (statusText) {
            statusText.textContent = camera.status || 'Unknown';
        }

        if (connectedText) {
            connectedText.textContent = camera.connected ? 'Connected' : 'Disconnected';
        }

        if (errorText) {
            if (camera.error) {
                errorText.textContent = camera.error;
                errorText.style.display = 'block';
            } else {
                errorText.style.display = 'none';
            }
        }
    }

    updateSessionStatusCard(session) {
        const card = document.getElementById('sessionStatusCard');
        if (!card) return;

        const statusText = card.querySelector('.status-text');
        const capturesText = card.querySelector('.captures-text');
        const intervalText = card.querySelector('.interval-text');
        const elapsedText = card.querySelector('.elapsed-text');

        if (statusText) {
            statusText.textContent = session.status || 'Inactive';
        }

        if (capturesText) {
            capturesText.textContent = session.captures || 0;
        }

        if (intervalText && session.interval) {
            intervalText.textContent = `${session.interval}s`;
        }

        if (elapsedText && session.elapsed_time) {
            elapsedText.textContent = this.formatDuration(session.elapsed_time);
        }
    }

    updateSystemStatusCard(system) {
        const card = document.getElementById('systemStatusCard');
        if (!card) return;

        const cpuText = card.querySelector('.cpu-text');
        const memoryText = card.querySelector('.memory-text');
        const diskText = card.querySelector('.disk-text');
        const uptimeText = card.querySelector('.uptime-text');

        if (cpuText) {
            cpuText.textContent = `${system.cpu_usage || 0}%`;
        }

        if (memoryText) {
            memoryText.textContent = `${system.memory_usage || 0}%`;
        }

        if (diskText) {
            diskText.textContent = `${system.disk_usage || 0}%`;
        }

        if (uptimeText) {
            uptimeText.textContent = this.formatDuration(system.uptime || 0);
        }
    }

    updateSettingsDisplay(settings, parameters = null) {
        // Update form fields with new UI elements
        const isoSlider = document.getElementById('isoSlider');
        const gainSlider = document.getElementById('gainSlider');
        const exposureToggle = document.getElementById('exposure');
        const resolutionInput = document.getElementById('resolution');

        // Update ISO slider
        if (isoSlider) {
            const isoValue = settings.iso || 400;
            isoSlider.value = isoValue;
            this.updateIsoDisplay(isoValue);
            
            // Update slider range if parameters provided
            if (parameters && parameters.iso) {
                isoSlider.min = parameters.iso.min || 100;
                isoSlider.max = parameters.iso.max || 800;
                isoSlider.step = parameters.iso.step || 100;
            }
        }

        // Update Gain slider
        if (gainSlider) {
            const gainValue = settings.gain || 2.0;
            gainSlider.value = gainValue;
            this.updateGainDisplay(gainValue);
            
            // Update slider range if parameters provided
            if (parameters && parameters.gain) {
                gainSlider.min = parameters.gain.min || 1.0;
                gainSlider.max = parameters.gain.max || 8.0;
                gainSlider.step = parameters.gain.step || 0.1;
            }
        }

        // Update Exposure toggle
        if (exposureToggle) {
            const isManual = settings.exposure_mode === 'manual';
            exposureToggle.checked = isManual;
            this.updateExposureLabel(isManual);
        }

        // Update Resolution dropdown
        if (resolutionInput) {
            resolutionInput.value = settings.resolution || '4056x3040';
            
            // Update options if parameters provided
            if (parameters && parameters.resolutions) {
                resolutionInput.innerHTML = '';
                parameters.resolutions.forEach(res => {
                    const option = document.createElement('option');
                    option.value = res;
                    option.textContent = res;
                    resolutionInput.appendChild(option);
                });
                resolutionInput.value = settings.resolution || parameters.resolutions[0];
            }
        }

        // Update current settings display
        this.updateCurrentSettingsDisplay(settings);
    }

    updateCurrentSettingsDisplay(settings) {
        const container = document.getElementById('currentSettings');
        if (!container) return;

        container.innerHTML = `
            <div class="settings-grid">
                <div class="form-group">
                    <label>ISO</label>
                    <div class="form-control">${settings.iso || 400}</div>
                </div>
                <div class="form-group">
                    <label>Gain</label>
                    <div class="form-control">${settings.gain || 2.0}</div>
                </div>
                <div class="form-group">
                    <label>Exposure Mode</label>
                    <div class="form-control">${settings.exposure_mode || 'auto'}</div>
                </div>
                <div class="form-group">
                    <label>Resolution</label>
                    <div class="form-control">${settings.resolution || '4056x3040'}</div>
                </div>
            </div>
        `;
    }

    updateIsoDisplay(value) {
        const display = document.getElementById('isoDisplay');
        if (display) {
            display.textContent = value;
        }
    }

    updateGainDisplay(value) {
        const display = document.getElementById('gainDisplay');
        if (display) {
            display.textContent = parseFloat(value).toFixed(1);
        }
    }

    updateExposureLabel(isManual) {
        const label = document.getElementById('exposureLabel');
        if (label) {
            label.textContent = isManual ? 'Manual' : 'Auto';
        }
    }

    updateSettingsStatus(status, text) {
        const indicator = document.getElementById('settingsStatus');
        const textElement = document.getElementById('settingsStatusText');
        
        if (indicator) {
            indicator.className = `status-indicator ${status}`;
        }
        
        if (textElement) {
            textElement.textContent = text;
        }
    }

    async resetSettings() {
        if (!confirm('Are you sure you want to reset camera settings to defaults?')) {
            return;
        }

        try {
            this.showLoading('resetSettings', true);
            this.updateSettingsStatus('loading', 'Resetting settings...');
            
            const defaultSettings = {
                exposure_mode: 'auto',
                iso: 400,
                gain: 2.0,
                resolution: '4056x3040'
            };

            const response = await fetch('/api/camera/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(defaultSettings)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Settings reset to defaults successfully!', 'success');
                this.loadSettings();
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
                this.updateSettingsStatus('error', 'Reset failed');
            }
        } catch (error) {
            console.error('Error resetting settings:', error);
            this.showNotification('Error resetting settings', 'error');
            this.updateSettingsStatus('error', 'Reset failed');
        } finally {
            this.showLoading('resetSettings', false);
        }
    }

    updateCapturesDisplay(captures) {
        const container = document.getElementById('recentCaptures');
        if (!container) return;

        if (captures.length === 0) {
            container.innerHTML = '<p class="text-center">No captures found</p>';
            return;
        }

        const capturesList = captures.map(capture => `
            <div class="capture-item">
                <div class="capture-info">
                    <strong>${capture.filename}</strong>
                    <span class="capture-time">${new Date(capture.timestamp).toLocaleString()}</span>
                </div>
                <div class="capture-actions">
                    <button class="button" onclick="dashboard.downloadCapture('${capture.filename}')">Download</button>
                    <button class="button danger" onclick="dashboard.deleteCapture('${capture.filename}')">Delete</button>
                </div>
            </div>
        `).join('');

        container.innerHTML = capturesList;
    }

    // Capture Control Methods
    async startCapture() {
        const interval = document.getElementById('intervalSlider')?.value || 30;
        
        try {
            this.showLoading('startCapture', true);
            
            const response = await fetch('/api/capture/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval: parseInt(interval) })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Timelapse started successfully!', 'success');
                this.loadStatus();
                this.updateCaptureStatusIndicators(data.session || { status: 'active', interval: interval });
            } else {
                this.showEnhancedError('Failed to start timelapse', data.error);
            }
        } catch (error) {
            console.error('Error starting capture:', error);
            this.showEnhancedError('Error starting timelapse', error.message);
        } finally {
            this.showLoading('startCapture', false);
        }
    }

    async stopCapture() {
        try {
            this.showLoading('stopCapture', true);
            
            const response = await fetch('/api/capture/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Timelapse stopped successfully!', 'success');
                this.loadStatus();
                this.updateCaptureStatusIndicators({ status: 'inactive' });
            } else {
                this.showEnhancedError('Failed to stop timelapse', data.error);
            }
        } catch (error) {
            console.error('Error stopping capture:', error);
            this.showEnhancedError('Error stopping timelapse', error.message);
        } finally {
            this.showLoading('stopCapture', false);
        }
    }

    async takeSnapshot() {
        try {
            this.showLoading('takeSnapshot', true);
            
            const response = await fetch('/api/capture/manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Snapshot taken successfully!', 'success');
                this.loadRecentCaptures();
                this.loadStatus();
            } else {
                this.showEnhancedError('Failed to take snapshot', data.error);
            }
        } catch (error) {
            console.error('Error taking snapshot:', error);
            this.showEnhancedError('Error taking snapshot', error.message);
        } finally {
            this.showLoading('takeSnapshot', false);
        }
    }

    async updateSettings() {
        const formData = new FormData(document.getElementById('settingsForm'));
        const settings = {
            iso: parseInt(formData.get('iso')),
            gain: parseFloat(formData.get('gain')),
            exposure_mode: formData.get('exposure_mode') === 'on' ? 'manual' : 'auto',
            resolution: formData.get('resolution')
        };

        try {
            this.showLoading('updateSettings', true);
            this.updateSettingsStatus('loading', 'Updating settings...');
            
            const response = await fetch('/api/camera/settings', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Settings updated successfully!', 'success');
                this.updateSettingsStatus('success', 'Settings updated');
                this.loadSettings();
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
                this.updateSettingsStatus('error', 'Update failed');
            }
        } catch (error) {
            console.error('Error updating settings:', error);
            this.showNotification('Error updating settings', 'error');
            this.updateSettingsStatus('error', 'Update failed');
        } finally {
            this.showLoading('updateSettings', false);
        }
    }

    async downloadCapture(filename) {
        try {
            window.open(`/api/capture/download/${filename}`, '_blank');
        } catch (error) {
            console.error('Error downloading capture:', error);
            this.showNotification('Error downloading capture', 'error');
        }
    }

    async deleteCapture(filename) {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/capture/delete/${filename}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Capture deleted successfully!', 'success');
                this.loadRecentCaptures();
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting capture:', error);
            this.showNotification('Error deleting capture', 'error');
        }
    }

    // Additional Methods
    async refreshCameraStatus() {
        try {
            await this.loadStatus();
            this.showNotification('Camera status refreshed', 'info');
        } catch (error) {
            console.error('Error refreshing camera status:', error);
            this.showNotification('Error refreshing camera status', 'error');
        }
    }

    toggleStream() {
        const container = document.getElementById('streamContainer');
        if (!container) return;

        if (this.streamActive) {
            // Stop stream
            this.streamActive = false;
            container.innerHTML = `
                <div class="stream-info">
                    <p>MJPEG Stream</p>
                    <p>Stream URL: /stream</p>
                    <button class="button" onclick="dashboard.toggleStream()">Start Stream</button>
                </div>
            `;
            this.showNotification('Stream stopped', 'info');
        } else {
            // Start stream
            this.streamActive = true;
            container.innerHTML = `
                <img src="/stream" alt="Live Stream" style="max-width: 100%; max-height: 100%; border-radius: 8px;">
                <div style="margin-top: 10px;">
                    <button class="button danger" onclick="dashboard.toggleStream()">Stop Stream</button>
                </div>
            `;
            this.showNotification('Stream started', 'success');
        }
    }

    openCapturesFolder() {
        try {
            // Try to open the captures folder in a new window/tab
            window.open('/api/capture/folder', '_blank');
        } catch (error) {
            console.error('Error opening captures folder:', error);
            this.showNotification('Error opening captures folder', 'error');
        }
    }

    // WebSocket Methods
    connectWebSocket() {
        try {
            this.ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus();
                
                // Join dashboard room
                this.ws.send(JSON.stringify({
                    event: 'join_dashboard'
                }));
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus();
                
                // Reconnect after 5 seconds
                setTimeout(() => this.connectWebSocket(), 5000);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnected = false;
                this.updateConnectionStatus();
            };
        } catch (error) {
            console.error('Error connecting to WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.event) {
            case 'status_update':
                this.updateStatusDisplay(data.data);
                break;
            case 'capture_event':
                this.handleCaptureEvent(data.data);
                break;
            case 'settings_update':
                this.updateSettingsDisplay(data.data);
                break;
            case 'error':
                this.showNotification(data.message, 'error');
                break;
        }
    }

    handleCaptureEvent(event) {
        switch (event.type) {
            case 'capture_started':
                this.showNotification('Timelapse started', 'success');
                this.loadStatus();
                break;
            case 'capture_stopped':
                this.showNotification('Timelapse stopped', 'warning');
                this.loadStatus();
                break;
            case 'snapshot_taken':
                this.showNotification('Snapshot taken', 'success');
                this.loadRecentCaptures();
                break;
        }
    }

    // Utility Methods
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} fade-in`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    showLoading(buttonId, show) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        if (show) {
            button.disabled = true;
            button.innerHTML = '<span class="loading"></span> Loading...';
        } else {
            button.disabled = false;
            button.innerHTML = button.getAttribute('data-original-text') || button.textContent;
        }
    }

    updateConnectionStatus() {
        const indicator = document.getElementById('connectionStatus');
        const text = document.getElementById('connectionText');
        
        if (indicator) {
            indicator.className = `status-indicator ${this.isConnected ? 'online' : 'offline'}`;
            indicator.title = this.isConnected ? 'Connected' : 'Disconnected';
        }
        
        if (text) {
            text.textContent = this.isConnected ? 'Connected' : 'Disconnected';
        }
    }

    startStatusPolling() {
        // Poll for status updates every 5 seconds as fallback
        this.statusInterval = setInterval(() => {
            if (!this.isConnected) {
                this.loadStatus();
            }
        }, 5000);
    }

    toggleRealtime(enabled) {
        if (enabled) {
            this.startStatusPolling();
        } else {
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
                this.statusInterval = null;
            }
        }
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    updateIntervalDisplay(interval) {
        const display = document.getElementById('intervalDisplay');
        if (display) {
            display.textContent = `${interval} seconds`;
        }
    }

    // Enhanced Capture Control Methods
    updateCaptureStatusIndicators(session) {
        const statusElement = document.getElementById('captureStatus');
        const countdownElement = document.getElementById('nextCaptureCountdown');
        const totalElement = document.getElementById('totalCaptures');
        const timeElement = document.getElementById('sessionTime');

        if (statusElement) {
            statusElement.textContent = session.status || 'Inactive';
            statusElement.className = `indicator-value ${session.status === 'active' ? 'updating' : ''}`;
        }

        if (totalElement) {
            totalElement.textContent = session.captures || 0;
        }

        if (timeElement) {
            timeElement.textContent = session.elapsed_time ? this.formatDuration(session.elapsed_time) : '--';
        }

        // Update countdown
        if (session.status === 'active' && session.interval) {
            this.startCountdown(session.interval, session.last_capture_time);
        } else {
            if (countdownElement) {
                countdownElement.textContent = '--';
            }
        }
    }

    startCountdown(interval, lastCaptureTime) {
        const countdownElement = document.getElementById('nextCaptureCountdown');
        if (!countdownElement) return;

        const updateCountdown = () => {
            if (!this.currentSession || this.currentSession.status !== 'active') {
                countdownElement.textContent = '--';
                return;
            }

            const now = Date.now();
            const lastCapture = lastCaptureTime ? new Date(lastCaptureTime).getTime() : now;
            const nextCapture = lastCapture + (interval * 1000);
            const timeLeft = Math.max(0, nextCapture - now);

            if (timeLeft <= 0) {
                countdownElement.textContent = 'Capturing...';
                countdownElement.className = 'indicator-value updating';
            } else {
                const seconds = Math.ceil(timeLeft / 1000);
                countdownElement.textContent = `${seconds}s`;
                countdownElement.className = 'indicator-value';
            }
        };

        updateCountdown();
        
        // Update countdown every second
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        this.countdownInterval = setInterval(updateCountdown, 1000);
    }

    updateProgressBar(session) {
        const container = document.getElementById('progressContainer');
        const fill = document.getElementById('progressFill');
        const text = document.getElementById('progressText');

        if (!container || !fill || !text) return;

        if (session.status === 'active' && session.interval) {
            container.style.display = 'block';
            
            // Calculate progress based on elapsed time and interval
            const elapsed = session.elapsed_time || 0;
            const captures = session.captures || 0;
            const expectedCaptures = Math.floor(elapsed / session.interval);
            
            let progress = 0;
            if (expectedCaptures > 0) {
                progress = Math.min(100, (captures / expectedCaptures) * 100);
            }

            fill.style.width = `${progress}%`;
            text.textContent = `Session Progress: ${captures} captures (${progress.toFixed(1)}%)`;
        } else {
            container.style.display = 'none';
        }
    }

    async updateInterval(newInterval) {
        if (!this.currentSession || this.currentSession.status !== 'active') {
            return;
        }

        try {
            const response = await fetch('/api/capture/interval', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interval: parseInt(newInterval) })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Interval updated to ${newInterval} seconds`, 'success');
                this.loadStatus();
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error updating interval:', error);
            this.showNotification('Error updating interval', 'error');
        }
    }

    // Enhanced error handling
    showEnhancedError(message, details = null) {
        const errorMessage = details ? `${message}: ${details}` : message;
        this.showNotification(errorMessage, 'error');
        
        // Update status indicators to show error state
        const statusElement = document.getElementById('captureStatus');
        if (statusElement) {
            statusElement.textContent = 'Error';
            statusElement.className = 'indicator-value error';
        }
    }

    async createConfigBackup() {
        try {
            this.showNotification('Creating configuration backup...', 'info');
            
            const response = await fetch('/api/editor/backup', {
                method: 'POST'
            });

            const data = await response.json();
            if (data.success) {
                this.showNotification('Configuration backup created successfully', 'success');
            } else {
                this.showNotification(`Failed to create backup: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error creating backup:', error);
            this.showNotification('Error creating backup', 'error');
        }
    }

    // Cleanup method
    cleanup() {
        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
        }
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new CinePiDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.cleanup();
    }
});

// Export for global access
window.CinePiDashboard = CinePiDashboard; 