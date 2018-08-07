# -*- coding: utf-8 -*-
"""
Module containing various utility functions for data retrieval and
calculations.
"""

import os
import re
import numpy as np
from constants import *


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
