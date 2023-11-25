import cv2

# Test each video device
for i in range(0, 11):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"Cihaz {i} Çalışıyot")
        cap.release()
    else:
        print(f"Cihaz {i} Çalışmıyor")