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
from homeassistant.helpers.event import async_track_state_change

from .const import DOMAIN, CONF_AGENT_ID, CONF_TTS_SPEAKERS

_LOGGER = logging.getLogger(__name__)


class LettaConversationAgent(AbstractConversationAgent):
    @property
    def supported_languages(self) -> list[str]:
        return ["en"]

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        self.hass = hass
        self.config = config
        # List of media_player entities to send TTS to
        self._tts_speakers: list[str] = config.get(CONF_TTS_SPEAKERS, [])
        # Keep unsubscribe callbacks here so we only listen once per speaker
        self._followup_unsubs: dict[str, callable] = {}

    async def async_process(self, user_input) -> ConversationResult:
        """Process user input, speak via TTS if voice, and handle follow-up triggers."""
        # ── Detect voice vs chat ────────────────────────────────
        src = getattr(user_input, "source", "") or ""
        is_voice = src.lower() not in ("text", "")
        prompt = user_input.text
        if is_voice:
            prompt = "[fromvoice:true] " + prompt

        # ── Query Letta backend ──────────────────────────────────
        result = await self.hass.services.async_call(
            DOMAIN,
            "query_letta",
            {"prompt": prompt},
            blocking=True,
            return_response=True,
        )
        raw = ""
        if isinstance(result, list) and result:
            raw = result[0].get("response", "") or ""
        elif isinstance(result, dict):
            raw = result.get("response", "") or ""
        _LOGGER.debug("Letta raw response: %s", raw)

        # ── Flags & cleanup ─────────────────────────────────────
        followup  = "[followup:true]" in raw
        fromvoice = "[fromvoice:true]"  in raw
        cleaned = raw.replace("[followup:true]", "").replace("[fromvoice:true]", "").strip()

        # ── Speak back on configured speakers ────────────────────
        if is_voice and self._tts_speakers and cleaned:
            for speaker in self._tts_speakers:
                try:
                    await self.hass.services.async_call(
                        "tts",
                        "speak",
                        {
                            "media_player_entity_id": speaker,
                            "message": cleaned,
                        },
                        blocking=False,
                    )
                    _LOGGER.debug("Letta: TTS sent to %s", speaker)
                except Exception as e:
                    _LOGGER.error("Letta: failed TTS on %s: %s", speaker, e)

        # ── State-based follow-up trigger ────────────────────────
        if followup and fromvoice and self._tts_speakers:
            for speaker in self._tts_speakers:
                # Only subscribe once per speaker
                if speaker in self._followup_unsubs:
                    continue

                _LOGGER.debug("Letta: will fire follow-up when %s stops playing", speaker)

                def _state_listener(entity_id, old, new):
                    old_state = old.state if old else None
                    new_state = new.state if new else None
                    # Trigger when it WAS playing/on and now is not
                    if old_state in ("playing", "on") and new_state not in ("playing", "on"):
                        _LOGGER.debug("%s stopped – firing follow-up", entity_id)
                        self.hass.bus.async_fire("letta_conversation_followup")
                        # Cleanup listener
                        unsub = self._followup_unsubs.pop(entity_id, None)
                        if unsub:
                            unsub()

                unsub = async_track_state_change(
                    self.hass,
                    speaker,
                    _state_listener
                )
                self._followup_unsubs[speaker] = unsub

        # ── Return cleaned response to HA conversation pipeline ───
        resp = IntentResponse(language=user_input.language, intent=None)
        resp.async_set_speech(cleaned)
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
                            response_text += msg["content"]
            _LOGGER.debug("Letta response_text: %s", response_text)
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
