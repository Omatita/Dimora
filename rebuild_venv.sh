#!/bin/bash

# Script per cancellare e ricreare da zero l'ambiente virtuale Python.

echo "🔥 Avvio procedura di ricostruzione dell'ambiente virtuale... 🔥"

# Controlla se siamo dentro un venv e lo disattiva
if [[ "$VIRTUAL_ENV" != "" ]]; then
  echo "-> Disattivazione ambiente virtuale attivo..."
  deactivate
fi

# Controlla se la cartella venv esiste e la cancella
if [ -d "venv" ]; then
    echo "-> Rimozione vecchia cartella 'venv'..."
    rm -rf venv
    echo "   ✅ Cartella rimossa."
else
    echo "-> Nessuna cartella 'venv' trovata, procedo con la creazione."
fi

# Crea il nuovo ambiente virtuale
echo "-> Creazione nuovo ambiente virtuale 'venv'..."
python3 -m venv venv
echo "   ✅ Ambiente creato."

# Attiva il nuovo ambiente e installa i pacchetti
echo "-> Attivazione ambiente e installazione dipendenze..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo -e "\n🎉 Perfetto! L'ambiente virtuale è stato ricostruito con successo."
echo "Ora puoi lanciare il sistema con ./launcher.sh"
