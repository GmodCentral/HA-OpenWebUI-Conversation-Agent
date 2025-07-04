# custom_components/letta_conversation/services.py

import aiohttp
import json
import logging
import voluptuous as vol

from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.conversation import AbstractConversationAgent, ConversationResult
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_AGENT_ID

_LOGGER = logging.getLogger(__name__)

class LettaConversationAgent(AbstractConversationAgent):
    @property
    def supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["en"]

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self.hass = hass
        self.config = config

    async def async_process(self, user_input) -> ConversationResult:
        """Process user input and return Letta's response."""
        result = await self.hass.services.async_call(
            DOMAIN,
            "query_letta",
            {"prompt": user_input.text},
            blocking=True,
            return_response=True,
        )
        response = result[0].get("response", "")
        return ConversationResult(response)

def register_services(hass: HomeAssistant, config: dict) -> None:
    """Register the `query_letta` service."""
    async def query_letta(call: ServiceCall) -> dict:
        prompt = call.data.get("prompt", "")
        url = f"{config[CONF_URL]}/v1/agents/{config[CONF_AGENT_ID]}/messages/stream"

        headers = {
            "Authorization": f"Bearer {config[CONF_API_KEY]}",
            "X-BARE-PASSWORD": config[CONF_PASSWORD],
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        body = {
            "messages": [{"role": "user", "content": prompt}],
            "stream_steps": True,
            "stream_tokens": True
        }

        response_text = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"Letta API error: {resp.status}")
                    async for chunk in resp.content:
                        line = chunk.decode().strip()
                        if not line.startswith("data: "):
                            continue
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        msg = json.loads(data)
                        response_text += msg.get("reasoning", msg.get("content", ""))
            _LOGGER.debug("Letta response: %s", response_text)
        except Exception as e:
            raise HomeAssistantError(f"Error talking to Letta: {e}")

        return {"response": response_text}

    schema = vol.Schema({vol.Required("prompt"): cv.string})
    hass.services.async_register(
        DOMAIN,
        "query_letta",
        query_letta,
        schema=schema,
        supports_response=SupportsResponse.ONLY,
    )
