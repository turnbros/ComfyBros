# ComfyBros Web Settings Interface

This document explains how to use the web-based settings interface for ComfyBros, similar to rgthree's configuration panel.

## Overview

The ComfyBros web interface provides a user-friendly settings panel directly within ComfyUI's settings menu. You can configure your RunPod API keys, manage serverless instances, and test connections all from the web interface.

## Access the Settings Panel

1. **Open ComfyUI in your browser**
2. **Click the ⚙️ Settings button** (usually in the top-right corner)
3. **Look for "ComfyBros" in the left sidebar**
4. **Click on "ComfyBros"** to open the settings panel

## Features

### 🚀 RunPod Configuration Section

- **API Key Input**: Enter your RunPod API key
- **Test Connection Button**: Validate your API key immediately
- **Enable RunPod Toggle**: Enable/disable the entire RunPod integration

### 🏃 Serverless Instances Section

- **Instance List**: View all configured RunPod instances
- **Add New Instance**: Click the dashed box to add new instances
- **Instance Management**: Edit, delete, or validate individual instances
- **Instance Status**: See which instances are enabled/disabled

### Instance Details

For each instance, you can configure:
- **Name**: Friendly name for the instance
- **Endpoint ID**: RunPod serverless endpoint ID
- **Description**: Optional description
- **Enabled**: Whether the instance is active
- **Max Workers**: Number of concurrent workers
- **Timeout**: Maximum execution time in seconds
- **Set as Default**: Make this the default instance

## How to Use

### Initial Setup

1. **Get your RunPod API key** from [RunPod.io](https://runpod.io)
2. **Open ComfyBros settings** in ComfyUI
3. **Enter your API key** in the RunPod Configuration section
4. **Click "Test Connection"** to verify it works
5. **Check "Enable RunPod"** to activate the integration
6. **Click "Save Settings"**

### Adding Serverless Instances

1. **Click the "+ Add New Instance" box**
2. **Fill in the instance details**:
   - Name: Something descriptive like "SDXL Generator"
   - Endpoint ID: Copy from your RunPod dashboard
   - Description: Optional notes about what this instance does
   - Set other parameters as needed
3. **Click "Add Instance"**
4. **Repeat for additional instances**
5. **Click "Save Settings"**

### Managing Instances

- **Validate**: Check if an instance is healthy and accessible
- **Edit**: Modify instance settings
- **Delete**: Remove an instance (with confirmation)

### Testing

Use the **Validate** button on any instance to check:
- ✅ Instance is accessible
- ✅ Endpoint responds correctly
- ✅ Authentication works
- ❌ Any connection issues

## Settings Storage

Settings are automatically saved to:
- **Primary**: ComfyUI's user directory (if available)
- **Fallback**: Extension directory
- **File**: `comfybros_settings.json`

## Troubleshooting

### Settings Panel Not Appearing

1. **Check browser console** for JavaScript errors
2. **Verify ComfyUI version** compatibility
3. **Restart ComfyUI** after installing the extension
4. **Check the extension is properly installed** in the correct directory

### API Connection Issues

1. **Verify API key** is correct and active
2. **Check internet connection**
3. **Try the "Test Connection" button**
4. **Check RunPod service status**

### Instance Validation Failures

1. **Verify endpoint ID** is correct
2. **Check instance is deployed** on RunPod
3. **Ensure instance is not suspended**
4. **Verify API key has access** to the endpoint

### Settings Not Saving

1. **Check file permissions** on ComfyUI directory
2. **Look for error messages** in the browser console
3. **Try reloading the page** and settings panel
4. **Check server logs** for backend errors

## Advanced Usage

### Custom Endpoints

You can configure multiple instances for different purposes:
- **Image Generation**: SDXL, FLUX, etc.
- **Text Processing**: LLM completion, summarization
- **Custom Models**: Your own deployed models

### Workflow Integration

Once configured, your instances will be available in:
- **RunPod Instance Selector** nodes
- **RunPod execution nodes** dropdown menus
- **Default instance** selection for quick workflows

## Security Notes

- **API keys are stored in plain text** in the settings file
- **Use proper file permissions** on your ComfyUI installation
- **Don't commit settings files** to version control
- **Consider environment variables** for production deployments

## File Structure

The web interface consists of:

```
ComfyBros/
├── web/
│   ├── comfybros.js              # Main entry point
│   └── comfybros_settings.js     # Settings panel implementation
├── web_api.py                    # Backend API endpoints
├── __web_init__.py              # ComfyUI web extension registration
└── settings.py                   # Settings data management
```

## Browser Compatibility

The web interface works with:
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## Support

If the web interface isn't working:

1. **Check this guide** for common solutions
2. **Look at browser developer tools** (F12) for errors
3. **Check ComfyUI console/logs** for backend errors
4. **Verify ComfyBros extension** is properly installed
5. **Try refreshing** the ComfyUI page

The web interface provides the same functionality as the node-based configuration but with a much more user-friendly experience!