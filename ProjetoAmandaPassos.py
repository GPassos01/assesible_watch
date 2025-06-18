from bluezero import peripheral
import RPi.GPIO as GPIO
import time
from gi.repository import GLib

# Configuração dos pinos do HC-SR04
TRIG = 23
ECHO = 24
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def medir_distancia():
    """Mede distância com o sensor HC-SR04"""
    try:
        # Envia pulso de trigger
        GPIO.output(TRIG, False)
        time.sleep(0.002)  # Pausa menor para melhor performance
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)
        
        # Aguarda início do pulso de echo com timeout
        timeout = time.time() + 0.1  # Timeout reduzido
        pulse_start = time.time()
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if time.time() > timeout:
                print("Timeout aguardando início do pulso")
                return 0
        
        # Aguarda fim do pulso de echo com timeout
        timeout = time.time() + 0.1
        pulse_end = time.time()
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if time.time() > timeout:
                print("Timeout aguardando fim do pulso")
                return 0
        
        # Calcula distância
        pulse_duration = pulse_end - pulse_start
        distancia = pulse_duration * 17150  # Velocidade do som
        distancia = round(distancia, 2)
        
        # Valida leitura (sensor HC-SR04 mede de 2cm a 400cm)
        if 2 <= distancia <= 400:
            return distancia
        else:
            print(f"Leitura fora do range: {distancia}cm")
            return 0
            
    except Exception as e:
        print(f"Erro na medição: {e}")
        return 0

def read_distance_callback():
    """Callback executado quando cliente BLE lê a característica"""
    distancia = medir_distancia()
    print(f"📏 Distância medida: {distancia} cm")
    
    # Converte para string e depois para lista de bytes ASCII
    distance_str = str(distancia)
    return [ord(c) for c in distance_str]

def main():
    try:
        print("🔧 Configurando Servidor BLE...")
        
        # Endereço MAC do seu adaptador Bluetooth
        ADAPTER_MAC = 'D8:3A:DD:20:0F:D1'
        
        # Criar peripheral BLE
        ble_peripheral = peripheral.Peripheral(adapter_address=ADAPTER_MAC)
        
        # Configurar nome do dispositivo
        ble_peripheral.local_name = 'Raspberry Pi'
        
        # Adicionar serviço BLE
        # Usando Blood Pressure Service (0x1810) como no código original
        ble_peripheral.add_service(
            srv_id=1, 
            uuid='00001810-0000-1000-8000-00805f9b34fb',  # Blood Pressure Service
            primary=True
        )
        
        # Adicionar característica BLE
        # Usando Blood Pressure Measurement (0x2A35)
        ble_peripheral.add_characteristic(
            srv_id=1,
            chr_id=1,
            uuid='00002a35-0000-1000-8000-00805f9b34fb',  # Blood Pressure Measurement
            value='0',
            notifying=False,
            flags=['read'],
            read_callback=read_distance_callback
        )
        
        print("📡 Publicando serviço BLE...")
        ble_peripheral.publish()
        
        print("✅ Servidor BLE iniciado com sucesso!")
        print("📱 Nome do dispositivo: 'Raspberry Pi'")
        print("🔗 UUID do Serviço: 00001810-0000-1000-8000-00805f9b34fb")
        print("📊 UUID da Característica: 00002a35-0000-1000-8000-00805f9b34fb")
        print("⏳ Aguardando conexões BLE...")
        print("🛑 Pressione Ctrl+C para parar\n")
        
        # Testar sensor uma vez
        teste_distancia = medir_distancia()
        print(f"🧪 Teste inicial do sensor: {teste_distancia} cm\n")
        
        # Executar loop principal
        main_loop = GLib.MainLoop()
        main_loop.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Encerrando servidor BLE...")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        print("\n🔍 Verificações:")
        print("1. Bluetooth ativo: sudo systemctl status bluetooth")
        print("2. Adaptador ativo: sudo hciconfig hci0 up")
        print("3. Permissões: groups $USER (deve incluir 'bluetooth')")
        print("4. Dependências: pip install PyGObject")
        
    finally:
        try:
            GPIO.cleanup()
            print("🧹 Recursos GPIO limpos")
        except:
            pass

if __name__ == "__main__":
    main()
