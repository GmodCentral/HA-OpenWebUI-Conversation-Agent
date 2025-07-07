import aiohttp
import json
import logging
import voluptuous as vol

from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse, Context
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.conversation import AbstractConversationAgent, ConversationResult
from homeassistant.helpers.intent import IntentResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event

from .const import DOMAIN, CONF_AGENT_ID, CONF_TTS_SPEAKERS

_LOGGER = logging.getLogger(__name__)

class LettaConversationAgent(AbstractConversationAgent):
    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self.hass = hass
        self.config = config

    async def async_process(self, user_input) -> ConversationResult:
        """Process user input and return Letta's response, then handle TTS and follow-up."""
        # Detect voice vs. chat
        src = getattr(user_input, "source", "").lower()
        is_voice = src not in ("text", "", None)
        prompt = user_input.text
        if is_voice:
            prompt = "[fromvoice:true] " + prompt

        # Query Letta backend
        result = await self.hass.services.async_call(
            DOMAIN,
            "query_letta",
            {"prompt": prompt},
            blocking=True,
            return_response=True,
        )

        # Extract raw response
        raw = ""
        if isinstance(result, list) and result:
            raw = result[0].get("response", "") or ""
        elif isinstance(result, dict):
            raw = result.get("response", "") or ""

        # Detect markers
        followup  = "[followup:true]" in raw
        fromvoice = "[fromvoice:true]" in raw

        # Clean speech text
        speech = raw.replace("[followup:true]", "").replace("[fromvoice:true]", "").strip()

        # Handle TTS playback and follow-up
        tts_speakers = self.config.get(CONF_TTS_SPEAKERS, [])
        if followup and fromvoice and tts_speakers:
            _LOGGER.debug("Letta: sending TTS to %s", tts_speakers)
            # Create context to filter our TTS
            tts_ctx = Context()
            # Call TTS speak
            await self.hass.services.async_call(
                "tts",
                "speak",
                {
                    "entity_id": tts_speakers,
                    "message": speech,
                },
                blocking=False,
                context=tts_ctx,
            )
            _LOGGER.debug("Letta: subscribing to TTS completion for context %s", tts_ctx.id)
            # Subscribe to state change only for our speakers and context
            def _listener(event):
                old = event.data.get("old_state")
                new = event.data.get("new_state")
                if (
                    old and new
                    and old.state == "playing"
                    and new.state in ("idle", "off")
                    and event.context.id == tts_ctx.id
                ):
                    _LOGGER.debug("Letta: TTS completed, firing follow-up")
                    unsub()
                    self.hass.bus.async_fire("letta_conversation_followup")
            unsub = async_track_state_change_event(self.hass, tts_speakers, _listener)
        else:
            # No configured speakers or no followup, just set speech
            _LOGGER.debug("Letta: using conversation TTS for response")
            # Use built-in conversation TTS
            speech = speech

        # Wrap in IntentResponse
        resp = IntentResponse(language=user_input.language, intent=None)
        resp.async_set_speech(speech)

        return ConversationResult(
            response=resp,
            conversation_id=user_input.conversation_id
        )

def register_services(hass: HomeAssistant, config: dict) -> None:
    """Register the `query_letta` service."""
    async def query_letta(call: ServiceCall) -> dict:
        prompt = call.data["prompt"]
        url = f"{config[CONF_URL]}/v1/agents/{config[CONF_AGENT_ID]}/messages"

        headers = {
            "Authorization": f"Bearer {config[CONF_API_KEY]}",
            "X-BARE-PASSWORD": config[CONF_PASSWORD],
            "Content-Type": "application/json",
        }
        body = {"messages": [{"role": "user", "content": prompt}]}

        response_text = ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"Letta API error: {resp.status}")
                    data = await resp.json()
                    for msg in data.get("messages", []):
                        if "content" in msg:
                            response_text += msg["content"] or ""
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
