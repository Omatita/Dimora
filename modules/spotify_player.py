import spotipy
import config
from spotipy.oauth2 import SpotifyOAuth
import paho.mqtt.client as mqtt
import json
import os

# --- INSERISCI QUI LE TUE CREDENZIALI SPOTIFY ---
SPOTIPY_CLIENT_ID = config.SPOTIPY_CLIENT_ID
SPOTIPY_CLIENT_SECRET = config.SPOTIPY_CLIENT_SECRET
SPOTIPY_REDIRECT_URI = config.SPOTIPY_REDIRECT_URI
# --------------------------------------------------

# Definiamo i permessi ("scope") di cui la nostra app ha bisogno
SCOPE = "user-modify-playback-state user-read-playback-state user-read-currently-playing"

def run(instance_name, room_config, mqtt_config):
    print("🎵 [Spotify] Avvio modulo...")

    # Gestione cache token per non dover fare il login ogni volta
    # Salva il file .cache nella cartella principale del progetto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_path = os.path.join(project_root, ".spotify_cache")
    
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=SCOPE,
            cache_path=cache_path
        ))
        # Prova a fare una chiamata per forzare l'autenticazione al primo avvio
        sp.devices()
        print("🎵 [Spotify] Autenticazione con Spotify riuscita.")
    except Exception as e:
        print(f"💥 [Spotify] ERRORE CRITICO: Impossibile autenticarsi con Spotify. Controlla le credenziali. Dettagli: {e}")
        return

    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print("🎵 [Spotify] Connesso al broker MQTT. In attesa di comandi musicali.")
        client.subscribe("humora/actions/play_music")
        client.subscribe("humora/actions/pause_music")
        client.subscribe("humora/actions/next_track")

    def on_message(client, userdata, msg):
        try:
            topic = msg.topic
            print(f"🎵 [Spotify] Ricevuto comando sul topic: {topic}")
            
            # Trova un dispositivo attivo su cui riprodurre la musica
            devices = sp.devices()
            active_device_id = None
            if devices['devices']:
                # Diamo priorità a un dispositivo già attivo
                for d in devices['devices']:
                    if d['is_active']:
                        active_device_id = d['id']
                        break
                # Se nessuno è attivo, prendiamo il primo della lista
                if not active_device_id:
                    active_device_id = devices['devices'][0]['id']
            
            if not active_device_id:
                print("⚠️ [Spotify] Nessun dispositivo Spotify attivo trovato.")
                client.publish("humora/aurora/response", "Non ho trovato nessun dispositivo Spotify attivo su cui riprodurre musica.")
                return

            if topic == "humora/actions/play_music":
                params = json.loads(msg.payload.decode())
                query = f"{params.get('track_name', '')} {params.get('artist_name', '')}"
                results = sp.search(q=query, type='track', limit=1)
                
                if results['tracks']['items']:
                    track_uri = results['tracks']['items'][0]['uri']
                    sp.start_playback(device_id=active_device_id, uris=[track_uri])
                    track_name = results['tracks']['items'][0]['name']
                    artist_name = results['tracks']['items'][0]['artists'][0]['name']
                    client.publish("humora/aurora/response", f"Ok, avvio {track_name} di {artist_name}.")
                else:
                    client.publish("humora/aurora/response", f"Non ho trovato la canzone {query} su Spotify.")

            elif topic == "humora/actions/pause_music":
                sp.pause_playback(device_id=active_device_id)

            elif topic == "humora/actions/next_track":
                sp.next_track(device_id=active_device_id)

        except Exception as e:
            print(f"💥 [Spotify] Errore durante l'esecuzione del comando: {e}")
            client.publish("humora/aurora/response", "Si è verificato un errore nel controllare Spotify.")

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
    client.loop_forever()
