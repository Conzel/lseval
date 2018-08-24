# -*- coding: utf-8 -*-
"""
Module containing various utility functions for data retrieval and
calculations.
"""

import os
import re
import numpy as np
from constants import *
import math


# Adjusts path separator depending on OS.
if os.name == "nt":
    PSEP = "\\"
elif os.name == "posix":
    PSEP = "/"
else:
    print("Operating System not recognized. Exiting.")
    exit()


def isFloat(num):
    """
    Returns True if input is a number, otherwise False.
    """
    try:
        float(num)
        return True
    except (TypeError, ValueError):
        return False


def match(regExp, string):
    """
    returns true if regExp matches string, false otherwise.
    """
    return re.search(regExp, string) is not None


def getFilesInFolder(path=os.getcwd(), searchReg="_averaged.ASC"):
    """
    Returns a list of all filenames from the folder specified in path
    with the searchString as regular expression.
    """
    fileList = os.listdir(path)
    filteredList = []
    for name in fileList:
        print(name)
        if match(searchReg, name):
            filteredList.append(name)
    return filteredList


def getHydroDynR(diffu, visc, temp):
    """
    Calculates hydrodynamic radius from inputs, all in SI units.

    diff: Diffusion coefficient
    visc: dynamic viscosity of solvent
    temp: Temperature of surroundings.
    """
    rhyd = KB * temp / (6 * np.pi * visc * diffu)
    return rhyd


def getQSqu(n, lambd, theta):
    """
    Calculates q^2 (reciproke scattering vector) from input.

    n: refractive index of solvent
    lambda: wavelength
    theta: angle in degrees
    """
    return (4*np.pi*n/lambd*math.sin(math.radians(theta/2)))**2


def hydroRfromGamma(gamma, n, lambd, theta, visc, temp):
    """
    Calculates hydrodynamic radius from gamma from cumulant/exponential fit of
    DLS.
    Input same as in getQSqu and getHydroDynR.
    """
    diffu = gamma/getQSqu(n, lambd, theta)
    return getHydroDynR(diffu, visc, temp)


def recursiveCall(function, filter, folder=os.getcwd()):
    """
    Calls the function specified recursively on a folder. Opens folder,
    every file found on the level of the folder, that fits the filter (regExp)
    gets passed as a list to the function. Every folder found gets used
    to call recursiveCall again.

    function: function of one argument, gets called with a list of the found
    files on everylevel.
    folder: starting folder, gets opened first.
    filter: function of one input which takes in a filename and returns True
    if the file should be passed on to function, False otherwise
    """

    # we are better off working only with absolute paths from now on. This is
    # just a safety measure essentially, this function does not change an
    # already absolute path at all.
    abspath = os.path.abspath(folder)
    folderContents = os.listdir(abspath)

    files = []
    folders = []
    if len(folderContents) != 0:
        for entry in folderContents:
            if os.path.isdir(entry):
                folders.append(entry)
            elif filter(entry):
                files.append(entry)

        # makes the contents list a list containing full paths.
        files = [abspath + PSEP + path for path in files]
        if len(files) > 0:
            function(files)

        folders = [abspath + PSEP + path for path in folders]
        if len(folders) > 0:
            for newFolder in folders:
                recursiveCall(function, filter, newFolder)
    return


def list2string(list):
    """
    Transforms each entry of a list into a string, returns list.
    """
    return [str(entry) for entry in list]


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
