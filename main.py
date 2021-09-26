import numpy as np
import cv2
import imutils
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import QMenu
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import json
import sys
from threadproc import *
from util import *
from track import *
import pandas as pd


class Ui(QtWidgets.QDialog):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('main.ui', self)
        self.setMaximumWidth(self.width())
        self.setMaximumHeight(self.height())
        self.is_start = False
        self.btn_open.clicked.connect(self.clicked_open_btn)
        self.btn_proc.clicked.connect(self.clicked_proc_btn)

        self.show()
        self.width = self.lbl_screen.geometry().width()
        self.height = self.lbl_screen.geometry().height()
        self.roi_points = []

        self.info_drop = [0, 0, 0]
        self.info_width = [10000, 0, 0]
        self.info_height = [10000, 0, 0]
        self.info_area = [100000, 0, 0]
        self.output_file = ""
        self.widths = []
        self.heights = []
        self.areas = []

    def clicked_open_btn(self):
        if self.is_start:
            return
        try:
            src_file_name = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', './',
                                                                  filter="MP4 File(*.mp4);;AVI File(*.avi);;All Files(*.*)")[0]
            if (src_file_name is None or src_file_name == ""):
                msg = QtWidgets.QMessageBox(self)
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Warning")
                msg.setInformativeText('There are no any Video File in the Selected Directory.')
                msg.setWindowTitle("Warning")
                msg.exec_()
            else:
                alarm = "Video : " + src_file_name
                self.lbl_video_path.setText(alarm)
                self.src_file_name = src_file_name

                cap = cv2.VideoCapture(src_file_name)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        roi_p1 = Point(frame.shape[1] // 2, 10)
                        roi_p2 = Point(frame.shape[1] // 2, frame.shape[0] - 10)
                        self.roi_points = [roi_p1, roi_p2]
                        h, w, ch = rgbImage.shape
                        bytesPerLine = ch * w
                        image = QtGui.QImage(rgbImage.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
                        p = image.scaled(self.width, self.height, Qt.KeepAspectRatio)
                        self.lbl_screen.setPixmap(QtGui.QPixmap(p))
                        cv2.waitKey(1)
                        self.backImg = frame
                    cap.release()

                else:
                    msg = QtWidgets.QMessageBox(self)
                    msg.setIcon(QtWidgets.QMessageBox.Critical)
                    msg.setText("Warning")
                    msg.setInformativeText('Can not Open Video File.')
                    msg.setWindowTitle("Warning")
                    msg.exec_()
        except:
            print("Error in \'clicked_open_btn\'")
            exit(0)

    def clicked_proc_btn(self):
        if self.is_start:
            self.btn_proc.setText("Start")
            self.is_start = False
            # save data to csv file
            result = {"Width" : self.widths, "Height": self.heights, "Area":self.areas}
            data = pd.DataFrame.from_dict(result)
            data.to_csv(self.output_file)
            self.widths = []
            self.heights = []
            self.areas = []
            self.info_drop = [0, 0, 0]
            self.info_width = [10000, 0, 0]
            self.info_height = [10000, 0, 0]
            self.info_area = [100000, 0, 0]
            try:
                self.main_thread.is_run = False
            except:
                pass
        else:
            if self.lineEdit_output.text() == "":
                return
            self.output_file = self.lineEdit_output.text() + ".csv"
            self.btn_proc.setText("Stop")
            self.is_start = True
            self.main_thread = MainThread(self)
            self.main_thread.is_run = True
            self.main_thread.src_file = self.src_file_name
            self.main_thread.rois = self.roi_points.copy()
            self.main_thread.changePixmap.connect(self.setImage)
            self.main_thread.submitObj.connect(self.updateDropInfo)
            self.main_thread.start()

    def setImage(self, image):
        p = image.scaled(self.width, self.height, Qt.KeepAspectRatio)
        self.lbl_screen.setPixmap(QtGui.QPixmap(p))
        cv2.waitKey(1)

    def updateDropInfo(self, width, height, area, bcrystal):
        # insert data
        self.widths.append(width)
        self.heights.append(height)
        self.areas.append(area)
        # calculate mean values
        self.info_width[2] = ((self.info_width[2] * self.info_drop[0] + width) / (self.info_drop[0] + 1))
        self.info_height[2] = ((self.info_height[2] * self.info_drop[0] + height) / (self.info_drop[0] + 1))
        self.info_area[2] = ((self.info_area[2] * self.info_drop[0] + area) / (self.info_drop[0] + 1))
        if self.info_width[0] > width:
            self.info_width[0] = width
        if self.info_width[1] < width:
            self.info_width[1] = width
        if self.info_height[0] > height:
            self.info_height[0] = height
        if self.info_height[1] < height:
            self.info_height[1] = height
        if self.info_area[0] > area:
            self.info_area[0] = area
        if self.info_area[1] < area:
            self.info_area[1] = area
        self.info_drop[0] += 1
        if bcrystal:
            self.info_drop[1] += 1
        else:
            self.info_drop[2] += 1

        # show info
        self.lbl_tot_drops.setText(str(self.info_drop[0]))
        self.lbl_tot_crystal_drops.setText(str(self.info_drop[1]))
        self.lbl_tot_blank_drops.setText(str(self.info_drop[2]))

        self.lbl_min_width.setText(str(self.info_width[0]))
        self.lbl_max_width.setText(str(self.info_width[1]))
        self.lbl_aver_width.setText("{:.1f}".format(self.info_width[2]))

        self.lbl_min_height.setText(str(self.info_height[0]))
        self.lbl_max_height.setText(str(self.info_height[1]))
        self.lbl_aver_height.setText("{:.1f}".format(self.info_height[2]))

        self.lbl_min_area.setText(str(self.info_area[0]))
        self.lbl_max_area.setText(str(self.info_area[1]))
        self.lbl_aver_area.setText("{:.1f}".format(self.info_area[2]))

        self.lbl_cur_width.setText(str(width))
        self.lbl_cur_height.setText(str(height))
        self.lbl_cur_area.setText(str(area))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    app.exec_()