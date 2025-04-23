"""
WhatsApp Monitor - Componente personalizado para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import os
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.const import (
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_START,
)
from homeassistant.helpers.event import async_track_time_interval

_LOGGER = logging.getLogger(__name__)

# Nome do domínio para o componente
DOMAIN = "whatsapp_monitor"
SCAN_INTERVAL = timedelta(minutes=15)

# Configuração do componente
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.time_period,
                vol.Optional("palavras_chave"): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional("contatos_importantes"): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional("intervalo_resumo", default=60): cv.positive_int,
                vol.Optional("max_mensagens_resumo", default=10): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Configuração do componente WhatsApp Monitor."""
    
    # Criar diretório de configuração se não existir
    component_config_dir = hass.config.path("custom_components", DOMAIN)
    os.makedirs(component_config_dir, exist_ok=True)
    
    # Criar diretórios para resumos e gráficos
    resumos_dir = os.path.join(component_config_dir, "resumos")
    graficos_dir = os.path.join(component_config_dir, "graficos")
    os.makedirs(resumos_dir, exist_ok=True)
    os.makedirs(graficos_dir, exist_ok=True)
    
    # Obter configuração
    conf = config.get(DOMAIN, {})
    scan_interval = conf.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)
    
    # Criar instância do componente
    component = EntityComponent(_LOGGER, DOMAIN, hass, scan_interval)
    
    # Armazenar configuração no hass.data
    hass.data[DOMAIN] = {
        "config": conf,
        "resumos_dir": resumos_dir,
        "graficos_dir": graficos_dir,
        "component": component,
        "monitor": None,
        "mensagens_importantes": [],
    }
    
    # Registrar serviços
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
    hass.services.async_register(DOMAIN, "check_messages", handle_check_messages)
    hass.services.async_register(DOMAIN, "generate_summary", handle_generate_summary)
    hass.services.async_register(DOMAIN, "connect", handle_connect)
    hass.services.async_register(DOMAIN, "disconnect", handle_disconnect)
    
    # Inicializar o monitor quando o Home Assistant iniciar
    async def init_whatsapp_monitor(event):
        """Inicializar o WhatsApp Monitor quando o Home Assistant iniciar."""
        from .whatsapp_monitor_core import init_monitor
        
        await hass.async_add_executor_job(
            init_monitor, hass
        )
        
        # Configurar verificação periódica
        async def periodic_check(now=None):
            """Executar verificação periódica de mensagens."""
            await handle_check_messages(None)
        
        async def periodic_summary(now=None):
            """Executar geração periódica de resumo."""
            await handle_generate_summary(None)
        
        # Agendar verificações e resumos
        intervalo_verificacao = timedelta(minutes=conf.get("intervalo_verificacao", 15))
        intervalo_resumo = timedelta(minutes=conf.get("intervalo_resumo", 60))
        
        async_track_time_interval(hass, periodic_check, intervalo_verificacao)
        async_track_time_interval(hass, periodic_summary, intervalo_resumo)
    
    # Registrar callback para inicialização
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, init_whatsapp_monitor)
    
    # Carregar plataformas (sensor)
    hass.async_create_task(
        async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    
    return True
