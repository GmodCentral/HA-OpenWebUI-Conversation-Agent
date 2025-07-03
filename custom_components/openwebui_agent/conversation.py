import logging
import requests
from homeassistant.components.conversation import agent
from .const import DOMAIN, CONF_URL, CONF_MODEL

_LOGGER = logging.getLogger(__name__)

async def async_setup_agent(hass, config):
    entry = config
    url = entry.data[CONF_URL]
    model = entry.data[CONF_MODEL]
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["agent"] = OpenWebUIAgent(hass, url, model)
    return hass.data[DOMAIN]["agent"]

class OpenWebUIAgent(agent.AbstractConversationAgent):
    def __init__(self, hass, api_url, model):
        self.hass = hass
        self.api_url = api_url
        self.model = model

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
