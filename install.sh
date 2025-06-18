#!/bin/bash

# Script de Instalação para SmartAssebility - Raspberry Pi
# Execute com: bash install.sh

echo "🔧 Configurando SmartAssebility na Raspberry Pi..."

# Atualizar sistema
echo "📦 Atualizando sistema..."
sudo apt update && sudo apt upgrade -y

# Instalar dependências do sistema
echo "🔗 Instalando dependências do sistema..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    bluetooth \
    bluez \
    bluez-tools \
    libglib2.0-dev \
    libcairo2-dev \
    libgirepository1.0-dev \
    pkg-config \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0

# Configurar Bluetooth
echo "📡 Configurando Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Adicionar usuário ao grupo bluetooth
echo "👤 Adicionando usuário ao grupo bluetooth..."
sudo usermod -a -G bluetooth $USER

# Criar ambiente virtual Python
echo "🐍 Criando ambiente virtual Python..."
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
echo "📚 Instalando dependências Python..."
pip install --upgrade pip
pip install \
    bluezero \
    PyGObject \
    RPi.GPIO

# Testar instalação
echo "🧪 Testando instalação..."
python3 -c "
try:
    import bluezero
    import RPi.GPIO as GPIO
    from gi.repository import GLib
    print('✅ Todas as dependências instaladas com sucesso!')
except ImportError as e:
    print(f'❌ Erro na importação: {e}')
"

# Configurar GPIO
echo "⚡ Configurando GPIO..."
sudo groupadd -f gpio
sudo usermod -a -G gpio $USER

# Criar arquivo de serviço systemd (opcional)
echo "🔧 Criando serviço systemd..."
sudo tee /etc/systemd/system/smartassebility.service > /dev/null << EOF
[Unit]
Description=SmartAssebility BLE Server
After=bluetooth.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python3 $PWD/ProjetoAmandaPassos.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "📋 Próximos passos:"
echo "1. Reiniciar o sistema: sudo reboot"
echo "2. Ativar ambiente virtual: source venv/bin/activate"
echo "3. Executar o programa: python3 ProjetoAmandaPassos.py"
echo ""
echo "🔧 Comandos úteis:"
echo "- Verificar Bluetooth: sudo systemctl status bluetooth"
echo "- Listar adaptadores: hciconfig"
echo "- Ativar adaptador: sudo hciconfig hci0 up"
echo "- Executar como serviço: sudo systemctl enable smartassebility"
echo ""
echo "⚠️  IMPORTANTE: Reinicie o sistema para aplicar as permissões!" 