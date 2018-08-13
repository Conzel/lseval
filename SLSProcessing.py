# -*- coding: utf-8 -*-
"""
Script for SLS Data processing.

@author: Alex
zuletzt modifiziert: 03.08.2018
"""
# import matplotlib
# matplotlib.use("Agg")

import re
import matplotlib.pyplot as plt
import os
import utils as ut

if os.name == "nt":
    PSEP = "\\"
elif os.name == "posix":
    PSEP = "/"
else:
    print("Operating System not recognized. Exiting.")
    exit()


def readElementsAndProcess(filenames):
    """
    Stripped function of readElementsAndProcessDLS. Only reads in average
    Countrate and angle.

    filenames: list of filenames that correspond to ALV Data.
    saveImg: Set to true if the fitfunctions should be plotted together with
             the data in a separate folder.

    returns dictionary of data about the whole sample for further processing.
    """
    # enables the function to also accept a single string as input.
    if type(filenames) is str:
        if os.path.isdir(filenames):
            contents = os.listdir(filenames)
            contents = ut.getFilesInFolder(filenames, r"\.txt$")
            filenames = [os.getcwd() + PSEP + filenames + PSEP
                         + name for name in contents]
        else:
            filenames = [filenames]

    if len(filenames) == 0:
        print("Empty List passed into function")
        return

    dataDict = {}
    meanCRs = []
    angles = []
    oneFileFoundFlag = False

    for data in filenames:

        sampleName = re.sub(r"\d+_SLS\.txt$", "", data)
        # prepares data to be returned in dictionary later
        try:
            with open(data, "r") as file:
                cont = file.read()
                cont = cont.strip("\\n")
                angle, cr = cont.split("\\t")
                meanCRs.append(float(cr))
                angles.append(float(angle))
            oneFileFoundFlag = True
        except:
            print("Could not open", data)

    if not oneFileFoundFlag:
        return None
    dataDict["meanCRs"] = meanCRs
    dataDict["angles"] = angles
    dataDict["samplename"] = re.search(r"[^\\]+$", sampleName).group(0)

    return dataDict


def plotMeanCRs(dataDict, plotmode=plt.plot):
    """
    Plots mean countrate over angle, extracted from the given filenames.
    """

    plt.figure(dataDict["samplename"], dpi=100)
    plt.clf()
    plotmode(dataDict["angles"], dataDict["meanCRs"], ' bo', markersize=2,
             label="meanCR")
    plt.legend()
    plt.title(dataDict["samplename"] + ", meanCR over angle")
    plt.xlabel(r"$\theta$ in °")
    plt.ylabel("Mean Countrate")
    plt.savefig(dataDict["samplename"] + "meanCR.png")
    plt.close()
    return


def compareCRs(filenames1, filenames2, plotmode=plt.plot):
    """
    Compares two mean countrates (diving 1 by 2 (1/2)) and plots them.
    """
    dataDict1 = readElementsAndProcess(filenames1)
    dataDict2 = readElementsAndProcess(filenames2)
    CRs1 = dataDict1["meanCRs"]
    CRs2 = dataDict2["meanCRs"]
    divCR = []
    for i in range(len(CRs1)):
        divCR.append(CRs1[i]/CRs2[i])

    plt.figure(dataDict1["samplename"], dpi=100)
    plt.clf()
    plotmode(dataDict1["angles"], divCR, ' bo', markersize=2,
             label="Mean CR divided")

    plt.legend()
    plt.title(dataDict1["samplename"] + " divided by "
              + dataDict2["samplename"])
    plt.xlabel(r"Angle in °")
    plt.ylabel("Countrate")
    plt.savefig(dataDict1["samplename"] + "By" + dataDict2["samplename"]
                + "dividedCR.png")
    plt.close()
    return

# --testing
# reg = r"^.*\.txt$"
# files = os.listdir(os.getcwd())
# files = [f for f in files if re.match(reg, f) is not None]
# ddict = readElementsAndProcess(files)
# plotMeanCRs(ddict)
