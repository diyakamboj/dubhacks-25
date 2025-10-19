import asyncio, cv2, json, websockets, yaml
from detectors.choking import detect_choking
from detectors.bleeding import detect_bleeding
from detectors.unresponsive import detect_unresponsive

# Load config
with open("config.yaml") as f:
    cfg = yaml.safe_load(f)

SEND_INTERVAL = 0.7  # smoother async performance
last_event_type = None

EVENT_PRIORITY = {
    "unresponsive": 3,
    "bleeding": 2,
    "choking": 1
}

async def send_events():
    uri = "ws://localhost:8765"
    print("📡 Starting prioritized CV stream...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

    if not cap.isOpened():
        print("❌ Camera not found.")
        return

    frame_id = 0
    global last_event_type

    async with websockets.connect(uri) as ws:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Frame capture failed.")
                break

            # Run all detectors
            results = []
            for detector in [detect_choking, detect_bleeding, detect_unresponsive]:
                evt = detector(frame, cfg, frame_id)
                if evt:
                    results.append(evt)

            event = None
            if results:
                event = max(results, key=lambda e: EVENT_PRIORITY.get(e.type, 0))

            # Prepare HUD text
            hud_lines = [f"Frame: {frame_id}"]
            if event:
                status = f"🚨 {event.type.upper()} ({event.confidence:.2f})"
                color = (0, 0, 255)
            else:
                status = "✅ Normal"
                color = (0, 255, 0)
            hud_lines.append(status)

            # Render HUD cleanly (top-left info)
            y = 40
            for line in hud_lines:
                cv2.putText(frame, line, (20, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                y += 30

            # --- Show all detector confidences neatly (bottom-left info) ---
            h, w, _ = frame.shape
            y0 = h - 100  # start near bottom
            dy = 25       # spacing between lines

            # if you track detector confidences, replace cfg thresholds with actual values
            cv2.putText(frame, f"Choking Conf: {cfg['detection']['choking_conf']:.2f}", (20, y0),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            cv2.putText(frame, f"Bleeding Conf: {cfg['detection']['bleeding_conf']:.2f}", (20, y0 + dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            cv2.putText(frame, f"Unresponsive Conf: {cfg['detection']['unresponsive_conf']:.2f}", (20, y0 + 2*dy),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

            cv2.imshow("AR Emergency CV Stream", frame)

            # Send websocket event
            if event and (event.type != last_event_type):
                msg = json.dumps({
                    "type": event.type,
                    "confidence": event.confidence,
                    "coords": event.coords,
                    "frame_id": event.frame_id,
                    "priority": EVENT_PRIORITY[event.type]
                })
                await ws.send(msg)
                print(f"📤 Sent event: {msg}")
                last_event_type = event.type

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            await asyncio.sleep(SEND_INTERVAL)
            frame_id += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    asyncio.run(send_events())
