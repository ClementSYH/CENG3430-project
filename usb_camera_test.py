
# for Jetson Nano USB Camera Test
import cv2

if __name__ == "__main__":
  
    cap = cv2.VideoCapture(1)
  
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow('USB Camera', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()