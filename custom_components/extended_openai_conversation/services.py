import httpx
import base64
import logging
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

from openai import AsyncOpenAI
from openai._exceptions import OpenAIError
from openai.types.chat.chat_completion_content_part_image_param import (
    ChatCompletionContentPartImageParam,
)
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

from .const import DOMAIN, SERVICE_QUERY_IMAGE

QUERY_IMAGE_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): selector.ConfigEntrySelector(
            {
                "integration": DOMAIN,
            }
        ),
        vol.Required("model", default="gpt-4-vision-preview"): cv.string,
        vol.Required("prompt"): cv.string,
        vol.Required("images"): vol.All(cv.ensure_list, [{"url": cv.string}]),
        vol.Optional("max_tokens", default=300): cv.positive_int,
    }
)

_LOGGER = logging.getLogger(__package__)


async def async_setup_services(hass: HomeAssistant, config: ConfigType) -> None:
    """Set up services for the extended openai conversation component."""

    async def query_image(call: ServiceCall) -> ServiceResponse:
        """Query an image."""
        try:
            model = call.data["model"]
            images = [
                {"type": "image_url", "image_url": to_image_param(hass, image)}
                for image in call.data["images"]
            ]

            messages = [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": call.data["prompt"]}] + images,
                }
            ]
            _LOGGER.info("Prompt for %s: %s", model, messages)

            async with httpx.AsyncClient() as client:
                letta_url = "https://letta.avcompute.com/v1/agents/agent-83fb49e0-29d8-4faa-84f5-22549782042f/messages/stream"
                headers = {
                    "Authorization": "Bearer Admin980845-",
                    "X-BARE-PASSWORD": "password Admin980845-",
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
                # Use streaming, assemble the full message from the event-stream lines
                resp = await client.post(letta_url, headers=headers, json=data, timeout=60)
                full_content = ""
                for raw_line in resp.iter_lines():
                    if raw_line.startswith(b"data:"):
                        line = raw_line[5:].strip()
                        try:
                            import json as _json
                            data_json = _json.loads(line)
                            # Try both OpenAI-style and your backend's field
                            if 'content' in data_json:
                                full_content += data_json['content']
                            elif 'reasoning' in data_json:
                                full_content += data_json['reasoning']
                        except Exception:
                            continue
                response_dict = {"content": full_content}

            _LOGGER.info("Response %s", response_dict)
        except OpenAIError as err:
            raise HomeAssistantError(f"Error generating image: {err}") from err

        return response_dict

    hass.services.async_register(
        DOMAIN,
        SERVICE_QUERY_IMAGE,
        query_image,
        schema=QUERY_IMAGE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def to_image_param(hass: HomeAssistant, image) -> ChatCompletionContentPartImageParam:
    """Convert url to base64 encoded image if local."""
    url = image["url"]

    if urlparse(url).scheme in cv.EXTERNAL_URL_PROTOCOL_SCHEMA_LIST:
        return image

    if not hass.config.is_allowed_path(url):
        raise HomeAssistantError(
            f"Cannot read `{url}`, no access to path; "
            "`allowlist_external_dirs` may need to be adjusted in "
            "`configuration.yaml`"
        )
    if not Path(url).exists():
        raise HomeAssistantError(f"`{url}` does not exist")
    mime_type, _ = mimetypes.guess_type(url)
    if mime_type is None or not mime_type.startswith("image"):
        raise HomeAssistantError(f"`{url}` is not an image")

    image["url"] = f"data:{mime_type};base64,{encode_image(url)}"
    return image


def encode_image(image_path):
    """Convert to base64 encoded image."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
