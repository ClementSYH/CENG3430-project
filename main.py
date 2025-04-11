import cv2
import mediapipe as mp

def detect_movement(curr_x, curr_y, prev_x, prev_y):
    movement_threshold = 20  # Tune this for sensitivity
    dx = curr_x - prev_x
    dy = curr_y - prev_y

    if abs(dx) > abs(dy):  # horizontal movement
        if dx > movement_threshold:
            return "RIGHT"
        elif dx < -movement_threshold:
            return "LEFT"
    else:  # vertical movement
        if dy > movement_threshold:
            return "DOWN"
        elif dy < -movement_threshold:
            return "UP"
    return None

def gesture_rec():
    # Initialize MediaPipe
    mp_hands = mp.solutions.hands
    mp_drawing = mp.solutions.drawing_utils
    # Track previous hand position
    prev_x, prev_y = None, None

    # Open video
    cap = cv2.VideoCapture("C:/Users/CLMNT/CENG3430_project/material.mp4")
    if not cap.isOpened():
        print("Failed to open video.")
    else:
        print("Video opened successfully.")

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as hands:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("can't read video input")
                break

            # Process frame
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Use wrist (landmark 0) as reference point
                wrist = hand_landmarks.landmark[0]
                h, w, _ = image.shape
                curr_x, curr_y = int(wrist.x * w), int(wrist.y * h)

                if prev_x is not None and prev_y is not None:
                    direction = detect_movement(curr_x, curr_y, prev_x, prev_y)
                    if direction:
                        print(f"Direction: {direction}")

                prev_x, prev_y = curr_x, curr_y

            cv2.imshow("Direction Control", image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # assume recorded video first
    gesture_rec()