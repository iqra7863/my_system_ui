import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Camera not opening")
    exit()

print("✅ Camera opened successfully")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Frame not reading")
        break

    # Show frame
    cv2.imshow("Camera Test", frame)

    # Press ESC to exit
    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
