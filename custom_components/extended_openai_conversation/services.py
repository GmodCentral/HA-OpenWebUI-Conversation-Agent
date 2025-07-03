import logging
import voluptuous as vol
import httpx

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, selector
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SERVICE_QUERY_IMAGE

QUERY_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Required("prompt"): cv.string,
    }
)

_LOGGER = logging.getLogger(__package__)

async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up services for the extended openai conversation component."""

    async def query_image(call: ServiceCall) -> ServiceResponse:
        """Query Letta backend for a text response."""
        # HARDCODED values for now!
        auth_key = "Admin980845-"
        password = "Admin980845-"
        url = "letta.avcompute.com"
        agent_id = "agent-83fb49e0-29d8-4faa-84f5-22549782042f"

        endpoint = f"https://{url}/v1/agents/{agent_id}/messages/stream"
        headers = {
            "Authorization": f"Bearer {auth_key}",
            "X-BARE-PASSWORD": f"password {password}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        data = {
            "messages": [
                {
                    "role": "user",
                    "content": call.data["prompt"]
                }
            ],
            "stream_steps": True,
            "stream_tokens": True
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(endpoint, headers=headers, json=data)
                full_content = ""
                for raw_line in resp.iter_lines():
                    if raw_line.startswith(b"data:"):
                        line = raw_line[5:].strip()
                        try:
                            import json as _json
                            data_json = _json.loads(line)
                            # Prefer 'content', fall back to 'reasoning'
                            if 'content' in data_json and data_json['content']:
                                full_content += data_json['content']
                            elif 'reasoning' in data_json and data_json['reasoning']:
                                full_content += data_json['reasoning']
                        except Exception:
                            continue

            response_dict = {"content": full_content}
            _LOGGER.info("Letta response: %s", response_dict)
            return response_dict

        except Exception as err:
            raise HomeAssistantError(f"Error communicating with Letta API: {err}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY_IMAGE,
        query_image,
        schema=QUERY_IMAGE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )