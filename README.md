# Letta Conversation Integration

Integrates Letta AI into Home Assistant as a conversation agent.

## Features
- Chat with Letta via services & conversation interface
- Control Home Assistant devices via Letta

## Installation
### HACS
1. Add this repository to HACS as a custom repository (Integration).
2. Install "Letta Conversation" via HACS.
3. Restart Home Assistant.

### YAML Configuration (optional)
Add the following to your `configuration.yaml`:
```yaml
letta_conversation:
  url: https://letta.avcompute.com
  agent_id: agent-83fb49e0-29d8-4faa-84f5-22549782042f
  password: Admin980845-
  api_key: Admin980845-
```

Restart Home Assistant. Then configure via UI if needed or use services directly.
