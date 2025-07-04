import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_URL, CONF_PASSWORD, CONF_API_KEY
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_AGENT_ID

class LettaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL  # or LOCAL_POLL if more appropriate

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Validate URL format (optional)
            if not user_input[CONF_URL].startswith("http"):
                errors["url"] = "invalid_url"

            if not errors:
                return self.async_create_entry(title="Letta Conversation", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_URL, default="https://letta.avcompute.com"): cv.string,
            vol.Required(CONF_AGENT_ID): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Required(CONF_API_KEY): cv.string,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
