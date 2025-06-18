#!/usr/bin/env python3
"""
Sistema de Acessibilidade com Sensor Ultrassônico
Servidor BLE que expõe leituras de distância via Bluetooth Low Energy
"""

try:
    from bluezero import peripheral
    from bluezero import adapter
    BLUEZERO_AVAILABLE = True
except ImportError:
    print("⚠️  bluezero não disponível - modo de teste")
    BLUEZERO_AVAILABLE = False

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    print("⚠️  RPi.GPIO não disponível - usando simulação")
    GPIO_AVAILABLE = False

import time
import threading
import logging
import random
from gi.repository import GLib

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuração dos pinos do HC-SR04
TRIG_PIN = 23
ECHO_PIN = 24

# Configuração BLE - UUIDs mais simples
BLE_SERVICE_UUID = '180F'  # Battery Service UUID (mais simples)
BLE_CHARACTERISTIC_UUID = '2A19'  # Battery Level Characteristic
BLE_DEVICE_NAME = 'SmartAssebility-RPi'

# Variáveis globais
current_distance = 0
distance_lock = threading.Lock()
measurement_active = True

class MockGPIO:
    """Mock GPIO para testes quando RPi.GPIO não está disponível"""
    BCM = 'BCM'
    OUT = 'OUT'
    IN = 'IN'
    
    @staticmethod
    def setwarnings(value):
        pass
    
    @staticmethod
    def setmode(mode):
        pass
    
    @staticmethod
    def setup(pin, mode):
        pass
    
    @staticmethod
    def output(pin, value):
        pass
    
    @staticmethod
    def input(pin):
        return random.choice([0, 1])
    
    @staticmethod
    def cleanup():
        pass

class UltrasonicSensor:
    """Classe para gerenciar o sensor ultrassônico HC-SR04"""
    
    def __init__(self, trig_pin, echo_pin):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.gpio = GPIO if GPIO_AVAILABLE else MockGPIO()
        self.setup_gpio()
        
    def setup_gpio(self):
        """Configura os pinos GPIO"""
        if GPIO_AVAILABLE:
            self.gpio.setwarnings(False)
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.trig_pin, self.gpio.OUT)
            self.gpio.setup(self.echo_pin, self.gpio.IN)
            self.gpio.output(self.trig_pin, False)
            time.sleep(0.5)
        else:
            logger.info("🔧 Usando GPIO simulado para testes")
        
    def measure_distance(self):
        """Mede distância com o sensor HC-SR04"""
        if not GPIO_AVAILABLE:
            # Simulação para testes
            distance = random.uniform(10, 200)
            logger.debug(f"📏 Distância simulada: {distance:.1f} cm")
            return round(distance, 1)
            
        try:
            # Garante que o trigger está em LOW
            self.gpio.output(self.trig_pin, False)
            time.sleep(0.002)
            
            # Envia pulso de trigger (10µs)
            self.gpio.output(self.trig_pin, True)
            time.sleep(0.00001)
            self.gpio.output(self.trig_pin, False)
            
            # Aguarda início do pulso de echo
            timeout_start = time.time()
            pulse_start = time.time()
            
            while self.gpio.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if (pulse_start - timeout_start) > 0.1:
                    logger.warning("Timeout aguardando início do pulso")
                    return None
            
            # Aguarda fim do pulso de echo
            timeout_start = time.time()
            pulse_end = time.time()
            
            while self.gpio.input(self.echo_pin) == 1:
                pulse_end = time.time()
                if (pulse_end - timeout_start) > 0.1:
                    logger.warning("Timeout aguardando fim do pulso")
                    return None
            
            # Calcula distância
            pulse_duration = pulse_end - pulse_start
            distance_cm = pulse_duration * 17150
            distance_cm = round(distance_cm, 1)
            
            # Valida leitura (HC-SR04: 2cm a 400cm)
            if 2 <= distance_cm <= 400:
                return distance_cm
            else:
                logger.warning(f"Leitura fora do range: {distance_cm}cm")
                return None
                
        except Exception as e:
            logger.error(f"Erro na medição: {e}")
            return None
            
    def cleanup(self):
        """Limpa os recursos GPIO"""
        if GPIO_AVAILABLE:
            self.gpio.cleanup()

class BLEDistanceServer:
    """Servidor BLE para expor leituras de distância"""
    
    def __init__(self, sensor):
        self.sensor = sensor
        self.peripheral = None
        
    def read_distance_callback(self):
        """Callback executado quando cliente BLE lê a característica"""
        global current_distance
        
        with distance_lock:
            distance = current_distance
            
        logger.info(f"📏 Cliente leu distância: {distance} cm")
        
        # Retorna apenas o valor da distância como string simples
        distance_str = str(int(distance)) if distance else "0"
        return [ord(c) for c in distance_str]
    
    def update_measurements(self):
        """Thread para atualizar medições continuamente"""
        global current_distance, measurement_active
        
        while measurement_active:
            distance = self.sensor.measure_distance()
            
            if distance is not None:
                with distance_lock:
                    current_distance = distance
                logger.debug(f"Distância atualizada: {distance} cm")
            
            time.sleep(1.0)  # Atualiza a cada 1 segundo
    
    def start(self):
        """Inicia o servidor BLE"""
        if not BLUEZERO_AVAILABLE:
            logger.error("❌ bluezero não disponível - instale com: pip install bluezero")
            logger.info("🧪 Executando apenas medições do sensor...")
            self.run_sensor_only()
            return
            
        try:
            logger.info("🔧 Configurando Servidor BLE...")
            
            # Abordagem mais simples - sem especificar adapter_address
            try:
                logger.info("📡 Tentando criar Peripheral sem adaptador específico...")
                self.peripheral = peripheral.Peripheral(
                    local_name=BLE_DEVICE_NAME
                )
                logger.info("✅ Peripheral criado com adaptador padrão")
                
            except Exception as e1:
                logger.warning(f"⚠️ Falha com adaptador padrão: {e1}")
                
                # Fallback: tentar com None
                try:
                    logger.info("📡 Tentando com adapter_address=None...")
                    self.peripheral = peripheral.Peripheral(
                        adapter_address=None,
                        local_name=BLE_DEVICE_NAME
                    )
                    logger.info("✅ Peripheral criado com adapter_address=None")
                    
                except Exception as e2:
                    logger.error(f"❌ Falha total na criação do Peripheral: {e2}")
                    logger.info("🧪 Executando apenas medições do sensor...")
                    self.run_sensor_only()
                    return
            
            logger.info("📡 Adicionando serviço BLE...")
            
            # Adicionar serviço usando UUID padrão
            self.peripheral.add_service(
                srv_id=1,
                uuid=BLE_SERVICE_UUID,
                primary=True
            )
            
            logger.info("📊 Adicionando característica...")
            
            # Adicionar característica com configuração simples
            self.peripheral.add_characteristic(
                srv_id=1,
                chr_id=1,
                uuid=BLE_CHARACTERISTIC_UUID,
                value="0",
                notifying=False,
                flags=['read'],
                read_callback=self.read_distance_callback
            )
            
            # Iniciar thread de medições
            logger.info("🔄 Iniciando medições...")
            measurement_thread = threading.Thread(
                target=self.update_measurements,
                daemon=True
            )
            measurement_thread.start()
            
            logger.info("📡 Publicando serviço BLE...")
            self.peripheral.publish()
            
            logger.info("✅ Servidor BLE iniciado com sucesso!")
            logger.info(f"📱 Nome: '{BLE_DEVICE_NAME}'")
            logger.info(f"🔗 Serviço: {BLE_SERVICE_UUID}")
            logger.info(f"📊 Característica: {BLE_CHARACTERISTIC_UUID}")
            logger.info("⏳ Aguardando conexões...\n")
            
            # Testar sensor
            test_distance = self.sensor.measure_distance()
            if test_distance:
                logger.info(f"🧪 Sensor OK: {test_distance} cm\n")
            
            # Executar loop principal
            main_loop = GLib.MainLoop()
            main_loop.run()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Encerrando...")
            
        except Exception as e:
            logger.error(f"\n❌ Erro BLE: {e}")
            logger.info("🔍 Soluções:")
            logger.info("1. sudo systemctl restart bluetooth")
            logger.info("2. sudo hciconfig hci0 up")
            logger.info("3. sudo hciconfig hci0 leadv")
            logger.info("4. pip install --force-reinstall bluezero")
            logger.info("\n🧪 Tentando modo apenas sensor...")
            self.run_sensor_only()
            
        finally:
            global measurement_active
            measurement_active = False
            self.sensor.cleanup()
            logger.info("�� Recursos limpos")
    
    def run_sensor_only(self):
        """Executa apenas as medições do sensor (sem BLE)"""
        try:
            logger.info("🧪 Modo teste - apenas sensor")
            
            measurement_thread = threading.Thread(
                target=self.update_measurements,
                daemon=True
            )
            measurement_thread.start()
            
            while True:
                with distance_lock:
                    distance = current_distance
                logger.info(f"📏 Distância atual: {distance} cm")
                time.sleep(2)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Encerrando...")
        finally:
            global measurement_active
            measurement_active = False
            self.sensor.cleanup()

def main():
    """Função principal"""
    logger.info("🚀 Iniciando SmartAssebility...")
    
    # Verificar dependências
    if not BLUEZERO_AVAILABLE:
        logger.warning("⚠️  bluezero não encontrado")
    if not GPIO_AVAILABLE:
        logger.warning("⚠️  RPi.GPIO não encontrado")
    
    # Criar sensor
    sensor = UltrasonicSensor(TRIG_PIN, ECHO_PIN)
    
    # Criar e iniciar servidor
    server = BLEDistanceServer(sensor)
    server.start()

if __name__ == "__main__":
    main()
