"""
WhatsApp Monitor - Componente simplificado para Home Assistant
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

    # Criar diretório www se não existir
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir)

    # Registrar serviço para mostrar QR code
    async def handle_show_qrcode(call):
        """Manipulador para o serviço de exibição do QR Code."""
        # Criar URL para o navegador
        qrcode_url = f"{hass.config.internal_url}/whatsapp_login"
        
        # Notificar o usuário
        hass.components.persistent_notification.create(
            f"Escaneie o QR Code para conectar ao WhatsApp Web. [Abrir QR Code]({qrcode_url})",
            title="WhatsApp QR Code",
            notification_id="whatsapp_qrcode"
        )
        
        return True

    # Registrar serviço
    hass.services.async_register(
        DOMAIN, "show_qrcode", handle_show_qrcode, schema=vol.Schema({})
    )

    # Criar notificação inicial
    hass.components.persistent_notification.create(
        f"WhatsApp Monitor foi inicializado. [Abrir WhatsApp Web]({hass.config.internal_url}/whatsapp_login)",
        title="WhatsApp Monitor",
        notification_id="whatsapp_monitor_init"
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configuração do componente a partir de uma entrada de configuração."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = dict(entry.data)

    # Criar diretório www se não existir
    www_dir = hass.config.path("www")
    if not os.path.exists(www_dir):
        os.makedirs(www_dir)

    # Registrar serviço para mostrar QR code
    async def handle_show_qrcode(call):
        """Manipulador para o serviço de exibição do QR Code."""
        # Criar URL para o navegador
        qrcode_url = f"{hass.config.internal_url}/whatsapp_login"
        
        # Notificar o usuário
        hass.components.persistent_notification.create(
            f"Escaneie o QR Code para conectar ao WhatsApp Web. [Abrir QR Code]({qrcode_url})",
            title="WhatsApp QR Code",
            notification_id="whatsapp_qrcode"
        )
        
        return True

    # Registrar serviço
    hass.services.async_register(
        DOMAIN, "show_qrcode", handle_show_qrcode, schema=vol.Schema({})
    )

    # Configurar sensores
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, entry.data)
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarregar uma entrada de configuração."""
    # Remover sensores
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    # Remover serviços
    hass.services.async_remove(DOMAIN, "show_qrcode")
    
    # Limpar dados
    hass.data.pop(DOMAIN)
    
    return True
