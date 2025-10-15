import importlib
import sys
import json
import traceback
import os

# ... la funzione load_config() rimane invariata ...
def load_config():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Errore: file 'config.json' non trovato.")
        return None

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    config = load_config()
    if not config:
        sys.exit(1)

    if len(sys.argv) < 3:
        print("❌ Uso: python main.py <nome_modulo> <nome_stanza_o_servizio>")
        sys.exit(1)

    module_name = sys.argv[1]
    instance_name = sys.argv[2] # Può essere una stanza o "global"
    full_module_name = f"modules.{module_name}"
    
    # Se è un modulo di stanza, prendi la sua config. Altrimenti, passa None.
    room_config = config['rooms'].get(instance_name)

    try:
        print(f"🚀 Avvio modulo '{module_name}' per l'istanza '{instance_name}'...")
        module = importlib.import_module(full_module_name)

        if hasattr(module, "run"):
            # Passiamo l'intera configurazione della stanza (o None) al modulo
            module.run(instance_name, room_config, config['mqtt'])
        else:
            print(f"⚠️ Il modulo '{module_name}' non ha una funzione 'run()'.")
    except ModuleNotFoundError:
        print(f"❌ Modulo '{full_module_name}' non trovato.")
        traceback.print_exc()
    except Exception as e:
        print(f"💥 Errore durante l'esecuzione: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
