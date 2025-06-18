#!/usr/bin/env python3
"""
Servidor BLE Simples para SmartAssebility
Versão simplificada que deve funcionar sem problemas de path
"""

import time
import logging
import threading
import random

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

try:
    from bluezero import peripheral
    BLUEZERO_AVAILABLE = True
except ImportError:
    BLUEZERO_AVAILABLE = False
    logger.error("bluezero não disponível")

# Configuração do sensor
TRIG_PIN = 23
ECHO_PIN = 24

# Variáveis globais
current_distance = 0
measurement_active = True

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

def distance_read_callback():
    """Callback quando cliente lê a distância via BLE"""
    global current_distance
    logger.info(f"📏 Cliente leu: {current_distance} cm")
    
    # Retorna apenas o número como string
    distance_str = str(int(current_distance))
    return [ord(c) for c in distance_str]

def main():
    """Função principal simplificada"""
    global measurement_active
    
    logger.info("🚀 Iniciando SmartAssebility (versão simples)...")
    
    # Configurar GPIO
    setup_gpio()
    
    # Testar sensor
    test_dist = measure_distance()
    logger.info(f"🧪 Teste sensor: {test_dist} cm")
    
    # Iniciar thread de medição
    measurement_thread = threading.Thread(target=update_distance, daemon=True)
    measurement_thread.start()
    
    if not BLUEZERO_AVAILABLE:
        logger.info("🧪 Modo apenas sensor (sem BLE)")
        try:
            while True:
                logger.info(f"📏 Distância atual: {current_distance} cm")
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info("🛑 Parando...")
        finally:
            measurement_active = False
            if GPIO_AVAILABLE:
                GPIO.cleanup()
        return
    
    # Configurar BLE
    try:
        logger.info("🔧 Criando servidor BLE...")
        
        # Usar configuração mais simples possível
        app = peripheral.Peripheral()
        app.local_name = 'SmartAssebility'
        
        # Adicionar serviço Battery (mais simples)
        app.add_service(srv_id=1, uuid='180F', primary=True)
        
        # Adicionar característica de distância
        app.add_characteristic(
            srv_id=1, 
            chr_id=1,
            uuid='2A19',  # Battery Level
            value="0",
            notifying=False,
            flags=['read'],
            read_callback=distance_read_callback
        )
        
        logger.info("📡 Publicando serviço...")
        app.publish()
        
        logger.info("✅ Servidor BLE ativo!")
        logger.info("📱 Nome: SmartAssebility")
        logger.info("🔗 Serviço: 180F (Battery)")
        logger.info("📊 Característica: 2A19")
        logger.info("⏳ Aguardando conexões...\n")
        
        # Loop principal
        from gi.repository import GLib
        main_loop = GLib.MainLoop()
        main_loop.run()
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Encerrando...")
        
    except Exception as e:
        logger.error(f"❌ Erro BLE: {e}")
        logger.info("🧪 Continuando apenas com sensor...")
        
        try:
            while True:
                logger.info(f"📏 Distância: {current_distance} cm")
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info("🛑 Parando...")
            
    finally:
        measurement_active = False
        if GPIO_AVAILABLE:
            GPIO.cleanup()
        logger.info("🧹 Limpeza concluída")

if __name__ == "__main__":
    main() 