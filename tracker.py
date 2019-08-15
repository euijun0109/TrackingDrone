from djitellopy import Tello
from imutils.video import VideoStream
import time
import argparse
import cv2
import imutils

#HSV Values
greenLower = (25, 75, 85)
greenUpper = (50, 220, 255)

#ambient light green
agreenLower = (27, 140, 101)
agreenUpper = (33, 255, 255)

#size 600(x) x 450(y)
class Track(object):
    def __init__(self):
        self.tello = Tello()
        self.tello.connect()
        self.forBack = 0
        self.turn = 0
        self.upDown = 0
        self.leftRight = 0
        self.speed = 20
        self.airborne = False

    def push(self):
        if self.airborne:
            self.tello.send_rc_control(self.leftRight, self.forBack, self.upDown, self.turn)

    def run(self):
        self.tello.streamoff()
        self.tello.streamon()
        frame_read = self.tello.get_frame_read()

        takeover = False
        self.airborne = False
        count = 0
        while True:
            self.push()
            self.forBack = 0
            self.upDown = 0
            self.leftRight = 0
            self.turn = 0
            frameOri = cv2.cvtColor(frame_read.frame, cv2.COLOR_BGR2RGB)
            frame = frame_read.frame

            if frame is None:
                break

            frame = imutils.resize(frame, width=600)
            blurred = cv2.GaussianBlur(frame, (11, 11), 0)
            hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

            mask = cv2.inRange(hsv, agreenLower, agreenUpper)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)

            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
            cnts = imutils.grab_contours(cnts)
            center = None

            if len(cnts) > 0 and self.airborne:
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if x > 300:
                    self.turn = int(self.speed + 10)
                elif x < 300:
                    self.turn = -int(self.speed + 10)
                if y > 225:
                    self.upDown = -int(self.speed + 5)
                elif y < 225:
                    self.upDown = int(self.speed + 5)
                if radius > 30:
                    self.forBack = -int(self.speed - 5)
                elif radius < 30:
                    self.forBack = int(self.speed - 5)

                if radius > 1:
                    cv2.circle(frame, (int(x), int(y)), int(radius),
                               (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)

            cv2.imshow("Frame", frame)
            k = cv2.waitKey(20)
            count += 1

            if count % 100 == 0:
                self.tello.get_battery()

            if k == ord("t"):
                print("Taking off")
                self.tello.takeoff()
                self.airborne = True

            if k == 27:
                print("Quitting")
                break

            #backspacetlt
            if k == 8:
                if not takeover:
                    takeover = True
                    print("Takeover enabled")
                else:
                    takeover = False
                    print("Takeover disabled")

            if k == ord("l"):
                print("Landing")
                self.tello.land()
                self.airborne = False

            if takeover:
                # S & W to fly forward & back
                if k == ord('w'):
                    self.forBack = int(self.speed)
                elif k == ord('s'):
                    self.forBack = -int(self.speed)
                else:
                    self.forBack = 0

                # a & d to pan left & right
                if k == ord('d'):
                    self.turn = int(self.speed)
                elif k == ord('a'):
                    self.turn = -int(self.speed)
                else:
                    self.turn = 0

                # Q & E to fly up & down
                if k == ord('e'):
                    self.upDown = int(self.speed)
                elif k == ord('q'):
                    self.upDown = -int(self.speed)
                else:
                    self.upDown = 0

                # c & z to fly left & right
                if k == ord('c'):
                    self.leftRight = int(self.speed)
                elif k == ord('z'):
                    self.leftRight = -int(self.speed)
                else:
                    self.leftRight = 0

        cv2.destroyAllWindows()
        self.tello.end()

def main():
    track = Track()
    track.run()

if __name__ == '__main__':
    main()