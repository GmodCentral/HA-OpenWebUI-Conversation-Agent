import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN

class LettaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            return self.async_create_entry(title="Letta Conversation", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_URL, default="https://letta.avcompute.com"): cv.string,
            vol.Required("agent_id"): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_API_KEY): cv.string,
        })

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
