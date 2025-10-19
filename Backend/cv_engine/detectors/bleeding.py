import cv2
import numpy as np
from collections import deque
from schemas import DetectionEvent

# Rolling buffer for confidence smoothing
CONF_HISTORY = deque(maxlen=5)

def detect_bleeding(frame, cfg, frame_id):
    """
    Detects bleeding by analyzing red color intensity and region size.
    Tuned for skin tones and variable lighting.
    Returns DetectionEvent or None.
    """

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # --- 1️⃣ Broader red hue ranges (handles bright/dark reds) ---
    lower_red1 = np.array([0, 70, 50])
    upper_red1 = np.array([12, 255, 255])
    lower_red2 = np.array([165, 70, 50])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # --- 2️⃣ Remove skin-tone regions to avoid blending errors ---
    lower_skin = np.array([0, 20, 70])
    upper_skin = np.array([30, 255, 255])
    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    red_mask = cv2.bitwise_and(red_mask, cv2.bitwise_not(skin_mask))

    # --- 3️⃣ Clean mask noise ---
    kernel = np.ones((5, 5), np.uint8)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
    red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_DILATE, kernel)

    # --- 4️⃣ Compute red area ratio ---
    red_area = np.sum(red_mask > 0)
    total_area = frame.shape[0] * frame.shape[1]
    red_ratio = red_area / total_area

    # --- 5️⃣ Brightness-adaptive sensitivity ---
    brightness = np.mean(hsv[:, :, 2]) / 255.0
    sensitivity_boost = 1.0 if brightness > 0.6 else 1.3
    adj_conf = red_ratio * sensitivity_boost

    # --- 6️⃣ Smooth confidence over frames ---
    CONF_HISTORY.append(adj_conf)
    avg_conf = np.mean(CONF_HISTORY)

    # --- 7️⃣ Debug overlays ---
    h, w, _ = frame.shape
    cv2.putText(frame, f"RedRatio={avg_conf:.3f}", (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imshow("Red Mask", red_mask)

    # --- 8️⃣ Trigger detection event ---
    if avg_conf > cfg["detection"]["bleeding_conf"]:
        print(f"🚨 Detected bleeding! ratio={avg_conf:.3f}")

        contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            M = cv2.moments(c)
            if M["m00"] != 0:
                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                norm_coords = (cx / w, cy / h)
                return DetectionEvent(
                    type="bleeding",
                    confidence=round(avg_conf, 2),
                    coords=norm_coords,
                    frame_id=frame_id
                )

    return None
