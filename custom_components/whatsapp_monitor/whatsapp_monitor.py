#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Monitor - Verificação e Resumo de Mensagens
Desenvolvido por Manus AI

Este script permite verificar mensagens do WhatsApp, identificar as importantes
e apresentar resumos em intervalos regulares.
"""

import os
import time
import json
import datetime
import schedule
import logging
import nltk
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from AllWhatsPy import AllWhatsPy
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whatsapp_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WhatsAppMonitor")

# Baixar recursos do NLTK necessários
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logger.error(f"Erro ao baixar recursos NLTK: {e}")

class WhatsAppMonitor:
    """
    Classe principal para monitoramento de mensagens do WhatsApp.
    """
    
    def __init__(self, config_file="config.json"):
        """
        Inicializa o monitor de WhatsApp.
        
        Args:
            config_file (str): Caminho para o arquivo de configuração.
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.awp = None
        self.connected = False
        self.last_check_time = None
        self.message_history = {}
        self.important_messages = []
        self.stopwords = set(stopwords.words('portuguese'))
        
        # Criar diretórios necessários
        os.makedirs("resumos", exist_ok=True)
        os.makedirs("graficos", exist_ok=True)
        
        logger.info("WhatsApp Monitor inicializado")
    
    def _load_config(self):
        """
        Carrega a configuração do arquivo JSON.
        
        Returns:
            dict: Configuração carregada.
        """
        default_config = {
            "palavras_chave": ["urgente", "importante", "atenção", "prioridade", "crítico"],
            "contatos_importantes": [],
            "intervalo_verificacao": 15,  # minutos
            "intervalo_resumo": 60,  # minutos
            "max_mensagens_resumo": 10
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Mesclar com configurações padrão
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Criar arquivo de configuração padrão
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                logger.info(f"Arquivo de configuração criado: {self.config_file}")
                return default_config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return default_config
    
    def connect(self):
        """
        Conecta ao WhatsApp usando AllWhatsPy.
        
        Returns:
            bool: True se conectado com sucesso, False caso contrário.
        """
        try:
            logger.info("Conectando ao WhatsApp...")
            self.awp = AllWhatsPy()
            self.awp.conexao()
            self.connected = True
            logger.info("Conectado ao WhatsApp com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao conectar ao WhatsApp: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Desconecta do WhatsApp.
        """
        if self.connected and self.awp:
            try:
                self.awp.desconectar()
                logger.info("Desconectado do WhatsApp")
            except Exception as e:
                logger.error(f"Erro ao desconectar do WhatsApp: {e}")
            finally:
                self.connected = False
    
    def check_messages(self):
        """
        Verifica novas mensagens e identifica as importantes.
        """
        if not self.connected:
            if not self.connect():
                logger.error("Não foi possível verificar mensagens: não conectado")
                return
        
        try:
            logger.info("Verificando mensagens...")
            current_time = datetime.datetime.now()
            
            # Obter contatos com mensagens não lidas
            contatos_nao_lidos = self.awp.contatos_nao_lidos()
            logger.info(f"Contatos com mensagens não lidas: {len(contatos_nao_lidos)}")
            
            for contato in contatos_nao_lidos:
                try:
                    # Acessar conversa
                    self.awp.acessar_conversa(contato)
                    time.sleep(2)  # Aguardar carregamento da conversa
                    
                    # Obter últimas mensagens
                    mensagens = self.awp.ultimas_mensagens_conversa(quantidade=10)
                    
                    # Processar mensagens
                    for msg in mensagens:
                        if isinstance(msg, dict) and 'mensagem' in msg:
                            # Verificar se a mensagem já foi processada
                            msg_id = f"{contato}_{msg.get('hora', '')}_{msg.get('mensagem', '')[:20]}"
                            if msg_id not in self.message_history:
                                self.message_history[msg_id] = msg
                                
                                # Verificar se é importante
                                if self._is_important_message(contato, msg):
                                    msg['contato'] = contato
                                    self.important_messages.append(msg)
                                    logger.info(f"Mensagem importante encontrada de {contato}")
                
                except Exception as e:
                    logger.error(f"Erro ao processar mensagens de {contato}: {e}")
            
            self.last_check_time = current_time
            logger.info(f"Verificação de mensagens concluída. {len(self.important_messages)} mensagens importantes encontradas.")
            
        except Exception as e:
            logger.error(f"Erro ao verificar mensagens: {e}")
    
    def _is_important_message(self, contato, mensagem):
        """
        Verifica se uma mensagem é importante com base em critérios configurados.
        
        Args:
            contato (str): Nome do contato.
            mensagem (dict): Dicionário contendo informações da mensagem.
            
        Returns:
            bool: True se a mensagem for importante, False caso contrário.
        """
        # Verificar se o contato está na lista de contatos importantes
        if contato in self.config["contatos_importantes"]:
            return True
        
        # Verificar se a mensagem contém palavras-chave
        if 'mensagem' in mensagem:
            texto = mensagem['mensagem'].lower()
            for palavra in self.config["palavras_chave"]:
                if palavra.lower() in texto:
                    return True
        
        # Análise de sentimento e urgência (implementação básica)
        if 'mensagem' in mensagem:
            texto = mensagem['mensagem'].lower()
            
            # Verificar padrões de urgência
            urgency_patterns = [
                "preciso", "agora", "urgente", "imediato", "emergência",
                "responda", "ajuda", "socorro", "rápido", "prazo"
            ]
            
            for pattern in urgency_patterns:
                if pattern in texto:
                    return True
        
        return False
    
    def generate_summary(self):
        """
        Gera um resumo das mensagens importantes.
        """
        if not self.important_messages:
            logger.info("Nenhuma mensagem importante para resumir")
            return
        
        try:
            logger.info("Gerando resumo de mensagens importantes...")
            current_time = datetime.datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            
            # Limitar ao número máximo de mensagens para o resumo
            messages_to_summarize = self.important_messages[-self.config["max_mensagens_resumo"]:]
            
            # Criar DataFrame para análise
            df = pd.DataFrame([
                {
                    'contato': msg.get('contato', 'Desconhecido'),
                    'mensagem': msg.get('mensagem', ''),
                    'hora': msg.get('hora', ''),
                    'data': current_time.strftime("%Y-%m-%d")
                }
                for msg in messages_to_summarize
            ])
            
            # Gerar resumo em texto
            resumo_texto = f"Resumo de Mensagens Importantes - {current_time.strftime('%d/%m/%Y %H:%M')}\n"
            resumo_texto += f"Total de mensagens importantes: {len(messages_to_summarize)}\n\n"
            
            # Agrupar por contato
            contatos_count = df['contato'].value_counts()
            resumo_texto += "Mensagens por contato:\n"
            for contato, count in contatos_count.items():
                resumo_texto += f"- {contato}: {count} mensagem(ns)\n"
            
            resumo_texto += "\nMensagens detalhadas:\n"
            for i, row in df.iterrows():
                resumo_texto += f"\n[{row['hora']}] {row['contato']}:\n{row['mensagem']}\n"
                resumo_texto += "-" * 50 + "\n"
            
            # Salvar resumo em arquivo
            resumo_file = f"resumos/resumo_{timestamp}.txt"
            with open(resumo_file, 'w', encoding='utf-8') as f:
                f.write(resumo_texto)
            
            # Gerar gráfico de mensagens por contato
            plt.figure(figsize=(10, 6))
            contatos_count.plot(kind='bar')
            plt.title('Mensagens Importantes por Contato')
            plt.xlabel('Contato')
            plt.ylabel('Número de Mensagens')
            plt.tight_layout()
            chart_file = f"graficos/mensagens_por_contato_{timestamp}.png"
            plt.savefig(chart_file)
            plt.close()
            
            logger.info(f"Resumo gerado e salvo em {resumo_file}")
            logger.info(f"Gráfico gerado e salvo em {chart_file}")
            
            return {
                'resumo_file': resumo_file,
                'chart_file': chart_file,
                'resumo_texto': resumo_texto,
                'timestamp': timestamp
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar resumo: {e}")
            return None
    
    def schedule_tasks(self):
        """
        Agenda as tarefas de verificação e resumo.
        """
        try:
            # Converter minutos para formato de agendamento
            verificacao_min = self.config["intervalo_verificacao"]
            resumo_min = self.config["intervalo_resumo"]
            
            logger.info(f"Agendando verificação a cada {verificacao_min} minutos")
            schedule.every(verificacao_min).minutes.do(self.check_messages)
            
            logger.info(f"Agendando resumo a cada {resumo_min} minutos")
            schedule.every(resumo_min).minutes.do(self.generate_summary)
            
            # Executar verificação inicial
            self.check_messages()
            
            # Loop principal
            while True:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Monitoramento interrompido pelo usuário")
            self.disconnect()
        except Exception as e:
            logger.error(f"Erro no agendamento de tarefas: {e}")
            self.disconnect()
    
    def update_config(self, new_config):
        """
        Atualiza a configuração do monitor.
        
        Args:
            new_config (dict): Nova configuração.
        """
        try:
            self.config.update(new_config)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("Configuração atualizada com sucesso")
            
            # Reconfigurar agendamentos
            schedule.clear()
            self.schedule_tasks()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar configuração: {e}")

def main():
    """
    Função principal para iniciar o monitor.
    """
    try:
        monitor = WhatsAppMonitor()
        monitor.schedule_tasks()
    except Exception as e:
        logger.error(f"Erro ao iniciar o monitor: {e}")

if __name__ == "__main__":
    main()
