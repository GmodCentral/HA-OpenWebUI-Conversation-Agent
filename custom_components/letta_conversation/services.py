import aiohttp
import json
import logging
from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError

DOMAIN = "letta_conversation"
_LOGGER = logging.getLogger(__name__)

def register_services(hass: HomeAssistant, config: dict) -> None:
    async def query_letta(call: ServiceCall) -> dict:
        prompt = call.data.get("prompt", "")
        url = f"{config[CONF_URL]}/v1/agents/{config['agent_id']}/messages/stream"

        headers = {
            "Authorization": f"Bearer {config[CONF_API_KEY]}",
            "X-BARE-PASSWORD": config[CONF_PASSWORD],
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        body = {"messages": [{"role": "user", "content": prompt}], "stream_steps": True, "stream_tokens": True}

        response_text = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"Letta API error: {resp.status}")
                    async for chunk in resp.content:
                        line = chunk.decode().strip()
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            msg = json.loads(data)
                            response_text += msg.get("reasoning", msg.get("content", ""))
            _LOGGER.debug("Letta response: %s", response_text)
        except Exception as e:
            raise HomeAssistantError(f"Error talking to Letta: {e}")

        return {"response": response_text}

    hass.services.async_register(
        DOMAIN,
        "query_letta",
        query_letta,
        schema={"prompt": str},
        supports_response=SupportsResponse.ONLY,
    )
