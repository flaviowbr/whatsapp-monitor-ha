"""
WhatsApp Monitor - Módulo principal para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import os
import time
import logging
import datetime
import base64
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image

_LOGGER = logging.getLogger(__name__)

# Constantes
DOMAIN = "whatsapp_monitor"
PROFILE_DIR = "whatsapp_profile"
RESUMOS_DIR = "resumos"
GRAFICOS_DIR = "graficos"

class WhatsAppMonitor:
    """Classe principal para monitoramento do WhatsApp."""
    
    def __init__(self, config_dir, config):
        """Inicializa o monitor do WhatsApp."""
        self.config_dir = config_dir
        self.config = config
        self.driver = None
        self.connected = False
        self.last_check_time = None
        self.important_messages = []
        self.hass = None
        
        # Criar diretórios necessários
        self.profile_dir = os.path.join(config_dir, PROFILE_DIR)
        self.resumos_dir = os.path.join(config_dir, RESUMOS_DIR)
        self.graficos_dir = os.path.join(config_dir, GRAFICOS_DIR)
        
        os.makedirs(self.profile_dir, exist_ok=True)
        os.makedirs(self.resumos_dir, exist_ok=True)
        os.makedirs(self.graficos_dir, exist_ok=True)
        
        # Inicializar driver
        self._init_driver()
    
    def _init_driver(self):
        """Inicializa o driver do Selenium."""
        try:
            # Configurar opções do Chrome
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1280,720")
            chrome_options.add_argument(f"--user-data-dir={self.profile_dir}")
            chrome_options.add_argument("--disable-features=TranslateUI")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins-discovery")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            # Inicializar driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            _LOGGER.info("Driver do Selenium inicializado com sucesso")
            return True
        except Exception as e:
            _LOGGER.error(f"Erro ao inicializar driver do Selenium: {e}")
            return False
    
    def capture_qr_code(self):
        """Captura o QR Code e salva como imagem."""
        try:
            # Esperar pelo QR Code aparecer
            qr_code_element = self.driver.find_element(By.XPATH, '//canvas[contains(@aria-label, "Scan me!") or contains(@aria-label, "Escanear")]')
            
            # Capturar o QR Code como imagem
            canvas_base64 = self.driver.execute_script("return arguments[0].toDataURL('image/png').substring(22);", qr_code_element)
            canvas_png = base64.b64decode(canvas_base64)
            
            # Criar diretório www se não existir
            www_dir = "/config/www"
            if not os.path.exists(www_dir):
                os.makedirs(www_dir)
            
            # Salvar a imagem
            qr_code_path = "/config/www/whatsapp_qrcode.png"
            with open(qr_code_path, "wb") as f:
                f.write(canvas_png)
            
            # Criar arquivo HTML para exibir o QR Code
            html_path = "/config/www/whatsapp_qrcode.html"
            with open(html_path, "w") as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <title>WhatsApp QR Code</title>
    <meta http-equiv="refresh" content="10">
    <style>
        body {
            font-family: sans-serif;
            text-align: center;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) ;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
        }
        h1 {
            color: #128C7E;
        }
        .instructions {
            margin: 20px 0;
            text-align: left;
            padding: 15px;
            background-color: #f8f8f8;
            border-left: 4px solid #128C7E;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>WhatsApp QR Code</h1>
        <div class="qrcode">
            <img src="/local/whatsapp_qrcode.png" alt="WhatsApp QR Code">
        </div>
        <div class="instructions">
            <h3>Instruções:</h3>
            <ol>
                <li>Abra o WhatsApp no seu smartphone</li>
                <li>Toque em Menu (três pontos) > WhatsApp Web</li>
                <li>Escaneie o QR Code acima</li>
                <li>Esta página será atualizada automaticamente a cada 10 segundos</li>
            </ol>
        </div>
        <p>Após escanear o QR Code com sucesso, você pode fechar esta página.</p>
    </div>
</body>
</html>""")
            
            # Registrar evento no Home Assistant
            if hasattr(self, 'hass') and self.hass:
                self.hass.bus.fire(f"{DOMAIN}_qrcode_generated", {
                    "qrcode_url": "/local/whatsapp_qrcode.png",
                    "html_page": "/local/whatsapp_qrcode.html",
                    "timestamp": time.time()
                })
                
                # Criar notificação persistente
                self.hass.services.call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "WhatsApp QR Code",
                        "message": f"Escaneie o QR Code para conectar ao WhatsApp Web. [Abrir QR Code](/local/whatsapp_qrcode.html)",
                        "notification_id": "whatsapp_qrcode"
                    }
                )
            
            _LOGGER.info(f"QR Code salvo em {qr_code_path}")
            return True
        except Exception as e:
            _LOGGER.error(f"Erro ao capturar QR Code: {e}")
            return False
    
    def connect(self):
        """Conecta ao WhatsApp Web."""
        try:
            if self.connected:
                return True
            
            _LOGGER.info("Conectando ao WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com/") 
            
            # Aguardar o QR Code carregar
            _LOGGER.info("Aguardando QR Code...")
            time.sleep(5)
            
            # Capturar e salvar o QR Code
            self.capture_qr_code()
            
            # Adicionar um loop para atualizar o QR Code periodicamente
            qr_update_count = 0
            while not self.connected and qr_update_count < 12:  # Tentar por 2 minutos (12 x 10s)
                time.sleep(10)
                if self.capture_qr_code():
                    qr_update_count += 1
                else:
                    break
                
                # Verificar se já está conectado
                try:
                    # Procurar por elemento que indica que está conectado
                    self.driver.find_element(By.XPATH, '//div[@data-testid="chat-list"]')
                    self.connected = True
                    _LOGGER.info("Conectado ao WhatsApp Web com sucesso!")
                    return True
                except:
                    pass
            
            # Aguardar a autenticação
            try:
                WebDriverWait(self.driver, 300).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list"]'))
                )
                self.connected = True
                _LOGGER.info("Conectado ao WhatsApp Web com sucesso!")
                return True
            except Exception as e:
                _LOGGER.error(f"Erro ao conectar ao WhatsApp Web: {e}")
                return False
        except Exception as e:
            _LOGGER.error(f"Erro ao conectar ao WhatsApp Web: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do WhatsApp Web."""
        try:
            if self.driver:
                self.driver.quit()
            self.driver = None
            self.connected = False
            _LOGGER.info("Desconectado do WhatsApp Web")
            return True
        except Exception as e:
            _LOGGER.error(f"Erro ao desconectar do WhatsApp Web: {e}")
            return False
    
    def check_messages(self):
        """Verifica novas mensagens no WhatsApp."""
        try:
            if not self.connected:
                if not self.connect():
                    return []
            
            _LOGGER.info("Verificando mensagens do WhatsApp...")
            
            # Atualizar timestamp da última verificação
            self.last_check_time = datetime.datetime.now()
            
            # Obter conversas
            chats = self.driver.find_elements(By.XPATH, '//div[@data-testid="chat-list"]//div[@role="row"]')
            
            # Verificar novas mensagens
            new_important_messages = []
            for chat in chats:
                try:
                    # Verificar se há mensagens não lidas
                    unread_badge = chat.find_elements(By.XPATH, './/span[@data-testid="icon-unread"]')
                    if not unread_badge:
                        continue
                    
                    # Obter informações do contato
                    contato = chat.find_element(By.XPATH, './/span[@data-testid="default-user"]').text
                    
                    # Clicar no chat para ver as mensagens
                    chat.click()
                    time.sleep(1)
                    
                    # Obter mensagens
                    messages = self.driver.find_elements(By.XPATH, '//div[@data-testid="msg-container"]')
                    
                    # Processar mensagens
                    for msg in messages[-5:]:  # Verificar apenas as 5 últimas mensagens
                        try:
                            # Obter texto da mensagem
                            texto = msg.find_element(By.XPATH, './/span[@data-testid="msg-text"]').text
                            
                            # Obter hora da mensagem
                            hora = msg.find_element(By.XPATH, './/div[@data-testid="msg-meta"]').text
                            
                            # Verificar se é uma mensagem importante
                            if self._is_important_message(contato, texto):
                                mensagem = {
                                    'contato': contato,
                                    'mensagem': texto,
                                    'hora': hora,
                                    'importante': True
                                }
                                new_important_messages.append(mensagem)
                                self.important_messages.append(mensagem)
                        except:
                            continue
                except Exception as e:
                    _LOGGER.error(f"Erro ao processar chat: {e}")
                    continue
            
            # Voltar para a lista de chats
            self.driver.find_element(By.XPATH, '//button[@data-testid="back"]').click()
            
            _LOGGER.info(f"Verificação concluída. {len(new_important_messages)} novas mensagens importantes encontradas.")
            return new_important_messages
        except Exception as e:
            _LOGGER.error(f"Erro ao verificar mensagens: {e}")
            return []
    
    def _is_important_message(self, contato, mensagem):
        """Verifica se uma mensagem é importante."""
        # Verificar por contato
        contatos_importantes = self.config.get('contatos_importantes', [])
        if contato in contatos_importantes:
            return True
        
        # Verificar por palavras-chave
        palavras_chave = self.config.get('palavras_chave', [
            'urgente', 'importante', 'atenção', 'prioridade', 'crítico',
            'emergência', 'ajuda', 'socorro', 'imediato', 'prazo'
        ])
        
        mensagem_lower = mensagem.lower()
        for palavra in palavras_chave:
            if palavra.lower() in mensagem_lower:
                return True
        
        # Verificar por padrões de urgência
        padroes_urgencia = [
            'preciso agora', 'preciso hoje', 'preciso urgente',
            'me ajuda', 'socorro', 'emergência', 'urgente',
            'não pode esperar', 'imediatamente'
        ]
        
        for padrao in padroes_urgencia:
            if padrao in mensagem_lower:
                return True
        
        return False
    
    def generate_summary(self):
        """Gera um resumo das mensagens importantes."""
        try:
            if not self.important_messages:
                _LOGGER.info("Nenhuma mensagem importante para resumir.")
                return None
            
            _LOGGER.info("Gerando resumo de mensagens importantes...")
            
            # Criar nome do arquivo de resumo
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            resumo_file = os.path.join(self.resumos_dir, f"resumo_{timestamp}.txt")
            
            # Limitar número de mensagens no resumo
            max_mensagens = self.config.get('max_mensagens_resumo', 10)
            mensagens_resumo = self.important_messages[-max_mensagens:] if len(self.important_messages) > max_mensagens else self.important_messages
            
            # Gerar conteúdo do resumo
            conteudo = "=== RESUMO DE MENSAGENS IMPORTANTES DO WHATSAPP ===\n\n"
            conteudo += f"Data e hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
            conteudo += f"Total de mensagens importantes: {len(self.important_messages)}\n\n"
            
            # Agrupar mensagens por contato
            mensagens_por_contato = {}
            for msg in mensagens_resumo:
                contato = msg.get('contato', 'Desconhecido')
                if contato not in mensagens_por_contato:
                    mensagens_por_contato[contato] = []
                mensagens_por_contato[contato].append(msg)
            
            # Adicionar mensagens ao resumo
            for contato, mensagens in mensagens_por_contato.items():
                conteudo += f"=== Mensagens de {contato} ===\n"
                for msg in mensagens:
                    conteudo += f"[{msg.get('hora', '')}] {msg.get('mensagem', '')}\n"
                conteudo += "\n"
            
            # Salvar resumo
            with open(resumo_file, "w") as f:
                f.write(conteudo)
            
            _LOGGER.info(f"Resumo gerado com sucesso: {resumo_file}")
            
            return {
                'resumo_file': resumo_file,
                'num_mensagens': len(mensagens_resumo),
                'timestamp': timestamp
            }
        except Exception as e:
            _LOGGER.error(f"Erro ao gerar resumo: {e}")
            return None

# Funções de serviço para Home Assistant

def init_monitor(hass):
    """Inicializa o monitor do WhatsApp."""
    try:
        config_dir = hass.config.path("custom_components", DOMAIN)
        
        # Obter configuração
        config = hass.data[DOMAIN].get("config", {})
        
        # Criar instância do monitor
        monitor = WhatsAppMonitor(config_dir, config)
        monitor.hass = hass
        hass.data[DOMAIN]["monitor"] = monitor
        
        _LOGGER.info("Monitor do WhatsApp inicializado com sucesso")
        return True
    except Exception as e:
        _LOGGER.error(f"Erro ao inicializar monitor do WhatsApp: {e}")
        return False

def check_messages_service(hass):
    """Serviço para verificar mensagens do WhatsApp."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("Monitor do WhatsApp não inicializado")
        return False
    
    new_messages = monitor.check_messages()
    
    if new_messages:
        # Disparar evento para notificar sobre novas mensagens importantes
        hass.bus.fire(f"{DOMAIN}_new_important_messages", {
            "messages": new_messages,
            "count": len(new_messages),
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    return True

def generate_summary_service(hass):
    """Serviço para gerar resumo de mensagens do WhatsApp."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("Monitor do WhatsApp não inicializado")
        return False
    
    summary = monitor.generate_summary()
    
    if summary:
        # Disparar evento para notificar sobre novo resumo
        hass.bus.fire(f"{DOMAIN}_new_summary", {
            "summary_file": summary['resumo_file'],
            "num_messages": summary['num_mensagens'],
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    return True

def connect_service(hass):
    """Serviço para conectar ao WhatsApp Web."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("Monitor do WhatsApp não inicializado")
        return False
    
    return monitor.connect()

def disconnect_service(hass):
    """Serviço para desconectar do WhatsApp Web."""
    monitor = hass.data[DOMAIN].get("monitor")
    if not monitor:
        _LOGGER.error("Monitor do WhatsApp não inicializado")
        return False
    
    return monitor.disconnect()
