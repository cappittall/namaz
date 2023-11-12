import cv2
import time

# Try changing camera index to 0
cap = cv2.VideoCapture(0)  

while cap.isOpened():
    ret, im = cap.read()
    
    if ret:
        cv2.putText(im, f'{time.time()}', (10,30), cv2.FONT_HERSHEY_COMPLEX, 1.0, (255,0,0), 1)
        cv2.imshow('Baslik', im)
    else:
        print("Failed to read frame")
        break

    key = cv2.waitKey(1)
    print(key)
    if key == 27:  # ASCII for ESC
        break

cap.release()
cv2.destroyAllWindows()