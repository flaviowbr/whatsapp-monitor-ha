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
        WhatsAppMonitorStatusSensor(hass)
    ]
    
    async_add_entities(sensors, True)

class WhatsAppMonitorSensor(SensorEntity):
    """Classe base para sensores do WhatsApp Monitor."""
    
    def __init__(self, hass):
        """Inicializar o sensor base."""
        self.hass = hass
        self._attr_should_poll = True
        self._attr_has_entity_name = True
        self._attr_available = True
    
    @property
    def device_info(self):
        """Retorna informações do dispositivo."""
        return {
            "identifiers": {(DOMAIN, "whatsapp_monitor")},
            "name": "WhatsApp Monitor",
            "manufacturer": "Manus AI",
            "model": "WhatsApp Monitor para Home Assistant",
            "sw_version": "1.0.4",
        }

class WhatsAppMonitorStatusSensor(WhatsAppMonitorSensor):
    """Sensor para o status do WhatsApp Monitor."""
    
    def __init__(self, hass):
        """Inicializar o sensor de status."""
        super().__init__(hass)
        self._attr_name = "Status"
        self._attr_unique_id = f"{DOMAIN}_status"
        self._attr_icon = "mdi:whatsapp"
        self._state = "configurado"
    
    @property
    def state(self):
        """Retorna o estado do sensor."""
        return self._state
    
    async def async_update(self):
        """Atualiza o estado do sensor."""
        self._attr_available = True
        self._state = "configurado"
