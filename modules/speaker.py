import paho.mqtt.client as mqtt
from datetime import datetime
import os
import subprocess
import shlex

# --- Configurazione ---
ASSISTANT_NAME = "Aurora"
LOG_FILE_NAME = "aurora_conversation.log"
# Il nome del tuo modello vocale. Assicurati che corrisponda al file che hai scaricato.
VOICE_MODEL_FILE = "it_IT-paola-medium.onnx" 
# --------------------

def get_project_root():
    """Trova e restituisce il percorso assoluto della cartella principale del progetto."""
    # os.path.abspath(__file__) -> /path/to/project/modules/speaker.py
    # os.path.dirname(...)    -> /path/to/project/modules
    # os.path.dirname(...)    -> /path/to/project
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_log_file_path(project_root):
    """Calcola il percorso completo del file di log."""
    return os.path.join(project_root, LOG_FILE_NAME)

def write_to_log(prefix, text, log_file_path):
    """Scrive un singolo messaggio sul file di log e lo stampa anche su console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"[{timestamp}] {prefix}: {text}"
    
    print(formatted_message) # Utile per il debug in tempo reale
    
    if not log_file_path: 
        print("💥 [Speaker] Percorso del file di log non disponibile.")
        return
    try:
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(formatted_message + '\n')
    except Exception as e:
        print(f"💥 [Speaker] ERRORE durante la scrittura del log: {e}")

def speak(text, project_root, log_file_path):
    """
    Usa Piper con percorsi assoluti per pronunciare il testo e lo logga.
    """
    # Per prima cosa, logghiamo la risposta di Aurora
    write_to_log(ASSISTANT_NAME.upper(), text, log_file_path)

    # Costruiamo i percorsi assoluti per Piper e il modello vocale
    piper_executable = os.path.join(project_root, "piper", "piper")
    voice_model = os.path.join(project_root, "piper", VOICE_MODEL_FILE) 

    # Controlliamo che i file necessari esistano per dare un errore più chiaro
    if not os.path.isfile(piper_executable):
        print(f"💥 [Speaker] ERRORE: Eseguibile di Piper non trovato in '{piper_executable}'")
        return
    if not os.path.isfile(voice_model):
        print(f"💥 [Speaker] ERRORE: Modello vocale non trovato in '{voice_model}'")
        return

    # Componiamo il comando da eseguire, usando shlex.quote per sicurezza
    command = f"echo '{shlex.quote(text)}' | {piper_executable} --model {voice_model} --output_raw | aplay -r 22050 -f S16_LE -t raw -"
    
    try:
        # Eseguiamo il comando, nascondendo l'output standard (stdout) per non riempire
        # il terminale, ma catturando l'output di errore (stderr) in caso di problemi.
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f"💥 [Speaker] Errore critico durante l'esecuzione di Piper: {e.stderr.decode()}")
    except FileNotFoundError:
        print("💥 [Speaker] Errore: 'aplay' non trovato. Assicurati che 'alsa-utils' sia installato e nel PATH di sistema.")
    except Exception as e:
        print(f"💥 [Speaker] Si è verificato un errore inaspettato: {e}")


def run(instance_name, room_config, mqtt_config):
    project_root = get_project_root()
    log_file_path = get_log_file_path(project_root)

    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print(f"🗣️  [{ASSISTANT_NAME}-Speaker] Connesso. Pronto a parlare e loggare.")
        client.subscribe("ai_home/user/request")
        client.subscribe("ai_home/aurora/response")

    def on_message(client, userdata, msg):
        message_text = msg.payload.decode()
        
        if msg.topic == "ai_home/user/request":
            write_to_log("UTENTE", message_text, log_file_path)
        elif msg.topic == "ai_home/aurora/response":
            speak(message_text, project_root, log_file_path)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
    client.loop_forever()
