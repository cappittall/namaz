
import cv2
import time

cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, im = cap.read()
    
    cv2.putText(im, f'{time.time()}', (10,30), cv2.FONT_HERSHEY_COMPLEX, 1.0, (255,0,0), 1)
    cv2.imshow('Baslik', im)
    
    key = cv2.waitKey(1)
    print(key)
    if key == 27:
        break
    
cap.release()
cv2.destroyAllWindows()