import logging
import requests
from homeassistant.components.conversation import agent
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    agent.async_set_agent(hass, "openwebui_agent", OpenWebUIAgent(hass))
    return True

class OpenWebUIAgent(agent.AbstractConversationAgent):
    def __init__(self, hass):
        self.hass = hass
        self.api_url = "http://<openwebui_ip>:3000/api/v1/chat/completions"
        self.model = "your-openwebui-model-name"

    @property
    def supported_languages(self):
        return ["en"]

    async def async_process(self, user_input: agent.ConversationInput) -> agent.ConversationResult:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": user_input.text}],
            "stream": False
        }

        try:
            response = await self.hass.async_add_executor_job(
                requests.post, self.api_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
        except Exception as e:
            _LOGGER.error(f"OpenWebUI Agent error: {e}")
            reply = "Sorry, something went wrong talking to OpenWebUI."

        return agent.ConversationResult(
            response=agent.ConversationResponse(speech=reply),
            conversation_id=user_input.conversation_id
        )