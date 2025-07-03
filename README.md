# OpenWebUI Agent for Home Assistant

This integration allows Home Assistant to directly communicate with OpenWebUI as a Conversation Agent.

## Installation (via HACS)

1. In Home Assistant, navigate to HACS → Integrations → Custom repositories.
2. Add the URL of this repository and select type "Integration."
3. Click "Add," then "Download."
4. Restart Home Assistant.

## Configuration

You must configure your OpenWebUI API endpoint and model via `configuration.yaml`:

```yaml
openwebui_agent:
  url: "http://<openwebui_ip>:3000/api/v1/chat/completions"
  model: "your-openwebui-model-name"
```

Replace placeholders:
- `<openwebui_ip>`: IP address or hostname of your OpenWebUI server.
- `your-openwebui-model-name`: Name of your OpenWebUI model.

Restart Home Assistant after saving these changes.

## Usage

Navigate to Home Assistant → Assist and select "OpenWebUI Agent" as your active conversation agent.

Enjoy!