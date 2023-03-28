# import cv2 as cv 
# import numpy as np
# from detect import Detect
# import os

# class DistanceEstimation:
   
#    def __init__(self):

      
  
   

# detect = Detect()

# opt = detect.opt

# opt.view_img = False

# opt.weights = 'weights/v5lite-s.pt'

     
# frame_count = 0

# cap = cv.VideoCapture(0)

# while True:
#    _, frame = cap.read()
 
#     # convert the frame to JPEG format
#    jpeg_img = cv.imencode('.jpg', frame)[1].tostring()

#     # save the frame as a JPEG image to the directory
#    filename = f"frame{frame_count}.jpg"
#    with open(f"captured_frames/{filename}", 'wb') as f:
#       f.write(jpeg_img)

#    # display the captured frame in a window
#    cv.imshow('Captured Frame', frame)
   
#    opt.source = f"captured_frames/{filename}"
   
#    detect.detect()
   
#    # delete the image file
#    os.remove(f"captured_frames/{filename}")
#    print("delete")
#    # exit the loop if the user presses the 'q' key
#    if cv.waitKey(1) & 0xFF == ord('q'):
#       break

#    # increment the frame counter
#    frame_count += 1
   
# cap.release()
# cv.destroyAllWindows()

