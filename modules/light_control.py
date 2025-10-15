import paho.mqtt.client as mqtt
import json
import time

# Questa funzione viene chiamata quando arriva un messaggio dalla telecamera
def on_camera_message(client, userdata, msg):
    room_name = userdata['room_name']
    light_devices = userdata['light_devices'] # Prendiamo la lista delle luci da comandare

    try:
        payload = json.loads(msg.payload.decode())
        is_person_detected = any(d.get('label') == 'person' for d in payload.get("detections", []))

        # Determina il comando da inviare
        command = "ON" if is_person_detected else "OFF"
        
        #if is_person_detected:
            #print(f"💡 [Luci-{room_name}] Persona rilevata!")
        #else:
            #print(f"💡 [Luci-{room_name}] Stanza vuota.")

        # Invia il comando a TUTTI i dispositivi di tipo 'light' per questa stanza
        for device in light_devices:
            control_topic = device['control_topic']
            #print(f"   -> Invio comando '{command}' al dispositivo '{device['name']}' sul topic: {control_topic}")
            client.publish(control_topic, command)

    except Exception as e:
        print(f"💥 [Luci-{room_name}] Errore durante l'elaborazione del messaggio: {e}")

# La funzione principale del modulo
def run(room_name, room_config, mqtt_config):
    print(f"🧠 Modulo 'light_control' in esecuzione per '{room_name}'.")

    # 1. Filtra i dispositivi di questa stanza per ottenere solo le luci
    light_devices = [
        device for device in room_config.get('devices', []) 
        if device.get('type') == 'light'
    ]

    if not light_devices:
        print(f"⚠️ [Luci-{room_name}] Nessun dispositivo di tipo 'light' trovato nella configurazione. Il modulo non farà nulla.")
        return

    print(f"   - Gestirò i seguenti dispositivi: {[d['name'] for d in light_devices]}")

    # 2. Prepara i dati utente da passare alle callback MQTT
    user_data = {
        "room_name": room_name,
        "light_devices": light_devices
    }
    
    client = mqtt.Client(userdata=user_data)
    client.on_message = on_camera_message # Imposta la funzione che gestirà i messaggi

    # Il topic di ascolto per i dati della telecamera rimane lo stesso
    camera_topic = f"humora/rooms/{room_name}/camera/detections"
    
    try:
        client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
        client.subscribe(camera_topic)
        #print(f"👂 [Luci-{room_name}] In ascolto su: {camera_topic}")
        client.loop_forever()
    except KeyboardInterrupt:
        #print(f"\n🛑 [Luci-{room_name}] Modulo in arresto.")
        client.disconnect()
