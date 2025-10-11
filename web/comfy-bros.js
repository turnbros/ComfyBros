import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "comfybros.serverlessConfig",

  // Declare a hidden setting to hold our list of serverless instances
  settings: [
    {
      id: "serverlessConfig.instances",
      name: "Serverless Instances",
      type: "hidden",
      defaultValue: []
    }
  ],

  // Add a sidebar tab with a custom form
  async setup() {
    app.extensionManager.registerSidebarTab({
      id: "serverlessConfigTab",
      icon: "pi pi-cloud",
      title: "Serverless Config",
      type: "custom",
      render: (el) => {
        // Load current state or start with an empty array
        let instances = app.extensionManager.setting.get("serverlessConfig.instances") || [];

        // Create container and controls
        const container = document.createElement("div");
        container.style.padding = "10px";

        const list = document.createElement("div");
        container.appendChild(list);

        // Render existing instances
        function redraw() {
          list.innerHTML = "";
          instances.forEach((instance, idx) => {
            const row = document.createElement("div");
            row.style.border = "1px solid #ccc";
            row.style.padding = "10px";
            row.style.marginBottom = "10px";
            row.style.borderRadius = "5px";

            // Instance name field
            const nameLabel = document.createElement("label");
            nameLabel.textContent = "Instance Name:";
            nameLabel.style.display = "block";
            nameLabel.style.marginBottom = "5px";
            row.appendChild(nameLabel);

            const name = document.createElement("input");
            name.type = "text";
            name.placeholder = "e.g., My RunPod Instance";
            name.value = instance.name ?? "";
            name.style.width = "100%";
            name.style.marginBottom = "10px";
            name.oninput = () => {
              instances[idx].name = name.value;
              save();
            };
            row.appendChild(name);

            // Endpoint URL field
            const endpointLabel = document.createElement("label");
            endpointLabel.textContent = "Endpoint URL:";
            endpointLabel.style.display = "block";
            endpointLabel.style.marginBottom = "5px";
            row.appendChild(endpointLabel);

            const endpoint = document.createElement("input");
            endpoint.type = "text";
            endpoint.placeholder = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync";
            endpoint.value = instance.endpoint ?? "";
            endpoint.style.width = "100%";
            endpoint.style.marginBottom = "10px";
            endpoint.oninput = () => {
              instances[idx].endpoint = endpoint.value;
              save();
            };
            row.appendChild(endpoint);

            // Auth Token field
            const tokenLabel = document.createElement("label");
            tokenLabel.textContent = "Auth Token:";
            tokenLabel.style.display = "block";
            tokenLabel.style.marginBottom = "5px";
            row.appendChild(tokenLabel);

            const token = document.createElement("input");
            token.type = "password";
            token.placeholder = "Your API token";
            token.value = instance.auth_token ?? "";
            token.style.width = "100%";
            token.style.marginBottom = "10px";
            token.oninput = () => {
              instances[idx].auth_token = token.value;
              save();
            };
            row.appendChild(token);

            // Provider field (optional)
            const providerLabel = document.createElement("label");
            providerLabel.textContent = "Provider:";
            providerLabel.style.display = "block";
            providerLabel.style.marginBottom = "5px";
            row.appendChild(providerLabel);

            const provider = document.createElement("select");
            provider.style.width = "100%";
            provider.style.marginBottom = "10px";
            
            const providers = ["RunPod", "Replicate", "HuggingFace", "Custom"];
            providers.forEach(p => {
              const option = document.createElement("option");
              option.value = p;
              option.textContent = p;
              option.selected = instance.provider === p;
              provider.appendChild(option);
            });
            
            provider.onchange = () => {
              instances[idx].provider = provider.value;
              save();
            };
            row.appendChild(provider);

            // Remove button
            const rm = document.createElement("button");
            rm.textContent = "Remove Instance";
            rm.style.backgroundColor = "#ff4444";
            rm.style.color = "white";
            rm.style.border = "none";
            rm.style.padding = "5px 10px";
            rm.style.borderRadius = "3px";
            rm.style.cursor = "pointer";
            rm.onclick = () => {
              if (confirm(`Are you sure you want to remove "${instance.name || 'Unnamed Instance'}"?`)) {
                instances.splice(idx, 1);
                save();
                redraw();
              }
            };
            row.appendChild(rm);

            list.appendChild(row);
          });
        }

        // Persist changes to the hidden setting
        function save() {
          app.extensionManager.setting.set("serverlessConfig.instances", instances);
        }

        // "Add Instance" button
        const add = document.createElement("button");
        add.textContent = "Add New Instance";
        add.style.backgroundColor = "#4CAF50";
        add.style.color = "white";
        add.style.border = "none";
        add.style.padding = "10px 20px";
        add.style.borderRadius = "5px";
        add.style.cursor = "pointer";
        add.style.marginBottom = "10px";
        add.onclick = () => {
          instances.push({ 
            name: "", 
            endpoint: "", 
            auth_token: "", 
            provider: "RunPod" 
          });
          save();
          redraw();
        };
        container.appendChild(add);

        // Export configurations button
        const exportBtn = document.createElement("button");
        exportBtn.textContent = "Export Configurations";
        exportBtn.style.backgroundColor = "#2196F3";
        exportBtn.style.color = "white";
        exportBtn.style.border = "none";
        exportBtn.style.padding = "10px 20px";
        exportBtn.style.borderRadius = "5px";
        exportBtn.style.cursor = "pointer";
        exportBtn.style.marginLeft = "10px";
        exportBtn.onclick = () => {
          const dataStr = JSON.stringify(instances, null, 2);
          const dataBlob = new Blob([dataStr], {type: 'application/json'});
          const url = URL.createObjectURL(dataBlob);
          const link = document.createElement('a');
          link.href = url;
          link.download = 'serverless-instances.json';
          link.click();
          URL.revokeObjectURL(url);
        };
        container.appendChild(exportBtn);

        // Import configurations button
        const importBtn = document.createElement("button");
        importBtn.textContent = "Import Configurations";
        importBtn.style.backgroundColor = "#FF9800";
        importBtn.style.color = "white";
        importBtn.style.border = "none";
        importBtn.style.padding = "10px 20px";
        importBtn.style.borderRadius = "5px";
        importBtn.style.cursor = "pointer";
        importBtn.style.marginLeft = "10px";
        importBtn.onclick = () => {
          const input = document.createElement('input');
          input.type = 'file';
          input.accept = '.json';
          input.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
              const reader = new FileReader();
              reader.onload = (e) => {
                try {
                  const imported = JSON.parse(e.target.result);
                  if (Array.isArray(imported)) {
                    instances.length = 0;
                    instances.push(...imported);
                    save();
                    redraw();
                    alert('Configurations imported successfully!');
                  } else {
                    alert('Invalid file format. Expected JSON array.');
                  }
                } catch (err) {
                  alert('Error parsing JSON file: ' + err.message);
                }
              };
              reader.readAsText(file);
            }
          };
          input.click();
        };
        container.appendChild(importBtn);

        redraw();
        el.appendChild(container);
      }
    });
  }
});