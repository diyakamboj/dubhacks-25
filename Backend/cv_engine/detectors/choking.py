import cv2
import mediapipe as mp
import numpy as np
from schemas import DetectionEvent
import yaml
import time

# Initialize Mediapipe pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

def detect_choking(frame, cfg, frame_id):
    """
    Detects choking based on hand-to-neck proximity using MediaPipe landmarks.
    Returns DetectionEvent or None.
    """
    results = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    if not results.pose_landmarks:
        return None

    landmarks = results.pose_landmarks.landmark

    # Key body points
    l_hand = np.array([landmarks[mp_pose.PoseLandmark.LEFT_WRIST].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_WRIST].y])
    r_hand = np.array([landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].x,
                       landmarks[mp_pose.PoseLandmark.RIGHT_WRIST].y])
    neck   = np.array([landmarks[mp_pose.PoseLandmark.NOSE].x,
                       landmarks[mp_pose.PoseLandmark.NOSE].y])

    # Measure distance from both hands to neck
    lh_dist = np.linalg.norm(l_hand - neck)
    rh_dist = np.linalg.norm(r_hand - neck)

    # Calculate confidence inversely (closer hands = higher confidence)
    conf = max(0, 1 - (lh_dist + rh_dist))
    if conf > cfg["detection"]["choking_conf"]:
        h, w, _ = frame.shape
        cx, cy = int(neck[0]*w), int(neck[1]*h)
        return DetectionEvent(
            type="choking",
            confidence=round(conf, 2),
            coords=(cx, cy),
            frame_id=frame_id
        )
    return None