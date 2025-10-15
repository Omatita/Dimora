#!/bin/bash

# Uccide tutti i processi figli (incluso ollama se avviato da qui) quando lo script viene terminato
trap "echo -e '\n🛑 Spegnimento in corso...'; trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

CONFIG_FILE="config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ File di configurazione '$CONFIG_FILE' non trovato!"
    exit 1
fi

# --- Gestione di Ollama ---
echo "🧠 Controllo dello stato di Ollama..."
if ! pgrep -x "ollama" > /dev/null
then
    echo "-> Ollama non è in esecuzione. Lo avvio in background..."
    ollama serve &
    # Diamo a Ollama qualche secondo per inizializzare prima che i moduli provino a connettersi
    sleep 5 
    echo "   ✅ Ollama avviato."
else
    echo "   ✅ Ollama è già in esecuzione."
fi
# -------------------------

# --- Gestione di Mosquitto (NUOVA SEZIONE) ---
echo "📮 Controllo dello stato del broker MQTT..."
if ! pgrep -x "mosquitto" > /dev/null
then
    echo "-> Mosquitto non è in esecuzione. Lo avvio in background..."
    # Questo comando presume che mosquitto sia installato a livello di sistema
    mosquitto &
    sleep 2
    echo "   ✅ Mosquitto avviato."
else
    echo "   ✅ Mosquitto è già in esecuzione."
fi
# ----------------------------------------------


echo "🚀 Avvio del sistema AI Home..."

# --- Avvio dei Servizi Globali ---
GLOBAL_SERVICES=$(jq -r '.global_services[]' $CONFIG_FILE)
if [ -n "$GLOBAL_SERVICES" ]; then
    echo "   - Configurazione Servizi Globali..."
    for service in $GLOBAL_SERVICES; do
        echo "     -> Avvio servizio '$service'..."
        # Avvia ogni servizio in background, passando "global" come nome istanza
        ./start.sh "$service" "global" &
    done
fi
# ------------------------------

# --- Avvio dei Moduli per Stanza ---
ROOMS=$(jq -r '.rooms | keys | .[]' $CONFIG_FILE)
if [ -n "$ROOMS" ]; then
    echo "   - Configurazione Stanze..."
    for room in $ROOMS; do
        MODULES=$(jq -r ".rooms.\"$room\".modules | .[]" $CONFIG_FILE)
        for module in $MODULES; do
            echo "     -> Avvio modulo '$module' per '$room'..."
            # Avvia ogni modulo in background
            ./start.sh "$module" "$room" &
        done
    done
fi
# ---------------------------------


echo "✅ Sistema avviato. Premi CTRL+C per fermare tutti i processi."
# Attende che tutti i processi in background terminino (non lo faranno mai da soli)
# Questo comando serve a mantenere lo script principale in vita
wait
