"""
WhatsApp Monitor - Persistência de dados para Home Assistant
Desenvolvido para Raspberry Pi 4 com Home Assistant
"""

import os
import json
import logging
import sqlite3
import datetime
from pathlib import Path

_LOGGER = logging.getLogger(__name__)

# Constantes
DOMAIN = "whatsapp_monitor"
DATABASE_FILE = "whatsapp_monitor.db"
BACKUP_DIR = "backups"

class WhatsAppMonitorStorage:
    """Classe para gerenciar a persistência de dados do WhatsApp Monitor."""
    
    def __init__(self, config_dir):
        """Inicializa o armazenamento de dados."""
        self.config_dir = config_dir
        self.db_path = os.path.join(config_dir, DATABASE_FILE)
        self.backup_dir = os.path.join(config_dir, BACKUP_DIR)
        
        # Criar diretório de backup se não existir
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Inicializar banco de dados
        self._init_database()
        
        _LOGGER.info(f"Armazenamento de dados inicializado em {self.db_path}")
    
    def _init_database(self):
        """Inicializa o banco de dados SQLite."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Criar tabela de mensagens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mensagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contato TEXT NOT NULL,
                    mensagem TEXT NOT NULL,
                    hora TEXT NOT NULL,
                    data TEXT NOT NULL,
                    nivel_prioridade TEXT,
                    categoria TEXT,
                    importante INTEGER NOT NULL,
                    timestamp INTEGER NOT NULL
                )
            ''')
            
            # Criar tabela de resumos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resumos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    arquivo TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    num_mensagens INTEGER NOT NULL
                )
            ''')
            
            # Criar tabela de configuração
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS configuracao (
                    chave TEXT PRIMARY KEY,
                    valor TEXT NOT NULL
                )
            ''')
            
            # Criar índices para melhorar performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mensagens_contato ON mensagens(contato)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mensagens_importante ON mensagens(importante)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_mensagens_timestamp ON mensagens(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resumos_timestamp ON resumos(timestamp)')
            
            conn.commit()
            conn.close()
            
            _LOGGER.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            _LOGGER.error(f"Erro ao inicializar banco de dados: {e}")
    
    def salvar_mensagem(self, mensagem):
        """Salva uma mensagem no banco de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Preparar dados
            timestamp = int(datetime.datetime.now().timestamp())
            data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # Inserir mensagem
            cursor.execute('''
                INSERT INTO mensagens (
                    contato, mensagem, hora, data, nivel_prioridade, 
                    categoria, importante, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                mensagem.get('contato', 'Desconhecido'),
                mensagem.get('mensagem', ''),
                mensagem.get('hora', ''),
                data_atual,
                mensagem.get('nivel_prioridade', 'baixa'),
                mensagem.get('categoria', 'geral'),
                1 if mensagem.get('importante', True) else 0,
                timestamp
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erro ao salvar mensagem: {e}")
            return False
    
    def salvar_resumo(self, resumo):
        """Salva informações sobre um resumo gerado."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Preparar dados
            timestamp = int(datetime.datetime.now().timestamp())
            
            # Inserir resumo
            cursor.execute('''
                INSERT INTO resumos (arquivo, timestamp, num_mensagens)
                VALUES (?, ?, ?)
            ''', (
                resumo.get('resumo_file', ''),
                timestamp,
                resumo.get('num_mensagens', 0)
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erro ao salvar resumo: {e}")
            return False
    
    def obter_mensagens_importantes(self, limite=100):
        """Obtém as mensagens importantes mais recentes."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM mensagens
                WHERE importante = 1
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limite,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Converter para lista de dicionários
            mensagens = []
            for row in rows:
                mensagens.append(dict(row))
            
            return mensagens
            
        except Exception as e:
            _LOGGER.error(f"Erro ao obter mensagens importantes: {e}")
            return []
    
    def obter_ultimo_resumo(self):
        """Obtém informações sobre o último resumo gerado."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM resumos
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            else:
                return None
            
        except Exception as e:
            _LOGGER.error(f"Erro ao obter último resumo: {e}")
            return None
    
    def salvar_configuracao(self, chave, valor):
        """Salva um item de configuração."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Converter valor para JSON se for um objeto
            if not isinstance(valor, str):
                valor = json.dumps(valor)
            
            # Inserir ou atualizar configuração
            cursor.execute('''
                INSERT OR REPLACE INTO configuracao (chave, valor)
                VALUES (?, ?)
            ''', (chave, valor))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erro ao salvar configuração: {e}")
            return False
    
    def obter_configuracao(self, chave, padrao=None):
        """Obtém um item de configuração."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT valor FROM configuracao
                WHERE chave = ?
            ''', (chave,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                valor = row[0]
                # Tentar converter de JSON para objeto
                try:
                    return json.loads(valor)
                except:
                    return valor
            else:
                return padrao
            
        except Exception as e:
            _LOGGER.error(f"Erro ao obter configuração: {e}")
            return padrao
    
    def limpar_mensagens_antigas(self, dias=30):
        """Remove mensagens mais antigas que o número de dias especificado."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calcular timestamp limite
            limite = int((datetime.datetime.now() - datetime.timedelta(days=dias)).timestamp())
            
            # Remover mensagens antigas
            cursor.execute('''
                DELETE FROM mensagens
                WHERE timestamp < ?
            ''', (limite,))
            
            num_removidas = cursor.rowcount
            conn.commit()
            conn.close()
            
            _LOGGER.info(f"Removidas {num_removidas} mensagens antigas")
            return num_removidas
            
        except Exception as e:
            _LOGGER.error(f"Erro ao limpar mensagens antigas: {e}")
            return 0
    
    def criar_backup(self):
        """Cria um backup do banco de dados."""
        try:
            # Gerar nome do arquivo de backup
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"whatsapp_monitor_backup_{timestamp}.db")
            
            # Conectar ao banco de dados original
            conn = sqlite3.connect(self.db_path)
            
            # Criar backup
            backup_conn = sqlite3.connect(backup_file)
            conn.backup(backup_conn)
            
            # Fechar conexões
            backup_conn.close()
            conn.close()
            
            _LOGGER.info(f"Backup criado em {backup_file}")
            return backup_file
            
        except Exception as e:
            _LOGGER.error(f"Erro ao criar backup: {e}")
            return None
    
    def restaurar_backup(self, backup_file):
        """Restaura um backup do banco de dados."""
        try:
            if not os.path.exists(backup_file):
                _LOGGER.error(f"Arquivo de backup não encontrado: {backup_file}")
                return False
            
            # Criar backup do banco atual antes de restaurar
            self.criar_backup()
            
            # Conectar ao banco de dados de backup
            backup_conn = sqlite3.connect(backup_file)
            
            # Conectar ao banco de dados principal
            conn = sqlite3.connect(self.db_path)
            
            # Restaurar backup
            backup_conn.backup(conn)
            
            # Fechar conexões
            conn.close()
            backup_conn.close()
            
            _LOGGER.info(f"Backup restaurado de {backup_file}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erro ao restaurar backup: {e}")
            return False
    
    def estatisticas_armazenamento(self):
        """Retorna estatísticas sobre o armazenamento de dados."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total de mensagens
            cursor.execute('SELECT COUNT(*) FROM mensagens')
            total_mensagens = cursor.fetchone()[0]
            
            # Total de mensagens importantes
            cursor.execute('SELECT COUNT(*) FROM mensagens WHERE importante = 1')
            total_importantes = cursor.fetchone()[0]
            
            # Total de resumos
            cursor.execute('SELECT COUNT(*) FROM resumos')
            total_resumos = cursor.fetchone()[0]
            
            # Mensagens por contato
            cursor.execute('''
                SELECT contato, COUNT(*) as total
                FROM mensagens
                GROUP BY contato
                ORDER BY total DESC
            ''')
            mensagens_por_contato = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Tamanho do banco de dados
            tamanho_db = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            # Tamanho dos backups
            tamanho_backups = sum(os.path.getsize(os.path.join(self.backup_dir, f)) 
                                for f in os.listdir(self.backup_dir) 
                                if os.path.isfile(os.path.join(self.backup_dir, f)))
            
            conn.close()
            
            return {
                'total_mensagens': total_mensagens,
                'total_importantes': total_importantes,
                'total_resumos': total_resumos,
                'mensagens_por_contato': mensagens_por_contato,
                'tamanho_db': tamanho_db,
                'tamanho_backups': tamanho_backups,
                'ultima_atualizacao': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            _LOGGER.error(f"Erro ao obter estatísticas de armazenamento: {e}")
            return {
                'erro': str(e),
                'ultima_atualizacao': datetime.datetime.now().isoformat()
            }

# Funções de serviço para Home Assistant

def init_storage(hass):
    """Inicializa o armazenamento de dados."""
    try:
        config_dir = hass.config.path("custom_components", DOMAIN)
        
        # Criar instância do armazenamento
        storage = WhatsAppMonitorStorage(config_dir)
        hass.data[DOMAIN]["storage"] = storage
        
        _LOGGER.info("Armazenamento de dados inicializado com sucesso")
        return True
    except Exception as e:
        _LOGGER.error(f"Erro ao inicializar armazenamento de dados: {e}")
        return False

def backup_service(hass):
    """Serviço para criar backup do banco de dados."""
    storage = hass.data[DOMAIN].get("storage")
    if not storage:
        _LOGGER.error("Armazenamento de dados não inicializado")
        return False
    
    backup_file = storage.criar_backup()
    
    if backup_file:
        # Disparar evento para notificar sobre novo backup
        hass.bus.fire(f"{DOMAIN}_new_backup", {
            "backup_file": backup_file,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        return True
    else:
        return False

def cleanup_service(hass, dias=30):
    """Serviço para limpar mensagens antigas."""
    storage = hass.data[DOMAIN].get("storage")
    if not storage:
        _LOGGER.error("Armazenamento de dados não inicializado")
        return False
    
    num_removidas = storage.limpar_mensagens_antigas(dias)
    
    # Disparar evento para notificar sobre limpeza
    hass.bus.fire(f"{DOMAIN}_storage_cleanup", {
        "mensagens_removidas": num_removidas,
        "dias": dias,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    return True
