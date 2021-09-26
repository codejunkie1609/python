import sys
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtCore, QtGui, QtWidgets
import cv2, numpy as np
import time
from util import *
from track import *

COLORS = [(0, 0, 255), (0, 80, 250)]
def draw_bounding_box(img, label, x, y, x_plus_w, y_plus_h, color=0, width=1, thick=4):

    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), COLORS[color], width)
    cv2.putText(img, label, (x - 10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, width, COLORS[color], thick)


def get_output_layers(classes):
    layer_names = classes.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in classes.getUnconnectedOutLayers()]
    return output_layers

def LineIntersectsRect(p1, p2, r):
    return LineIntersectsLine(p1, p2, Point(r.x, r.y), Point(r.right(), r.y))\
           or LineIntersectsLine(p1, p2, Point(r.right(), r.y), Point(r.right(), r.bottom()))\
           or LineIntersectsLine(p1, p2, Point(r.right(), r.bottom()), Point(r.x, r.bottom()))\
           or LineIntersectsLine(p1, p2, Point(r.x, r.bottom()), Point(r.x, r.y))


def LineIntersectsLine(l1p1, l1p2, l2p1, l2p2):
    q = (l1p1.y - l2p1.y) * (l2p2.x - l2p1.x) - (l1p1.x - l2p1.x) * (l2p2.y - l2p1.y)
    d = (l1p2.x - l1p1.x) * (l2p2.y - l2p1.y) - (l1p2.y - l1p1.y) * (l2p2.x - l2p1.x)

    if (d == 0):
        return False
    r = q / d
    q = (l1p1.y - l2p1.y) * (l1p2.x - l1p1.x) - (l1p1.x - l2p1.x) * (l1p2.y - l1p1.y)
    s = q / d
    if (r < 0 or r > 1 or s < 0 or s > 1):
        return False
    return True


class MainThread(QThread):
    changePixmap = pyqtSignal(QImage)
    submitObj = pyqtSignal(int, int, int, bool)   # width, height, area, crystal

    def __init__(self, parent=None):
        QThread.__init__(self, parent=parent)
        self.parent = parent
        self.src_file = None
        self.is_run = False
        self.delay = 1
        self.rois = []

        self.tracker = Tracker()

        # self.classes = ["droplet", "crystal"]
        self.load_model()

    def load_model(self):
        self.droplet_net = cv2.dnn.readNet("./model/droplet.weights", "./model/droplet.cfg")
        self.crystal_net = cv2.dnn.readNet("./model/crystal.weights", "./model/crystal.cfg")

    def process_crystal(self, image):
        scale = 0.00392

        # read pre-trained model and config file
        # create input blob
        blob = cv2.dnn.blobFromImage(image, scale, (128, 64), (0, 0, 0), True, crop=False)

        # set input blob for the network
        self.crystal_net.setInput(blob)

        # run inference through the network
        # and gather predictions from output layers
        outs = self.crystal_net.forward(get_output_layers(self.crystal_net))

        # initialization
        class_ids = []
        confidences = []
        boxes = []
        center_X = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        # for each detetion from each output layer
        # get the confidence, class id, bounding box params
        # and ignore weak detections (confidence < 0.5)
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * image.shape[1])
                    center_y = int(detection[1] * image.shape[0])
                    w = int(detection[2] * image.shape[1])
                    h = int(detection[3] * image.shape[0])
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])
                    center_X.append(center_x)

        # apply non-max suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)
        # print(boxes)
        crystals = []
        for i in indices:
            i = i[0]
            (x, y, w, h) = boxes[i]
            if w < 5 or h < 5:
                continue
            crystals.append(boxes[i])

        return crystals

    def detect_droplet(self, image):

        scale = 0.00392

        # read pre-trained model and config file
        # create input blob
        blob = cv2.dnn.blobFromImage(image, scale, (128, 128), (0, 0, 0), True, crop=False)

        # set input blob for the classeswork
        self.droplet_net.setInput(blob)

        # run inference through the classeswork
        # and gather predictions from output layers
        outs = self.droplet_net.forward(get_output_layers(self.droplet_net))

        # initialization
        class_ids = []
        confidences = []
        boxes = []
        center_X = []
        conf_threshold = 0.5
        nms_threshold = 0.4

        # for each detetion from each output layer
        # get the confidence, class id, bounding box params
        # and ignore weak detections (confidence < 0.5)
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    center_x = int(detection[0] * image.shape[1])
                    center_y = int(detection[1] * image.shape[0])
                    w = int(detection[2] * image.shape[1])
                    h = int(detection[3] * image.shape[0])
                    x = int(max(0, center_x - w / 2))
                    y = int(max(0, center_y - h / 2))

                    class_ids.append(class_id)
                    confidences.append(float(confidence))
                    boxes.append([x, y, w, h])
                    center_X.append(center_x)

        # apply non-max suppression
        indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

        new_drops = []
        for i in indices:
            i = i[0]
            (x, y, w, h) = boxes[i]
            # print(boxes[i])
            crystals = []
            if x < 10 or x + w > image.shape[1] + 5:
                continue
            if w > 10 and h > 10:
                droplet = image[y:y + h, x:x + w]
                # cv2.imshow("droplet", droplet)
                # cv2.waitKey(1)
                crystals = self.process_crystal(droplet)
                for (xx, yy, ww, hh) in crystals:
                    cv2.rectangle(image, (x + xx, y + yy), (x + xx + ww, y + yy + hh), COLORS[1], 1)
            cv2.rectangle(image, (x, y), (x + w, y + h), COLORS[0], 2)

            # create new Drop object
            drop = Drop()
            drop.detect_rect = Rect(x, y, w, h)
            drop.droplet_rect = Rect(int(x + w * .05), int(y + h * .1), int(w * .9), int(h * .8))
            drop.count_rect = Rect(int(x + w // 6), int(y + h // 6), int(w * 4 // 6), int(h * 4 // 6))
            drop.crystal_rects = crystals
            if crystals.__len__() > 0:
                drop.ncrystals = 1

            new_drops.append(drop)
        for d in self.tracker.drops:
            print(d.count_rect)

        removed_drops = self.tracker.update(new_drops)

        for drop in removed_drops:
            is_crystal = False
            if drop.ndetected > 10:
                if drop.ncrystals / drop.ndetected > .3:
                    is_crystal = True
                drop.get_final_area()
                drop.get_final_width()
                drop.get_final_height()
                self.submitObj.emit(drop.final_wdth, drop.final_hght, drop.final_area, is_crystal)





        # if new_drops.__len__() > 0:
        #     # # check small drops
        #     # lenths = []
        #     # for drop in new_drops:
        #     #     lenths.append(drop.count_rect.w)
        #     #
        #     # # check close two drops or not
        #     #
        #     #
        #     # f_drop = new_drops.pop(0)
        #     # near_drops = []
        #     # while new_drops.__len__() > 0:
        #     #     for s_drop in new_drops:
        #     #         diff = f_drop.detect_rect.dist(s_drop.detect_rect)
        #     #
        #     #         if diff < f_drop.detect_rect.w + s_drop.detect_rect.w + 10:
        #     #             # change count_rect
        #
        #     for i, _ in enumerate(new_drops):
        #         ret = LineIntersectsRect(self.rois[0], self.rois[1], new_drops[i].droplet_rect)
        #         print(ret)
        #         if ret:
        #             new_drops[i].status = 0
        #     self.tracker.update(new_drops)
        #     for i, _ in enumerate(self.tracker.drops):
        #         if self.tracker.drops[i].start_cnt:
        #             self.tracker.drops[i].get_final_area()
        #             self.tracker.drops[i].get_final_width()
        #             self.tracker.drops[i].get_final_height()
        #             is_crystal = self.tracker.drops[i].ncrystals > 7
        #             self.submitObj.emit(self.tracker.drops[i].final_wdth, self.tracker.drops[i].final_hght, self.tracker.drops[i].final_area, is_crystal)
        #             cv2.waitKey(2)
        #             self.tracker.drops[i].start_cnt = False
            # check signal
        # cv2.line(image, (self.rois[0].x, self.rois[0].y), (self.rois[1].x, self.rois[1].y), (0, 255, 255), 2)

    def run(self):
        if self.src_file is None:
            return
        cap = cv2.VideoCapture(self.src_file)
        while True:
            if not self.is_run:
                return
            ret, frame = cap.read()
            if ret:
                self.detect_droplet(frame)
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QtGui.QImage(rgbImage.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
                self.changePixmap.emit(convertToQtFormat)
                cv2.waitKey(1)
                # print("main thread")
                print(time.time())
                print()

            else:
                print("end main thread")
                break

