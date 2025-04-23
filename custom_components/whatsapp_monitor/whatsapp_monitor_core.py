"""
WhatsApp Monitor Core - Implementação principal para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import os
import time
import json
import logging
import datetime
import threading
from pathlib import Path

# Importações específicas para WhatsApp Monitor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
_LOGGER = logging.getLogger(__name__)

# Constantes
DOMAIN = "whatsapp_monitor"
CONFIG_FILE = "whatsapp_monitor_config.json"
PROFILE_DIR = "whatsapp_profile"

# Classe principal do WhatsApp Monitor
class WhatsAppMonitor:
    """Classe principal para monitoramento de mensagens do WhatsApp."""
    
    def __init__(self, config_dir, config):
        """Inicializa o monitor de WhatsApp."""
        self.config_dir = config_dir
        self.config = config
        self.driver = None
        self.connected = False
        self.last_check_time = None
        self.message_history = {}
        self.important_messages = []
        
        # Diretórios
        self.profile_dir = os.path.join(config_dir, PROFILE_DIR)
        self.resumos_dir = os.path.join(config_dir, "resumos")
        self.graficos_dir = os.path.join(config_dir, "graficos")
        
        # Criar diretórios necessários
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.resumos_dir, exist_ok=True)
        os.makedirs(self.graficos_dir, exist_ok=True)
        
        _LOGGER.info("WhatsApp Monitor inicializado")
    
    def connect(self):
        """Conecta ao WhatsApp Web usando Selenium."""
        try:
            _LOGGER.info("Conectando ao WhatsApp Web...")
            
            # Configurar opções do Chrome otimizadas para Raspberry Pi
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
            
            # Inicializar o driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Abrir WhatsApp Web
            self.driver.get("https://web.whatsapp.com/")
            
            # Verificar se já está logado ou precisa escanear QR code
            try:
                # Aguardar até que a página seja carregada (verificar elemento que só aparece após login)
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
                )
                _LOGGER.info("Já logado no WhatsApp Web")
                self.connected = True
            except TimeoutException:
                # Provavelmente precisa escanear o QR code
                _LOGGER.warning("QR Code detectado. Por favor, escaneie o QR code com seu WhatsApp")
                
                # Verificar se o QR code está visível
                try:
                    qr_code = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@data-testid="qrcode"]'))
                    )
                    _LOGGER.info("QR Code está visível. Aguardando escaneamento...")
                    
                    # Aguardar até que a página seja carregada após o escaneamento
                    WebDriverWait(self.driver, 60).until(
                        EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
                    )
                    _LOGGER.info("Login bem-sucedido após escaneamento do QR code")
                    self.connected = True
                except TimeoutException:
                    _LOGGER.error("Tempo esgotado aguardando o escaneamento do QR code")
                    self.disconnect()
                    return False
            
            return self.connected
        
        except Exception as e:
            _LOGGER.error(f"Erro ao conectar ao WhatsApp Web: {e}")
            self.disconnect()
            return False
    
    def disconnect(self):
        """Desconecta do WhatsApp Web."""
        if self.driver:
            try:
                self.driver.quit()
                _LOGGER.info("Desconectado do WhatsApp Web")
            except Exception as e:
                _LOGGER.error(f"Erro ao desconectar do WhatsApp Web: {e}")
            finally:
                self.driver = None
                self.connected = False
    
    def check_messages(self):
        """Verifica novas mensagens e identifica as importantes."""
        if not self.connected:
            if not self.connect():
                _LOGGER.error("Não foi possível verificar mensagens: não conectado")
                return []
        
        try:
            _LOGGER.info("Verificando mensagens...")
            current_time = datetime.datetime.now()
            new_important_messages = []
            
            # Obter contatos com mensagens não lidas
            try:
                # Aguardar carregamento da lista de chats
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
                )
                
                # Encontrar chats com notificações não lidas
                unread_chats = self.driver.find_elements(By.XPATH, '//span[@data-testid="icon-unread-count"]/..')
                _LOGGER.info(f"Contatos com mensagens não lidas: {len(unread_chats)}")
                
                for chat in unread_chats:
                    try:
                        # Clicar no chat para abrir a conversa
                        chat.click()
                        time.sleep(2)  # Aguardar carregamento da conversa
                        
                        # Obter nome do contato
                        contact_name_elem = self.driver.find_element(By.XPATH, '//div[@data-testid="conversation-header"]//span[@title]')
                        contact_name = contact_name_elem.get_attribute('title')
                        
                        # Obter mensagens recentes
                        message_elements = self.driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]')
                        
                        for msg_elem in message_elements[-10:]:  # Últimas 10 mensagens
                            try:
                                # Obter texto da mensagem
                                msg_text_elem = msg_elem.find_element(By.XPATH, './/span[@class="selectable-text copyable-text"]')
                                msg_text = msg_text_elem.text
                                
                                # Obter hora da mensagem
                                msg_time_elem = msg_elem.find_element(By.XPATH, './/div[@data-testid="msg-meta"]//span')
                                msg_time = msg_time_elem.text
                                
                                # Criar identificador único para a mensagem
                                msg_id = f"{contact_name}_{msg_time}_{msg_text[:20]}"
                                
                                # Verificar se a mensagem já foi processada
                                if msg_id not in self.message_history:
                                    self.message_history[msg_id] = True
                                    
                                    # Criar objeto de mensagem
                                    message = {
                                        'contato': contact_name,
                                        'mensagem': msg_text,
                                        'hora': msg_time
                                    }
                                    
                                    # Verificar se é importante
                                    if self._is_important_message(contact_name, msg_text):
                                        self.important_messages.append(message)
                                        new_important_messages.append(message)
                                        _LOGGER.info(f"Mensagem importante encontrada de {contact_name}")
                            
                            except Exception as e:
                                _LOGGER.error(f"Erro ao processar mensagem: {e}")
                    
                    except Exception as e:
                        _LOGGER.error(f"Erro ao processar chat: {e}")
            
            except Exception as e:
                _LOGGER.error(f"Erro ao obter chats não lidos: {e}")
            
            self.last_check_time = current_time
            _LOGGER.info(f"Verificação de mensagens concluída. {len(new_important_messages)} novas mensagens importantes encontradas.")
            
            return new_important_messages
            
        except Exception as e:
            _LOGGER.error(f"Erro ao verificar mensagens: {e}")
            return []
    
    def _is_important_message(self, contact, message_text):
        """Verifica se uma mensagem é importante com base em critérios configurados."""
        # Verificar se o contato está na lista de contatos importantes
        if contact in self.config.get("contatos_importantes", []):
            return True
        
        # Verificar se a mensagem contém palavras-chave
        for palavra in self.config.get("palavras_chave", []):
            if palavra.lower() in message_text.lower():
                return True
        
        # Análise de padrões de urgência (implementação básica)
        urgency_patterns = [
            "preciso", "agora", "urgente", "imediato", "emergência",
            "responda", "ajuda", "socorro", "rápido", "prazo"
        ]
        
        for pattern in urgency_patterns:
            if pattern in message_text.lower():
                return True
        
        return False
    
    def generate_summary(self):
        """Gera um resumo das mensagens importantes."""
        if not self.important_messages:
            _LOGGER.info("Nenhuma mensagem importante para resumir")
            return None
        
        try:
            _LOGGER.info("Gerando resumo de mensagens importantes...")
            current_time = datetime.datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            # Limitar ao número máximo de mensagens para o resumo
            max_messages = self.config.get("max_mensagens_resumo", 10)
            messages_to_summarize = self.important_messages[-max_messages:]
            
            # Gerar resumo em texto
            resumo_texto = f"Resumo de Mensagens Importantes - {current_time.strftime('%d/%m/%Y %H:%M')}\n"
            resumo_texto += f"Total de mensagens importantes: {len(messages_to_summarize)}\n\n"
            
            # Agrupar por contato
            contatos = {}
            for msg in messages_to_summarize:
                contato = msg.get('contato', 'Desconhecido')
                if contato not in contatos:
                    contatos[contato] = 0
                contatos[contato] += 1
            
            resumo_texto += "Mensagens por contato:\n"
            for contato, count in contatos.items():
                resumo_texto += f"- {contato}: {count} mensagem(ns)\n"
            
            resumo_texto += "\nMensagens detalhadas:\n"
            for msg in messages_to_summarize:
                resumo_texto += f"\n[{msg.get('hora', '')}] {msg.get('contato', 'Desconhecido')}:\n{msg.get('mensagem', '')}\n"
                resumo_texto += "-" * 50 + "\n"
            
            # Salvar resumo em arquivo
            resumo_file = os.path.join(self.resumos_dir, f"resumo_{timestamp}.txt")
            with open(resumo_file, 'w', encoding='utf-8') as f:
                f.write(resumo_texto)
            
            _LOGGER.info(f"Resumo gerado e salvo em {resumo_file}")
            
            return {
                'resumo_file': resumo_file,
                'resumo_texto': resumo_texto,
                'timestamp': timestamp
            }
            
        except Exception as e:
            _LOGGER.error(f"Erro ao gerar resumo: {e}")
            return None

# Funções de serviço para Home Assistant

def init_monitor(hass):
    """Inicializa o WhatsApp Monitor."""
    try:
        config = hass.data[DOMAIN]["config"]
        config_dir = hass.config.path("custom_components", DOMAIN)
        
        # Criar instância do monitor
        monitor = WhatsAppMonitor(config_dir, config)
        hass.data[DOMAIN]["monitor"] = monitor
        
        _LOGGER.info("WhatsApp Monitor inicializado com sucesso")
        return True
    except Exception as e:
        _LOGGER.error(f"Erro ao inicializar WhatsApp Monitor: {e}")
        return False

def connect_service(hass):
    """Serviço para conectar ao WhatsApp Web."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("WhatsApp Monitor não inicializado")
        return False
    
    return monitor.connect()

def disconnect_service(hass):
    """Serviço para desconectar do WhatsApp Web."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("WhatsApp Monitor não inicializado")
        return False
    
    monitor.disconnect()
    return True

def check_messages_service(hass):
    """Serviço para verificar mensagens."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("WhatsApp Monitor não inicializado")
        return False
    
    new_messages = monitor.check_messages()
    
    # Atualizar estado das entidades
    if new_messages:
        hass.data[DOMAIN]["mensagens_importantes"] = monitor.important_messages
        
        # Disparar evento para notificar sobre novas mensagens importantes
        hass.bus.fire(f"{DOMAIN}_new_important_messages", {
            "count": len(new_messages),
            "messages": new_messages
        })
    
    return True

def generate_summary_service(hass):
    """Serviço para gerar resumo."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("WhatsApp Monitor não inicializado")
        return False
    
    summary = monitor.generate_summary()
    
    if summary:
        # Disparar evento para notificar sobre novo resumo
        hass.bus.fire(f"{DOMAIN}_new_summary", {
            "summary_file": summary.get("resumo_file"),
            "timestamp": summary.get("timestamp")
        })
        
        # Enviar notificação
        hass.services.call("persistent_notification", "create", {
            "title": "Novo Resumo de Mensagens do WhatsApp",
            "message": f"Um novo resumo de mensagens importantes do WhatsApp foi gerado.\n\nArquivo: {summary.get('resumo_file')}"
        })
    
    return True
