/**
 * ComfyBros Settings Extension for ComfyUI
 * Provides settings integration for RunPod configuration
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Global settings state
let comfyBrosSettings = {
    runpod: {
        api_key: "",
        enabled: false,
        instances: [],
        default_instance: ""
    }
};

// Register ComfyBros settings with ComfyUI's built-in settings system
app.registerExtension({
    name: "ComfyBros",
    settings: [
        {
            id: "ComfyBros.runpod_config",
            category: ["ComfyBros"],
            name: "RunPod Configuration",
            type: "custom",
            render: () => {
                return createRunPodSettingsPanel();
            }
        }
    ],
    
    async setup() {
        console.log("ComfyBros: Extension loaded");
        
        // Load settings from backend on startup
        await loadRunPodSettings();
        
        // Add instance management commands
        this.addInstanceManagementCommands();
    },
    
    commands: [
        {
            id: "ComfyBros.test_runpod_connection",
            label: "Test RunPod Connection",
            function: async () => {
                await testRunPodConnection();
            }
        },
        {
            id: "ComfyBros.add_runpod_instance",
            label: "Add RunPod Instance",
            function: async () => {
                await showAddInstanceDialog();
            }
        },
        {
            id: "ComfyBros.manage_runpod_instances",
            label: "Manage RunPod Instances",
            function: async () => {
                await showInstanceManagerDialog();
            }
        }
    ],
    
    menuCommands: [
        {
            path: ["Extensions", "ComfyBros"],
            commands: ["ComfyBros.test_runpod_connection", "ComfyBros.add_runpod_instance", "ComfyBros.manage_runpod_instances"]
        }
    ],

    addInstanceManagementCommands() {
        console.log("ComfyBros: Instance management commands added to Extensions menu");
    }
});

// Create the custom RunPod settings panel with proper UI components
function createRunPodSettingsPanel() {
    const container = document.createElement("div");
    container.style.cssText = `
        padding: 20px;
        max-width: 800px;
        color: var(--fg-color);
    `;
    
    container.innerHTML = `
        <style>
            .comfybros-section {
                margin-bottom: 25px;
                padding: 15px;
                border: 1px solid var(--border-color);
                border-radius: 8px;
                background: var(--comfy-input-bg);
            }
            
            .comfybros-section h3 {
                margin: 0 0 15px 0;
                color: var(--fg-color);
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 8px;
                font-size: 16px;
            }
            
            .comfybros-field {
                display: flex;
                align-items: center;
                margin-bottom: 12px;
                gap: 10px;
            }
            
            .comfybros-field label {
                min-width: 140px;
                color: var(--fg-color);
                font-weight: 500;
                font-size: 14px;
            }
            
            .comfybros-field input[type="text"], 
            .comfybros-field input[type="password"],
            .comfybros-field select {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid var(--border-color);
                border-radius: 4px;
                background: var(--comfy-input-bg);
                color: var(--fg-color);
                font-size: 14px;
            }
            
            .comfybros-field input[type="checkbox"] {
                width: 18px;
                height: 18px;
            }
            
            .comfybros-btn {
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
                transition: background-color 0.2s;
            }
            
            .comfybros-btn-primary {
                background: #007bff;
                color: white;
            }
            
            .comfybros-btn-primary:hover {
                background: #0056b3;
            }
            
            .comfybros-btn-secondary {
                background: var(--comfy-input-bg);
                color: var(--fg-color);
                border: 1px solid var(--border-color);
            }
            
            .comfybros-btn-secondary:hover {
                background: var(--border-color);
            }
            
            .comfybros-btn-danger {
                background: #dc3545;
                color: white;
            }
            
            .comfybros-btn-danger:hover {
                background: #c82333;
            }
            
            .comfybros-btn-success {
                background: #28a745;
                color: white;
            }
            
            .comfybros-btn-success:hover {
                background: #1e7e34;
            }
            
            .comfybros-instance-item {
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
                margin-bottom: 8px;
            }
            
            .comfybros-instance-name {
                font-weight: bold;
                font-size: 16px;
            }
            
            .comfybros-instance-status {
                padding: 4px 8px;
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
            
            .comfybros-instance-status.default {
                background: #ffc107;
                color: #212529;
            }
            
            .comfybros-instance-details {
                font-size: 13px;
                color: var(--descrip-text);
                margin-bottom: 8px;
            }
            
            .comfybros-instance-actions {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            
            .comfybros-add-instance {
                border: 2px dashed var(--border-color);
                border-radius: 6px;
                padding: 30px;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s ease;
                background: var(--comfy-input-bg);
            }
            
            .comfybros-add-instance:hover {
                border-color: var(--fg-color);
                background: var(--bg-color);
            }
            
            .comfybros-status-message {
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 15px;
                font-size: 14px;
            }
            
            .comfybros-status-message.success {
                background: rgba(40, 167, 69, 0.1);
                color: #28a745;
                border: 1px solid rgba(40, 167, 69, 0.3);
            }
            
            .comfybros-status-message.error {
                background: rgba(220, 53, 69, 0.1);
                color: #dc3545;
                border: 1px solid rgba(220, 53, 69, 0.3);
            }
            
            .comfybros-status-message.info {
                background: rgba(0, 123, 255, 0.1);
                color: #007bff;
                border: 1px solid rgba(0, 123, 255, 0.3);
            }
        </style>
        
        <!-- Status message area -->
        <div id="comfybros-status" style="display: none;"></div>
        
        <!-- API Configuration Section -->
        <div class="comfybros-section">
            <h3>🚀 RunPod API Configuration</h3>
            
            <div class="comfybros-field">
                <label for="runpod-api-key">API Key:</label>
                <input type="password" id="runpod-api-key" placeholder="Enter your RunPod API key">
                <button class="comfybros-btn comfybros-btn-secondary" id="test-connection">
                    Test Connection
                </button>
            </div>
            
            <div class="comfybros-field">
                <label for="runpod-enabled">Enable RunPod:</label>
                <input type="checkbox" id="runpod-enabled">
                <span style="color: var(--descrip-text); font-size: 13px; margin-left: 10px;">
                    Enable RunPod serverless integration
                </span>
            </div>
        </div>
        
        <!-- Default Instance Section -->
        <div class="comfybros-section">
            <h3>🎯 Default Instance</h3>
            
            <div class="comfybros-field">
                <label for="default-instance">Default Instance:</label>
                <select id="default-instance">
                    <option value="">None selected</option>
                </select>
            </div>
        </div>
        
        <!-- Instances Management Section -->
        <div class="comfybros-section">
            <h3>🏃 Serverless Instances</h3>
            
            <div id="instances-list">
                <!-- Instances will be populated here -->
            </div>
            
            <div class="comfybros-add-instance" id="add-instance-btn">
                <div style="font-size: 18px; margin-bottom: 5px;">+</div>
                <div style="font-weight: 500;">Add New Instance</div>
            </div>
        </div>
        
        <!-- Save Section -->
        <div class="comfybros-section">
            <div style="display: flex; gap: 10px;">
                <button class="comfybros-btn comfybros-btn-success" id="save-settings">
                    💾 Save All Settings
                </button>
                <button class="comfybros-btn comfybros-btn-secondary" id="reload-settings">
                    🔄 Reload Settings
                </button>
            </div>
        </div>
    `;
    
    // Initialize the panel
    setTimeout(() => {
        initializeRunPodSettingsPanel(container);
    }, 100);
    
    return container;
}

// Initialize the settings panel with event handlers and data
async function initializeRunPodSettingsPanel(container) {
    console.log("ComfyBros: Initializing settings panel");
    
    // Load settings first
    await loadRunPodSettings();
    
    // Populate the form with current settings
    populateSettingsForm(container);
    
    // Attach event handlers
    attachEventHandlers(container);
    
    // Render instances list
    renderInstancesList(container);
}

// Load settings from backend
async function loadRunPodSettings() {
    try {
        const response = await api.fetchApi("/comfybros/settings");
        if (response.ok) {
            comfyBrosSettings = await response.json();
            console.log("ComfyBros: Settings loaded from backend");
        } else {
            console.warn("ComfyBros: Could not load settings, using defaults");
        }
    } catch (error) {
        console.warn("ComfyBros: Error loading settings from backend:", error);
    }
}

// Populate form fields with current settings
function populateSettingsForm(container) {
    const apiKeyInput = container.querySelector("#runpod-api-key");
    const enabledCheckbox = container.querySelector("#runpod-enabled");
    const defaultInstanceSelect = container.querySelector("#default-instance");
    
    if (apiKeyInput) apiKeyInput.value = comfyBrosSettings.runpod.api_key || "";
    if (enabledCheckbox) enabledCheckbox.checked = comfyBrosSettings.runpod.enabled || false;
    
    // Populate default instance dropdown
    if (defaultInstanceSelect) {
        defaultInstanceSelect.innerHTML = '<option value="">None selected</option>';
        comfyBrosSettings.runpod.instances.forEach(instance => {
            const option = document.createElement("option");
            option.value = instance.name;
            option.textContent = instance.name;
            option.selected = instance.name === comfyBrosSettings.runpod.default_instance;
            defaultInstanceSelect.appendChild(option);
        });
    }
}

// Attach event handlers to form elements
function attachEventHandlers(container) {
    // Test connection button
    const testBtn = container.querySelector("#test-connection");
    if (testBtn) {
        testBtn.addEventListener("click", () => testConnection(container));
    }
    
    // Save settings button
    const saveBtn = container.querySelector("#save-settings");
    if (saveBtn) {
        saveBtn.addEventListener("click", () => saveAllSettings(container));
    }
    
    // Reload settings button
    const reloadBtn = container.querySelector("#reload-settings");
    if (reloadBtn) {
        reloadBtn.addEventListener("click", () => reloadAllSettings(container));
    }
    
    // Add instance button
    const addBtn = container.querySelector("#add-instance-btn");
    if (addBtn) {
        addBtn.addEventListener("click", () => showAddInstanceForm(container));
    }
    
    // Form change handlers
    const apiKeyInput = container.querySelector("#runpod-api-key");
    if (apiKeyInput) {
        apiKeyInput.addEventListener("change", (e) => {
            comfyBrosSettings.runpod.api_key = e.target.value;
        });
    }
    
    const enabledCheckbox = container.querySelector("#runpod-enabled");
    if (enabledCheckbox) {
        enabledCheckbox.addEventListener("change", (e) => {
            comfyBrosSettings.runpod.enabled = e.target.checked;
        });
    }
    
    const defaultInstanceSelect = container.querySelector("#default-instance");
    if (defaultInstanceSelect) {
        defaultInstanceSelect.addEventListener("change", (e) => {
            comfyBrosSettings.runpod.default_instance = e.target.value;
        });
    }
}

// Render the instances list
function renderInstancesList(container) {
    const instancesList = container.querySelector("#instances-list");
    if (!instancesList) return;
    
    instancesList.innerHTML = "";
    
    if (comfyBrosSettings.runpod.instances.length === 0) {
        instancesList.innerHTML = `
            <div style="text-align: center; padding: 30px; color: var(--descrip-text);">
                No instances configured yet. Click "Add New Instance" to get started.
            </div>
        `;
        return;
    }
    
    comfyBrosSettings.runpod.instances.forEach((instance, index) => {
        const instanceDiv = createInstanceElement(instance, index, container);
        instancesList.appendChild(instanceDiv);
    });
}

// Create an instance list item element
function createInstanceElement(instance, index, container) {
    const div = document.createElement("div");
    div.className = "comfybros-instance-item";
    
    const isDefault = instance.name === comfyBrosSettings.runpod.default_instance;
    const statusClass = isDefault ? "default" : (instance.enabled ? "enabled" : "disabled");
    const statusText = isDefault ? "Default" : (instance.enabled ? "Enabled" : "Disabled");
    
    div.innerHTML = `
        <div class="comfybros-instance-header">
            <div class="comfybros-instance-name">${instance.name}</div>
            <div class="comfybros-instance-status ${statusClass}">${statusText}</div>
        </div>
        
        <div class="comfybros-instance-details">
            <div><strong>Endpoint:</strong> ${instance.endpoint_id}</div>
            ${instance.description ? `<div><strong>Description:</strong> ${instance.description}</div>` : ''}
            <div><strong>Timeout:</strong> ${instance.timeout_seconds}s | <strong>Workers:</strong> ${instance.max_workers}</div>
        </div>
        
        <div class="comfybros-instance-actions">
            <button class="comfybros-btn comfybros-btn-secondary" onclick="editInstance(${index})">
                ✏️ Edit
            </button>
            <button class="comfybros-btn comfybros-btn-secondary" onclick="validateInstance(${index})">
                🔍 Validate
            </button>
            <button class="comfybros-btn comfybros-btn-secondary" onclick="toggleInstanceEnabled(${index})">
                ${instance.enabled ? '⏸️ Disable' : '▶️ Enable'}
            </button>
            <button class="comfybros-btn comfybros-btn-secondary" onclick="setAsDefault(${index})">
                🎯 Set Default
            </button>
            <button class="comfybros-btn comfybros-btn-danger" onclick="deleteInstance(${index})">
                🗑️ Delete
            </button>
        </div>
    `;
    
    return div;
}

// Show status message
function showStatus(container, message, type = "info") {
    const statusDiv = container.querySelector("#comfybros-status");
    if (!statusDiv) return;
    
    statusDiv.className = `comfybros-status-message ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = "block";
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = "none";
    }, 5000);
}

// Test RunPod connection
async function testConnection(container) {
    const apiKey = container.querySelector("#runpod-api-key").value;
    
    if (!apiKey) {
        showStatus(container, "Please enter an API key first", "error");
        return;
    }
    
    const testBtn = container.querySelector("#test-connection");
    const originalText = testBtn.textContent;
    testBtn.textContent = "Testing...";
    testBtn.disabled = true;
    
    try {
        const response = await api.fetchApi("/comfybros/test_connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(container, "✅ RunPod connection successful!", "success");
        } else {
            showStatus(container, `❌ Connection failed: ${result.message}`, "error");
        }
    } catch (error) {
        showStatus(container, `❌ Connection test failed: ${error.message}`, "error");
    } finally {
        testBtn.textContent = originalText;
        testBtn.disabled = false;
    }
}

// Save all settings
async function saveAllSettings(container) {
    const saveBtn = container.querySelector("#save-settings");
    const originalText = saveBtn.textContent;
    saveBtn.textContent = "💾 Saving...";
    saveBtn.disabled = true;
    
    try {
        const response = await api.fetchApi("/comfybros/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(comfyBrosSettings)
        });
        
        if (response.ok) {
            showStatus(container, "✅ Settings saved successfully!", "success");
        } else {
            showStatus(container, "❌ Failed to save settings", "error");
        }
    } catch (error) {
        showStatus(container, `❌ Error saving settings: ${error.message}`, "error");
    } finally {
        saveBtn.textContent = originalText;
        saveBtn.disabled = false;
    }
}

// Reload all settings
async function reloadAllSettings(container) {
    await loadRunPodSettings();
    populateSettingsForm(container);
    renderInstancesList(container);
    showStatus(container, "🔄 Settings reloaded from server", "info");
}

// Show add instance form
function showAddInstanceForm(container) {
    const name = prompt("Instance name:");
    if (!name) return;
    
    const endpointId = prompt("RunPod endpoint ID:");
    if (!endpointId) return;
    
    const description = prompt("Description (optional):") || "";
    
    // Check for duplicate names
    if (comfyBrosSettings.runpod.instances.some(inst => inst.name === name)) {
        showStatus(container, "❌ An instance with this name already exists", "error");
        return;
    }
    
    const newInstance = {
        name: name,
        endpoint_id: endpointId,
        description: description,
        enabled: true,
        max_workers: 1,
        timeout_seconds: 300
    };
    
    comfyBrosSettings.runpod.instances.push(newInstance);
    
    // Set as default if it's the first instance
    if (comfyBrosSettings.runpod.instances.length === 1) {
        comfyBrosSettings.runpod.default_instance = name;
    }
    
    populateSettingsForm(container);
    renderInstancesList(container);
    showStatus(container, `✅ Instance '${name}' added successfully!`, "success");
}

// Global functions for instance management (accessible from onclick handlers)
window.editInstance = function(index) {
    const instance = comfyBrosSettings.runpod.instances[index];
    const newName = prompt("Instance name:", instance.name);
    if (!newName) return;
    
    const newEndpointId = prompt("Endpoint ID:", instance.endpoint_id);
    if (!newEndpointId) return;
    
    const newDescription = prompt("Description:", instance.description);
    
    // Check for duplicate names (except current)
    if (newName !== instance.name && comfyBrosSettings.runpod.instances.some(inst => inst.name === newName)) {
        alert("An instance with this name already exists");
        return;
    }
    
    instance.name = newName;
    instance.endpoint_id = newEndpointId;
    instance.description = newDescription;
    
    // Update default instance reference if needed
    if (comfyBrosSettings.runpod.default_instance === instance.name && newName !== instance.name) {
        comfyBrosSettings.runpod.default_instance = newName;
    }
    
    const container = document.querySelector('.comfybros-section').closest('div');
    populateSettingsForm(container);
    renderInstancesList(container);
    showStatus(container, `✅ Instance '${newName}' updated!`, "success");
}

window.validateInstance = async function(index) {
    const instance = comfyBrosSettings.runpod.instances[index];
    
    try {
        const response = await api.fetchApi("/comfybros/validate_instance", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ instance_name: instance.name })
        });
        
        const result = await response.json();
        const container = document.querySelector('.comfybros-section').closest('div');
        
        if (result.success) {
            showStatus(container, `✅ Instance '${instance.name}' is healthy`, "success");
        } else {
            showStatus(container, `❌ Instance '${instance.name}' validation failed: ${result.message}`, "error");
        }
    } catch (error) {
        const container = document.querySelector('.comfybros-section').closest('div');
        showStatus(container, `❌ Validation failed: ${error.message}`, "error");
    }
}

window.toggleInstanceEnabled = function(index) {
    const instance = comfyBrosSettings.runpod.instances[index];
    instance.enabled = !instance.enabled;
    
    const container = document.querySelector('.comfybros-section').closest('div');
    renderInstancesList(container);
    showStatus(container, `✅ Instance '${instance.name}' ${instance.enabled ? 'enabled' : 'disabled'}`, "success");
}

window.setAsDefault = function(index) {
    const instance = comfyBrosSettings.runpod.instances[index];
    comfyBrosSettings.runpod.default_instance = instance.name;
    
    const container = document.querySelector('.comfybros-section').closest('div');
    populateSettingsForm(container);
    renderInstancesList(container);
    showStatus(container, `✅ Instance '${instance.name}' set as default`, "success");
}

window.deleteInstance = function(index) {
    const instance = comfyBrosSettings.runpod.instances[index];
    
    if (!confirm(`Are you sure you want to delete instance '${instance.name}'?`)) {
        return;
    }
    
    comfyBrosSettings.runpod.instances.splice(index, 1);
    
    // Update default instance if needed
    if (comfyBrosSettings.runpod.default_instance === instance.name) {
        comfyBrosSettings.runpod.default_instance = comfyBrosSettings.runpod.instances.length > 0 
            ? comfyBrosSettings.runpod.instances[0].name 
            : "";
    }
    
    const container = document.querySelector('.comfybros-section').closest('div');
    populateSettingsForm(container);
    renderInstancesList(container);
    showStatus(container, `✅ Instance '${instance.name}' deleted`, "success");
}