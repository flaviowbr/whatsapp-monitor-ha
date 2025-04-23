"""
WhatsApp Monitor - Sensor para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity import Entity

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Configurar a plataforma de sensor WhatsApp Monitor."""
    if discovery_info is None:
        return
    
    # Criar sensores
    sensors = [
        WhatsAppMonitorStatusSensor(hass),
        WhatsAppMonitorMessageCountSensor(hass),
        WhatsAppMonitorLastCheckSensor(hass),
        WhatsAppMonitorLastSummarySensor(hass)
    ]
    
    async_add_entities(sensors, True)

class WhatsAppMonitorSensor(SensorEntity):
    """Classe base para sensores do WhatsApp Monitor."""
    
    def __init__(self, hass):
        """Inicializar o sensor base."""
        self.hass = hass
        self._attr_should_poll = True
        self._attr_has_entity_name = True
        self._attr_available = False
    
    @property
    def device_info(self):
        """Retorna informações do dispositivo."""
        return {
            "identifiers": {(DOMAIN, "whatsapp_monitor")},
            "name": "WhatsApp Monitor",
            "manufacturer": "Manus AI",
            "model": "WhatsApp Monitor para Home Assistant",
            "sw_version": "1.0.0",
        }

class WhatsAppMonitorStatusSensor(WhatsAppMonitorSensor):
    """Sensor para o status do WhatsApp Monitor."""
    
    def __init__(self, hass):
        """Inicializar o sensor de status."""
        super().__init__(hass)
        self._attr_name = "Status"
        self._attr_unique_id = f"{DOMAIN}_status"
        self._attr_icon = "mdi:whatsapp"
        self._state = "desconectado"
    
    @property
    def state(self):
        """Retorna o estado do sensor."""
        return self._state
    
    async def async_update(self):
        """Atualiza o estado do sensor."""
        monitor = self.hass.data[DOMAIN].get("monitor")
        if monitor:
            self._attr_available = True
            self._state = "conectado" if monitor.connected else "desconectado"
        else:
            self._attr_available = False
            self._state = "não inicializado"

class WhatsAppMonitorMessageCountSensor(WhatsAppMonitorSensor):
    """Sensor para a contagem de mensagens importantes."""
    
    def __init__(self, hass):
        """Inicializar o sensor de contagem de mensagens."""
        super().__init__(hass)
        self._attr_name = "Mensagens Importantes"
        self._attr_unique_id = f"{DOMAIN}_message_count"
        self._attr_icon = "mdi:message-alert"
        self._state = 0
        self._attr_unit_of_measurement = "mensagens"
    
    @property
    def state(self):
        """Retorna o estado do sensor."""
        return self._state
    
    @property
    def extra_state_attributes(self):
        """Retorna atributos adicionais do sensor."""
        monitor = self.hass.data[DOMAIN].get("monitor")
        if not monitor:
            return {}
        
        # Obter contatos com mensagens importantes
        contatos = {}
        for msg in monitor.important_messages:
            contato = msg.get('contato', 'Desconhecido')
            if contato not in contatos:
                contatos[contato] = 0
            contatos[contato] += 1
        
        return {
            "contatos": contatos,
            "ultima_mensagem": monitor.important_messages[-1] if monitor.important_messages else None
        }
    
    async def async_update(self):
        """Atualiza o estado do sensor."""
        monitor = self.hass.data[DOMAIN].get("monitor")
        if monitor:
            self._attr_available = True
            self._state = len(monitor.important_messages)
        else:
            self._attr_available = False
            self._state = 0

class WhatsAppMonitorLastCheckSensor(WhatsAppMonitorSensor):
    """Sensor para a última verificação de mensagens."""
    
    def __init__(self, hass):
        """Inicializar o sensor de última verificação."""
        super().__init__(hass)
        self._attr_name = "Última Verificação"
        self._attr_unique_id = f"{DOMAIN}_last_check"
        self._attr_icon = "mdi:clock-check"
        self._state = None
    
    @property
    def state(self):
        """Retorna o estado do sensor."""
        return self._state
    
    async def async_update(self):
        """Atualiza o estado do sensor."""
        monitor = self.hass.data[DOMAIN].get("monitor")
        if monitor and monitor.last_check_time:
            self._attr_available = True
            self._state = monitor.last_check_time.isoformat()
        else:
            self._attr_available = False
            self._state = None

class WhatsAppMonitorLastSummarySensor(WhatsAppMonitorSensor):
    """Sensor para o último resumo gerado."""
    
    def __init__(self, hass):
        """Inicializar o sensor de último resumo."""
        super().__init__(hass)
        self._attr_name = "Último Resumo"
        self._attr_unique_id = f"{DOMAIN}_last_summary"
        self._attr_icon = "mdi:file-document"
        self._state = None
        self._attr_extra_state_attributes = {}
    
    @property
    def state(self):
        """Retorna o estado do sensor."""
        return self._state
    
    async def async_update(self):
        """Atualiza o estado do sensor."""
        # Verificar se há eventos de resumo
        last_summary_event = None
        for event in self.hass.bus.async_listeners().get(f"{DOMAIN}_new_summary", []):
            if hasattr(event, "data") and "timestamp" in event.data:
                if not last_summary_event or event.data["timestamp"] > last_summary_event.data["timestamp"]:
                    last_summary_event = event
        
        if last_summary_event:
            self._attr_available = True
            self._state = last_summary_event.data.get("timestamp")
            self._attr_extra_state_attributes = {
                "arquivo": last_summary_event.data.get("summary_file")
            }
        else:
            self._attr_available = False
            self._state = None
            self._attr_extra_state_attributes = {}
