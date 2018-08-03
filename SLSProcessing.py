# -*- coding: utf-8 -*-
"""
Script for SLS Data processing.

@author: Alex
zuletzt modifiziert: 03.08.2018
"""
# import matplotlib
# matplotlib.use("Agg")

import re
import math
import fitfunctions as ff
from constants import KB
from utils import *
import sys


try:
    import numpy as np
except ImportError:
    input("Numpy not installed.")
    exit

try:
    import matplotlib.pyplot as plt
except ImportError:
    input("Matplotlib not installed.")
    exit

try:
    import scipy.optimize as sco
except ImportError:
    input("Scipy not installed.")

try:
    import os
except ImportError:
    input("os module not installed.")

    def createDir(self):
        """
        Creates a directory for the current unique sample, if the directory
        doesnt already exist.

        returns: path of the directory
        """
        targetPath = os.getcwd() + "\\" + self.samplename
        if not os.path.exists(targetPath):
            os.makedirs(targetPath)
            return targetPath
        else:
            return targetPath


def getFilesInFolder(path=os.getcwd(), searchReg="_averaged.ASC"):
    """
    Returns a list of all filenames from the folder specified in path
    with the searchString as regular expression.
    """
    fileList = os.listdir(path)
    filteredList = []
    for name in fileList:
        if re.match(searchReg, name):
            filteredList.append(name)
    return filteredList


def readElementsAndProcessSLS(filenames):
    """
    Stripped function of readElementsAndProcessDLS. Only reads in average
    Counrate and angle.

    filenames: list of filenames that correspond to ALV Data.
    saveImg: Set to true if the fitfunctions should be plotted together with
             the data in a separate folder.

    returns dictionary of data about the whole sample for further processing.
    """
    # enables the function to also accept a single string as input.
    if type(filenames) is str:
        filenames = [filenames]

    dataDict = {}
    meanCRs = []
    angles = []

    for data in filenames:

        sampleName = re.sub(r"\d+.txt$", "", data)
        # prepares data to be returned in dictionary later
        with open(data, "r") as file:
            cont = file.read()
            cont = cont.strip("\\n")
            angle, cr = cont.split("\\t")
            meanCRs.append(float(cr))
            angles.append(float(angle))

    dataDict["meanCRs"] = meanCRs
    dataDict["angles"] = angles
    dataDict["samplename"] = sampleName

    return dataDict


def plotMeanCRs(filenames):
    """
    Plots mean countrate over angle, extracted from the given filenames.
    """
    # fit function not relevant for countrate, we just take the simplest one
    dataDict = readElementsAndProcessSLS(filenames, sampleName)

    plt.figure(dataDict["samplename"], dpi=100)
    plt.clf()
    plt.plot(dataDict["angles"], dataDict["meanCRs"], ' bo', markersize=2,
             label="meanCR")
    plt.legend()
    plt.title(dataDict["samplename"] + ", meanCR over angle")
    plt.xlabel(r"$\theta$ in °")
    plt.ylabel("Mean Countrate")
    plt.savefig(dataDict["samplename"] + "meanCR.png")
    plt.close()
    return

def compare(folder1, folder2):
    """
    Takes content from folder1 and folder2, divides the meanCRs at every angles
    against each other and plots the result.
    """
    


if __name__ == "__main__":
    sampleName = sys.argv[1]
reg = r"^.*\.txt$"
files = os.listdir(os.getcwd())
files = [f for f in files if re.match(reg, f) is not None]
plotMeanCRs(files, sampleName)

#
# def schoepeProcess(regString=r"DLS.*\.txt", samplereg="_", path=os.getcwd(),
#                    fallOffFunction=(lambda x: 0.8*x), channelStart=12):
#     """
#     DOES WAYYYY TOO MUCH; NEEDS TO BE CHANGE.
#     Takes in a path. Creates ALV Objects from the ALV files contained in the
#     path. Reduces Data contained in the samples, start with the value given in
#     channelStart and ending after the initial value has fallen under a certain
#     point specified by the fallOffFunction in dependence of the initial value.
#
#     The log of the correlation function then gets plotted over the delay time
#     (ln (g^2(q,tau) -1) again tau) and fitted in a linear function.
#
#     The intercept that is obtained in the linear function for every ALVObject
#     is then plotted against the scattering angle q.
#
#     Input:
#         samplereg: regular expression that assigns sample name by splitting
#         at the pattern given.
#
#         regString: Regular expression as string, gets compiled to reexp object
#         and passed in into getALVFiles to find files that match the regexp.
#
#         path: string, full path to operating system
#
#         fallOffFunction: function that takes at the starting value (at index
#         channelStart), operates on it and determines the value where the cut-
#         off (last value that is used in the fitting later) value lies.
#
#         channelStart: int, determine the index of the first element that should
#         be taken into consideration at data evaluation.
#
#     Output:
#         Plots of data, relevant coefficients in .txt files.
#     """
#     objList = createALVObjs(regString)
#
#     # deletes fit textfile should it already exist.
#     for ALV in objList:
#         ALV.samplename = re.split(samplereg, ALV.filename)[0]
#
#         path = ALV.createDir()
#         txpath = path + "\\" + ALV.samplename + "Fit.txt"
#         if os.path.isfile(txpath):
#             os.remove(txpath)
#
#     for ALV in objList:
#
#         # konfuse Methode um den Endpunkt herauszufinden
#         end = [k for k in range(channelStart+2, len(ALV.akf)) if ALV.akf[k]
#                < fallOffFunction(ALV.akf[channelStart])][0]
#         datarange = (channelStart, end)
#         print(datarange)
#
#         # Saves images to folders
#         print(ALV)
#         path = ALV.createDir()
#         impath = path + "\\" + ALV.samplename + str(int(ALV.angle)) \
#             + "Grad.png"
#         ALV.saveAKFln(impath, datarange)
#
#         # saves fit parameters to textfile.
#         txpath = path + "\\" + ALV.samplename + "Fit.txt"
#         if not os.path.isfile(txpath):
#             with open(txpath, "w+") as txfile:
#                 txfile.write(
#                      "Angle\t\tq^2\t\t\t\tA\t\tGamma [1/s]\t\tMeanCR0 \t\t\n")
#
#         with open(txpath, "a") as txfile:
#             txfile.write(str(ALV.angle) + "\t\t" + "%.4E" % ALV.q**2 + "\t\t"
#                          + "%.4f" % ALV.A + "\t\t"
#                          + "%.4f" % ALV.gamma + "\t\t"
#                          + "%.4f" % ALV.countrate + "\t\t\n")
#
#     # plottet Gamma gegen q^2, gewinnt daraus Diffusionskoeffizient
#     namediff = None
#     for ALV in objList:
#         if namediff is None or not namediff == ALV.samplename:
#             qList = []
#             gammaList = []
#             aList = []
#             angleList = []
#             countList = []
#             namediff = ALV.samplename
#             txpath = ALV.createDir() + "\\" + ALV.samplename + "Fit.txt"
#             with open(txpath, "r") as txfile:
#                 next(txfile)
#                 for line in txfile:
#                     line = line.split("\t\t")
#                     qList.append(float(line[1]))
#                     gammaList.append(float(line[3]))
#                     angleList.append(float(line[0]))
#                     aList.append(float(line[2]))
#                     countList.append(float(line[4]))
#
#             # Muss aus irgendwelchen Gründen ein numpy array sein
#             # plottet gamma, mit von gamma
#             plt.figure(ALV.samplename, dpi=100)
#             plt.clf()
#             qList = np.array(qList)
#             gammaList = np.array(gammaList)
#             plt.plot(qList, gammaList, ' ko', markersize=2, label="Gamma")
#             popt, pcov = fitlin(qList, gammaList)
#             diffcoff = popt[0]
#             plt.plot(qList, linfun(qList, *popt), '-r',
#                      label="Lin. Gamma Fit, a = " + "%.2E" % diffcoff)
#             plt.legend()
#             plt.xlabel("q^2 [m^-2]")
#             plt.ylabel(r"$\Gamma$ [1/s]")
#             plt.title(ALV.samplename + ", Gamma over q^2")
#             plt.savefig(
#                 ALV.createDir() + "\\" + ALV.samplename + "GammaFit.png")
#             plt.close()
#
#             # plots intercept over angle
#             plt.figure(ALV.samplename, dpi=100)
#             plt.clf()
#             plt.plot(
#                 angleList, aList, ' bo', markersize=2, label="y-Intercept")
#             plt.legend()
#             plt.title(ALV.samplename + ", y-Intercept over angle")
#             plt.xlabel(r"$\theta$ in °")
#             plt.ylabel("y-intercept (logarithmical, from fit)")
#             plt.savefig(
#                 ALV.createDir() + "\\" + ALV.samplename + "y-intercept.png")
#             plt.close()
#
#             # plots Mean Countrate over angle
#             plt.figure(ALV.samplename, dpi=100)
#             plt.clf()
#             plt.plot(angleList, countList, ' bo', markersize=2, label="meanCR")
#             plt.legend()
#             plt.title(ALV.samplename + ", meanCR over angle")
#             plt.xlabel(r"$\theta$ in °")
#             plt.ylabel("Mean Countrate")
#             plt.savefig(ALV.createDir() + "\\" + ALV.samplename + "meanCR.png")
#             plt.close()
#
#             hydr = getHydroDynR(diffcoff, ALV.visc, ALV.temp)
#
#             with open(txpath, "a") as tx:
#                 tx.write("\nDiffusion coefficient: " + str(diffcoff))
#                 tx.write("\nHydrodynamic Radius [m]: " + str(hydr))
#
#     input("Erfolgreich abgeschlossen."
#           "Enter drücken um das Programm zu beenden.")
#     return
