# WhatsApp Monitor para Home Assistant

Um componente personalizado para Home Assistant que monitora mensagens do WhatsApp, identifica as importantes e apresenta resumos em intervalos regulares. Otimizado para Raspberry Pi 4.

## Recursos

- **Monitoramento Automático**: Verifica periodicamente novas mensagens no WhatsApp
- **Identificação Inteligente**: Identifica mensagens importantes com base em palavras-chave, contatos prioritários e padrões de urgência
- **Resumos Personalizados**: Gera resumos detalhados das mensagens importantes
- **Visualizações Gráficas**: Cria gráficos para análise das mensagens importantes
- **Integração Completa**: Funciona como um componente nativo do Home Assistant
- **Otimizado para Raspberry Pi**: Projetado para funcionar eficientemente em recursos limitados

## Requisitos

- Raspberry Pi 4 (recomendado pelo menos 2GB de RAM)
- Home Assistant OS instalado e funcionando
- Acesso SSH ao Raspberry Pi
- Conta WhatsApp ativa em um smartphone

## Instalação

### Via HACS (Recomendado)

1. Certifique-se de que o [HACS](https://hacs.xyz/) está instalado
2. Vá para HACS > Integrações
3. Clique no botão de três pontos no canto superior direito
4. Selecione "Repositórios Personalizados"
5. Adicione este repositório URL e selecione a categoria "Integração"
6. Clique em "Adicionar"
7. Procure por "WhatsApp Monitor" e instale

### Manual

1. Copie a pasta `custom_components/whatsapp_monitor` para o diretório `custom_components` do seu Home Assistant
2. Reinicie o Home Assistant
3. Vá para Configurações > Dispositivos e Serviços
4. Clique em "+ Adicionar Integração"
5. Procure por "WhatsApp Monitor"

## Configuração

Após a instalação, você pode configurar o WhatsApp Monitor através da interface do Home Assistant:

1. Vá para Configurações > Dispositivos e Serviços
2. Encontre e clique em "WhatsApp Monitor"
3. Configure as seguintes opções:
   - Palavras-chave para identificar mensagens importantes
   - Contatos prioritários
   - Intervalo de verificação de mensagens
   - Intervalo de geração de resumos

## Primeira Execução

Na primeira execução, você precisará autenticar o WhatsApp Web:

1. O sistema gerará um QR code
2. Abra o WhatsApp no seu smartphone
3. Toque em Menu > WhatsApp Web
4. Escaneie o QR code exibido

## Sensores Disponíveis

O componente cria os seguintes sensores:

- **Status do WhatsApp Monitor**: Mostra se está conectado ou desconectado
- **Mensagens Importantes**: Contagem de mensagens importantes identificadas
- **Última Verificação**: Timestamp da última verificação de mensagens
- **Último Resumo**: Timestamp do último resumo gerado

## Serviços

O componente fornece os seguintes serviços:

- **whatsapp_monitor.check_messages**: Verifica manualmente novas mensagens
- **whatsapp_monitor.generate_summary**: Gera manualmente um resumo
- **whatsapp_monitor.connect**: Conecta ao WhatsApp Web
- **whatsapp_monitor.disconnect**: Desconecta do WhatsApp Web

## Automações

Exemplo de automação para notificar sobre novas mensagens importantes:

```yaml
automation:
  - alias: "Notificar sobre novas mensagens importantes do WhatsApp"
    trigger:
      platform: event
      event_type: whatsapp_monitor_new_important_messages
    action:
      - service: notify.mobile_app_seu_dispositivo
        data:
          title: "Novas mensagens importantes do WhatsApp"
          message: "{{ trigger.event.data.count }} novas mensagens importantes foram detectadas."
```

## Solução de Problemas

### Problemas de Conexão

Se o WhatsApp Monitor não conseguir se conectar:

1. Verifique se o Chromium está instalado corretamente:
   ```bash
   chromium-browser --version
   ```

2. Verifique se o ChromeDriver está instalado e compatível:
   ```bash
   chromedriver --version
   ```

3. Limpe os dados de sessão e tente novamente:
   ```bash
   rm -rf /config/custom_components/whatsapp_monitor/whatsapp_profile
   ```

### Problemas de Recursos

Se o Raspberry Pi estiver com problemas de desempenho:

1. Aumente o intervalo de verificação para 30 minutos ou mais
2. Aumente o intervalo de resumo para 120 minutos ou mais

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Agradecimentos

- [Home Assistant](https://www.home-assistant.io/) pela incrível plataforma de automação residencial
- [Selenium](https://www.selenium.dev/) pela automação de navegador web
