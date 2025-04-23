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
SCHEMA_CHECK_MESSAGES = vol.Schema({})

SCHEMA_GENERATE_SUMMARY = vol.Schema({})

SCHEMA_CONNECT = vol.Schema({})

SCHEMA_DISCONNECT = vol.Schema({})

async def async_setup_services(hass):
    """Configurar serviços para WhatsApp Monitor."""
    
    async def handle_check_messages(call):
        """Manipulador para o serviço de verificação de mensagens."""
        from .whatsapp_monitor_core import check_messages_service
        
        await hass.async_add_executor_job(
            check_messages_service, hass
        )
    
    async def handle_generate_summary(call):
        """Manipulador para o serviço de geração de resumo."""
        from .whatsapp_monitor_core import generate_summary_service
        
        await hass.async_add_executor_job(
            generate_summary_service, hass
        )
    
    async def handle_connect(call):
        """Manipulador para o serviço de conexão ao WhatsApp."""
        from .whatsapp_monitor_core import connect_service
        
        await hass.async_add_executor_job(
            connect_service, hass
        )
    
    async def handle_disconnect(call):
        """Manipulador para o serviço de desconexão do WhatsApp."""
        from .whatsapp_monitor_core import disconnect_service
        
        await hass.async_add_executor_job(
            disconnect_service, hass
        )
    
    # Registrar serviços
    hass.services.async_register(
        DOMAIN, "check_messages", handle_check_messages, schema=SCHEMA_CHECK_MESSAGES
    )
    
    hass.services.async_register(
        DOMAIN, "generate_summary", handle_generate_summary, schema=SCHEMA_GENERATE_SUMMARY
    )
    
    hass.services.async_register(
        DOMAIN, "connect", handle_connect, schema=SCHEMA_CONNECT
    )
    
    hass.services.async_register(
        DOMAIN, "disconnect", handle_disconnect, schema=SCHEMA_DISCONNECT
    )
    
    return True
