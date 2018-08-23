# -*- coding: utf-8 -*-
"""
Created on Fri May 11 11:04:44 2018

@author: Alexander Conzelmann | lexan@kabelbw.de
"""
import numpy as np
from datetime import datetime
from scipy import signal
import os
import matplotlib.pyplot as plt
import utils as ut
import re
import cv2


def xcorr(x, y, scale='none', SciPy=True):
    """
    Exact implementation of matlab function xcorr, refer to Matlab Doc for
    further information.

    Input:
        x, y: Vectors that should be cross correlated. Enter same vector twice
        for autocorrelation.
        scale: Scaling of the cross-correlation.
        SciPy: Bool, False lets the function use the numpy.correlate function,
        True lets it use the fftconvolve function from the signal toolbox.
        Result is identical, speed may vary (normally the fftconvolve is con-
        siderably faster.) Default True.

    Returns:
        Numpy array containing the cross correlation values.

    From: https://stackoverflow.com/questions/43652911/python-normalizing-1d-cross-correlation
    """
    if x.size > y.size:
        pad_amount = x.size - y.size
        y = np.append(y, np.repeat(0, pad_amount))
    elif y.size > x.size:
        pad_amount = y.size - x.size
        x = np.append(x, np.repeat(0, pad_amount))

    if SciPy:
        # does convolution with one array turned around
        corr = signal.fftconvolve(x, y[::-1], mode='full')
    else:
        corr = np.correlate(x, y, mode='full')  # scale = 'none'
    lags = np.arange(-(x.size - 1), x.size)

    if scale == 'biased':
        corr = corr / x.size
    elif scale == 'unbiased':
        corr /= (x.size - abs(lags))
    elif scale == 'coeff':
        corr /= np.sqrt(np.dot(x, x) * np.dot(y, y))
    return corr, lags


class Speckle(object):
    """
    Class of speckle object. Represents a speckle in a camera image of a
    multispeckle DLS setup. Can be added to a whole ensemble (every speckle
    of the frame), from which ensemble averaged values can be calculated.
    """

    def __init__(self, timeInt):
        """
        Can take in an intensity list which maps specific points in
        measurement time (images) to the intensity that the speckle held at
        this point.
        Calculates time average and autocorrelation function. Turns list into
        numpy array.

        Input: List with intensity values, sorted by time.
        """
        self.timeInt = np.array(timeInt)
        self.updateSpeckle()
        return

    def __str__(self):
        """
        String representation prints time-intensity dict.
        """
        strrepr = ""
        for val in self.timeInt:
            strrepr += str(val) + "\n"
        return strrepr

    def getIntList(self):
        """
        Returns list of intensities, ordered increasingly by time.
        """
        return self.timeInt

    def getTimeAverage(self):
        """
        Getter Method for time average.
        """
        return self.timeAvg

    def getTimeIAKF(self):
        """
        Getter method for time Intensity Autocorrelation Function
        of the speckle.
        """
        return self.timeIAKF

    def getTimeFAKF(self):
        """
        Getter method for Field Autocorrelation Function of the speckle.
        """
        return self.timeFAKF

    def addInt(self, timeInt, update=True):
        """
        Adds an intensity-time point to the timeInt dictionary that is held
        by the speckle. Accepts both floats and lists. Also updates timeAvg.

        Inputs:
        timeInt: Tuple of the form (time, intensity) or dict that uses time as
        key and value as intensity.
        update: Set to true updates the speckles various other attributes such
        as intensity average etc. Default True.

        """
        try:
            timeInt = np.array(timeInt)
            np.concatenate((self.timeInt, timeInt))
        except:
            print("Wrong input format!")
            return
        if update:
            self.updateSpeckle()
        return

    def calcTimeAverage(self):
        """
        Calculates and updates time-averaged intensity for the speckle.
        """
        self.timeAvg = np.sum(self.timeInt) / len(self.timeInt)
        return

    def calcTimeIAKF(self):
        """
        Calculates time-averaged IAKF (Intensity Autocorrelation Function) for
        the speckle, normalized with the mean intensity.
        """
        intArr = np.array(self.getIntList())
        # unnormalized autocorrelation function
        unnAKF = xcorr(intArr, intArr, 'unbiased', True)[0]

        # Weird indexing is because of how the function xcorr produces
        # its array
        self.timeIAKF = unnAKF[(len(intArr)-1):(2*len(intArr))] \
                        / (self.timeAvg)**2
        return

    def calcTimeFAKF(self):
        self.timeFAKF = (abs((self.timeIAKF-1)
                             / (self.timeIAKF[0]-1)))**(1/2)

    def updateSpeckle(self):
        """
        Re-calculates various speckle attributes. Used after modifying the
        the speckle.
        """
        self.calcTimeAverage()
        self.calcTimeIAKF()
        self.calcTimeFAKF()


class Ensemble(object):
    """
    Represents an ensemble consisting of multiple speckles. Capable of taking
    speckles in and calculating ensemble-averaged values.

    All speckles should have the same number of images associated with them,
    else problems may occur.
    """

    def __init__(self, speckles=[]):
        self.speckles = []
        self.numSpeckles = 0
        self.ensembleIAKF = 0
        self.ensembleFAKF = 0
        self.ensembleAvg = 0

    def addSpeckle(self, speckles):
        """
        Adds speckle or list of speckles to the ensemble.
        """
        try:
            speckles[0]
        except TypeError:
            speckles = [speckles]

        for speck in speckles:
            assert(isinstance(speck, Speckle))

        self.speckles += speckles
        self.numSpeckles = len(self.speckles)
        return

    def printStats(self):
        """
        Prints information about the ensemble.
        """
        print("Number of Speckles:", self.numSpeckles)
        print("Intensity Average:", self.ensembleAvg)
        print("Ensemble IAKF:\n", self.ensembleIAKF)
        print("Ensemble FAKF:\n", self.ensembleFAKF)

    def calcEnsembleAvg(self):
        """
        Calculates Intensity average over the whole ensemble (Average all
        time averaged intensities for every speckle.)
        """
        timeavgList = []
        for speck in self.speckles:
            timeavgList.append(speck.timeAvg)
        self.ensembleAvg = np.sum(timeavgList)/len(self.speckles)
        return

    def calcEnsembleIAKF(self):
        """
        Calculates Ensemble Intensity Autocorrelation function (sometimes g2_E)
        for the ensemble using the speckle information.
        """
        for speck in self.speckles:
            try:
                eIAKF += speck.timeIAKF * speck.timeAvg**2
            except UnboundLocalError:
                eIAKF = speck.timeIAKF * speck.timeAvg**2
        ensembleIAKF = eIAKF/(len(self.speckles) * self.ensembleAvg**2)
        self.ensembleIAKF = ensembleIAKF
        return

    def plot(self, FAKF=True, IAKF=False, plotmode=plt.semilogx, timeStep=1):
        """
        Plotting Interface, can be used to display the ensemble stats to the
        outside world.

        input:
            FAKF: bool, True plots ensemble FAKF
            IAKF: bool, True plots ensemble IAKF
            timeKey: list, contains the exact time-step between each image
            that the speckles were read from. Used to scale the x-axis and to
            Incorporate different FPS from different measurementsself.
            Default just assumes that the time passed between each image is
            identical.
        """
        numImages = len(self.speckles[0].timeInt)
        xValues = timeStep*np.linspace(1, numImages, num=numImages)

        if FAKF:
            yValues = self.ensembleFAKF
            if type(yValues) is int:
                raise ValueError("No list-type FAKF detected."
                                 + "Try updating ensemble.")
            plt.figure("ensemble", dpi=100)
            plt.clf()
            plotmode(xValues, yValues, " bo", markersize=2,
                     label="EnsembleFAKF")
            plt.legend()
            plt.xlabel(r"Time")
            plt.ylabel("FAKF")
            plt.title("Ensemble FAKF over relative timestep")

            plt.savefig("EnsembleFAKF.jpg")
            plt.close()

        if IAKF:
            yValues = self.ensembleIAKF
            if type(yValues) is int:
                raise ValueError("No list-type IAKF detected."
                                 + "Try updating ensemble.")
            plt.figure("ensemble", dpi=100)
            plt.clf()
            plotmode(xValues, yValues, " bo", markersize=2,
                     label="Ensemble IAKF")
            plt.legend()
            plt.xlabel(r"Time")
            plt.ylabel("IAKF")
            plt.title("Ensemble IAKF over relative timestep")

            plt.savefig("EnsembleIAKF.jpg")
            plt.close()

    def log(self):
        """
        Exports calculated data into machine-readable format (for use by
        programs such as origin)
        """
        with open("enslog.asc", "w+") as log:
            log.write("time \tFAKF \tIAKF\n")
            for i in range(len(ens.ensembleFAKF)):
                log.write(str(i) + "\t" + str(ens.ensembleFAKF[i]) + "\t"
                          + str(ens.ensembleIAKF[i]) + "\n")

    def calcEnsembleFAKF(self):
        """
        Calculates field autocorrelation function (FAKF, g1, f_E
        (dynamic structure factor)) for the ensemble,
        based on the ensemble IAKF.
        """
        self.ensembleFAKF = (abs((self.ensembleIAKF-1)
                                 / (self.ensembleIAKF[0]-1)))**(1/2)
        return

    def updateEnsemble(self):
        """
        Updates Ensemble by calculating Intensity Average, IAKF, FAKF.
        """
        self.calcEnsembleAvg()
        self.calcEnsembleIAKF()
        self.calcEnsembleFAKF()
        return

    def findExtremeSpeckles(self, percent, corrImg=0, best=True,
                            worst=True, sortFunc=Speckle.getTimeIAKF):
        """
        Returns Ensemble containing the most extreme speckles by sortFunc.
        Input:
            percent: float, percentage of extreme speckles (0.2 returns
            ensemble with the 20% fastest and/or 20% slowest speckles).
            corrIm: integer, denoting the image (and thus the point in time)
            where the extreme speckles should be found (default is the img. 0)
            best: bool, True includes x% best speckles in the ensemble.
            worst: bool, False includes x% worst speckles in the ensemble.
            sortFunc: Function that is used to sort the extreme speckles with.
            Standard is Intensity Autocorrelation Function, (yields fastest/
            slowest speckles) but other methods can be employed aswell (
            for example least intense / most intense speckles with
            Speckles.getTimeInt).

        Return:
            Ensemble object, containing fastest and/or slowest speckles.
        """

        if corrImg > len(self.speckles[0].getIntList()):
            raise IndexError("Correlation image higher than"
                             + "number of total images")

        if not (best or worst):
            print("Either fast or slow must be set to True!")
            return

        numExtremeSpeckles = int(percent*self.numSpeckles)

        # copies speckle list to not modify the origial
        speckles = self.speckles[:]

        # Sorts speckles by intensity at positiong (image) corrImg.
        # Index error means that an integer was produced by the sort function,
        # in which case we catch the error and use an unsubscripted sortFunc.
        try:
            speckles.sort(key=lambda x: sortFunc(x)[corrImg])
        except IndexError:
            speckles.sort(key=lambda x: sortFunc(x))

        extremeSpeckles = []
        if best:
            extremeSpeckles += speckles[:numExtremeSpeckles]
        if worst:
            extremeSpeckles += speckles[-numExtremeSpeckles:]

        ens = Ensemble()
        ens.addSpeckle(extremeSpeckles)
        ens.updateEnsemble()
        return ens


def readFramesSquare(directory, squareSize=10, logging=True):
    """
    Accepts directory as input, reads out all the frames in the folder,
    divides the frame evenly into squares (1 square = 1 speckle),
    then reads out the mean intensity of the square. Writes the Intensity
    of every speckle in every frame in a log file (if log is true)
    and outputs an Ensemble object containing the found speckles.

    input:
        directory: string, Directory containing the frames.
        squareSize: int, Length of each square side in pixel.

    output:
        ens: Ensemble object, containing the speckles found in the picture.
    """
    # Sorts frames by frame number. Frame numbers equals to timestep number.
    # Frames have to be sorted in order to correctly order akf.
    frames = [frame for frame in os.listdir(directory)
              if ut.match(r"\.bmp$", frame)]
    frames = sorted(frames, key=keyfunc)
    print("Found data: \n" + "\n".join(frames))


    # is used in the for loop for initiliation steps. assumes all frames
    # have equal dimensions (which they should have!)
    firstFlag = True

    count = 0

    # processing of each frame
    for f in frames:

        # count used to show processing progress and to number the images
        count += 1
        print("Reading Frame No." +  str(count) + "...")

        # reads image out to a numpy matrix, dimensions are img length
        path = directory + "\\" + f
        imgMat = cv2.imread(path, 0)

        if firstFlag:
            width = len(imgMat)
            height = len(imgMat[1])
            if width % squareSize != 0 or height % squareSize != 0:
                raise TypeError("Detector not divisble into even squares. "
                                + "Change Square Size to proceed.")

            # Determines the number of squares in both horizontal and vertical
            # direction
            numSquaresWidth = width // squareSize
            numSquaresHeight = height // squareSize

            # Initiliazes numpy array that later holds the intensity values for
            # every speckle.
            speckleInt = np.empty((numSquaresWidth, numSquaresHeight),
                                  dtype=np.object_)
            speckleInt.fill([])
            speckleInt = np.frompyfunc(list, 1, 1)(speckleInt)

            # writes header for log data. Array filled with empty lists.
            # Log data is not meant to be human readable, but rather for use
            # with table calculation programs such as origin
            if logging:
                numSpeckles = numSquaresWidth*numSquaresHeight
                logfilename = directory + ".asc"
                with open(logfilename, "w+") as log:
                    speckleString = "\t".join(["Speckle %d" % i
                                               for i in range(numSpeckles)])
                    log.write("Im. No." + "\t" + speckleString + "\n")
                firstFlag = False
        # prepares list of intensities so writing to log is easier
        intensityList = []

        # divides one frame into squares and reads
        # the mean intensity info into the speckleInt matrix
        for x in range(numSquaresWidth):
            for y in range(numSquaresHeight):
                pixelInts = imgMat[x*squareSize:(x+1)*squareSize,
                                   y*squareSize:(y+1)*squareSize]
                meanInt = pixelInts.mean()
                speckleInt[x, y].append(meanInt)
                intensityList.append(meanInt)

        if logging:
            with open(logfilename, "a") as log:
                intensityString = str(count) + "\t" \
                                  + "\t".join(ut.list2string(intensityList)) \
                                  + "\n"
                log.write(intensityString)

    # speckleInt now contains the intensity lists of every speckle in x,y
    # directions. An Ensemble can be initiliazed and then filled with
    # all the speckles, that are created with the speckle intensities and then
    # accumulated in a list.

    speckleList = []

    print("Creating Ensemble...")

    for x in range(numSquaresWidth):
        for y in range(numSquaresHeight):
            speckleList.append(Speckle(speckleInt[x, y]))

    ens = Ensemble()
    ens.addSpeckle(speckleList)

    print("Calculating AKFs...")
    ens.updateEnsemble()

    print("Finished.")

    return ens


def keyfunc(frame):
    """
    Extracts number of frame from framename, used to sort the frames with a
    custom sort function.

    input:
        frame: str, name of frame.
    output:
        int, number of frame, extraced from name of frame
    """
    return int(re.search(r"\d+", frame).group(0))


ens = readFramesSquare("frames1")
ens.plot(plotmode=plt.plot)
ens.log()


























# #------------------------------------------------------------------------------
# #Testing Area
# def randIntList(num):
#     return [np.random.normal() for x in range(num)]
#
#
# dictDur = datetime.now()
#
# #sets seed for testing
# np.random.seed(0)
#
# #interactive Test
# #numImg = int(input("Anzahl Bilder: "))
# #numSpeckles = int(input("Anzahl Speckles: "))
# numImg = 10000
# numSpeckles = 500
#
# #gives out random normal distribution
# speckList = [Speckle(np.random.random_sample(numImg)*np.random.normal()) for x in range(numSpeckles)]
#
# #Uniform random distribution
# #speckList = [Speckle(randIntList(numImg)) for x in range(numSpeckles)]
#
# #makes speed test for image number
# start = datetime.now()
#
#
# ens = Ensemble()
# ens.addSpeckle(speckList)
# ens.updateEnsemble()
#
# end = datetime.now()
#
# #prints results of speed tests.
# print("Algorithm speed test results for", numImg, "Images and", numSpeckles, "Speckles.")
# print("Time needed for IAKF and List-making:", start-dictDur)
# print("Time needed for ensemble:", end-start)
#
# compImg = 10
#
# #compares histograms and tests extreme speckles method.
# arr = []
# for k in range(len(ens.speckles)):
#     arr.append(ens.speckles[k].getTimeIAKF()[compImg])
# arr = np.array(arr)
# plt.hist(arr, label = "Normal Speckles")
#
# ensext = ens.findExtremeSpeckles(0.1, compImg, worst = True, sortFunc = Speckle.getTimeIAKF)
# arr2 = []
# for k in range(ensext.numSpeckles):
#     arr2.append(ensext.speckles[k].getTimeIAKF()[compImg])
# arr2 = np.array(arr2)
# plt.hist(arr2, label = "Extreme Speckles")
# plt.legend(loc = "best")
#
# #for use in the shell
# #input("Finished. Press enter to exit.")
# #------------------------------------------------------------------------------
