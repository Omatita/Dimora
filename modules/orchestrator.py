import paho.mqtt.client as mqtt
import json
import requests
from datetime import datetime # <-- Import per data e ora
import psutil # <-- Import per stato del PC

# --- Configurazione ---
OLLAMA_API_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "phi3" # -> mistral appena girera' su un pd dedicato
# --------------------

# La lista di strumenti che compiono AZIONI rimane la stessa
ACTION_TOOLS = """
- set_timer(minutes: int, seconds: int): Imposta un timer.
- set_reminder(reminder_text: str, time: str): Imposta un promemoria per un'ora specifica (formato HH:MM).
- turn_on_light(room_name: str): Accende tutte le luci in una stanza.
- turn_off_light(room_name: str): Spegne tutte le luci in una stanza.
- play_music(track_name: str, artist_name: str): Cerca e riproduce una canzone di un artista.
- pause_music(): Mette in pausa la riproduzione musicale.
- next_track(): Passa alla canzone successiva.
"""

def get_system_context():
    """Raccoglie informazioni di contesto dal sistema."""
    now = datetime.now()
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    
    context = f"""
INFORMAZIONI DI CONTESTO:
- Data e ora correnti: {now.strftime('%A %d %B %Y, ore %H:%M:%S')}
- Utilizzo CPU: {cpu_usage}%
- Utilizzo RAM: {ram_usage}%
"""
    return context

def get_ai_decision(user_request):
    """Interroga l'API locale di Ollama con contesto arricchito."""
    
    system_context = get_system_context()
    
    prompt = f"""
    {system_context}

    STRUMENTI DI AZIONE DISPONIBILI:
    {ACTION_TOOLS}

    Analizza la richiesta dell'utente: "{user_request}"

    - Se la richiesta può essere soddisfatta usando le INFORMAZIONI DI CONTESTO, formula una risposta diretta e imposta "tool_to_call" su "none".
    - Se la richiesta richiede di eseguire un'AZIONE, usa lo strumento appropriato.
    - Se è una conversazione generale, rispondi normalmente.

    Rispondi SOLO con un oggetto JSON valido.

    Esempio per info di contesto:
    {{
      "tool_to_call": "none",
      "parameters": {{}},
      "spoken_response": "Sono le 10 e 30 del mattino."
    }}

    Esempio per un'azione:
    {{
      "tool_to_call": "turn_on_light",
      "parameters": {{ "room_name": "cucina" }},
      "spoken_response": "Certo, accendo subito la luce in cucina."
    }}
    """
    
    try:
        payload = {
            "model": MODEL_NAME, "format": "json", "stream": False,
            "messages": [
                {"role": "system", "content": "Sei Aurora, un'assistente AI. Usa le informazioni di contesto e gli strumenti di azione per rispondere."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        response_content = json.loads(response.text)
        decision = json.loads(response_content['message']['content'])
        return decision
    except Exception as e:
        print(f"💥 [Orchestratore] Errore durante la chiamata a Ollama: {e}")
        return {"tool_to_call": "none", "parameters": {}, "spoken_response": "Si è verificato un errore con il modello locale."}
# ... tutti gli import e le funzioni precedenti rimangono invariati ...
# (OLLAMA_API_URL, MODEL_NAME, ACTION_TOOLS, get_system_context, get_ai_decision)

def run(instance_name, room_config, mqtt_config):
    """
    Modulo principale dell'Orchestratore.
    Ascolta le richieste dell'utente, interroga l'AI e smista le azioni e le risposte.
    """
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print("🧠 [Orchestratore] Connesso.")
        print("   -> In ascolto su 'humora/user/request'")
        client.subscribe("humora/user/request")
        print("   -> In ascolto su 'humora/events/timer_finished'")
        client.subscribe("humora/events/timer_finished")
        print("   -> In ascolto su 'humora/events/reminder_triggered'")
        client.subscribe("humora/events/reminder_triggered")

    def on_message(client, userdata, msg):
        # --- BLOCCO MODIFICATO PER ESSERE PIÙ ROBUSTO ---
        
        if msg.topic == "humora/user/request":
            user_request = msg.payload.decode()
            print(f"🧠 [Orchestratore] Ricevuta richiesta utente: '{user_request}'")
            
            decision = get_ai_decision(user_request)
            print(f"   -> Decisione AI: {decision}")

            # MODIFICA 1: Accesso sicuro alla risposta vocale
            # Se 'spoken_response' non c'è, usiamo una frase di default.
            spoken_response = decision.get('spoken_response', "Mi dispiace, non so come rispondere a questo.")
            client.publish("humora/aurora/response", spoken_response)

            # MODIFICA 2: Accesso sicuro allo strumento da chiamare
            tool_to_call = decision.get('tool_to_call')
            
            if tool_to_call and tool_to_call != "none":
                # MODIFICA 3: Accesso sicuro ai parametri
                action_payload = json.dumps(decision.get('parameters', {}))
                action_topic = f"humora/actions/{tool_to_call}"
                
                print(f"   -> Eseguo azione: Pubblico su '{action_topic}'")
                client.publish(action_topic, action_payload)
        
        elif msg.topic == "humora/events/timer_finished":
            print(f"🧠 [Orchestratore] Ricevuto evento: Timer scaduto!")
            spoken_response = "Il timer che avevi impostato è scaduto."
            client.publish("humora/aurora/response", spoken_response)
        
        elif msg.topic == "humora/events/reminder_triggered":
            reminder_text = msg.payload.decode()
            print(f"🧠 [Orchestratore] Ricevuto evento: Promemoria scattato!")
            spoken_response = f"Promemoria: è ora di {reminder_text}."
            client.publish("humora/aurora/response", spoken_response)
        # --------------------------------------------------

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
    client.loop_forever()
