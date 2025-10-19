import cv2
import mediapipe as mp
import numpy as np
from collections import deque
from schemas import DetectionEvent

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

CONF_HISTORY = deque(maxlen=10)
STILL_FRAMES = deque(maxlen=15)  # buffer for motion tracking

def detect_unresponsive(frame, cfg, frame_id):
    """
    Detects potential cardiac arrest / unresponsiveness.
    Uses body pose flatness + low motion + optional face stillness.
    Returns DetectionEvent or None.
    """

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if not results.pose_landmarks:
        CONF_HISTORY.append(0)
        return None

    landmarks = results.pose_landmarks.landmark

    # --- 1️⃣ Key body landmarks ---
    try:
        nose = np.array([landmarks[mp_pose.PoseLandmark.NOSE].x,
                         landmarks[mp_pose.PoseLandmark.NOSE].y])
        shoulders = np.array([
            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y,
            landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y])
        hips = np.array([
            landmarks[mp_pose.PoseLandmark.LEFT_HIP].y,
            landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y])
    except IndexError:
        CONF_HISTORY.append(0)
        return None

    # --- 2️⃣ Flatness heuristic: small height difference between shoulders & hips ---
    flatness = abs(np.mean(shoulders) - np.mean(hips))
    flat_conf = max(0, 1 - flatness * 4.0)  # scaled confidence for flatness

    # --- 3️⃣ Motion detection (compare frame difference) ---
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (21, 21), 0)
    STILL_FRAMES.append(gray)

    motion_score = 0
    if len(STILL_FRAMES) > 1:
        diff = cv2.absdiff(STILL_FRAMES[-1], STILL_FRAMES[0])
        motion_score = np.sum(diff > 15) / (h * w)
        motion_score = np.clip(motion_score, 0, 1)

    motion_conf = 1 - motion_score  # less motion = higher confidence

    # --- 4️⃣ Combine ---
    conf = (flat_conf * 0.6 + motion_conf * 0.4)
    CONF_HISTORY.append(conf)
    avg_conf = np.mean(CONF_HISTORY)

    # --- 5️⃣ Overlay visualization ---
    cv2.putText(frame, f"Unresponsive={avg_conf:.2f}", (20, h - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

    # --- 6️⃣ Trigger event ---
    if avg_conf > cfg["detection"]["unresponsive_conf"]:
        print(f"🚨 Detected unresponsiveness! conf={avg_conf:.2f}")
        cx, cy = int(nose[0] * w), int(nose[1] * h)
        return DetectionEvent(
            type="unresponsive",
            confidence=round(avg_conf, 2),
            coords=(cx / w, cy / h),
            frame_id=frame_id
        )

    return None
