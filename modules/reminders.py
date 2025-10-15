import paho.mqtt.client as mqtt
import json
import time
import threading
from datetime import datetime
import os

# --- Configurazione ---
REMINDERS_FILE = "reminders.json"
CHECK_INTERVAL_SECONDS = 30 # Ogni quanto controlla se ci sono promemoria dovuti
# --------------------

class ReminderManager:
    def __init__(self, client):
        self.client = client
        self.reminders = []
        self.file_path = self._get_file_path()
        self.load_reminders()
        self.running = True
        self.thread = threading.Thread(target=self.check_loop)
        self.thread.start()

    def _get_file_path(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(project_root, REMINDERS_FILE)

    def load_reminders(self):
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
                print(f"🗓️  [Reminders] Caricati {len(self.reminders)} promemoria dal file.")
        except Exception as e:
            print(f"💥 [Reminders] Errore nel caricamento dei promemoria: {e}")

    def save_reminders(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, indent=2)
        except Exception as e:
            print(f"💥 [Reminders] Errore nel salvataggio dei promemoria: {e}")

    def add_reminder(self, text, trigger_time_str):
        try:
            # Converte il tempo (es. "21:30") in un oggetto datetime completo di oggi
            hour, minute = map(int, trigger_time_str.split(':'))
            now = datetime.now()
            trigger_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Se l'ora è già passata oggi, imposta il promemoria per domani
            if trigger_dt < now:
                trigger_dt = trigger_dt.replace(day=now.day + 1) # Semplificato, non gestisce il cambio mese

            reminder = {
                "text": text,
                "trigger_time_iso": trigger_dt.isoformat(),
                "triggered": False
            }
            self.reminders.append(reminder)
            self.save_reminders()
            print(f"🗓️  [Reminders] Nuovo promemoria aggiunto per le {trigger_time_str}: '{text}'")
            return f"Ok, ti ricorderò di {text} alle {trigger_time_str}."
        except Exception as e:
            print(f"💥 [Reminders] Formato ora non valido: {e}")
            return "Mi dispiace, non ho capito l'orario."

    def check_loop(self):
        while self.running:
            now = datetime.now()
            for reminder in self.reminders:
                trigger_dt = datetime.fromisoformat(reminder['trigger_time_iso'])
                if not reminder['triggered'] and now >= trigger_dt:
                    print(f"🗓️  [Reminders] Promemoria scattato: '{reminder['text']}'! Invio evento...")
                    self.client.publish("humora/events/reminder_triggered", reminder['text'])
                    reminder['triggered'] = True
                    self.save_reminders() # Salva lo stato "triggered"
            time.sleep(CHECK_INTERVAL_SECONDS)

    def stop(self):
        self.running = False

def run(instance_name, room_config, mqtt_config):
    client = mqtt.Client()
    reminder_manager = ReminderManager(client)

    def on_connect(client, userdata, flags, rc):
        print("🗓️  [Reminders] Connesso e in attesa di comandi su 'humora/actions/set_reminder'")
        client.subscribe("humora/actions/set_reminder")

    def on_message(client, userdata, msg):
        try:
            params = json.loads(msg.payload.decode())
            text = params.get("reminder_text")
            time_str = params.get("time")
            if text and time_str:
                response = reminder_manager.add_reminder(text, time_str)
                # Invia una conferma immediata ad Aurora
                client.publish("humora/aurora/response", response)
        except Exception as e:
            print(f"💥 [Reminders] Errore nel processare il comando: {e}")

    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
        client.loop_forever()
    finally:
        reminder_manager.stop()
