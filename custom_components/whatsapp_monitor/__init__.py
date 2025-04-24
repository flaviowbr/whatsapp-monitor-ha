"""
WhatsApp Monitor - Componente para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
import os
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME

_LOGGER = logging.getLogger(__name__)

# Constantes
DOMAIN = "whatsapp_monitor"
DEFAULT_NAME = "WhatsApp Monitor"

# Esquema de configuração
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional("palavras_chave", default=[]): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional("contatos_importantes", default=[]): vol.All(cv.ensure_list, [cv.string]),
                vol.Optional("intervalo_verificacao", default=15): cv.positive_int,
                vol.Optional("intervalo_resumo", default=60): cv.positive_int,
                vol.Optional("max_mensagens_resumo", default=10): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: dict):
    """Configuração do componente a partir do configuration.yaml."""
    if DOMAIN not in config:
        return True

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config[DOMAIN]

    # Inicializar monitor
    from .whatsapp_monitor_core import init_monitor
    await hass.async_add_executor_job(init_monitor, hass)

    # Configurar serviços
    from .services import async_setup_services
    await async_setup_services(hass)

    # Configurar sensores
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, config)
    )

    # Criar diretório www se não existir
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir)

    # Criar notificação inicial
    hass.components.persistent_notification.create(
        "WhatsApp Monitor foi inicializado. Use o serviço whatsapp_monitor.connect para conectar ao WhatsApp Web.",
        title="WhatsApp Monitor",
        notification_id="whatsapp_monitor_init"
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configuração do componente a partir de uma entrada de configuração."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = dict(entry.data)

    # Inicializar monitor
    from .whatsapp_monitor_core import init_monitor
    await hass.async_add_executor_job(init_monitor, hass)

    # Configurar serviços
    from .services import async_setup_services
    await async_setup_services(hass)

    # Configurar sensores
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, entry.data)
    )

    # Criar diretório www se não existir
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir)

    # Criar notificação inicial
    hass.components.persistent_notification.create(
        "WhatsApp Monitor foi inicializado. Use o serviço whatsapp_monitor.connect para conectar ao WhatsApp Web.",
        title="WhatsApp Monitor",
        notification_id="whatsapp_monitor_init"
    )

    # Registrar serviço para mostrar QR code
    async def handle_show_qrcode(call):
        """Manipulador para o serviço de exibição do QR Code."""
        # Criar URL para o navegador
        qrcode_url = f"{hass.config.internal_url}/local/whatsapp_qrcode.html"
        
        # Notificar o usuário
        hass.components.persistent_notification.create(
            f"Escaneie o QR Code para conectar ao WhatsApp Web. [Abrir QR Code]({qrcode_url})",
            title="WhatsApp QR Code",
            notification_id="whatsapp_qrcode"
        )
        
        return True

    # Registrar serviço adicional diretamente aqui para garantir
    hass.services.async_register(
        DOMAIN, "show_qrcode", handle_show_qrcode, schema=vol.Schema({})
    )

    # Iniciar conexão automaticamente
    from .whatsapp_monitor_core import connect_service
    hass.async_add_job(hass.async_add_executor_job, connect_service, hass)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarregar uma entrada de configuração."""
    # Desconectar do WhatsApp Web
    from .whatsapp_monitor_core import disconnect_service
    await hass.async_add_executor_job(disconnect_service, hass)
    
    # Remover sensores
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    # Remover serviços
    for service_name in ["check_messages", "generate_summary", "connect", "disconnect", "show_qrcode"]:
        hass.services.async_remove(DOMAIN, service_name)
    
    # Limpar dados
    hass.data.pop(DOMAIN)
    
    return True
