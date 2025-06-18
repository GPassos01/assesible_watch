#!/usr/bin/env python3
"""
Script simples para testar advertising BLE
"""

import subprocess
import time
import sys

def run_cmd(cmd, description):
    """Executa comando e retorna sucesso/falha"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ OK")
            return True
        else:
            print(f"❌ Erro: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Falha: {e}")
        return False

def main():
    print("🚀 Teste Simples BLE - SmartAssebility")
    print("=" * 40)
    
    # 1. Verificar Bluetooth
    if not run_cmd("sudo systemctl is-active bluetooth", "Verificando Bluetooth"):
        print("❌ Bluetooth não está ativo")
        return
    
    # 2. Resetar adaptador
    print("\n🔄 Resetando adaptador...")
    run_cmd("sudo hciconfig hci0 down", "Desligando hci0")
    time.sleep(1)
    run_cmd("sudo hciconfig hci0 up", "Ligando hci0")
    time.sleep(2)
    
    # 3. Parar advertising existente
    run_cmd("sudo hciconfig hci0 noleadv", "Parando advertising")
    time.sleep(1)
    
    # 4. Configurar advertising simples
    print("\n📡 Configurando advertising...")
    
    # Nome: SmartAsb (mais curto)
    name = "SmartAsb"
    name_hex = name.encode().hex()
    
    # Dados de advertising: Flags + Nome
    adv_data = f"02011A{len(name)+1:02x}09{name_hex}"
    
    # Comando para definir dados
    cmd = f"sudo hcitool -i hci0 cmd 0x08 0x0008 {len(adv_data)//2:02x} {adv_data}"
    
    if run_cmd(cmd, "Definindo dados"):
        # Ativar advertising
        if run_cmd("sudo hcitool -i hci0 cmd 0x08 0x000A 01", "Ativando advertising"):
            print("\n✅ ADVERTISING ATIVO!")
            print(f"📱 Dispositivo: '{name}'")
            print("🔍 Procure no Galaxy Watch5!")
            
            # Verificar status
            result = subprocess.run("sudo hciconfig hci0", shell=True, capture_output=True, text=True)
            if "ADVERTISE" in result.stdout:
                print("✅ Status confirmado: ADVERTISING")
            
            print("\n⏳ Mantendo ativo por 60 segundos...")
            print("   Pressione Ctrl+C para parar")
            
            try:
                time.sleep(60)
            except KeyboardInterrupt:
                print("\n🛑 Interrompido")
            
            # Parar advertising
            run_cmd("sudo hcitool -i hci0 cmd 0x08 0x000A 00", "Parando advertising")
            print("✅ Advertising parado")
    
    print("\n🔧 Para debug adicional:")
    print("- Verificar logs: sudo journalctl -f -u bluetooth")
    print("- Monitor BLE: sudo hcidump -i hci0")
    print("- Reiniciar: sudo systemctl restart bluetooth")

if __name__ == "__main__":
    main() 