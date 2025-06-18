#!/usr/bin/env python3
"""
Sistema de Acessibilidade com Sensor Ultrassônico
Servidor BLE que expõe leituras de distância via Bluetooth Low Energy
"""

from bluezero import peripheral
import RPi.GPIO as GPIO
import time
import threading
import logging
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

# Configuração BLE
BLE_SERVICE_UUID = '12345678-1234-5678-1234-56789abcdef0'  # UUID customizado
BLE_CHARACTERISTIC_UUID = '12345678-1234-5678-1234-56789abcdef1'  # UUID customizado
BLE_DEVICE_NAME = 'SmartAssebility-RPi'

# Variáveis globais
current_distance = 0
distance_lock = threading.Lock()
measurement_active = True

class UltrasonicSensor:
    """Classe para gerenciar o sensor ultrassônico HC-SR04"""
    
    def __init__(self, trig_pin, echo_pin):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.setup_gpio()
        
    def setup_gpio(self):
        """Configura os pinos GPIO"""
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        GPIO.output(self.trig_pin, False)
        time.sleep(0.5)  # Aguarda estabilização
        
    def measure_distance(self):
        """Mede distância com o sensor HC-SR04"""
        try:
            # Garante que o trigger está em LOW
            GPIO.output(self.trig_pin, False)
            time.sleep(0.002)
            
            # Envia pulso de trigger (10µs)
            GPIO.output(self.trig_pin, True)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, False)
            
            # Aguarda início do pulso de echo
            timeout_start = time.time()
            pulse_start = time.time()
            
            while GPIO.input(self.echo_pin) == 0:
                pulse_start = time.time()
                if (pulse_start - timeout_start) > 0.1:
                    logger.warning("Timeout aguardando início do pulso")
                    return None
            
            # Aguarda fim do pulso de echo
            timeout_start = time.time()
            pulse_end = time.time()
            
            while GPIO.input(self.echo_pin) == 1:
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
        GPIO.cleanup()

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
        
        # Formata como JSON para melhor estrutura
        response = f'{{"distance": {distance}, "unit": "cm"}}'
        return [ord(c) for c in response]
    
    def update_measurements(self):
        """Thread para atualizar medições continuamente"""
        global current_distance, measurement_active
        
        while measurement_active:
            distance = self.sensor.measure_distance()
            
            if distance is not None:
                with distance_lock:
                    current_distance = distance
                logger.debug(f"Distância atualizada: {distance} cm")
            
            time.sleep(0.5)  # Atualiza a cada 500ms
    
    def start(self):
        """Inicia o servidor BLE"""
        try:
            logger.info("🔧 Configurando Servidor BLE...")
            
            # Detectar adaptador automaticamente
            try:
                from bluezero import adapter
                dongles = adapter.Adapter.available()
                if dongles:
                    adapter_address = dongles[0]
                    logger.info(f"Usando adaptador: {adapter_address}")
                else:
                    raise Exception("Nenhum adaptador Bluetooth encontrado")
            except:
                # Fallback para endereço padrão
                adapter_address = None
                logger.warning("Usando adaptador padrão")
            
            # Criar peripheral BLE
            self.peripheral = peripheral.Peripheral(
                adapter_address=adapter_address,
                local_name=BLE_DEVICE_NAME
            )
            
            # Adicionar serviço customizado
            self.peripheral.add_service(
                srv_id=1,
                uuid=BLE_SERVICE_UUID,
                primary=True
            )
            
            # Adicionar característica de distância
            self.peripheral.add_characteristic(
                srv_id=1,
                chr_id=1,
                uuid=BLE_CHARACTERISTIC_UUID,
                value=[],
                notifying=False,
                flags=['read', 'notify'],
                read_callback=self.read_distance_callback,
                write_callback=None,
                notify_callback=None
            )
            
            # Iniciar thread de medições
            measurement_thread = threading.Thread(
                target=self.update_measurements,
                daemon=True
            )
            measurement_thread.start()
            
            logger.info("📡 Publicando serviço BLE...")
            self.peripheral.publish()
            
            logger.info("✅ Servidor BLE iniciado com sucesso!")
            logger.info(f"📱 Nome do dispositivo: '{BLE_DEVICE_NAME}'")
            logger.info(f"🔗 UUID do Serviço: {BLE_SERVICE_UUID}")
            logger.info(f"📊 UUID da Característica: {BLE_CHARACTERISTIC_UUID}")
            logger.info("⏳ Aguardando conexões BLE...")
            logger.info("🛑 Pressione Ctrl+C para parar\n")
            
            # Testar sensor
            test_distance = self.sensor.measure_distance()
            if test_distance:
                logger.info(f"🧪 Teste do sensor OK: {test_distance} cm\n")
            else:
                logger.warning("⚠️  Teste do sensor falhou - verifique conexões\n")
            
            # Executar loop principal
            main_loop = GLib.MainLoop()
            main_loop.run()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Encerrando servidor BLE...")
            
        except Exception as e:
            logger.error(f"\n❌ Erro: {e}")
            logger.info("\n🔍 Verificações:")
            logger.info("1. Bluetooth ativo: sudo systemctl status bluetooth")
            logger.info("2. Adaptador ativo: sudo hciconfig hci0 up")
            logger.info("3. Permissões: sudo usermod -a -G bluetooth $USER")
            logger.info("4. Dependências: pip install bluezero PyGObject")
            logger.info("5. Reiniciar Bluetooth: sudo systemctl restart bluetooth")
            
        finally:
            global measurement_active
            measurement_active = False
            self.sensor.cleanup()
            logger.info("🧹 Recursos limpos")

def main():
    """Função principal"""
    # Criar sensor
    sensor = UltrasonicSensor(TRIG_PIN, ECHO_PIN)
    
    # Criar e iniciar servidor BLE
    server = BLEDistanceServer(sensor)
    server.start()

if __name__ == "__main__":
    main()
