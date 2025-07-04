import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant import config_entries
from homeassistant.components import conversation

from .const import DOMAIN, CONF_AGENT_ID
from .config_flow import LettaConfigFlow
from .services import register_services, LettaConversationAgent

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    if DOMAIN in config:
        entry_data = {**config[DOMAIN]}
        await hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_IMPORT},
                data=entry_data,
            )
        )
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    hass.data[DOMAIN][entry.entry_id] = entry.data
    register_services(hass, entry.data)
    # Register Letta as a conversation agent under this entry_id
    conversation.async_set_agent(
        hass,
        entry.entry_id,
        LettaConversationAgent(hass, entry.data)
    )
    return True

async def async_unload_entry(hass, entry) -> bool:
    hass.services.async_remove(DOMAIN, "query_letta")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
