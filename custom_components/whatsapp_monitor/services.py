"""
WhatsApp Monitor - Serviços para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import service

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Esquemas para serviços
SCHEMA_SHOW_QRCODE = vol.Schema({})

async def async_setup_services(hass):
    """Configurar serviços para WhatsApp Monitor."""
    
    async def handle_show_qrcode(call):
        """Manipulador para o serviço de exibição do QR Code."""
        # Criar URL para o navegador
        qrcode_url = f"{hass.config.internal_url}/local/whatsapp_login.html"
        
        # Notificar o usuário
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "WhatsApp QR Code",
                "message": f"Escaneie o QR Code para conectar ao WhatsApp Web. [Abrir QR Code]({qrcode_url})",
                "notification_id": "whatsapp_qrcode"
            }
        )
        
        return True
    
    # Registrar serviços
    hass.services.async_register(
        DOMAIN, "show_qrcode", handle_show_qrcode, schema=SCHEMA_SHOW_QRCODE
    )
    
    return True
