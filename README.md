# OpenWebUI Agent for Home Assistant

This integration allows Home Assistant to directly communicate with OpenWebUI as a Conversation Agent.

## Installation (via HACS)

1. Go to HACS → Integrations → Custom repositories
2. Add the URL of this GitHub repository and select type "Integration".
3. Click "Add".
4. Restart Home Assistant.
5. Navigate to Home Assistant → Assist and select "OpenWebUI Agent" as your active conversation agent.

## Configuration

No additional YAML required. Your OpenWebUI API endpoint and model should be directly edited in:

`custom_components/openwebui_agent/__init__.py`

Replace placeholders:
- `<openwebui_ip>`
- `your-openwebui-model-name`

Restart Home Assistant after changes.