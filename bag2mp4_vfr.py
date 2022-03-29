# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 15:17:01 2021

@author: Icarus
"""

import pyrealsense2 as rs
import numpy as np
import cv2
import logging
from datetime import datetime
from time import time
import av
from fractions import Fraction


load_dir = r"C:\Users\yes\Desktop\ICS\recordcams\recs\\"
filename = "cam0_911222060790_record_24_11_2021_1408_44.bag"

save_dir = r'C:\Users\yes\Desktop\ICS\recordcams\recs\\'



pipeline = rs.pipeline()
config = rs.config()
rs.config.enable_device_from_file(config, load_dir + filename)
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)


container = av.open(save_dir+ filename[:-4]+'.mp4', mode='w')
stream = container.add_stream('mpeg4', rate=30)
stream.width = 640
stream.height = 480
stream.pix_fmt = 'yuv420p'

stream.codec_context.time_base = Fraction(1, 1000) # milliseconds time base

pipeline.start(config)

first = True
prev_ts = -1
max_frame_nb = 0

try:
    while True:

        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        frame_nb = color_frame.get_frame_number()

        if frame_nb < max_frame_nb:
            break #FIXME

        max_frame_nb = frame_nb

        ts = frames.get_timestamp()

        if first: 
            t0 = ts
            first = False

        # Convert images to numpy arrays
        depth_image_1 = np.asanyarray(depth_frame.get_data())
        color_image_1 = np.asanyarray(color_frame.get_data())

        if prev_ts >= int(ts-t0):
            continue

        frame = av.VideoFrame.from_ndarray(color_image_1, format='bgr24')
        frame.pts = int(ts-t0)

        for packet in stream.encode(frame):
            container.mux(packet)

        prev_ts = int(ts-t0)

        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap_1 = cv2.applyColorMap(cv2.convertScaleAbs(depth_image_1, alpha=0.05), cv2.COLORMAP_JET)
       
        images = np.hstack((color_image_1, depth_colormap_1))#,color_image_2, depth_colormap_2))

        # Show images from both cameras
        cv2.namedWindow('RealSense', cv2.WINDOW_NORMAL)
        cv2.imshow('RealSense', images)
        cv2.waitKey(1)

        # Save images and depth maps from both cameras by pressing 's'
        ch = cv2.waitKey(25)
            
        if ch==113: #q pressed
            break

finally:
    for packet in stream.encode():
        container.mux(packet)

    # Close the file
    container.close()

    # Stop streaming
    pipeline.stop()
    cv2.destroyAllWindows()
