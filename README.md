# Changes

CCTV - Delayed real-time object detection the more time we run the model the more it delays.
Fix: https://github.com/ultralytics/yolov5/issues/4465#issuecomment-1113038325

datasets.py:362 comment  time.sleep(1 / self.fps[i]) # wait time

Fix the rotation augmentation of the image using roboflow
* first we augment the images we annotate using roboflow including rotation augmentation after the augmentation we notice that the bounding box expanded that's why we decided to not use the rotation augmentation.

Forked from ppogg - here is the repo: https://github.com/ppogg/YOLOv5-Lite