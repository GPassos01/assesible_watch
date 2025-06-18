#!/bin/bash

echo "🔍 Verificando configuração Bluetooth..."

# Verificar se o Bluetooth está ativo
echo "1. Status do serviço Bluetooth:"
sudo systemctl status bluetooth --no-pager | head -5

echo ""
echo "2. Adaptadores disponíveis:"
hciconfig

echo ""
echo "3. Ativando adaptador hci0..."
sudo hciconfig hci0 up
sudo hciconfig hci0 leadv

echo ""
echo "4. Verificando modo advertising:"
sudo hciconfig hci0 | grep -E "(UP|RUNNING|PSCAN|ISCAN)"

echo ""
echo "5. Testando scan BLE:"
timeout 5s sudo hcitool lescan || echo "Scan timeout (normal)"

echo ""
echo "6. Permissões do usuário:"
groups $USER | grep -E "(bluetooth|gpio)"

echo ""
echo "7. Testando Python bluezero:"
python3 -c "
try:
    from bluezero import adapter
    dongles = list(adapter.Adapter.available())
    print(f'✅ Adaptadores encontrados: {dongles}')
    if dongles:
        print(f'Usando: {dongles[0]}')
    else:
        print('⚠️ Nenhum adaptador detectado')
except Exception as e:
    print(f'❌ Erro: {e}')
"

echo ""
echo "8. Verificar processo bluetoothd:"
ps aux | grep bluetoothd | grep -v grep

echo ""
echo "🔧 Comandos de correção (se necessário):"
echo "sudo systemctl restart bluetooth"
echo "sudo hciconfig hci0 up"
echo "sudo hciconfig hci0 leadv"
echo "sudo usermod -a -G bluetooth $USER" 