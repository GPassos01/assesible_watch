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
echo "7. Testando Python bluezero (detalhado):"
python3 -c "
try:
    from bluezero import adapter
    print('📡 Testando adapter.Adapter.available()...')
    dongles = list(adapter.Adapter.available())
    print(f'Número de adaptadores: {len(dongles)}')
    
    if dongles:
        adapter_obj = dongles[0]
        print(f'Tipo do objeto: {type(adapter_obj)}')
        print(f'Atributos disponíveis: {dir(adapter_obj)}')
        
        if hasattr(adapter_obj, 'address'):
            print(f'✅ address: {adapter_obj.address}')
        if hasattr(adapter_obj, 'path'):
            print(f'✅ path: {adapter_obj.path}')
        if hasattr(adapter_obj, 'name'):
            print(f'✅ name: {adapter_obj.name}')
            
        print(f'String do objeto: {str(adapter_obj)}')
    else:
        print('⚠️ Nenhum adaptador detectado')
        
except Exception as e:
    print(f'❌ Erro: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "8. Verificar processo bluetoothd:"
ps aux | grep bluetoothd | grep -v grep

echo ""
echo "9. Testando criação de Peripheral:"
python3 -c "
try:
    from bluezero import peripheral, adapter
    dongles = list(adapter.Adapter.available())
    if dongles:
        adapter_obj = dongles[0]
        if hasattr(adapter_obj, 'address'):
            addr = adapter_obj.address
        elif hasattr(adapter_obj, 'path'):
            addr = adapter_obj.path
        else:
            addr = str(adapter_obj)
        
        print(f'Tentando criar Peripheral com: {addr}')
        p = peripheral.Peripheral(adapter_address=addr, local_name='Teste')
        print('✅ Peripheral criado com sucesso!')
    else:
        print('❌ Nenhum adaptador para testar')
except Exception as e:
    print(f'❌ Erro na criação: {e}')
"

echo ""
echo "🔧 Comandos de correção (se necessário):"
echo "sudo systemctl restart bluetooth"
echo "sudo hciconfig hci0 up"
echo "sudo hciconfig hci0 leadv"
echo "sudo usermod -a -G bluetooth $USER" 