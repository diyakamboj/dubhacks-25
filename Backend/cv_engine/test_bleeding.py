import cv2
import yaml
import numpy as np
from detectors.bleeding import detect_bleeding

# --- Load config ---
with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# --- Initialize webcam ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not found.")
    exit()

frame_id = 0
print("🎥 Testing Bleeding Detector + On-Screen Color Debug...")
print("👉 Show your red pen or cloth to the camera to inspect color values.\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_id += 1

    # --- Convert to HSV for color debugging ---
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define your current red mask
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([179, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # --- Calculate average color values for red regions ---
    red_pixels = frame[red_mask > 0]
    if len(red_pixels) > 0:
        avg_bgr = np.mean(red_pixels, axis=0)
        avg_hsv = np.mean(hsv[red_mask > 0], axis=0)
    else:
        avg_bgr = [0, 0, 0]
        avg_hsv = [0, 0, 0]

    # --- Run the bleeding detection ---
    event = detect_bleeding(frame, cfg, frame_id)

    h, w, _ = frame.shape

    # --- Display detections + color values ---
    if event:
        text_color = (0, 0, 255)
        print(f"🩸 Detected bleeding! conf={event.confidence:.2f}")
    else:
        text_color = (0, 255, 0)
        print("✅ No bleeding detected.")

    print(f"   → Avg BGR: {avg_bgr.astype(int)} | Avg HSV: {avg_hsv.astype(int)}\n")

    # Draw text overlay on video feed
    cv2.putText(frame, f"Avg BGR: {avg_bgr.astype(int)}", (30, h - 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Avg HSV: {avg_hsv.astype(int)}", (30, h - 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if event:
        cv2.putText(frame, "🩸 BLEEDING DETECTED", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, text_color, 3)
    else:
        cv2.putText(frame, "No bleeding detected", (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, text_color, 2)

    cv2.imshow("Bleeding Detection + Color Debug", frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
