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
    
    # Primeiro, verificar se já existe advertising ativo
    result = subprocess.run("sudo hciconfig hci0", shell=True, capture_output=True, text=True)
    if "ADVERTISE" in result.stdout:
        print("⚠️ Advertising já está ativo, parando primeiro...")
        run_command("sudo hciconfig hci0 noleadv", "Forçando parada do advertising")
        time.sleep(1)
    
    # Resetar o adaptador Bluetooth
    run_command("sudo hciconfig hci0 down", "Desativando hci0")
    time.sleep(1)
    run_command("sudo hciconfig hci0 up", "Reativando hci0")
    time.sleep(2)
    
    # Configurar advertising data com nome mais curto
    device_name = "SmartAsb"  # Nome mais curto para evitar problemas
    name_hex = device_name.encode('utf-8').hex()
    
    # Advertising data mais simples
    # 02 01 1A = Flags (General Discoverable + BR/EDR Not Supported)
    # XX 09 = Local Name Complete
    flags = "02011A"
    name_data = f"{len(device_name)+1:02x}09{name_hex}"
    adv_data = flags + name_data
    
    # Padding para 31 bytes
    padding_length = 31 - len(adv_data)//2
    padding = "00" * padding_length
    full_adv_data = adv_data + padding
    
    print(f"📝 Dados de advertising: {full_adv_data}")
    
    # Comando para definir advertising data
    cmd_data = f"sudo hcitool -i hci0 cmd 0x08 0x0008 {len(adv_data)//2:02x} {adv_data}"
    
    if run_command(cmd_data, "Configurando advertising data"):
        # Configurar parâmetros de advertising
        if run_command("sudo hcitool -i hci0 cmd 0x08 0x0006 A0 00 A0 00 00 00 00 00 00 00 00 00 00 07 00", "Configurando parâmetros"):
            # Ativar advertising
            if run_command("sudo hcitool -i hci0 cmd 0x08 0x000A 01", "Ativando advertising"):
                print("✅ Advertising ativo!")
                
                # Verificar se está realmente ativo
                result = subprocess.run("sudo hciconfig hci0", shell=True, capture_output=True, text=True)
                if "ADVERTISE" in result.stdout:
                    print("✅ Confirmado: Advertising está funcionando!")
                    return True
                else:
                    print("⚠️ Advertising pode não estar funcionando corretamente")
    
    print("❌ Falha no advertising")
    return False

def scan_for_devices():
    """Escaneia por dispositivos BLE próximos"""
    print("\n🔍 Escaneando dispositivos BLE...")
    
    try:
        # Parar qualquer scan anterior
        subprocess.run(["sudo", "killall", "hcitool"], capture_output=True)
        time.sleep(1)
        
        # Usar lescan com timeout
        print("📡 Iniciando scan BLE (10 segundos)...")
        result = subprocess.run(
            ["timeout", "10s", "sudo", "hcitool", "lescan", "--duplicates"],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        if result.stdout and result.stdout.strip():
            lines = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            unique_devices = set()
            
            print(f"📱 Processando resultados do scan...")
            for line in lines:
                if " " in line and len(line) > 10:  # Filtrar linhas válidas
                    mac_part = line.split()[0]
                    name_part = " ".join(line.split()[1:]) if len(line.split()) > 1 else "Unknown"
                    
                    if ":" in mac_part and len(mac_part) == 17:  # MAC address válido
                        unique_devices.add((mac_part, name_part))
            
            if unique_devices:
                print(f"📱 Encontrados {len(unique_devices)} dispositivos únicos:")
                for mac, name in sorted(unique_devices):
                    if "SmartAsb" in name or "SmartAssebility" in name:
                        print(f"  🎯 {mac} -> {name} (NOSSO DISPOSITIVO!)")
                    else:
                        print(f"  📱 {mac} -> {name}")
            else:
                print("❌ Nenhum dispositivo válido encontrado")
        else:
            print("❌ Scan não retornou resultados")
            
        # Tentar também com bluetoothctl
        print("\n🔍 Tentando scan alternativo com bluetoothctl...")
        result2 = subprocess.run(
            ["timeout", "5s", "bluetoothctl", "scan", "on"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result2.returncode == 0:
            time.sleep(3)
            result3 = subprocess.run(
                ["bluetoothctl", "devices"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result3.stdout:
                print("📋 Dispositivos conhecidos:")
                for line in result3.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  📱 {line}")
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout no scan - isso é normal")
    except Exception as e:
        print(f"❌ Erro no scan: {e}")
        
    finally:
        # Limpar processos
        subprocess.run(["sudo", "killall", "hcitool"], capture_output=True)
        subprocess.run(["bluetoothctl", "scan", "off"], capture_output=True)

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