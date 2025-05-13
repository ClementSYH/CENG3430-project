import cv2
import numpy as np
from pynq.lib.video import *

# === Initialize video input (assuming USB camera via OpenCV) ===
cap = cv2.VideoCapture(0)  # Adjust index if needed

if not cap.isOpened():
    raise IOError("Cannot open camera")

print("Camera initialized.")

# === Parameters ===
history_length = 10  # Number of frames to track movement
centroid_history = []

fgbg = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=50)

def get_hand_centroid(frame):
    """Detect hand and return the centroid of the largest contour."""
    # Convert to HSV for better color segmentation
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define skin color range in HSV
    lower_skin = np.array([0, 30, 60], dtype=np.uint8)
    upper_skin = np.array([20, 180, 255], dtype=np.uint8)

    fgmask = fgbg.apply(frame)
    
    # Threshold the HSV image to get only skin colors
    mask = cv2.inRange(hsv, lower_skin, upper_skin)

    # Apply morphological operations to filter noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (5, 5), 100)

    # Compatible with OpenCV 3.x (used in many PYNQ builds)
    _, contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    if contours:
        # Find the largest contour
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 1000:
            return None  # Ignore small movements

        # Calculate centroid
        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        return (cx, cy)
    return None

def get_direction(history):
    """Determine direction of movement based on centroid history."""
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
    print("Starting hand direction detection... (Press Ctrl+C to stop)")
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Flip image for natural mirror view
        frame = cv2.flip(frame, 1)

        # Resize for performance (optional)
        frame = cv2.resize(frame, (320, 240))

        # Detect hand and get centroid
        centroid = get_hand_centroid(frame)
        if centroid:
            centroid_history.append(centroid)
            if len(centroid_history) > history_length:
                centroid_history.pop(0)

            # Draw centroid on frame
            cv2.circle(frame, centroid, 5, (0, 255, 0), -1)

            # Detect direction
            direction = get_direction(centroid_history)
            if direction:
                print(f"Hand Direction: {direction}")
                # Optionally draw direction text
                cv2.putText(frame, direction, (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

        # Display the processed frame (in a Jupyter-compatible way)
        _, jpeg = cv2.imencode('.jpg', frame)
        from IPython.display import display, Image, clear_output
        clear_output(wait=True)
        display(Image(data=jpeg.tobytes()))

except KeyboardInterrupt:
    print("Stopped by user.")

finally:
    cap.release()
