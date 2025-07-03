import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .config_flow import LettaConfigFlow

_LOGGER = logging.getLogger(__name__)
DOMAIN = "letta_conversation"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry) -> bool:
    from .services import register_services
    hass.data[DOMAIN][entry.entry_id] = entry.data
    register_services(hass, entry.data)
    return True

async def async_unload_entry(hass, entry) -> bool:
    hass.services.async_remove(DOMAIN, "query_letta")
    hass.data[DOMAIN].pop(entry.entry_id)
    return True
