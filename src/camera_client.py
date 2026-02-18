import cv2

# URL of the video feed
VIDEO_URL = 'http://192.168.222.178:5000/video_feed'  # replace with server IP if remote

# Open the video stream
cap = cv2.VideoCapture(VIDEO_URL)

if not cap.isOpened():
    print("Failed to connect to video feed")
    exit(1)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    # Display the frame
    cv2.imshow('Camera Feed', frame)

    # Exit on 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
