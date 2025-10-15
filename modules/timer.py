import paho.mqtt.client as mqtt
import json
import time
import threading

def run(instance_name, room_config, mqtt_config):
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print("⏱️  [Timer] Connesso e in attesa di comandi su 'humora/actions/set_timer'")
        client.subscribe("humora/actions/set_timer")

    def start_timer_thread(minutes, seconds):
        total_seconds = minutes * 60 + seconds
        print(f"⏱️  [Timer] Avvio timer di {total_seconds} secondi.")
        time.sleep(total_seconds)
        print("⏱️  [Timer] TIMER SCADUTO! Invio evento...")
        
        # --- MODIFICA CHIAVE ---
        # Pubblica un messaggio per notificare all'Orchestratore che il timer è finito.
        client.publish("humora/events/timer_finished", json.dumps({"status": "expired"}))
        # -----------------------

    def on_message(client, userdata, msg):
        try:
            params = json.loads(msg.payload.decode())
            minutes = params.get("minutes", 0)
            seconds = params.get("seconds", 0)
            threading.Thread(target=start_timer_thread, args=(minutes, seconds)).start()
        except Exception as e:
            print(f"💥 [Timer] Errore nel processare il comando: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
    client.loop_forever()
