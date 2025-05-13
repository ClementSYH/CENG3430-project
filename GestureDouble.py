import cv2
import numpy as np
from pynq.lib.video import *

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise IOError("Cannot open camera")

print("Camera initialized.")

history_length = 10
centroid_history_1 = []
centroid_history_2 = []

fgbg = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)

def get_two_hand_centroids(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_skin = np.array([0, 30, 60], dtype=np.uint8)
    upper_skin = np.array([20, 180, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    contours = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]

    centroids = []
    if contours:
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        for cnt in contours[:2]:  # Get up to 2 largest contours
            if cv2.contourArea(cnt) < 1000:
                continue
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                centroids.append((cx, cy))
    return centroids

def get_direction(history):
    if len(history) < 2:
        return None
    dx = history[-1][0] - history[0][0]
    dy = history[-1][1] - history[0][1]
    if abs(dx) > abs(dy):
        return "Right" if dx > 40 else "Left" if dx < -40 else None
    else:
        return "Down" if dy > 40 else "Up" if dy < -40 else None

# === Main loop ===
try:
    from IPython.display import display, Image, clear_output
    print("Starting two-hand detection... (Press Ctrl+C to stop)")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (320, 240))

        centroids = get_two_hand_centroids(frame)

        if len(centroids) >= 1:
            centroid_history_1.append(centroids[0])
            if len(centroid_history_1) > history_length:
                centroid_history_1.pop(0)
            cv2.circle(frame, centroids[0], 5, (0, 255, 0), -1)  # Green dot

            dir1 = get_direction(centroid_history_1)
            if dir1:
                cv2.putText(frame, f"Hand 1: {dir1}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                print(f"Hand 1 Direction: {dir1}")

        if len(centroids) == 2:
            centroid_history_2.append(centroids[1])
            if len(centroid_history_2) > history_length:
                centroid_history_2.pop(0)
            cv2.circle(frame, centroids[1], 5, (0, 0, 255), -1)  # Red dot

            dir2 = get_direction(centroid_history_2)
            if dir2:
                cv2.putText(frame, f"Hand 2: {dir2}", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                print(f"Hand 2 Direction: {dir2}")

        _, jpeg = cv2.imencode('.jpg', frame)
        clear_output(wait=True)
        display(Image(data=jpeg.tobytes()))

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    cap.release()
