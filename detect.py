import argparse
import time
from pathlib import Path
import pyttsx3
import cv2
import torch
import torch.backends.cudnn as cudnn
import threading

from flask import Flask, request
from numpy import random

from models.experimental import attempt_load
from utils.datasets import LoadStreams, LoadImages
from utils.general import check_img_size, check_requirements, check_imshow, non_max_suppression, apply_classifier, \
    scale_coords, xyxy2xywh, strip_optimizer, set_logging, increment_path
from utils.plots import plot_one_box
from utils.torch_utils import select_device, load_classifier, time_synchronized

engine = pyttsx3.init()
voice = engine.getProperty('voices') #get the available voices
# eng.setProperty('voice', voice[0].id) #set the voice to index 0 for male voice
engine.setProperty('voice', voice[0].id) #changing voice to index 1 for female voice


class Detect:
    def __init__(self):
       self.opt = argparse.Namespace(agnostic_nms=False, 
                                     augment=False, 
                                     classes=None, 
                                     conf_thres=0.25, 
                                     device='',
                                     exist_ok=False, 
                                     img_size=640, 
                                     iou_thres=0.45, 
                                     name='test/exp', 
                                     nosave=False,
                                     project='', 
                                     save_conf=False, 
                                     save_txt=False, 
                                     source='',
                                     update=False, 
                                     view_img=False, 
                                     weights='', 
                                     read = False)
       self.width_in_rf = 0
       self.label = ''
       self.KNOWN_DISTANCE = 25.0
       self.PERSON_WIDTH = 40
       self.MOBILE_WIDTH = 3.0
       self.CONFIDENCE_THRESHOLD = 0.4
       self.NMS_THRESHOLD = 0.3
       self.distance = 0
       self.haptics = 'off'
       engine.stop()
    
    def focalLength(self, width_in_rf):
        focal_length = (width_in_rf * self.KNOWN_DISTANCE) / self.PERSON_WIDTH
      
        return focal_length
   
    def get_haptics(self):
        return self.haptics
    
    def distanceEstimate(self, focal_length, width_in_rf):
        distance = (focal_length * self.KNOWN_DISTANCE) / width_in_rf
        
        # convert inches to feet
        distance = distance / 100
        
        return distance
    
    
    def detect(self, save_img=False):
        source, weights, view_img, save_txt, imgsz = self.opt.source, self.opt.weights, self.opt.view_img, self.opt.save_txt, self.opt.img_size
        save_img = not self.opt.nosave and not source.endswith('.txt')  # save inference images
        webcam = source.isnumeric() or source.endswith('.txt') or source.lower().startswith(
            ('rtsp://', 'rtmp://', 'http://', 'https://'))
    
        
        # Directories
        save_dir = Path(increment_path(Path(self.opt.project) / self.opt.name, exist_ok=self.opt.exist_ok))  # increment run
        (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

        # Initialize
        set_logging()
        device = select_device(self.opt.device)
        half = device.type != 'cpu'  # half precision only supported on CUDA

        # Load model
        model = attempt_load(weights, map_location=device)  # load FP32 model
        stride = int(model.stride.max())  # model stride
        imgsz = check_img_size(imgsz, s=stride)  # check img_size
        if half:
            model.half()  # to FP16

        # Second-stage classifier
        classify = False
        if classify:
            modelc = load_classifier(name='resnet101', n=2)  # initialize
            modelc.load_state_dict(torch.load('weights/resnet101.pt', map_location=device)['model']).to(device).eval()

        # Set Dataloader
        vid_path, vid_writer = None, None
        if webcam:
            view_img = check_imshow()
            cudnn.benchmark = True  # set True to speed up constant image size inference
            dataset = LoadStreams(source, img_size=imgsz, stride=stride)
        else:
            dataset = LoadImages(source, img_size=imgsz, stride=stride)

        # Get names and colors
        names = model.module.names if hasattr(model, 'module') else model.names
        colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

        # Run inference
        if device.type != 'cpu':
            model(torch.zeros(1, 3, imgsz, imgsz).to(device).type_as(next(model.parameters())))  # run once
        t0 = time.time()
        for path, img, im0s, vid_cap in dataset:
            img = torch.from_numpy(img).to(device)
            img = img.half() if half else img.float()  # uint8 to fp16/32   
            img /= 255.0  # 0 - 255 to 0.0 - 1.0
            if img.ndimension() == 3:
                img = img.unsqueeze(0)
            
            # Inference
            t1 = time_synchronized()
            pred = model(img, augment=self.opt.augment)[0]

            # Apply NMS
            pred = non_max_suppression(pred, self.opt.conf_thres, self.opt.iou_thres, classes=self.opt.classes, agnostic=self.opt.agnostic_nms)
            t2 = time_synchronized()

            # Apply Classifier
            if classify:
                pred = apply_classifier(pred, modelc, img, im0s)

        
            # Process detections
            for i, det in enumerate(pred):  # detections per image
                if webcam:  # batch_size >= 1
                    p, s, im0, frame = path[i], '%g: ' % i, im0s[i].copy(), dataset.count
                else:
                    p, s, im0, frame = path, '', im0s, getattr(dataset, 'frame', 0)

                p = Path(p)  # to Path
                save_path = str(save_dir / p.name)  # img.jpg
                txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # img.txt
                s += '%gx%g ' % img.shape[2:]  # print string
                
                gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
                if len(det):
                    # Rescale boxes from img_size to im0 size
                    detected_classes = []
                    detected_distance = []
                    detected_area = []
                    det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()

                    # Print results
                    for c in det[:, -1].unique():
                        n = (det[:, -1] == c).sum()  # detections per class
                        s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                    # Write results
                    for *xyxy, conf, cls in reversed(det):
                        if save_txt:  # Write to file
                            xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf) if self.opt.save_conf else (cls, *xywh)  # label format
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img or view_img:  # Add bbox to image
                            label = f'{names[int(cls)]} {conf:.2f}'
                            # get the width and height of the bounding box
                            self.width_in_rf = xyxy[2] - xyxy[0]
                            # Get the x-coordinate of the center of the bounding box
                            bbox_center = (xyxy[0] + xyxy[2]) / 2
                            # Get the x-coordinate of the center of the image
                            image_center = im0.shape[1] / 2

                            # Determine if the bounding box is on the left, center, or right of the image
                            if bbox_center < image_center - 50:
                                positionInFrame = "left"
                                detected_area.append("left")
                            elif bbox_center > image_center + 50:
                                positionInFrame = "right"
                                detected_area.append("right")
                            else:
                                positionInFrame = "center"
                                detected_area.append("center")
                            # urlPos = "http://127.0.0.1:5000/api/haptics/" + positionInFrame
                            # print(urlPos)
                            # response = request.get("http://127.0.0.1:5000/api/haptics/" + positionInFrame)
                            # print (response.text)
                            self.label = f'{names[int(cls)]} {int(cls)}'
                            # print width
                            # print(f'width: {self.width_in_rf} label: {self.label}')
                            
                            if (self.opt.read == False):
                                
                                if names[int(cls)] == 'person':
                                    self.distance = self.distanceEstimate(focal_person, self.width_in_rf)
                                elif names[int(cls)] == 'dog':
                                    self.distance = self.distanceEstimate(focal_phone, self.width_in_rf)
                                
                                if self.distance < 4:
                                    # set colors to red
                                    if self.distance < 2:
                                        detected_classes.append(names[int(cls)])
                                        detected_distance.append(self.distance)
                                        label = f'{names[int(cls)]} {conf:.2f} {self.distance:.2f} meters'
                                        colors[int(cls)] = [0, 0, 255]
                                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)
                                    else:
                                      #  detected_classes.append(names[int(cls)])
                                        # detected_distance.append(self.distance)
                                        label = f'{names[int(cls)]} {conf:.2f} {self.distance:.2f} meters'
                                        colors[int(cls)] = [0, 255, 0]
                                        plot_one_box(xyxy, im0, label=label, color=colors[int(cls)], line_thickness=1)
                                

                    # Construct detected_string
                    distance_strings = [f"too close to you" if distance < 3 else f"{round(float(distance), 1)} meters away" for distance in detected_distance]
                    position_strings = ["on your left side" if detected_area[i] == 'left' else "ahead of you" if detected_area[i] == 'center' else "on your right side" for i in range(len(detected_area))]

                    detected_string = ", ".join([f"{clazz} {distance_strings[i]} {position_strings[i]}" for i, clazz in enumerate(detected_classes)])
                    
                    # Construct speech output
                    if len(detected_classes) == 1:
                        speech = f"{detected_string}."
                    else:
                        speech = f"{detected_string}."
                  #      speech = ""
                    print(f'Speech: {speech}')

                    # Start a new thread to run the speak_warning function
                    
                    if len(detected_distance) > 0:
                        tts_thread = threading.Thread(target=self.speak_warning, args=(speech,))
                        tts_thread.start()
                          
                # Print time (inference + NMS)
                # print(f'{s}Done. ({t2 - t1:.3f}s)')``

                # Stream results
                if view_img:
                    cv2.imshow(str(p), im0)
                    cv2.waitKey(1)  # 1 millisecond
                    
                key= cv2.waitKey(1)
                if key == ord('q'):
                    engine.stop()
                    break

                # Save results (image with detections)
                if save_img:
                    if dataset.mode == 'image':
                        cv2.imwrite(save_path, im0)
                    else:  # 'video' or 'stream'
                        if vid_path != save_path:  # new video
                            vid_path = save_path
                            if isinstance(vid_writer, cv2.VideoWriter):
                                vid_writer.release()  # release previous video writer
                            if vid_cap:  # video
                                fps = vid_cap.get(cv2.CAP_PROP_FPS)
                                w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            else:  # stream
                                fps, w, h = 30, im0.shape[1], im0.shape[0]
                                save_path += '.mp4'
                            vid_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                        vid_writer.write(im0)

        if save_txt or save_img:
            s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
            print(f"Results saved to {save_dir}{s}")
            
        print(f'Done. ({time.time() - t0:.3f}s)')

    def speak_warning(self, str):
        if not engine._inLoop:
            engine.say(str)
            engine.runAndWait()
            
    
    def config(self, weights, source, classes, read, view_img):
        self.opt.weights = weights
        self.opt.source = source
        self.opt.classes = classes
        self.opt.read = read
        self.opt.view_img = view_img
        
    def parse_opt(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', nargs='+', type=str, default='weights/v5lite-s.pt', help='model.pt path(s)')
        parser.add_argument('--source', type=str, default='sample', help='source')  # file/folder, 0 for webcam
        parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=0.45, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.5, help='IOU threshold for NMS')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--view-img', action='store_true', help='display results')
        parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
        parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
        parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--update', action='store_true', help='update all models')
        parser.add_argument('--project', default='runs/detect', help='save results to project/name')
        parser.add_argument('--name', default='exp', help='save results to project/name')
        parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
        parser.add_argument('--read', action='store_true')
        self.opt = parser.parse_args()
        print(self.opt)
        check_requirements(exclude=('pycocotools', 'thop'))

        with torch.no_grad():
            if self.opt.update:  # update all models (to fix SourceChangeWarning)
                for self.opt.weights in ['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt']:
                    self.detect()
                    strip_optimizer(self.opt.weights)
            else:
                self.detect()



focal_person = None
focal_phone = None  

def inference(): 
    global focal_person, focal_phone               
    detect = Detect()

    detect.config('weights/v5lite-g.pt', 'ref/50.jpg', 0, True, False)

    detect.detect()

    person, plabel = detect.width_in_rf, detect.label

    detect.config('weights/v5lite-g.pt', 'ref/dog50.jpg', 16, True, False)

    detect.detect()

    phone, phLabel = detect.width_in_rf, detect.label

    print(f'{plabel}: {person} | {phLabel}: {phone}')

    focal_person = detect.focalLength(person)
    focal_phone = detect.focalLength(phone)

    print(f'focal length of person: {focal_person} | focal length of phone: {focal_phone}')

    detect.config('weights/v5lite-s.pt', 'http://192.168.100.224:8080/video', [0,17], False, False)

    detect.detect()
    print(detect.get_haptics())
