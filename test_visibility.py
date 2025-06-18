#!/usr/bin/env python3
"""
Script para testar se a Raspberry Pi está visível via BLE
"""

import subprocess
import time
import sys

def run_command(cmd, description):
    """Executa comando e mostra resultado"""
    print(f"\n🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Sucesso: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Erro: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Timeout")
        return False
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return False

def check_bluetooth_status():
    """Verifica status do Bluetooth"""
    print("🔍 Verificando status do Bluetooth...")
    
    # Status do serviço
    run_command("sudo systemctl is-active bluetooth", "Status do serviço bluetooth")
    
    # Adaptadores disponíveis
    run_command("hciconfig", "Listando adaptadores")
    
    # Status específico do hci0
    run_command("hciconfig hci0", "Status do hci0")

def test_advertising():
    """Testa se o advertising está funcionando"""
    print("\n📡 Testando BLE Advertising...")
    
    # Parar advertising anterior
    run_command("sudo hciconfig hci0 noleadv", "Parando advertising anterior")
    
    # Configurar advertising data
    device_name = "SmartAssebility"
    name_hex = device_name.encode('utf-8').hex()
    adv_data = f"02011A{len(device_name)+1:02x}09{name_hex}0303F018"
    
    # Comando completo
    cmd_data = f"sudo hcitool -i hci0 cmd 0x08 0x0008 {len(adv_data)//2:02x} {adv_data} " + "00" * (31 - len(adv_data)//2)
    
    if run_command(cmd_data, "Configurando advertising data"):
        if run_command("sudo hcitool -i hci0 cmd 0x08 0x000A 01", "Ativando advertising"):
            print("✅ Advertising ativo!")
            return True
    
    print("❌ Falha no advertising")
    return False

def scan_for_devices():
    """Escaneia por dispositivos BLE próximos"""
    print("\n🔍 Escaneando dispositivos BLE...")
    
    try:
        # Usar timeout de 10 segundos
        result = subprocess.run(
            ["timeout", "10s", "sudo", "hcitool", "lescan"],
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            print(f"📱 Encontrados {len(lines)} dispositivos:")
            for line in lines:
                if line.strip():
                    print(f"  - {line}")
        else:
            print("❌ Nenhum dispositivo encontrado")
            
    except Exception as e:
        print(f"❌ Erro no scan: {e}")

def test_from_another_device():
    """Instruções para testar de outro dispositivo"""
    print("\n📱 Para testar de outro dispositivo:")
    print("1. No Android, use um app como 'BLE Scanner' ou 'nRF Connect'")
    print("2. Procure por 'SmartAssebility' na lista")
    print("3. Se aparecer, o advertising está funcionando")
    print("4. Se não aparecer, tente os comandos de correção abaixo")

def main():
    print("🚀 Teste de Visibilidade BLE - SmartAssebility")
    print("=" * 50)
    
    # Verificar status
    check_bluetooth_status()
    
    # Configurar e testar advertising
    if test_advertising():
        print("\n⏳ Advertising ativo por 30 segundos...")
        print("🔍 Agora tente escanear com o Galaxy Watch5!")
        
        try:
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")
        
        # Parar advertising
        run_command("sudo hcitool -i hci0 cmd 0x08 0x000A 00", "Parando advertising")
    
    # Escanear dispositivos próximos
    scan_for_devices()
    
    # Instruções adicionais
    test_from_another_device()
    
    print("\n🔧 Comandos úteis:")
    print("- Reiniciar Bluetooth: sudo systemctl restart bluetooth")
    print("- Ativar hci0: sudo hciconfig hci0 up")
    print("- Verificar advertising: sudo hcidump -i hci0")
    print("- Ver logs: sudo journalctl -f -u bluetooth")

if __name__ == "__main__":
    main() 