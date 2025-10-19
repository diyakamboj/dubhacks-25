import cv2
from detectors.unresponsive import detect_unresponsive
from schemas import DetectionEvent
import yaml

# --- Load config ---
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# --- Initialize webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not found.")
    exit()

frame_id = 0
print("🎥 Testing Unresponsive (Cardiac Arrest) Detector...")
print("Move normally for a few seconds, then lie still to simulate unresponsiveness.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_id += 1
    event = detect_unresponsive(frame, cfg, frame_id)

    if event:
        print(f"🚨 Detected cardiac arrest! conf={event.confidence:.2f}")
        cv2.putText(frame, "🚨 CARDIAC ARREST DETECTED!", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
    else:
        print("✅ No cardiac arrest detected.")
        cv2.putText(frame, "Normal movement detected", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Unresponsive Detection Test", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
