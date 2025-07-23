import cv2
import numpy as np

def nothing(x): pass

cv2.namedWindow("Trackbars")

cv2.createTrackbar("H_min", "Trackbars", 0, 180, nothing)
cv2.createTrackbar("S_min", "Trackbars", 0, 255, nothing)
cv2.createTrackbar("V_min", "Trackbars", 170, 255, nothing)
cv2.createTrackbar("H_max", "Trackbars", 180, 180, nothing)
cv2.createTrackbar("S_max", "Trackbars", 255, 255, nothing)
cv2.createTrackbar("V_max", "Trackbars", 255, 255, nothing)

# 0 0 170

while True:
    image = cv2.imread("seal.png") 
    # image = cv2.medianBlur(image, 5)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(
        hsv_image,
        np.array([
            cv2.getTrackbarPos("H_min", "Trackbars"),
            cv2.getTrackbarPos("S_min", "Trackbars"),
            cv2.getTrackbarPos("V_min", "Trackbars"),
        ]),
        np.array([
            cv2.getTrackbarPos("H_max", "Trackbars"),
            cv2.getTrackbarPos("S_max", "Trackbars"),
            cv2.getTrackbarPos("V_max", "Trackbars"),
        ]),
    )
    _mask = mask.copy()
    mask = cv2.cvtColor(255-mask, cv2.COLOR_GRAY2BGR)

    processed = cv2.bitwise_not(mask, image, mask=_mask)
    output = cv2.bitwise_and(image, mask)

    cv2.imshow('processed', processed)
    cv2.imshow("Trackbars", output)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
