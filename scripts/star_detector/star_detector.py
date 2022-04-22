#!/usr/bin/env python
""" Constellano Star Recognition
Python script for finding biggest and brightest stars in images and overlaying a target over them.

Command format:
    py star_detector.py <image_dir> <min_contour_area_percision>

Command example:
    py preparing_samples.py img/ 0.18
"""

import sys
import os
import cv2
import numpy as np
import math
from colorama import Fore, Back, Style

__author__ = "Marin Maslov"
__license__ = "MIT Licence"
__version__ = "1.0.1"
__maintainer__ = "Marin Maslov"
__email__ = "mmaslo00@fesb.hr"
__status__ = "Stable"

# Constants --------------------------------------- START
# USED RGB COLORS
RGB_WHITE = (255, 255, 255)
RGB_BLACK = (0, 0, 0)
RBG_GREEN = (0, 255, 0)

# USED BRIGHTNESS, CONTRAST AND GAMMA VALUES
BRIGHTNESS = 20
CONTRAST = 1.0
GAMMA = 0.2

# USED CONTOUR AREA PRECISSION
MIN_CONTOUR_AREA_PRECISION = 0.18
if(len(sys.argv) > 2):
    MIN_CONTOUR_AREA_PRECISION = float(sys.argv[2])

# USE BLUR
UNSET_MINIMUM_STARS = 0
if(len(sys.argv) > 3):
    UNSET_MINIMUM_STARS = int(sys.argv[3])

# USED MARK SIZE
MARK_SIZE_PERCENTAGE = 0.05
# Constants --------------------------------------- END

# Functions --------------------------------------- START
# GAMMA CORRECTION


def gammaCorrection(img, gamma):
    invGamma = 1 / gamma
    table = [((i / 255) ** invGamma) * 255 for i in range(256)]
    table = np.array(table, np.uint8)
    return cv2.LUT(img, table)
# Functions --------------------------------------- END


if len(sys.argv) < 2:
    print("No path to image set defined! Exiting...")
    exit()

# Algorithm --------------------------------------- START
# 'C:/Users/easmsma/Desktop/Diplomski/constellation-recognition/constellation-recognition/targets/lyra/positive/'
location = str(sys.argv[1])
output = location + 'output/'

if not os.path.exists(output) != False:
    print("Creating directory: " + output)
    os.mkdir(output)

counter = 0

for file in os.listdir(location):
    if file.endswith(".jpg"):
        new_file_name = str(output + os.path.splitext(file)[0] + "_detected.jpg")

        # READ IMAGE (RGB and BW)
        img_rgb = cv2.imread(location + file)

        # CONTRAST, BRIGHTNESS AND GAMMA CORRECTIONS
        adjusted = cv2.convertScaleAbs(img_rgb, alpha=CONTRAST, beta=BRIGHTNESS)
        adjusted = gammaCorrection(adjusted, GAMMA)

        # DENOISING
        adjusted = cv2.fastNlMeansDenoisingColored(adjusted, None, 5, 5, 2, 2)

        #if USE_BLUR == 1:
        #    ksize = (1, 1)
        #    adjusted = cv2.blur(adjusted, ksize)

        # CONVERT IMAGE TO BW
        img_bw = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

        #plt.imshow(img_bw, 'gray')
        #plt.title('stars')
        #plt.show()

        # RESIZE IMAGE
        rows, cols = img_bw.shape
        new_cols = int((1000 * cols) / rows)
        dimensions = (new_cols, 1000)
        img_bw_resized = cv2.resize(img_bw, dimensions)
        img_rgb_resized = cv2.resize(img_rgb, dimensions)

        # CREATE THRASHOLDS (STARS)
        thresholds = cv2.threshold(
            img_bw_resized, 180, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        #cv2.imshow("Input", thresholds)

        # FIND CONTURES (STARS)
        contours = cv2.findContours(
            thresholds, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

        # FIND THE GREATEST CONTOUR AREA
        contours_areas = []
        for contour in contours:
            contours_areas.append(cv2.contourArea(contour))

        # DEFINE MIN-MAX CONTOUR AREA
        contours_areas.sort(reverse=True)
        max_contour_area = contours_areas[0]
        min_contour_area = MIN_CONTOUR_AREA_PRECISION * max_contour_area  # * len(contours_areas) #
        #print("MAX: " + str(max_contour_area) + " MIN: " + str(min_contour_area))

        # TRIM CONTOURS BY MIN-MAX CONTOUR AREA
        trimmed_contours = []
        trimmed_contours_areas = []
        for contour in contours:
            if min_contour_area <= float(cv2.contourArea(contour)) <= max_contour_area:
                trimmed_contours_areas.append(cv2.contourArea(contour))
                trimmed_contours.append(contour)

        # THERE SHOULD BE A MINIMUM OF 10 STARS
        if len(trimmed_contours) < 10 and UNSET_MINIMUM_STARS != 0:
            while len(trimmed_contours) <= 10:
                min_contour_area = round(min_contour_area - 0.1, 2)
                trimmed_contours = []
                trimmed_contours_areas = []
                for contour in contours:
                    if min_contour_area <= cv2.contourArea(contour) <= max_contour_area:
                        trimmed_contours_areas.append(cv2.contourArea(contour))
                        trimmed_contours.append(contour)

        # IF ENABLED REMOVE ALL CONTOURS BUT THE FIRST <NUMBER OF CONTOURES> IN LIST
        """
        contours_areas = []
        for contour in trimmed_contours:
            contours_areas.append(cv2.contourArea(contour))
        contours_areas.sort(reverse=True)

        new_trimmed_contours = []
        if MAX_NUMBER_OF_CONTOURES != 0:
            while len(trimmed_contours) >= MAX_NUMBER_OF_CONTOURES:
                for i in range(0, MAX_NUMBER_OF_CONTOURES - 1):
                    for contour in trimmed_contours:
                        if contours_areas[i] == cv2.contourArea(contour):
                            print("USLO")
                            new_trimmed_contours.append(contour)
        trimmed_contours = new_trimmed_contours
        """

        # SELECT DIMENSIONS FOR THE MARK
        current_file_name = __file__.replace("\\", "/").split("/")[-1]
        current_file_parent_directory = __file__.replace(current_file_name, "")
        mark_path = current_file_parent_directory + '/img/target.png'
        mark = cv2.imread(mark_path)
        mark_dimensions = int(math.ceil(dimensions[1] * MARK_SIZE_PERCENTAGE))
        mark_dimensions_offset = int(
            math.ceil(mark_dimensions/2 - 0.15*mark_dimensions))
        mark_resized = cv2.resize(mark, (mark_dimensions, mark_dimensions))

        print("[INFO]" + "\tDetected: " + str(len(trimmed_contours)) + " in file: " + str(file) + " saving output to: " + new_file_name)
        #trimmed_contours_areas.sort(reverse=True)
        #print(trimmed_contours_areas)

        mark_rgba_resized = cv2.cvtColor(mark_resized, cv2.COLOR_RGB2RGBA)
        img_rgba_resized = cv2.cvtColor(img_rgb_resized, cv2.COLOR_RGB2RGBA)

        for trimmed_cnt in trimmed_contours:
            x, y, w, h = cv2.boundingRect(trimmed_cnt)

            x_offset = x - mark_dimensions_offset
            y_offset = y - mark_dimensions_offset

            x_end = x_offset + mark_dimensions
            y_end = y_offset + mark_dimensions

            """
            THERE ARE 6 POSSIBLE SCENARIOS FOR OVERFLOW
            (ACTUALLY THERE ARE MORE, BUT THE OPTIONS WHERE THE MARK WILL OVERFLOW THE WHOLE,
            OR AT LAST GREATER PARTS OF THE IMAGE CAN BE IGNORED AS THE MARK SIZE IS:
            MARK_SIZE_PERCENTAGE × 'the greater dimension of the image')
            1. At the START for x OR y                  - NAPISANO
            2. At the END for x OR y                    - NAPISANO
            3. At the START for x AND y
            4. At the END for x AND y
            5. At the START for x AND END for y
            6. At the END for x AND START for y
            """

            # 3. At the START for x AND y
            if x_offset < 0 and y_offset < 0:
                mark_cropped = mark_rgba_resized[abs(
                    y_offset): mark_dimensions, abs(x_offset): mark_dimensions]
                img_rgba_resized[0: y_end, 0: x_end] = mark_cropped

            # 4. At the END for x AND y
            elif x_end > dimensions[0] and y_end > dimensions[1]:
                mark_cropped = mark_rgba_resized[0: mark_dimensions - (
                    y_end - dimensions[1]), 0: mark_dimensions - (x_end - dimensions[0])]
                img_rgba_resized[y_offset: dimensions[1], x_offset: dimensions[0]] = mark_cropped

            # 5. and 6.
            elif (x_offset < 0 or y_offset < 0) and (x_end > dimensions[0] or y_end > dimensions[1]):
                # 5. At the START for x AND END for y
                if x_offset < 0 and y_end > dimensions[1]:
                    mark_cropped = mark_rgba_resized[0: mark_dimensions - (
                        y_end - dimensions[1]), abs(x_offset): mark_dimensions]
                    img_rgba_resized[y_offset: dimensions[1], 0: x_end] = mark_cropped

                # 6. At the END for x AND START for y
                if y_offset < 0 and x_end > dimensions[0]:
                    mark_cropped = mark_rgba_resized[abs(
                        y_offset): mark_dimensions, 0: mark_dimensions - (x_end - dimensions[0])]
                    img_rgba_resized[0: y_end, x_offset: dimensions[0]] = mark_cropped
            # 2. At the END for x OR y  POPRAVI KOMENTARE
            elif (x_end > dimensions[0] or y_end > dimensions[1]) and not (x_offset < 0 or y_offset < 0):
                if x_end > dimensions[0] or y_end > dimensions[1]:
                    if x_end > dimensions[0]:
                        mark_cropped = mark_rgba_resized[0:mark_dimensions, 0: mark_dimensions - (x_end - dimensions[0])]
                        img_rgba_resized[y_offset: y_end, x_offset: dimensions[0]] = mark_cropped
                    if y_end > dimensions[1]:
                        mark_cropped = mark_rgba_resized[0:mark_dimensions - (
                            y_end - dimensions[1]), 0:mark_dimensions]
                        img_rgba_resized[y_offset: dimensions[1], x_offset: x_end] = mark_cropped
            # 2. At the END for x OR y   POPRAVI KOMENTARE
            elif (x_offset < 0 or y_offset < 0) and not (x_end > dimensions[0] or y_end > dimensions[1]):
                if x_offset < 0 or y_offset < 0:
                    if x_offset < 0:
                        mark_cropped = mark_rgba_resized[0:mark_dimensions, abs(
                            x_offset):mark_dimensions]
                        img_rgba_resized[y_offset: y_end, 0: x_end] = mark_cropped
                    if y_offset < 0:
                        mark_cropped = mark_rgba_resized[abs(
                            y_offset):mark_dimensions, 0:mark_dimensions]
                        img_rgba_resized[0: y_end, x_offset: x_end] = mark_cropped
            # Anything else (not on edges)
            else:
                # ROI on the bigger image
                roi = img_rgb_resized[y_offset: y_end, x_offset: x_end]

                # mark (mask and inverse mask)
                img2gray = cv2.cvtColor(mark_resized, cv2.COLOR_BGR2GRAY)
                ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
                mask_inv = cv2.bitwise_not(mask)

                img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
                img2_fg = cv2.bitwise_and(
                    mark_resized, mark_resized, mask=mask)

                dst = cv2.add(img1_bg, img2_fg)
                img_rgb_resized[y_offset: y_end, x_offset: x_end] = dst

                #img_rgba_resized[y_offset : y_end, x_offset : x_end] = cv2.resize(cv2.cvtColor(mark, cv2.COLOR_RGB2RGBA), (mark_dimensions, mark_dimensions))
                #cv2.addWeighted(cv2.resize(mark, (mark_dimensions, mark_dimensions)), alpha, output, 1 - alpha, 0, output)

        # SAVE FINAL IMAGE
        cv2.imwrite(new_file_name, img_rgb_resized)
        cv2.waitKey(0)
        counter = counter + 1
print("------------------------------------")
print("Total files created: " + str(counter))
# Algorithm --------------------------------------- END