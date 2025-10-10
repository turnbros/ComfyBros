/**
 * ComfyBros Settings Extension for ComfyUI
 * Provides settings integration for RunPod configuration
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Register ComfyBros settings with ComfyUI's built-in settings system
app.registerExtension({
    name: "ComfyBros",
    settings: [
        {
            id: "ComfyBros.runpod.api_key",
            category: ["ComfyBros", "RunPod"],
            name: "RunPod API Key",
            tooltip: "Your RunPod API key for serverless instances",
            type: "text",
            defaultValue: "",
            onChange: async (newVal, oldVal) => {
                console.log("ComfyBros: RunPod API key updated");
                await saveRunPodSettings();
            },
        },
        {
            id: "ComfyBros.runpod.enabled",
            category: ["ComfyBros", "RunPod"],
            name: "Enable RunPod Integration",
            tooltip: "Enable or disable RunPod serverless integration",
            type: "boolean",
            defaultValue: false,
            onChange: async (newVal, oldVal) => {
                console.log(`ComfyBros: RunPod integration ${newVal ? 'enabled' : 'disabled'}`);
                await saveRunPodSettings();
            },
        },
        {
            id: "ComfyBros.runpod.default_instance",
            category: ["ComfyBros", "RunPod"],
            name: "Default Instance",
            tooltip: "Default RunPod instance to use for workflows",
            type: "text",
            defaultValue: "",
            onChange: async (newVal, oldVal) => {
                console.log(`ComfyBros: Default instance set to '${newVal}'`);
                await saveRunPodSettings();
            },
        },
        {
            id: "ComfyBros.runpod.instances_json",
            category: ["ComfyBros", "RunPod"],
            name: "Instances Configuration (JSON)",
            tooltip: "JSON configuration of RunPod serverless instances",
            type: "text",
            defaultValue: "[]",
            onChange: async (newVal, oldVal) => {
                try {
                    JSON.parse(newVal);
                    console.log("ComfyBros: Instances configuration updated");
                    await saveRunPodSettings();
                } catch (e) {
                    console.error("ComfyBros: Invalid JSON in instances configuration:", e);
                }
            },
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

// Utility functions for RunPod settings management
async function loadRunPodSettings() {
    try {
        const response = await api.fetchApi("/comfybros/settings");
        if (response.ok) {
            const settings = await response.json();
            
            // Update ComfyUI settings with loaded values
            await app.extensionManager.setting.set("ComfyBros.runpod.api_key", settings.runpod.api_key || "");
            await app.extensionManager.setting.set("ComfyBros.runpod.enabled", settings.runpod.enabled || false);
            await app.extensionManager.setting.set("ComfyBros.runpod.default_instance", settings.runpod.default_instance || "");
            await app.extensionManager.setting.set("ComfyBros.runpod.instances_json", JSON.stringify(settings.runpod.instances || []));
            
            console.log("ComfyBros: Settings loaded from backend");
        }
    } catch (error) {
        console.warn("ComfyBros: Could not load settings from backend:", error);
    }
}

async function saveRunPodSettings() {
    try {
        const apiKey = app.extensionManager.setting.get("ComfyBros.runpod.api_key");
        const enabled = app.extensionManager.setting.get("ComfyBros.runpod.enabled");
        const defaultInstance = app.extensionManager.setting.get("ComfyBros.runpod.default_instance");
        const instancesJson = app.extensionManager.setting.get("ComfyBros.runpod.instances_json");
        
        let instances = [];
        try {
            instances = JSON.parse(instancesJson);
        } catch (e) {
            console.error("ComfyBros: Invalid instances JSON, using empty array");
        }
        
        const settings = {
            runpod: {
                api_key: apiKey,
                enabled: enabled,
                default_instance: defaultInstance,
                instances: instances
            }
        };
        
        const response = await api.fetchApi("/comfybros/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings)
        });
        
        if (response.ok) {
            console.log("ComfyBros: Settings saved to backend");
        } else {
            console.error("ComfyBros: Failed to save settings to backend");
        }
    } catch (error) {
        console.error("ComfyBros: Error saving settings:", error);
    }
}

async function testRunPodConnection() {
    const apiKey = app.extensionManager.setting.get("ComfyBros.runpod.api_key");
    
    if (!apiKey) {
        alert("Please set your RunPod API key in settings first");
        return;
    }
    
    try {
        const response = await api.fetchApi("/comfybros/test_connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert("RunPod connection successful!");
        } else {
            alert(`RunPod connection failed: ${result.message}`);
        }
    } catch (error) {
        alert(`Connection test failed: ${error.message}`);
    }
}

async function showAddInstanceDialog() {
    const name = prompt("Instance name:");
    if (!name) return;
    
    const endpointId = prompt("RunPod endpoint ID:");
    if (!endpointId) return;
    
    const description = prompt("Description (optional):") || "";
    
    try {
        const instancesJson = app.extensionManager.setting.get("ComfyBros.runpod.instances_json");
        const instances = JSON.parse(instancesJson);
        
        // Check for duplicate names
        if (instances.some(inst => inst.name === name)) {
            alert("An instance with this name already exists");
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
        
        instances.push(newInstance);
        
        await app.extensionManager.setting.set("ComfyBros.runpod.instances_json", JSON.stringify(instances));
        
        // Set as default if it's the first instance
        if (instances.length === 1) {
            await app.extensionManager.setting.set("ComfyBros.runpod.default_instance", name);
        }
        
        alert(`Instance '${name}' added successfully!`);
        
    } catch (error) {
        alert(`Failed to add instance: ${error.message}`);
    }
}

async function showInstanceManagerDialog() {
    try {
        const instancesJson = app.extensionManager.setting.get("ComfyBros.runpod.instances_json");
        const instances = JSON.parse(instancesJson);
        
        if (instances.length === 0) {
            alert("No instances configured. Use 'Add RunPod Instance' to create one.");
            return;
        }
        
        const instanceNames = instances.map(inst => inst.name);
        const selectedName = prompt(`Select instance to manage:\n${instanceNames.join(", ")}\n\nEnter instance name:`);
        
        if (!selectedName || !instanceNames.includes(selectedName)) {
            return;
        }
        
        const action = prompt(`Manage instance '${selectedName}':\n1. Delete\n2. Toggle Enable/Disable\n3. Set as Default\n\nEnter action number:`);
        
        const instanceIndex = instances.findIndex(inst => inst.name === selectedName);
        
        switch (action) {
            case "1": // Delete
                if (confirm(`Are you sure you want to delete instance '${selectedName}'?`)) {
                    instances.splice(instanceIndex, 1);
                    
                    // Update default if needed
                    const currentDefault = app.extensionManager.setting.get("ComfyBros.runpod.default_instance");
                    if (currentDefault === selectedName) {
                        const newDefault = instances.length > 0 ? instances[0].name : "";
                        await app.extensionManager.setting.set("ComfyBros.runpod.default_instance", newDefault);
                    }
                    
                    await app.extensionManager.setting.set("ComfyBros.runpod.instances_json", JSON.stringify(instances));
                    alert(`Instance '${selectedName}' deleted`);
                }
                break;
                
            case "2": // Toggle enable/disable
                instances[instanceIndex].enabled = !instances[instanceIndex].enabled;
                await app.extensionManager.setting.set("ComfyBros.runpod.instances_json", JSON.stringify(instances));
                alert(`Instance '${selectedName}' ${instances[instanceIndex].enabled ? 'enabled' : 'disabled'}`);
                break;
                
            case "3": // Set as default
                await app.extensionManager.setting.set("ComfyBros.runpod.default_instance", selectedName);
                alert(`Instance '${selectedName}' set as default`);
                break;
                
            default:
                alert("Invalid action");
        }
        
    } catch (error) {
        alert(`Error managing instances: ${error.message}`);
    }
}