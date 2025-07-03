import logging
import requests
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.conversation import agent
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DOMAIN = "openwebui_agent"
CONF_MODEL = "model"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_URL): cv.url,
                vol.Required(CONF_MODEL): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    conf = config[DOMAIN]
    api_url = conf[CONF_URL]
    model = conf[CONF_MODEL]

    agent.async_set_agent(hass, DOMAIN, OpenWebUIAgent(hass, api_url, model))
    return True

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