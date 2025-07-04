import aiohttp
import json
import logging
import voluptuous as vol

from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.conversation import AbstractConversationAgent, ConversationResult
from homeassistant.helpers.intent import IntentResponse
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_AGENT_ID

_LOGGER = logging.getLogger(__name__)


class LettaConversationAgent(AbstractConversationAgent):
    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self.hass = hass
        self.config = config

    async def async_process(self, user_input) -> ConversationResult:
        """Process user input and return Letta's response."""
        # Call the query service
        result = await self.hass.services.async_call(
            DOMAIN,
            "query_letta",
            {"prompt": user_input.text},
            blocking=True,
            return_response=True,
        )

        # Normalize service result
        raw = ""
        if isinstance(result, list) and result:
            raw = result[0].get("response", "")
        elif isinstance(result, dict):
            raw = result.get("response", "")

        # Wrap in IntentResponse so HA can serialize it
        resp = IntentResponse(language=user_input.language, intent=None)
        resp.async_set_speech(raw)

        return ConversationResult(response=resp, conversation_id=user_input.conversation_id)


def register_services(hass: HomeAssistant, config: dict) -> None:
    """Register the `query_letta` service."""
    async def query_letta(call: ServiceCall) -> dict:
        prompt = call.data["prompt"]
        # Use non‐streaming endpoint
        url = f"{config[CONF_URL]}/v1/agents/{config[CONF_AGENT_ID]}/messages"

        headers = {
            "Authorization": f"Bearer {config[CONF_API_KEY]}",
            "X-BARE-PASSWORD": config[CONF_PASSWORD],
            "Content-Type": "application/json",
        }
        body = {
            "messages": [{"role": "user", "content": prompt}]
        }

        response_text = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"Letta API error: {resp.status}")
                    data = await resp.json()
                    for msg in data.get("messages", []):
                        # accumulate any assistant message content
                        if "content" in msg:
                            response_text += msg["content"]

            _LOGGER.debug("Letta response: %s", response_text)
        except Exception as e:
            raise HomeAssistantError(f"Error talking to Letta: {e}") from e

        return {"response": response_text}

    schema = vol.Schema({vol.Required("prompt"): cv.string})
    hass.services.async_register(
        DOMAIN,
        "query_letta",
        query_letta,
        schema=schema,
        supports_response=SupportsResponse.ONLY,
    )
