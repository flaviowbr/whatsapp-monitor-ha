"""
WhatsApp Monitor - Configuração da interface do usuário para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
import voluptuous as vol

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

_LOGGER = logging.getLogger(__name__) 

# Esquema de configuração para o fluxo de configuração
CONFIG_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default="WhatsApp Monitor"): cv.string,
    vol.Optional("palavras_chave"): cv.multi_select({
        "urgente": "Urgente",
        "importante": "Importante",
        "atenção": "Atenção",
        "prioridade": "Prioridade",
        "crítico": "Crítico",
        "emergência": "Emergência",
        "ajuda": "Ajuda",
        "socorro": "Socorro",
        "imediato": "Imediato",
        "prazo": "Prazo"
    }),
    vol.Optional("intervalo_verificacao", default=15): vol.All(
        vol.Coerce(int), vol.Range(min=5, max=60)
    ),
    vol.Optional("intervalo_resumo", default=60): vol.All(
        vol.Coerce(int), vol.Range(min=15, max=1440)
    ),
    vol.Optional("max_mensagens_resumo", default=10): vol.All(
        vol.Coerce(int), vol.Range(min=5, max=50)
    ),
})

class WhatsAppMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Manipula o fluxo de configuração para WhatsApp Monitor."""
    
    VERSION = 1
    CONNECTION_CLASS = "local_poll"
    
    async def async_step_user(self, user_input=None):
        """Manipula o fluxo de configuração iniciado pelo usuário."""
        errors = {}
        
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME, "WhatsApp Monitor"),
                data=user_input
            )
        
        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )
