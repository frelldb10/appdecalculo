import cv2
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1, detectionCon=0.8)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    hands, img = detector.findHands(img)

    if hands:
        mano1 = hands[0]
        dedos = detector.fingersUp(mano1)
        total_dedos = dedos.count(1)
        cv2.putText(img, f'Dedos: {total_dedos}', (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)

    cv2.imshow("Prueba de Camara", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()