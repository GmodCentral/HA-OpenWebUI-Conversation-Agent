import aiohttp
import logging
import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.typing import ConfigType

DOMAIN = "extended_openai_conversation"

LETT_API_URL = "https://letta.avcompute.com/v1/agents/agent-83fb49e0-29d8-4faa-84f5-22549782042f/messages/stream"
AUTHORIZATION_TOKEN = "Admin980845-"  # Should ideally come from secure storage
PASSWORD_HEADER = "password Admin980845-"  # Should ideally come from secure storage

_LOGGER = logging.getLogger(__package__)

QUERY_SCHEMA = vol.Schema(
    {
        vol.Required("prompt"): cv.string,
        vol.Optional("max_tokens", default=300): cv.positive_int,
    }
)

async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:

    async def query_letta(call: ServiceCall) -> ServiceResponse:
        prompt = call.data["prompt"]
        max_tokens = call.data.get("max_tokens", 300)

        headers = {
            "Authorization": f"Bearer {AUTHORIZATION_TOKEN}",
            "X-BARE-PASSWORD": PASSWORD_HEADER,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        body = {
            "messages": [{"role": "user", "content": prompt}],
            "stream_steps": True,
            "stream_tokens": True,
        }

        response_text = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(LETT_API_URL, json=body, headers=headers) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"API Error: {resp.status}")

                    async for line in resp.content:
                        decoded_line = line.decode("utf-8").strip()
                        if decoded_line.startswith("data: "):
                            data = decoded_line[6:]
                            if data == "[DONE]":
                                break
                            message = json.loads(data)
                            if "reasoning" in message:
                                response_text += message["reasoning"]
                            elif "content" in message:
                                response_text += message["content"]

            _LOGGER.info("Final response from Letta: %s", response_text)

        except Exception as err:
            raise HomeAssistantError(f"Error communicating with Letta: {err}") from err

        return {"response": response_text}

    hass.services.async_register(
        DOMAIN,
        "query_letta",
        query_letta,
        schema=QUERY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
