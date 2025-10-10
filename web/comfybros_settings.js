/**
 * ComfyBros Settings Panel for ComfyUI
 * Provides a web-based settings interface for RunPod configuration
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const COMFYBROS_SETTINGS_ID = "ComfyBros.Settings";

class ComfyBrosSettingsPanel {
    constructor() {
        this.settings = {
            runpod: {
                api_key: "",
                enabled: false,
                instances: [],
                default_instance: ""
            }
        };
        this.element = null;
        this.setupAPI();
    }

    setupAPI() {
        // Register API endpoints for settings management
        this.apiEndpoints = {
            getSettings: "/comfybros/settings",
            saveSettings: "/comfybros/settings",
            testConnection: "/comfybros/test_connection",
            validateInstance: "/comfybros/validate_instance"
        };
    }

    async loadSettings() {
        try {
            const response = await api.fetchApi(this.apiEndpoints.getSettings);
            if (response.ok) {
                this.settings = await response.json();
            } else {
                console.warn("ComfyBros: Could not load settings, using defaults");
            }
        } catch (error) {
            console.error("ComfyBros: Error loading settings:", error);
        }
    }

    async saveSettings() {
        try {
            const response = await api.fetchApi(this.apiEndpoints.saveSettings, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(this.settings)
            });

            if (response.ok) {
                this.showMessage("Settings saved successfully", "success");
                return true;
            } else {
                const error = await response.json();
                this.showMessage(`Failed to save settings: ${error.message}`, "error");
                return false;
            }
        } catch (error) {
            console.error("ComfyBros: Error saving settings:", error);
            this.showMessage(`Error saving settings: ${error.message}`, "error");
            return false;
        }
    }

    async testConnection() {
        const apiKey = this.element.querySelector("#comfybros-api-key").value;
        if (!apiKey) {
            this.showMessage("Please enter an API key first", "warning");
            return;
        }

        const testButton = this.element.querySelector("#comfybros-test-connection");
        testButton.disabled = true;
        testButton.textContent = "Testing...";

        try {
            const response = await api.fetchApi(this.apiEndpoints.testConnection, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ api_key: apiKey })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showMessage("Connection successful!", "success");
            } else {
                this.showMessage(`Connection failed: ${result.message}`, "error");
            }
        } catch (error) {
            this.showMessage(`Connection test failed: ${error.message}`, "error");
        } finally {
            testButton.disabled = false;
            testButton.textContent = "Test Connection";
        }
    }

    async validateInstance(instanceName) {
        try {
            const response = await api.fetchApi(this.apiEndpoints.validateInstance, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ instance_name: instanceName })
            });

            const result = await response.json();
            return result;
        } catch (error) {
            console.error("ComfyBros: Error validating instance:", error);
            return { success: false, message: error.message };
        }
    }

    createSettingsPanel() {
        const panel = document.createElement("div");
        panel.className = "comfy-modal-content comfybros-settings-panel";
        panel.innerHTML = `
            <style>
                .comfybros-settings-panel {
                    max-width: 800px;
                    max-height: 80vh;
                    overflow-y: auto;
                    padding: 20px;
                }

                .comfybros-section {
                    margin-bottom: 25px;
                    border: 1px solid var(--border-color);
                    border-radius: 8px;
                    padding: 15px;
                    background: var(--comfy-input-bg);
                }

                .comfybros-section h3 {
                    margin-top: 0;
                    margin-bottom: 15px;
                    color: var(--fg-color);
                    border-bottom: 1px solid var(--border-color);
                    padding-bottom: 5px;
                }

                .comfybros-field {
                    display: flex;
                    align-items: center;
                    margin-bottom: 12px;
                    gap: 10px;
                }

                .comfybros-field label {
                    min-width: 120px;
                    color: var(--fg-color);
                    font-weight: 500;
                }

                .comfybros-field input, .comfybros-field select {
                    flex: 1;
                    padding: 6px 10px;
                    border: 1px solid var(--border-color);
                    border-radius: 4px;
                    background: var(--comfy-input-bg);
                    color: var(--fg-color);
                }

                .comfybros-field button {
                    padding: 6px 15px;
                    border: none;
                    border-radius: 4px;
                    background: var(--comfy-input-bg);
                    color: var(--fg-color);
                    cursor: pointer;
                    border: 1px solid var(--border-color);
                }

                .comfybros-field button:hover {
                    background: var(--border-color);
                }

                .comfybros-field button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .comfybros-instance {
                    border: 1px solid var(--border-color);
                    border-radius: 6px;
                    padding: 12px;
                    margin-bottom: 10px;
                    background: var(--bg-color);
                }

                .comfybros-instance-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }

                .comfybros-instance-name {
                    font-weight: bold;
                    color: var(--fg-color);
                }

                .comfybros-instance-status {
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 500;
                }

                .comfybros-instance-status.enabled {
                    background: #28a745;
                    color: white;
                }

                .comfybros-instance-status.disabled {
                    background: #6c757d;
                    color: white;
                }

                .comfybros-instance-actions {
                    display: flex;
                    gap: 5px;
                }

                .comfybros-instance-actions button {
                    padding: 4px 8px;
                    font-size: 12px;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                }

                .comfybros-btn-edit {
                    background: #007bff;
                    color: white;
                }

                .comfybros-btn-delete {
                    background: #dc3545;
                    color: white;
                }

                .comfybros-btn-validate {
                    background: #28a745;
                    color: white;
                }

                .comfybros-message {
                    padding: 10px;
                    border-radius: 4px;
                    margin-bottom: 15px;
                    display: none;
                }

                .comfybros-message.success {
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }

                .comfybros-message.error {
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }

                .comfybros-message.warning {
                    background: #fff3cd;
                    color: #856404;
                    border: 1px solid #ffeaa7;
                }

                .comfybros-add-instance {
                    border: 2px dashed var(--border-color);
                    border-radius: 6px;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }

                .comfybros-add-instance:hover {
                    border-color: var(--fg-color);
                    background: var(--comfy-input-bg);
                }

                .comfybros-modal {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.7);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 10000;
                }

                .comfybros-modal-content {
                    background: var(--bg-color);
                    padding: 20px;
                    border-radius: 8px;
                    border: 1px solid var(--border-color);
                    max-width: 500px;
                    width: 90%;
                }

                .comfybros-modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    border-bottom: 1px solid var(--border-color);
                    padding-bottom: 10px;
                }

                .comfybros-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: var(--fg-color);
                }
            </style>

            <div id="comfybros-message" class="comfybros-message"></div>

            <div class="comfybros-section">
                <h3>🚀 RunPod Configuration</h3>
                
                <div class="comfybros-field">
                    <label for="comfybros-api-key">API Key:</label>
                    <input type="password" id="comfybros-api-key" placeholder="Enter your RunPod API key">
                    <button id="comfybros-test-connection">Test Connection</button>
                </div>

                <div class="comfybros-field">
                    <label for="comfybros-enabled">Enable RunPod:</label>
                    <input type="checkbox" id="comfybros-enabled">
                </div>
            </div>

            <div class="comfybros-section">
                <h3>🏃 Serverless Instances</h3>
                <div id="comfybros-instances-list"></div>
                
                <div class="comfybros-add-instance" id="comfybros-add-instance">
                    <span>+ Add New Instance</span>
                </div>
            </div>

            <div class="comfybros-section">
                <div class="comfybros-field">
                    <button id="comfybros-save-settings" style="background: #28a745; color: white; font-weight: bold;">
                        Save Settings
                    </button>
                    <button id="comfybros-reload-settings" style="background: #6c757d; color: white;">
                        Reload Settings
                    </button>
                </div>
            </div>
        `;

        this.element = panel;
        this.attachEventListeners();
        return panel;
    }

    attachEventListeners() {
        // Test connection button
        this.element.querySelector("#comfybros-test-connection").addEventListener("click", () => {
            this.testConnection();
        });

        // Save settings button
        this.element.querySelector("#comfybros-save-settings").addEventListener("click", () => {
            this.collectAndSaveSettings();
        });

        // Reload settings button
        this.element.querySelector("#comfybros-reload-settings").addEventListener("click", () => {
            this.loadAndPopulateSettings();
        });

        // Add instance button
        this.element.querySelector("#comfybros-add-instance").addEventListener("click", () => {
            this.showInstanceModal();
        });
    }

    async loadAndPopulateSettings() {
        await this.loadSettings();
        this.populateSettings();
    }

    populateSettings() {
        // Populate RunPod settings
        this.element.querySelector("#comfybros-api-key").value = this.settings.runpod.api_key || "";
        this.element.querySelector("#comfybros-enabled").checked = this.settings.runpod.enabled || false;

        // Populate instances
        this.renderInstances();
    }

    renderInstances() {
        const instancesList = this.element.querySelector("#comfybros-instances-list");
        instancesList.innerHTML = "";

        if (!this.settings.runpod.instances || this.settings.runpod.instances.length === 0) {
            instancesList.innerHTML = "<p style='color: var(--fg-color); text-align: center; padding: 20px;'>No instances configured</p>";
            return;
        }

        this.settings.runpod.instances.forEach((instance, index) => {
            const instanceElement = this.createInstanceElement(instance, index);
            instancesList.appendChild(instanceElement);
        });
    }

    createInstanceElement(instance, index) {
        const div = document.createElement("div");
        div.className = "comfybros-instance";
        div.innerHTML = `
            <div class="comfybros-instance-header">
                <div class="comfybros-instance-name">${instance.name}</div>
                <div class="comfybros-instance-status ${instance.enabled ? 'enabled' : 'disabled'}">
                    ${instance.enabled ? 'Enabled' : 'Disabled'}
                </div>
                <div class="comfybros-instance-actions">
                    <button class="comfybros-btn-validate" data-index="${index}">Validate</button>
                    <button class="comfybros-btn-edit" data-index="${index}">Edit</button>
                    <button class="comfybros-btn-delete" data-index="${index}">Delete</button>
                </div>
            </div>
            <div style="font-size: 12px; color: var(--fg-color); opacity: 0.8;">
                <div><strong>Endpoint:</strong> ${instance.endpoint_id}</div>
                <div><strong>Description:</strong> ${instance.description || 'No description'}</div>
                <div><strong>Timeout:</strong> ${instance.timeout_seconds}s | <strong>Workers:</strong> ${instance.max_workers}</div>
            </div>
        `;

        // Attach event listeners
        div.querySelector(".comfybros-btn-validate").addEventListener("click", () => {
            this.validateInstanceByIndex(index);
        });

        div.querySelector(".comfybros-btn-edit").addEventListener("click", () => {
            this.showInstanceModal(instance, index);
        });

        div.querySelector(".comfybros-btn-delete").addEventListener("click", () => {
            this.deleteInstance(index);
        });

        return div;
    }

    async validateInstanceByIndex(index) {
        const instance = this.settings.runpod.instances[index];
        const validateButton = this.element.querySelector(`[data-index="${index}"].comfybros-btn-validate`);
        
        validateButton.disabled = true;
        validateButton.textContent = "Validating...";

        try {
            const result = await this.validateInstance(instance.name);
            
            if (result.success) {
                this.showMessage(`Instance "${instance.name}" is healthy`, "success");
            } else {
                this.showMessage(`Instance "${instance.name}" validation failed: ${result.message}`, "error");
            }
        } finally {
            validateButton.disabled = false;
            validateButton.textContent = "Validate";
        }
    }

    deleteInstance(index) {
        const instance = this.settings.runpod.instances[index];
        
        if (confirm(`Are you sure you want to delete instance "${instance.name}"?`)) {
            this.settings.runpod.instances.splice(index, 1);
            
            // Update default instance if needed
            if (this.settings.runpod.default_instance === instance.name) {
                this.settings.runpod.default_instance = this.settings.runpod.instances.length > 0 
                    ? this.settings.runpod.instances[0].name 
                    : "";
            }
            
            this.renderInstances();
            this.showMessage(`Instance "${instance.name}" deleted`, "success");
        }
    }

    showInstanceModal(instance = null, index = null) {
        const isEditing = instance !== null;
        
        const modal = document.createElement("div");
        modal.className = "comfybros-modal";
        modal.innerHTML = `
            <div class="comfybros-modal-content">
                <div class="comfybros-modal-header">
                    <h3>${isEditing ? 'Edit Instance' : 'Add New Instance'}</h3>
                    <button class="comfybros-close">&times;</button>
                </div>
                
                <div class="comfybros-field">
                    <label>Name:</label>
                    <input type="text" id="modal-instance-name" value="${instance?.name || ''}" placeholder="Instance name">
                </div>
                
                <div class="comfybros-field">
                    <label>Endpoint ID:</label>
                    <input type="text" id="modal-endpoint-id" value="${instance?.endpoint_id || ''}" placeholder="RunPod endpoint ID">
                </div>
                
                <div class="comfybros-field">
                    <label>Description:</label>
                    <input type="text" id="modal-description" value="${instance?.description || ''}" placeholder="Optional description">
                </div>
                
                <div class="comfybros-field">
                    <label>Enabled:</label>
                    <input type="checkbox" id="modal-enabled" ${instance?.enabled !== false ? 'checked' : ''}>
                </div>
                
                <div class="comfybros-field">
                    <label>Max Workers:</label>
                    <input type="number" id="modal-max-workers" value="${instance?.max_workers || 1}" min="1" max="10">
                </div>
                
                <div class="comfybros-field">
                    <label>Timeout (seconds):</label>
                    <input type="number" id="modal-timeout" value="${instance?.timeout_seconds || 300}" min="30" max="3600">
                </div>
                
                <div class="comfybros-field">
                    <label>Set as Default:</label>
                    <input type="checkbox" id="modal-set-default" ${this.settings.runpod.default_instance === instance?.name ? 'checked' : ''}>
                </div>
                
                <div class="comfybros-field">
                    <button id="modal-save" style="background: #28a745; color: white;">
                        ${isEditing ? 'Update Instance' : 'Add Instance'}
                    </button>
                    <button id="modal-cancel" style="background: #6c757d; color: white;">
                        Cancel
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector(".comfybros-close").addEventListener("click", () => {
            document.body.removeChild(modal);
        });

        modal.querySelector("#modal-cancel").addEventListener("click", () => {
            document.body.removeChild(modal);
        });

        modal.querySelector("#modal-save").addEventListener("click", () => {
            this.saveInstanceFromModal(modal, isEditing, index);
        });

        // Close on background click
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    saveInstanceFromModal(modal, isEditing, index) {
        const name = modal.querySelector("#modal-instance-name").value.trim();
        const endpointId = modal.querySelector("#modal-endpoint-id").value.trim();
        const description = modal.querySelector("#modal-description").value.trim();
        const enabled = modal.querySelector("#modal-enabled").checked;
        const maxWorkers = parseInt(modal.querySelector("#modal-max-workers").value);
        const timeout = parseInt(modal.querySelector("#modal-timeout").value);
        const setDefault = modal.querySelector("#modal-set-default").checked;

        // Validation
        if (!name) {
            this.showMessage("Instance name is required", "error");
            return;
        }

        if (!endpointId) {
            this.showMessage("Endpoint ID is required", "error");
            return;
        }

        // Check for duplicate names (except when editing the same instance)
        const existingIndex = this.settings.runpod.instances.findIndex(inst => inst.name === name);
        if (existingIndex !== -1 && (!isEditing || existingIndex !== index)) {
            this.showMessage("Instance name already exists", "error");
            return;
        }

        const instanceData = {
            name,
            endpoint_id: endpointId,
            description,
            enabled,
            max_workers: maxWorkers,
            timeout_seconds: timeout
        };

        if (isEditing) {
            this.settings.runpod.instances[index] = instanceData;
        } else {
            this.settings.runpod.instances.push(instanceData);
        }

        // Set as default if requested
        if (setDefault) {
            this.settings.runpod.default_instance = name;
        }

        this.renderInstances();
        document.body.removeChild(modal);
        
        this.showMessage(`Instance "${name}" ${isEditing ? 'updated' : 'added'} successfully`, "success");
    }

    collectAndSaveSettings() {
        // Collect current form values
        this.settings.runpod.api_key = this.element.querySelector("#comfybros-api-key").value;
        this.settings.runpod.enabled = this.element.querySelector("#comfybros-enabled").checked;

        this.saveSettings();
    }

    showMessage(message, type) {
        const messageElement = this.element.querySelector("#comfybros-message");
        messageElement.textContent = message;
        messageElement.className = `comfybros-message ${type}`;
        messageElement.style.display = "block";

        // Auto hide after 5 seconds
        setTimeout(() => {
            messageElement.style.display = "none";
        }, 5000);
    }
}

// Register the settings panel with ComfyUI
app.registerExtension({
    name: COMFYBROS_SETTINGS_ID,
    
    async setup() {
        // Create settings panel instance
        const settingsPanel = new ComfyBrosSettingsPanel();
        
        // Register with ComfyUI settings system
        app.ui.settings.addSetting({
            id: COMFYBROS_SETTINGS_ID,
            name: "ComfyBros",
            type: "custom",
            render: () => {
                const panel = settingsPanel.createSettingsPanel();
                // Load settings when panel is created
                settingsPanel.loadAndPopulateSettings();
                return panel;
            }
        });
    }
});

export { ComfyBrosSettingsPanel };