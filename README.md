# Letta Conversation Integration

Integrates Letta AI into Home Assistant as a conversation agent.

## Features
- Chat with Letta via services & conversation interface
- Control Home Assistant devices via Letta

## Installation
1. Copy `custom_components/letta_conversation` to your HA `custom_components` folder.
2. Restart Home Assistant.
3. In Configuration → Integrations, add the Letta Conversation integration.

## Configuration Options
| Option    | Description                              |
|-----------|------------------------------------------|
| URL       | Base URL (e.g. https://letta.avcompute.com) |
| Agent ID  | Your agent identifier                    |
| Password  | X-BARE-PASSWORD                          |
| Auth Key  | Authorization Bearer token               |
