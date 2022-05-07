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
import time
import getopt

__author__ = "Marin Maslov"
__license__ = "MIT Licence"
__version__ = "2.0.2"
__maintainer__ = "Marin Maslov"
__email__ = "mmaslo00@fesb.hr"
__status__ = "Stable"

COMMAND_FORMAT = "Error! The command should be: py resizer.py --images <images_dir> --markersize <size_in_percentage> --outputname <name> --percision <percision> --log <log_level>"

# Constants --------------------------------------- START
# USED RGB COLORS
RGB_WHITE = (255, 255, 255)
RGB_BLACK = (0, 0, 0)
RBG_GREEN = (0, 255, 0)

# USED BRIGHTNESS, CONTRAST AND GAMMA VALUES
BRIGHTNESS = 20
CONTRAST = 1.0
GAMMA = 0.2

# USE BLUR
# UNSET_MINIMUM_STARS = 0
# if(len(sys.argv) > 3):
#     UNSET_MINIMUM_STARS = int(sys.argv[3])

# USED MARK SIZE
MARK_SIZE_PERCENTAGE = 0.08
# Constants --------------------------------------- END

# Functions --------------------------------------- START
# GAMMA CORRECTION
def gammaCorrection(img, gamma):
    invGamma = 1 / gamma
    table = [((i / 255) ** invGamma) * 255 for i in range(256)]
    table = np.array(table, np.uint8)
    return cv2.LUT(img, table)

# IMAGE OVERLAY
def overlayImages(roi, mark_cropped):
    # mark (mask and inverse mask)
    img2gray = cv2.cvtColor(mark_cropped, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
    img2_fg = cv2.bitwise_and(mark_cropped, mark_cropped, mask=mask)

    return cv2.add(img1_bg, img2_fg)
# Functions --------------------------------------- END


# Algorithm --------------------------------------- START
def main(argv):
    images_dir = ''
    marker_size = ''
    output_name = ''
    percision = ''
    log_level = ''

    try:
        opts, args = getopt.getopt(argv, "h", ["images=", "markersize=", "outputname=", "percision=", "log="])
    except getopt.GetoptError:
        print(COMMAND_FORMAT)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(COMMAND_FORMAT)
            sys.exit()
        elif opt in ("--images"):
            images_dir = arg
        elif opt in ("--markersize"):
            marker_size = arg
        elif opt in ("--outputname"):
            output_name = arg
        elif opt in ("--percision"):
            percision = arg
        elif opt in ("--log"):
            log_level = arg

    #logging.basicConfig(filename=images_dir + 'output.log', encoding='utf-8', level=log_level.upper())

    output = images_dir + 'output/'

    if not os.path.exists(output) != False:
        print("\033[2;32;40m[INFO]\033[0;0m" + "\tCreating directory: " + output)
        os.mkdir(output)

    counter = 0
    for file in os.listdir(images_dir):
        if file.endswith(".jpg"):
            # PREPARE OUTPUT NAME
            zeros = "00000"
            zeros_counter = len(str(counter))
            while zeros_counter > 0:
                zeros = zeros[:-1]
                zeros_counter = zeros_counter - 1

            new_file_name = str(output + str(output_name) + "_" + str(zeros) + str(counter) + ".jpg")

            # READ IMAGE (RGB and BW)
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tOpening: " + file)
            img_rgb = cv2.imread(images_dir + file)

            # CONTRAST, BRIGHTNESS AND GAMMA CORRECTIONS
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tApplying contrast, brightness and gamma corrections.")
            adjusted = cv2.convertScaleAbs(img_rgb, alpha=CONTRAST, beta=BRIGHTNESS)
            adjusted = gammaCorrection(adjusted, GAMMA)

            # DENOISING
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tDenoising image.")
            adjusted = cv2.fastNlMeansDenoisingColored(adjusted, None, 5, 5, 2, 2)

            #if USE_BLUR == 1:
            #    ksize = (1, 1)
            #    adjusted = cv2.blur(adjusted, ksize)

            # CONVERT IMAGE TO BW
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tConverting image to grayscale.")
            img_bw = cv2.cvtColor(adjusted, cv2.COLOR_BGR2GRAY)

            #plt.imshow(img_bw, 'gray')
            #plt.title('stars')
            #plt.show()

            # RESIZE IMAGE
            rows, cols = img_bw.shape
            new_cols = int((1000 * cols) / rows)
            dimensions = (new_cols, 1000)
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tResizing image from: (" + str(rows) + ", " + str(cols) + ") to (" + str(1000) + ", " + str(new_cols) + ").")
            img_bw_resized = cv2.resize(img_bw, dimensions)
            img_rgb_resized = cv2.resize(img_rgb, dimensions)

            # CREATE THRASHOLDS (STARS)
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tCreating thresholds.")
            thresholds = cv2.threshold(img_bw_resized, 180, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            #cv2.imshow("Input", thresholds)

            # FIND CONTURES (STARS)
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tDetecting stars.")
            contours = cv2.findContours(
                thresholds, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)[-2]

            # FIND THE GREATEST CONTOUR AREA
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tDetecting biggest star.")
            contours_areas = []
            for contour in contours:
                contours_areas.append(cv2.contourArea(contour))

            # DEFINE MIN-MAX CONTOUR AREA
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tDefining minimum star size.")
            contours_areas.sort(reverse=True)
            max_contour_area = contours_areas[0]
            min_contour_area = float(percision) * float(max_contour_area)  # * len(contours_areas) #
            #print("MAX: " + str(max_contour_area) + " MIN: " + str(min_contour_area))

            # TRIM CONTOURS BY MIN-MAX CONTOUR AREA
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tTrimming detected star list.")
            trimmed_contours = []
            trimmed_contours_areas = []
            for contour in contours:
                if min_contour_area <= float(cv2.contourArea(contour)) <= max_contour_area:
                    trimmed_contours_areas.append(cv2.contourArea(contour))
                    trimmed_contours.append(contour)

            # THERE SHOULD BE A MINIMUM OF 10 STARS
            if len(trimmed_contours) < 5:
                if (log_level.upper() == "DEBUG"):
                    print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tNumber of stars should not be below 5. Adding back the biggest from the removed ones.")
                while len(trimmed_contours) <= 5:
                    min_contour_area = round(min_contour_area - 0.1, 2)
                    trimmed_contours = []
                    trimmed_contours_areas = []
                    for contour in contours:
                        if min_contour_area <= cv2.contourArea(contour) <= max_contour_area:
                            trimmed_contours_areas.append(cv2.contourArea(contour))
                            trimmed_contours.append(contour)

            # SELECT DIMENSIONS FOR THE MARK
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tSelecting dimensions for the mark based on image dimensions.")
            current_file_name = __file__.replace("\\", "/").split("/")[-1]
            current_file_parent_directory = __file__.replace(current_file_name, "")
            mark_path = current_file_parent_directory + '/img/target.png'
            mark = cv2.imread(mark_path)
            mark_dimensions = int(math.ceil(dimensions[1] * float(marker_size)))
            if (log_level.upper() == "DEBUG"):
                print("\033[2;35;40m[DEBUG]\033[0;0m" + "\tMark dimensions selected: (" + str(mark_dimensions) + ", " + str(mark_dimensions) + ").")
            #mark_dimensions_offset = int(math.ceil(mark_dimensions/2 - 0.15*mark_dimensions))
            mark_resized = cv2.resize(mark, (mark_dimensions, mark_dimensions))

            print("[INFO]\tDetected: " + str(len(trimmed_contours)) + " in file: " + str(file) + " (saving output to: " + new_file_name + ")")

            for trimmed_cnt in trimmed_contours:
                # x_contour and y_contour represent the contour center which refers to its position in the big image
                x_contour, y_contour, _, _ = cv2.boundingRect(trimmed_cnt)

                x_big_image = int(dimensions[0])
                y_big_image = int(dimensions[1])

                x_mark_start = int(x_contour - mark_dimensions / 2)
                y_mark_start = int(y_contour - mark_dimensions / 2)

                x_mark_end = int(x_contour + mark_dimensions / 2)
                y_mark_end = int(y_contour + mark_dimensions / 2)

                # DECISION TREE
                # CHECK: Is the contour on any image border?
                if x_mark_start < 0 or y_mark_start < 0 or x_mark_end > x_big_image or y_mark_end > y_big_image:
                    # CHECK: Is the contour in any corner?
                    if (x_mark_start < 0 and y_mark_start < 0) or (x_mark_end > x_big_image and y_mark_end > y_big_image) or (x_mark_start < 0 and y_mark_end > y_big_image) or (x_mark_end > x_big_image and y_mark_start < 0):
                        # CHECK: Is the corner on the main diagonal?
                        if (x_mark_start < 0 and y_mark_start < 0) or (x_mark_end > x_big_image and y_mark_end > y_big_image):
                            # CHECK: Is the corner TOP-LEFT?
                            if (x_mark_start < 0 and y_mark_start < 0):
                                mark_cropped = mark_resized[int(mark_dimensions - (mark_dimensions / 2 + y_contour)) : mark_dimensions, int(mark_dimensions - (mark_dimensions / 2 + x_contour)) : mark_dimensions]
                                img_rgb_resized[0 : y_mark_end, 0 : x_mark_end] = overlayImages(img_rgb_resized[0 : y_mark_end, 0 : x_mark_end], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " in TOP-LEFT corner.\tApplying mask with corner fix.")
                            # The corner is BOTTOM-RIGHT
                            else:
                                mark_cropped = mark_resized[0 : int(mark_dimensions / 2 + (y_big_image - y_contour)), 0 : int(mark_dimensions / 2 + (x_big_image - x_contour))]
                                img_rgb_resized[y_mark_start : y_big_image, x_mark_start : x_big_image] = overlayImages(img_rgb_resized[y_mark_start : y_big_image, x_mark_start : x_big_image], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " in BOTTOM-RIGHT corner.\tApplying mask with corner fix.")
                        # The contour is on the secondary diagonal
                        else:
                            # CHECK: Is the corner TOP-RIGHT?
                            if (y_mark_start < 0 and x_mark_end > x_big_image):
                                mark_cropped = mark_resized[int(mark_dimensions - (mark_dimensions / 2 + y_contour)) : mark_dimensions, 0 : int((mark_dimensions / 2) + (x_big_image - x_contour))]
                                img_rgb_resized[0 : y_mark_end, x_mark_start : x_big_image] = overlayImages(img_rgb_resized[0 : y_mark_end, x_mark_start : x_big_image], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " in TOP-RIGHT corner.\tApplying mask with corner fix.")
                            # The croner is BOTTOM-LEFT
                            else:
                                mark_cropped = mark_resized[0 : int((y_big_image - y_contour) + (mark_dimensions / 2)), int(mark_dimensions - (mark_dimensions / 2 + x_contour)) : mark_dimensions]
                                img_rgb_resized[y_mark_start : y_big_image, 0 : x_mark_end] = overlayImages(img_rgb_resized[y_mark_start : y_big_image, 0 : x_mark_end], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " in BOTTOM-LEFT corner.\tApplying mask with corner fix.")
                    # The contour is not in any corner, which means that is just on one of the borders
                    else:
                        # CHECK: Is the contour on the starting (top-left) borders?
                        if (x_mark_start < 0 or y_mark_start < 0):
                            # CHECK: Is the contour on the left border?
                            if x_mark_start < 0:
                                mark_cropped = mark_resized[0 : mark_dimensions, int(mark_dimensions - (mark_dimensions / 2 + x_contour)) : mark_dimensions]
                                img_rgb_resized[y_mark_start : y_mark_end, 0 : x_mark_end] = overlayImages(img_rgb_resized[y_mark_start : y_mark_end, 0 : x_mark_end], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " on the LEFT border.\tApplying mask with border fix.")
                            # The contour is on the top border
                            else:
                                mark_cropped = mark_resized[int(mark_dimensions - (mark_dimensions / 2 + y_contour)) : mark_dimensions, 0 : mark_dimensions]
                                img_rgb_resized[0 : y_mark_end, x_mark_start : x_mark_end] = overlayImages(img_rgb_resized[0 : y_mark_end, x_mark_start : x_mark_end], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " on the TOP border.\tApplying mask with border fix.")
                        # The contour is on the ending (bottom-right) borders
                        else:
                            # CHECK: Is the contour on the right border?
                            if x_mark_end > x_big_image:
                                mark_cropped = mark_resized[0 : mark_dimensions, 0 : int(mark_dimensions / 2 + (x_big_image - x_contour))]
                                img_rgb_resized[y_mark_start : y_mark_end, x_mark_start : x_big_image] = overlayImages(img_rgb_resized[y_mark_start : y_mark_end, x_mark_start : x_big_image], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " on the RIGHT border.\tApplying mask with border fix.")
                            # The contour is on the bottom border
                            else:
                                mark_cropped = mark_resized[0 : int(mark_dimensions / 2 + (y_big_image - y_contour)), 0 : mark_dimensions]
                                img_rgb_resized[y_mark_start : y_big_image, x_mark_start : x_mark_end] = overlayImages(img_rgb_resized[y_mark_start : y_big_image, x_mark_start : x_mark_end], mark_cropped)
                                if (log_level.upper() == "DEBUG"):
                                    print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " on the BOTTOM border.\tApplying mask with border fix.")
                # The contour is in not on the border, no further preparation is needed
                else:
                    img_rgb_resized[y_mark_start: y_mark_end, x_mark_start: x_mark_end] = overlayImages(img_rgb_resized[y_mark_start: y_mark_end, x_mark_start: x_mark_end], mark_resized)
                    if (log_level.upper() == "DEBUG"):
                        print("[DEBUG]\tDetected star of size: " + str(cv2.contourArea(trimmed_cnt)) + " in image.\tApplying mask.")

            # SAVE THE FINAL IMAGE
            print("\033[2;32;40m[INFO]\033[0;0m" + "\tSaving image: " + str(new_file_name))
            cv2.imwrite(new_file_name, img_rgb_resized)
            cv2.waitKey(0)
            counter = counter + 1
    print("------------------------------------")
    print("\033[2;32;40m[INFO]\033[0;0m" + "\t\033[2;44;47mTotal files created:\t" + str(counter) + "\033[0;0m")
    # Algorithm --------------------------------------- END

if __name__ == "__main__":
    start_time = time.time()
    main(sys.argv[1:])
    print("\033[2;32;40m[INFO]\033[0;0m" + "\tTotal execution time: " + str((time.time() - start_time)) + " seconds.\033[0;0m")