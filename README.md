# SmartAssebility - Raspberry Pi Setup

Sistema de acessibilidade que usa sensor ultrassônico HC-SR04 e Bluetooth Low Energy para comunicação com smartwatch.

## 🔧 Instalação Automática

Execute o script de instalação:

```bash
chmod +x install.sh
bash install.sh
sudo reboot
```

## 📱 Instalação Manual

### 1. Dependências do Sistema

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
    python3-pip python3-venv \
    bluetooth bluez bluez-tools \
    libglib2.0-dev libcairo2-dev \
    libgirepository1.0-dev pkg-config \
    python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0
```

### 2. Configurar Bluetooth

```bash
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
sudo usermod -a -G bluetooth $USER
```

### 3. Ambiente Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install bluezero PyGObject RPi.GPIO
```

## ⚡ Hardware - Sensor HC-SR04

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

## 🚀 Uso

### Executar Programa

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar
python3 ProjetoAmandaPassos.py
```

### Como Serviço (Auto-inicialização)

```bash
# Habilitar serviço
sudo systemctl enable smartassebility

# Iniciar serviço
sudo systemctl start smartassebility

# Ver logs
sudo journalctl -u smartassebility -f
```

## 📡 Configuração BLE

O programa cria um dispositivo BLE com:

- **Nome**: `SmartAssebility-RPi`
- **Serviço UUID**: `12345678-1234-5678-1234-56789abcdef0`
- **Característica UUID**: `12345678-1234-5678-1234-56789abcdef1`

## 🔍 Troubleshooting

### Problemas Comuns

#### 1. Bluetooth não funciona
```bash
sudo systemctl status bluetooth
sudo hciconfig hci0 up
sudo systemctl restart bluetooth
```

#### 2. Permissões GPIO
```bash
sudo usermod -a -G gpio $USER
sudo reboot
```

#### 3. Import bluezero falha
```bash
# Verificar instalação
pip list | grep bluezero

# Reinstalar se necessário
pip install --force-reinstall bluezero
```

#### 4. Sensor não responde
- Verificar conexões físicas
- Testar com multímetro
- Verificar alimentação 5V

### Comandos de Debug

```bash
# Ver dispositivos Bluetooth
hciconfig -a

# Escanear dispositivos BLE
sudo hcitool lescan

# Monitor GPIO
gpio readall  # Se wiringpi instalado

# Logs do sistema
sudo journalctl -u bluetooth -f
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