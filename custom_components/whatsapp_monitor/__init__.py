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

    # Registrar serviço para atualizar palavras-chave
    async def handle_update_keywords(call):
        """Manipulador para o serviço de atualização de palavras-chave."""
        palavras_chave = call.data.get("palavras_chave", [])
        
        # Atualizar configuração
        if "config" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["config"]["palavras_chave"] = palavras_chave
            _LOGGER.info(f"Palavras-chave atualizadas: {palavras_chave}")
        
        return True

    # Registrar serviço
    hass.services.async_register(
        DOMAIN, 
        "update_keywords", 
        handle_update_keywords, 
        schema=vol.Schema({
            vol.Required("palavras_chave"): vol.All(cv.ensure_list, [cv.string]),
        })
    )

    # Criar notificação inicial
    hass.components.persistent_notification.create(
        "WhatsApp Monitor foi inicializado. Use as opções de configuração para personalizar as palavras-chave.",
        title="WhatsApp Monitor",
        notification_id="whatsapp_monitor_init"
    )

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Configuração do componente a partir de uma entrada de configuração."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = dict(entry.data)

    # Registrar serviço para atualizar palavras-chave
    async def handle_update_keywords(call):
        """Manipulador para o serviço de atualização de palavras-chave."""
        palavras_chave = call.data.get("palavras_chave", [])
        
        # Atualizar configuração
        if "config" in hass.data[DOMAIN]:
            hass.data[DOMAIN]["config"]["palavras_chave"] = palavras_chave
            _LOGGER.info(f"Palavras-chave atualizadas: {palavras_chave}")
        
        return True

    # Registrar serviço
    hass.services.async_register(
        DOMAIN, 
        "update_keywords", 
        handle_update_keywords, 
        schema=vol.Schema({
            vol.Required("palavras_chave"): vol.All(cv.ensure_list, [cv.string]),
        })
    )

    # Configurar sensores
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("sensor", DOMAIN, {}, entry.data)
    )

    # Criar notificação com instruções para WhatsApp Web
    codigo = entry.data.get("codigo_autenticacao", "")
    if codigo:
        hass.components.persistent_notification.create(
            f"Para conectar ao WhatsApp Web:\n\n"
            f"1. Abra o WhatsApp no seu smartphone\n"
            f"2. Toque em Menu (três pontos) > Aparelhos conectados > Conectar um aparelho\n"
            f"3. Digite o código: {codigo}\n\n"
            f"Você pode editar as palavras-chave a qualquer momento nas opções de configuração da integração.",
            title="WhatsApp Monitor - Código de Autenticação",
            notification_id="whatsapp_auth_code"
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Descarregar uma entrada de configuração."""
    # Remover sensores
    await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    # Remover serviços
    hass.services.async_remove(DOMAIN, "update_keywords")
    
    # Limpar dados
    hass.data.pop(DOMAIN)
    
    return True

async def async_options_updated(hass, entry):
    """Manipular opções atualizadas."""
    hass.data[DOMAIN]["config"] = {**entry.data, **entry.options}
