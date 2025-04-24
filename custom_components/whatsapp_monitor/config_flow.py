"""
WhatsApp Monitor - Configuração da interface do usuário para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
import voluptuous as vol
import os
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Esquema de configuração para o fluxo de configuração
CONFIG_SCHEMA = vol.Schema({
    vol.Optional(CONF_NAME, default="WhatsApp Monitor"): cv.string,
    vol.Optional("palavras_chave_predefinidas"): cv.multi_select({
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
    vol.Optional("palavras_chave_personalizadas", default=""): cv.string,
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

# Esquema para a autenticação com código
AUTH_CODE_SCHEMA = vol.Schema({
    vol.Required("codigo_autenticacao"): cv.string,
})

class WhatsAppMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Manipula o fluxo de configuração para WhatsApp Monitor."""
    
    VERSION = 1
    CONNECTION_CLASS = "local_poll"
    
    def __init__(self):
        """Inicializa o fluxo de configuração."""
        self._auth_code = None
    
    async def async_step_user(self, user_input=None):
        """Manipula o fluxo de configuração iniciado pelo usuário."""
        errors = {}
        
        if user_input is not None:
            self._auth_code = user_input.get("codigo_autenticacao")
            # Simular verificação bem-sucedida do código
            return await self.async_step_config()
        
        # Mostrar a página de entrada do código de autenticação
        return self.async_show_form(
            step_id="user",
            data_schema=AUTH_CODE_SCHEMA,
            errors=errors,
        )
    
    async def async_step_config(self, user_input=None):
        """Segunda etapa: configuração após autenticação."""
        errors = {}
        
        if user_input is not None:
            # Processar palavras-chave personalizadas
            palavras_chave_predefinidas = user_input.get("palavras_chave_predefinidas", [])
            palavras_chave_personalizadas = user_input.get("palavras_chave_personalizadas", "")
            
            # Converter string de palavras-chave personalizadas em lista
            palavras_personalizadas = []
            if palavras_chave_personalizadas:
                palavras_personalizadas = [p.strip() for p in palavras_chave_personalizadas.split(",") if p.strip()]
            
            # Combinar palavras-chave predefinidas e personalizadas
            todas_palavras_chave = list(palavras_chave_predefinidas) + palavras_personalizadas
            
            # Criar dados de configuração
            config_data = {
                CONF_NAME: user_input.get(CONF_NAME, "WhatsApp Monitor"),
                "palavras_chave": todas_palavras_chave,
                "palavras_chave_predefinidas": list(palavras_chave_predefinidas),
                "palavras_chave_personalizadas": palavras_chave_personalizadas,
                "intervalo_verificacao": user_input.get("intervalo_verificacao", 15),
                "intervalo_resumo": user_input.get("intervalo_resumo", 60),
                "max_mensagens_resumo": user_input.get("max_mensagens_resumo", 10),
                "codigo_autenticacao": self._auth_code,
            }
            
            return self.async_create_entry(
                title=config_data[CONF_NAME],
                data=config_data
            )
        
        return self.async_show_form(
            step_id="config",
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )
    
    @staticmethod
    def async_get_options_flow(config_entry):
        """Obter o fluxo de opções para esta entrada."""
        return WhatsAppMonitorOptionsFlow(config_entry)

class WhatsAppMonitorOptionsFlow(OptionsFlow):
    """Fluxo de opções para WhatsApp Monitor."""

    def __init__(self, config_entry):
        """Inicializa o fluxo de opções."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manipula as opções."""
        if user_input is not None:
            # Processar palavras-chave personalizadas
            palavras_chave_predefinidas = user_input.get("palavras_chave_predefinidas", [])
            palavras_chave_personalizadas = user_input.get("palavras_chave_personalizadas", "")
            
            # Converter string de palavras-chave personalizadas em lista
            palavras_personalizadas = []
            if palavras_chave_personalizadas:
                palavras_personalizadas = [p.strip() for p in palavras_chave_personalizadas.split(",") if p.strip()]
            
            # Combinar palavras-chave predefinidas e personalizadas
            todas_palavras_chave = list(palavras_chave_predefinidas) + palavras_personalizadas
            
            # Atualizar dados de configuração
            return self.async_create_entry(title="", data={
                "palavras_chave": todas_palavras_chave,
                "palavras_chave_predefinidas": list(palavras_chave_predefinidas),
                "palavras_chave_personalizadas": palavras_chave_personalizadas,
                "intervalo_verificacao": user_input.get("intervalo_verificacao", 15),
                "intervalo_resumo": user_input.get("intervalo_resumo", 60),
                "max_mensagens_resumo": user_input.get("max_mensagens_resumo", 10),
            })

        # Obter valores atuais
        palavras_chave_predefinidas = self.config_entry.data.get("palavras_chave_predefinidas", [])
        palavras_chave_personalizadas = self.config_entry.data.get("palavras_chave_personalizadas", "")
        intervalo_verificacao = self.config_entry.data.get("intervalo_verificacao", 15)
        intervalo_resumo = self.config_entry.data.get("intervalo_resumo", 60)
        max_mensagens_resumo = self.config_entry.data.get("max_mensagens_resumo", 10)

        # Criar esquema de opções
        options_schema = vol.Schema({
            vol.Optional("palavras_chave_predefinidas", default=palavras_chave_predefinidas): cv.multi_select({
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
            vol.Optional("palavras_chave_personalizadas", default=palavras_chave_personalizadas): cv.string,
            vol.Optional("intervalo_verificacao", default=intervalo_verificacao): vol.All(
                vol.Coerce(int), vol.Range(min=5, max=60)
            ),
            vol.Optional("intervalo_resumo", default=intervalo_resumo): vol.All(
                vol.Coerce(int), vol.Range(min=15, max=1440)
            ),
            vol.Optional("max_mensagens_resumo", default=max_mensagens_resumo): vol.All(
                vol.Coerce(int), vol.Range(min=5, max=50)
            ),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
