#!/usr/bin/env python3
"""
Servidor BLE Básico para SmartAssebility
Usa comandos diretos do sistema - mais confiável que bluezero
"""

import time
import logging
import threading
import subprocess
import random
import os
import signal

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Tentar imports
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO não disponível - usando simulação")

# Configuração do sensor
TRIG_PIN = 23
ECHO_PIN = 24

# Variáveis globais
current_distance = 0
measurement_active = True
advertise_process = None

def setup_gpio():
    """Configura GPIO do sensor HC-SR04"""
    if GPIO_AVAILABLE:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(TRIG_PIN, GPIO.OUT)
        GPIO.setup(ECHO_PIN, GPIO.IN)
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.5)
        logger.info("✅ GPIO configurado")
    else:
        logger.info("🧪 GPIO simulado")

def measure_distance():
    """Mede distância com HC-SR04 ou simula"""
    if not GPIO_AVAILABLE:
        return round(random.uniform(10, 100), 1)
    
    try:
        # Pulso trigger
        GPIO.output(TRIG_PIN, False)
        time.sleep(0.002)
        GPIO.output(TRIG_PIN, True)
        time.sleep(0.00001)
        GPIO.output(TRIG_PIN, False)
        
        # Medir echo
        timeout = time.time() + 0.1
        pulse_start = time.time()
        
        while GPIO.input(ECHO_PIN) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                return None
        
        pulse_end = time.time()
        while GPIO.input(ECHO_PIN) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                return None
        
        # Calcular distância
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        
        if 2 <= distance <= 400:
            return round(distance, 1)
        return None
        
    except Exception as e:
        logger.error(f"Erro no sensor: {e}")
        return None

def update_distance():
    """Thread para atualizar distância continuamente"""
    global current_distance, measurement_active
    
    while measurement_active:
        distance = measure_distance()
        if distance:
            current_distance = distance
            logger.debug(f"Distância: {distance} cm")
        time.sleep(1)

def setup_bluetooth():
    """Configura Bluetooth usando comandos do sistema"""
    try:
        logger.info("🔧 Configurando Bluetooth...")
        
        # Parar bluetoothd se estiver rodando
        subprocess.run(['sudo', 'systemctl', 'stop', 'bluetooth'], 
                      capture_output=True, check=False)
        time.sleep(1)
        
        # Reiniciar bluetoothd
        subprocess.run(['sudo', 'systemctl', 'start', 'bluetooth'], 
                      capture_output=True, check=True)
        time.sleep(2)
        
        # Ativar adaptador
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'up'], 
                      capture_output=True, check=True)
        
        # Configurar modo discoverable
        subprocess.run(['sudo', 'hciconfig', 'hci0', 'piscan'], 
                      capture_output=True, check=True)
        
        logger.info("✅ Bluetooth configurado")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro na configuração Bluetooth: {e}")
        return False

def start_ble_advertising():
    """Inicia advertising BLE usando hcitool"""
    global advertise_process
    
    try:
        logger.info("📡 Iniciando BLE advertising...")
        
        # Criar nome em hex (SmartAssebility)
        device_name = "SmartAssebility"
        name_hex = device_name.encode('utf-8').hex()
        
        # Dados de advertising (formato básico)
        # Flags + Nome completo + UUID de serviço
        adv_data = f"02011A{len(device_name)+1:02x}09{name_hex}0303F018"
        
        # Iniciar advertising
        cmd = [
            'sudo', 'hcitool', '-i', 'hci0', 'cmd',
            '0x08', '0x0008',  # LE Set Advertising Data
            f'{len(adv_data)//2:02x}',  # Length
            adv_data,
            '00' * (31 - len(adv_data)//2)  # Padding
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        # Ativar advertising
        subprocess.run([
            'sudo', 'hcitool', '-i', 'hci0', 'cmd',
            '0x08', '0x000A',  # LE Set Advertise Enable
            '01'  # Enable
        ], capture_output=True, check=True)
        
        logger.info("✅ BLE Advertising ativo!")
        logger.info(f"📱 Nome: {device_name}")
        logger.info("🔗 Visível para smartwatches")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro no advertising: {e}")
        return False

def stop_ble_advertising():
    """Para o advertising BLE"""
    try:
        subprocess.run([
            'sudo', 'hcitool', '-i', 'hci0', 'cmd',
            '0x08', '0x000A',  # LE Set Advertise Enable
            '00'  # Disable
        ], capture_output=True, check=False)
        logger.info("🛑 BLE Advertising parado")
    except:
        pass

def signal_handler(sig, frame):
    """Handler para Ctrl+C"""
    global measurement_active
    logger.info("\n🛑 Recebido sinal de parada...")
    measurement_active = False
    stop_ble_advertising()
    if GPIO_AVAILABLE:
        GPIO.cleanup()
    logger.info("🧹 Limpeza concluída")
    exit(0)

def main():
    """Função principal"""
    global measurement_active
    
    logger.info("🚀 Iniciando SmartAssebility (BLE básico)...")
    
    # Configurar handler de sinais
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configurar GPIO
    setup_gpio()
    
    # Testar sensor
    test_dist = measure_distance()
    logger.info(f"🧪 Teste sensor: {test_dist} cm")
    
    # Iniciar thread de medição
    measurement_thread = threading.Thread(target=update_distance, daemon=True)
    measurement_thread.start()
    
    # Configurar Bluetooth
    if setup_bluetooth():
        if start_ble_advertising():
            logger.info("⏳ Dispositivo visível - aguardando conexões...\n")
        else:
            logger.warning("⚠️ Advertising falhou, mas sensor continua funcionando")
    else:
        logger.warning("⚠️ Bluetooth falhou, executando apenas sensor")
    
    # Loop principal
    try:
        while measurement_active:
            logger.info(f"📏 Distância atual: {current_distance} cm")
            time.sleep(5)
            
    except KeyboardInterrupt:
        pass
    
    # Limpeza final
    measurement_active = False
    stop_ble_advertising()
    if GPIO_AVAILABLE:
        GPIO.cleanup()
    logger.info("🧹 Programa encerrado")

if __name__ == "__main__":
    main() 