# RunPod Serverless Integration for ComfyBros

This guide explains how to set up and use the RunPod serverless integration in ComfyBros.

## Overview

The RunPod integration allows you to execute computational tasks on RunPod's serverless infrastructure directly from ComfyUI workflows. This is useful for:

- Offloading heavy computation to powerful cloud instances
- Running specialized models not available locally
- Scaling workloads beyond local hardware limitations

## Setup Instructions

### 1. Get RunPod API Key

1. Sign up at [RunPod.io](https://runpod.io)
2. Go to your dashboard and generate an API key
3. Keep this key secure - you'll need it for configuration

### 2. Create RunPod Serverless Endpoints

Before using the ComfyBros integration, you need to set up serverless endpoints on RunPod:

1. In RunPod dashboard, go to "Serverless"
2. Create new endpoint(s) with your desired Docker images
3. Note the endpoint IDs - you'll need these for configuration

### 3. Configure RunPod in ComfyUI

#### Step 1: Basic Configuration

1. Add the `RunPod Configuration` node to your workflow
2. Enter your RunPod API key
3. Set `enabled` to `true`
4. Execute the node to save your configuration

#### Step 2: Add Serverless Instances

1. Add the `RunPod Instance Manager` node to your workflow
2. Set `action` to "CREATE_NEW"
3. Fill in the details:
   - **Instance Name**: A friendly name for your instance
   - **Endpoint ID**: The endpoint ID from RunPod dashboard
   - **Description**: Optional description
   - **Max Workers**: Number of concurrent workers (usually 1)
   - **Timeout**: Maximum execution time in seconds
   - **Set as Default**: Check if this should be your default instance
4. Execute the node to add the instance

#### Step 3: Verify Setup

1. Add the `RunPod Health Checker` node
2. Set `instance` to "ALL" and `check_connectivity` to `true`
3. Execute to verify all instances are working correctly

## Available Nodes

### Configuration Nodes

- **RunPod Configuration**: Set up API key and global settings
- **RunPod Instance Manager**: Add, update, or delete serverless instances
- **RunPod Instance Selector**: Select and output instance configurations

### Execution Nodes

- **RunPod Generic Executor**: Execute arbitrary tasks with custom JSON input
- **RunPod Image Generator**: Generate images using serverless endpoints
- **RunPod Text Processor**: Process text (completion, summarization, etc.)
- **RunPod Health Checker**: Monitor instance health and connectivity

## Usage Examples

### Example 1: Image Generation

```
[RunPod Instance Selector] → [RunPod Image Generator] → [Image Output]
```

1. Use `RunPod Instance Selector` to pick your image generation endpoint
2. Connect to `RunPod Image Generator`
3. Set your prompt, negative prompt, and generation parameters
4. The generated image will be returned as a standard ComfyUI image

### Example 2: Text Processing

```
[Text Input] → [RunPod Text Processor] → [Text Output]
```

1. Input your text to process
2. Select task type (completion, summarization, translation, custom)
3. Set parameters like max_tokens and temperature
4. Processed text is returned

### Example 3: Custom Processing

```
[JSON Input] → [RunPod Generic Executor] → [JSON Output]
```

1. Prepare your input data as JSON
2. Use `RunPod Generic Executor` for maximum flexibility
3. Results depend on your serverless endpoint implementation

## Instance Management

### Adding New Instances

Use the `RunPod Instance Manager` node with action "CREATE_NEW":

- **Instance Name**: Must be unique within your configuration
- **Endpoint ID**: From your RunPod dashboard
- **Description**: Optional, for documentation
- **Enabled**: Whether this instance is available for use
- **Max Workers**: Concurrent execution limit
- **Timeout**: Maximum execution time before cancellation

### Updating Instances

1. Set action to the name of an existing instance
2. Modify the fields you want to update
3. Execute to save changes

### Deleting Instances

1. Set action to "DELETE_SELECTED"
2. Enter the instance name to delete
3. Execute to remove the instance

## Error Handling

The system includes comprehensive error handling:

- **Connection Errors**: Reported when RunPod API is unreachable
- **Authentication Errors**: Shown when API key is invalid
- **Job Failures**: Detailed error messages from serverless endpoints
- **Timeout Errors**: When jobs exceed configured timeout limits

## Troubleshooting

### Common Issues

1. **"No API key configured"**
   - Solution: Use `RunPod Configuration` node to set your API key

2. **"Instance not found"**
   - Solution: Check instance name spelling or use `RunPod Instance Manager` to verify instances

3. **"Connection failed"**
   - Solution: Check internet connection and API key validity

4. **"Job timed out"**
   - Solution: Increase timeout in instance configuration or optimize your serverless function

### Debug Information

- All nodes provide detailed status messages
- Check the ComfyUI console for detailed logging
- Use `RunPod Health Checker` to diagnose connectivity issues

## Settings Storage

Settings are automatically saved to:
- Primary: ComfyUI user directory (if available)
- Fallback: Extension directory

Settings file: `comfybros_settings.json`

## Security Notes

- API keys are stored in plain text in the settings file
- Ensure proper file permissions on your ComfyUI installation
- Never commit settings files to version control
- Consider using environment variables for sensitive deployments

## API Reference

### Input Data Formats

Different serverless endpoints expect different input formats. Common patterns:

**Image Generation:**
```json
{
  "prompt": "A beautiful landscape",
  "negative_prompt": "blurry, low quality",
  "width": 512,
  "height": 512,
  "num_inference_steps": 20,
  "guidance_scale": 7.0,
  "seed": 42
}
```

**Text Processing:**
```json
{
  "task_type": "completion",
  "input_text": "Complete this sentence:",
  "max_tokens": 150,
  "temperature": 0.7
}
```

### Output Formats

**Successful Response:**
```json
{
  "output": { /* your result data */ },
  "execution_time": 2.34
}
```

**Error Response:**
```json
{
  "error": "Error description",
  "status": "FAILED"
}
```

## Advanced Configuration

### Custom Policies

You can set execution policies in the `RunPod Generic Executor`:

```json
{
  "input": { /* your input data */ },
  "policy": {
    "executionTimeout": 300,
    "idleTimeout": 10
  }
}
```

### Webhook Integration

For long-running jobs, you can specify webhook URLs:

1. Set up a webhook endpoint to receive results
2. Use the webhook_url parameter in execution nodes
3. Jobs will POST results to your webhook when complete

This is useful for asynchronous processing workflows.

## Support

For issues with the ComfyBros RunPod integration:
1. Check this documentation first
2. Verify your RunPod dashboard configuration
3. Test with `RunPod Health Checker`
4. Check ComfyUI console logs for detailed error messages

For RunPod platform issues, refer to [RunPod Documentation](https://docs.runpod.io/).