import paho.mqtt.client as mqtt

# --- Configurazione ---
USER_NAME = "Utente" # Puoi cambiarlo se vuoi
# --------------------

def run(instance_name, room_config, mqtt_config):
    """
    Modulo che cattura l'input dell'utente da riga di comando e lo pubblica su MQTT.
    """
    client = mqtt.Client()
    
    try:
        client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
        print(f"🎤 [{USER_NAME}-Listener] Connesso. Scrivi il tuo messaggio e premi Invio.")
        print("   Per uscire, scrivi 'exit' o premi CTRL+C.")
        
        # Mantiene il client in esecuzione in un thread separato
        client.loop_start()

        while True:
            # Attende l'input dell'utente
            user_input = input(f"{USER_NAME}: ")
            
            if user_input.lower() == 'exit':
                break
                
            # Pubblica l'input sul topic delle richieste utente
            client.publish("humora/user/request", user_input)

    except KeyboardInterrupt:
        print(f"\n🎤 [{USER_NAME}-Listener] Uscita in corso...")
    except Exception as e:
        print(f"💥 Errore nel Listener: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("🎤 Listener disconnesso.")
