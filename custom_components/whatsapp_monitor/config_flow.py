"""
WhatsApp Monitor - Configuração da interface do usuário para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
import voluptuous as vol
import os
import aiohttp
import async_timeout
from homeassistant import config_entries
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_NAME
import homeassistant.helpers.config_validation as cv

from . import DOMAIN

_LOGGER = logging.getLogger(__name__) 

# Esquema de configuração para o fluxo de configuração - Etapa 2
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

# Esquema para a primeira etapa - QR Code
QR_CODE_SCHEMA = vol.Schema({
    vol.Optional("qr_code_scanned", default=False): cv.boolean,
})

class WhatsAppLoginView(HomeAssistantView):
    """View para exibir a página de login do WhatsApp."""
    
    requires_auth = False
    url = "/whatsapp_login"
    name = "whatsapp_login"
    
    async def get(self, request):
        """Handle GET request."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhatsApp Web Login</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 10px;
                }
                .qr-container {
                    width: 100%;
                    height: 500px;
                    overflow: hidden;
                    position: relative;
                }
                .qr-container iframe {
                    width: 100%;
                    height: 100%;
                    border: none;
                    transform: scale(1.2);
                    transform-origin: 0 0;
                    position: absolute;
                    top: 0;
                    left: 0;
                }
                .button {
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    text-decoration: none;
                    display: inline-block;
                    font-size: 16px;
                    margin: 20px 2px;
                    cursor: pointer;
                    border-radius: 4px;
                }
                .note {
                    margin-top: 20px;
                    padding: 10px;
                    background-color: #f8f8f8;
                    border-left: 4px solid #4CAF50;
                    text-align: left;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>WhatsApp Web Login</h1>
                <p>Escaneie o QR code abaixo com seu smartphone para fazer login no WhatsApp Web:</p>
                <div class="qr-container">
                    <iframe src="https://web.whatsapp.com/" sandbox="allow-same-origin allow-scripts allow-forms"></iframe>
                </div>
                <div class="note">
                    <p><strong>Nota:</strong> Se o QR code não aparecer, tente:</p>
                    <ol>
                        <li>Abrir diretamente <a href="https://web.whatsapp.com/" target="_blank">web.whatsapp.com</a> em uma nova aba</li>
                        <li>Escanear o QR code nessa nova aba</li>
                        <li>Voltar para esta página e clicar em "Continuar Configuração"</li>
                    </ol>
                </div>
                <a href="/config/integrations/config_flow_start?domain=whatsapp_monitor&qr_code_scanned=true" class="button">Continuar Configuração</a>
            </div>
        </body>
        </html>
        """
        return aiohttp.web.Response(text=html_content, content_type="text/html") 

class WhatsAppMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Manipula o fluxo de configuração para WhatsApp Monitor."""
    
    VERSION = 1
    CONNECTION_CLASS = "local_poll"
    
    def __init__(self):
        """Inicializa o fluxo de configuração."""
        self._qr_code_scanned = False
    
    async def async_step_user(self, user_input=None):
        """Manipula o fluxo de configuração iniciado pelo usuário."""
        # Registrar a view para o QR code
        if not hasattr(self.hass.http, "_registered_views")  or not any(view.url == "/whatsapp_login" for view in self.hass.http._registered_views) :
            self.hass.http.register_view(WhatsAppLoginView() )
        
        # Verificar se o QR code já foi escaneado
        if user_input is not None and user_input.get("qr_code_scanned", False):
            self._qr_code_scanned = True
            return await self.async_step_config()
        
        # Mostrar a página de QR code
        return self.async_show_form(
            step_id="user",
            data_schema=QR_CODE_SCHEMA,
            description_placeholders={
                "qr_code_url": f"{self.hass.config.internal_url}/whatsapp_login"
            },
            errors={},
        )
    
    async def async_step_config(self, user_input=None):
        """Segunda etapa: configuração após escanear o QR code."""
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
                "intervalo_verificacao": user_input.get("intervalo_verificacao", 15),
                "intervalo_resumo": user_input.get("intervalo_resumo", 60),
                "max_mensagens_resumo": user_input.get("max_mensagens_resumo", 10),
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
