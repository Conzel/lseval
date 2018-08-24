# -*- coding: utf-8 -*-
import os


def avi2frames(names, directory="frames", numbering=0):
    """
    Takes in name of an avi file (or path) and transforms it into sequence of
    frames that are saved in a new directory specified by directory.

    name: name of avi files to use (or path) as list.
          Multiple can be specified.
    directory: directory where to save the frames to
    """
    import cv2
    count = 0
    os.makedirs(directory, exist_ok=True)
    for name in names:
        vidcap = cv2.VideoCapture(name)
        success, image = vidcap.read()
        if not success:
            print("Video read failed.")
        print("Importing", name + "...")
        while success:
            cv2.imwrite(directory + "\\frame%d.bmp" % (count + numbering), image)
            success, image = vidcap.read()
            count += 1
    print("Finished. Imported %d images" % count)
    return


names = input("Enter avi file names (separate by space): ")
names = names.split()
dir = input("Enter destination directory: ")
numbering = input("Enter numbering start: ")

print("Importing...")

avi2frames(names, dir, int(numbering))

input("Press enter to exit.")
