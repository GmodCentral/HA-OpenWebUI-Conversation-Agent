import logging
import requests
from homeassistant.components.conversation import agent, DISCOVERY_SCHEMA
from .const import CONF_URL, CONF_MODEL, CONF_AUTH_KEY

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = DISCOVERY_SCHEMA

async def async_get_agent(hass, entry):
    url = entry.data[CONF_URL]
    model = entry.data[CONF_MODEL]
    auth_key = entry.data[CONF_AUTH_KEY]
    return OpenWebUIAgent(hass, url, model, auth_key)

class OpenWebUIAgent(agent.AbstractConversationAgent):
    def __init__(self, hass, api_url, model, auth_key):
        self.hass = hass
        self.api_url = api_url
        self.model = model
        self.auth_key = auth_key

    @property
    def supported_languages(self):
        return ["en"]

    async def async_process(self, user_input: agent.ConversationInput) -> agent.ConversationResult:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.auth_key}",
        }
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
