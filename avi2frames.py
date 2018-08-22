# -*- coding: utf-8 -*-
import cv2
import os

def avi2frames(name, directory="frames"):
    """
    Takes in name of an avi file (or path) and transforms it into sequence of
    frames that are saved in a new directory specified by directory.

    name: name of avi file to use (or path)
    directory: directory where to save the frames to
    """
    import cv2
    vidcap = cv2.VideoCapture(name)
    success, image = vidcap.read()
    os.makedirs(directory)
    if not success:
        print("Video read failed.")
    count = 0
    while success:
        cv2.imwrite(directory + "\\frame%d.bmp" % count, image)
        success, image = vidcap.read()
        count += 1
    print("Finished. Imported %d images" % count)


name = input("Enter avi file name: ")
dir = input("Enter destination directory: ")

print("Importing...")

avi2frames(name, dir)

input("Press enter to exit.")
