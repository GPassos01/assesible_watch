# SmartAssebility - Raspberry Pi Setup

Sistema de acessibilidade que usa sensor ultrassônico HC-SR04 e Bluetooth Low Energy para comunicação com smartwatch.

## 🔧 Instalação Rápida

Execute o script de instalação:

```bash
chmod +x install.sh
bash install.sh
sudo reboot
```

## 📱 Dependências Necessárias

### Sistema:
```bash
sudo apt install -y python3-pip python3-venv bluetooth bluez python3-gi
```

### Python:
```bash
pip install bluezero PyGObject RPi.GPIO
```

## ⚡ Hardware - HC-SR04

### Conexões:

| HC-SR04 | Raspberry Pi |
|---------|--------------|
| VCC     | 5V (Pin 2)   |
| GND     | GND (Pin 6)  |
| TRIG    | GPIO 23      |
| ECHO    | GPIO 24      |

### Esquema:
```
Raspberry Pi          HC-SR04
    GPIO 23  ------>  TRIG
    GPIO 24  <------  ECHO
    5V       ------>  VCC
    GND      ------>  GND
```

## 🚀 Executar

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar
python3 ProjetoAmandaPassos.py
```

## 📡 BLE Config

O programa cria um dispositivo BLE com:

- **Nome**: `SmartAssebility-RPi`
- **Serviço UUID**: `12345678-1234-5678-1234-56789abcdef0`
- **Característica UUID**: `12345678-1234-5678-1234-56789abcdef1`

## 🔍 Problemas

### Bluezero não reconhecido
```bash
# No Windows (desenvolvimento)
# Os erros são normais - o código roda na Raspberry Pi

# Na Raspberry Pi
pip install bluezero
sudo systemctl restart bluetooth
```

### Permissões
```bash
sudo usermod -a -G bluetooth $USER
sudo usermod -a -G gpio $USER
sudo reboot
```

## 📊 Formato dos Dados

O sensor retorna dados em formato JSON:

```json
{
  "distance": 25.3,
  "unit": "cm"
}
```

## 🔧 Configurações Avançadas

### Alterar Pinos GPIO

Edite as constantes no arquivo `ProjetoAmandaPassos.py`:

```python
TRIG_PIN = 23  # Altere aqui
ECHO_PIN = 24  # Altere aqui
```

### Alterar Nome BLE

```python
BLE_DEVICE_NAME = 'SeuNome-RPi'
```

### Alterar Frequência de Medição

```python
time.sleep(0.5)  # Medir a cada 500ms
```

## 📈 Monitoramento

### Ver Distância em Tempo Real

```bash
# Em um terminal separado
watch -n 1 'echo "Distância atual sendo medida..."'
```

### Logs Detalhados

Altere o nível de log no código:

```python
logging.basicConfig(level=logging.DEBUG)  # Mais verboso
```

## 🔒 Segurança

- O serviço BLE não requer autenticação (para simplicidade)
- Para uso em produção, considere adicionar autenticação
- Dados são transmitidos em texto plano

## 🆘 Suporte

Se encontrar problemas:

1. Verifique todas as conexões físicas
2. Execute `sudo systemctl status bluetooth`
3. Verifique os logs: `sudo journalctl -u smartassebility`
4. Teste o sensor individualmente
5. Reinicie o sistema se necessário

## 📝 Notas de Desenvolvimento

- O código usa threading para medições contínuas
- Implementa timeouts para evitar travamentos
- Inclui validação de range do sensor (2-400cm)
- Logs estruturados para debug 