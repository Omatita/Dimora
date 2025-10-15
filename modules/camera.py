import cv2
import paho.mqtt.client as mqtt
import json
from ultralytics import YOLO
from datetime import datetime

# La funzione ora accetta i parametri!
def run(room_name, room_config, mqtt_config):
    print(f"🧠 Modulo 'camera' in esecuzione per '{room_name}'.")

    client = mqtt.Client()
    try:
        client.connect(mqtt_config['broker'], mqtt_config['port'], 60)
        client.loop_start()
    except Exception as e:
        print(f"❌ [Camera-{room_name}] Impossibile connettersi a MQTT: {e}")
        return

    model = YOLO("yolov8n.pt")
    source = room_config['camera_source']
    cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"❌ [Camera-{room_name}] Impossibile aprire la sorgente video: {source}")
        return

    # Il topic è ora specifico per la stanza
    topic = f"humora/rooms/{room_name}/camera/detections"
    print(f"📹 [Camera-{room_name}] Analisi avviata. Pubblico su topic: {topic}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret: break

            results = model(frame, verbose=False)
            boxes = results[0].boxes
            
            detected_objects = [
                {"label": model.names[int(b.cls[0])], "confidence": round(float(b.conf[0]), 2)}
                for b in boxes
            ]
            
            message = { "timestamp": datetime.now().isoformat(), "detections": detected_objects }
            client.publish(topic, json.dumps(message))

            # Finestra di debug (opzionale)
            # annotated = results[0].plot()
            # cv2.imshow(f"Camera - {room_name}", annotated)
            # if cv2.waitKey(1) & 0xFF == ord('q'): break
    finally:
#        print(f"🛑 [Camera-{room_name}] Modulo in arresto.")
        cap.release()
        # cv2.destroyAllWindows()
        client.loop_stop()
        client.disconnect()
