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
import platform
import warnings

bits, linkage = platform.architecture()
if bits == "32bit":
    warnings.warn("Program is running in 32-bit mode, placing an upper limit "
                  + "on usable RAM of 2 GB. This may cause memory errors "
                  + "during calculation of Correlationfunction when a large "
                  + "amount of images is read in. Consider running in 64 bit "
                  + "mode.")
    input("Press enter to proceed.")

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

    Be sure to add a time key and update the ensemble before you do
    any other interesting tasks with your ensemble!
    """

    def __init__(self, speckles=[]):
        self.speckles = []
        self.numSpeckles = 0
        self.ensembleIAKF = 0
        self.ensembleFAKF = 0
        self.ensembleAvg = 0
        self.timeKey = 0

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

    def createTimeKey(self, numImList, timeStepList, default=False):
        """
        Creates time key for logging and plotting.

        Explanation: The time passed between each image may not be the same.
        If you first take 10000 images with 1000 FPS, then 10000 images with
        100 FPS, then 10000 images with 10 FPS, the time passed between
        the images is different. This is of no importance for the calculation
        of autocorrelation functions, but important for plotting. The AKFs
        always get plotted over the timekey.

        input:
            numImList: list of integers, showing how many images are
            in each batch.
            timeStepList: list of floats, shows the time passed between
            each image in a batch.
            default: When default is used, just creates a linearly increasing
            timekey for the number of images used. Other specified arguments
            can be anything.

        output: list of floats, showing the timeKey. Also adds timeKey to the
        ensemble attributes.

        Example: For 15 images, 10 recorded with 10 FPS and 5 with 1 FPS:
            numImList = [10, 5]; timeStepList = [0.1, 1]
        """
        timeKey = []

        if default:
            timeKey = [i+1 for i in range(len(self.speckles[0].timeInt))]
            self.timeKey = timeKey
            return timeKey

        # Throws error for incorrect numImList
        if sum(numImList) != len(self.speckles[0].timeInt):
            raise ValueError("Sum of images in numList not equal to total "
                             + "number of images from frames.")
        total = 0
        for k in range(len(numImList)):
            for i in range(numImList[k]):
                total += timeStepList[k]
                timeKey.append(total)
        self.timeKey = timeKey
        return timeKey

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

    def plot(self, FAKF=True, IAKF=False, plotmode=plt.semilogx):
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
        xValues = self.timeKey
        if type(xValues) is int:
            raise ValueError("No Time key specified.")

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

            plt.savefig("EnsembleFAKF.eps")
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

    def log(self, name="enslog.asc"):
        """
        Exports calculated data into machine-readable format (for use by
        programs such as origin)
        """
        with open(name, "w+") as log:
            log.write("time \tFAKF \tIAKF-1\n")
            for i in range(len(self.ensembleFAKF)):
                # truncate time key because of floating point error.
                log.write("%.6f" % self.timeKey[i] + "\t"
                          + str(self.ensembleFAKF[i]) + "\t"
                          + str(self.ensembleIAKF[i]-1) + "\n")

    def logIAKF(self, directory="IAKFs", numSpeckles=0):
        """
        Exports calculated speckle IAKFS to machine-readable format.
        """
        if numSpeckles == 0 or numSpeckles > self.numSpeckles:
            numSpeckles = self.numSpeckles
        os.makedirs(directory, exist_ok=True)
        for i in range(numSpeckles):
            name = "Speckle%d.asc" % i
            speck = self.speckles[i]
            tIAKF = speck.getTimeIAKF()
            with open(directory + "\\" + name, "w+") as log:
                log.write("time [ms]\t time IAKF")
                for k in range(len(tIAKF)):
                    log.write("%.6f" % self.timeKey[k] + "\t")
                    log.write(str(tIAKF[k]) + "\n")

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
        return "Updated Ensemble."

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
            Speckles.getTimeAverage). Best speckles means: first X speckles
            that the sort function produces. Sort function sorts reverse,
            so if you use intensity average over time f.e., the most intense
            speckles (highest value) will be the first (best) speckles.
            On the other hand, if you use getTimeIAKF, the best speckles will
            actually be the slowest ones. best/worst is ambigous here, think
            exactly about what values will be produced by the sort function.

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
        # Reverse
        try:
            speckles.sort(key=lambda x: sortFunc(x)[corrImg], reverse=True)
        except IndexError:
            speckles.sort(key=lambda x: sortFunc(x), reverse=True)

        extremeSpeckles = []
        if best:
            extremeSpeckles += speckles[:numExtremeSpeckles]
        if worst:
            extremeSpeckles += speckles[-numExtremeSpeckles:]

        ens = Ensemble()
        ens.addSpeckle(extremeSpeckles)
        ens.updateEnsemble()
        ens.timeKey = self.timeKey
        return ens


def readFramesSquare(directory, squareSize=10, logging=True, skipStart=(0, 0),
                     skipEnd=(0, 0)):
    """
    Accepts directory as input, reads out all the frames in the folder,
    divides the frame evenly into squares (1 square = 1 speckle),
    then reads out the mean intensity of the square. Writes the Intensity
    of every speckle in every frame in a log file (if log is true)
    and outputs an Ensemble object containing the found speckles.

    input:
        directory: string, Directory containing the frames.
        squareSize: int, Length of each square side in pixel.
        skipStart: tuple consisting of int, skips the first squares in (x, y)
        direction.
        skipEnd: tuple, consisting of int, skips the last squares in (x, y)
        direction.
    output:
        ens: Ensemble object, containing the speckles found in the picture.
    """
    # Sorts frames by frame number. Frame numbers equals to timestep number.
    # Frames have to be sorted in order to correctly order akf.
    frames = [frame for frame in os.listdir(directory)
              if ut.match(r"\.bmp$", frame)]
    frames = sorted(frames, key=keyfunc)
    if frames == []:
        raise ValueError("Error: Could not find any frames in the given"
                          +  "directory. Aborting.")
    print("Found data: \n" + "\n".join(frames))

    # is used in the for loop for initiliation steps. assumes all frames
    # have equal dimensions (which they should have!)
    firstFlag = True

    count = 0

    xskipStart, yskipStart = skipStart
    xskipEnd, yskipEnd = skipEnd

    # processing of each frame
    for f in frames:

        # count used to show processing progress and to number the images
        count += 1
        print("Reading Frame No." + str(count) + "...")

        # reads image out to a numpy matrix, dimensions are img length
        path = directory + "\\" + f
        imgMat = cv2.imread(path, 0)

# -----------------------------------------------------------------------------
# Initiliazing log data headers and the lists that hold the data.
        if firstFlag:
            width = len(imgMat)
            height = len(imgMat[1])
            if width % squareSize != 0 or height % squareSize != 0:
                raise TypeError("Detector not divisble into even squares. "
                                + "Change Square Size to proceed.")

            # Determines the number of squares in both horizontal and vertical
            # direction
            numSquaresWidth = width // squareSize - xskipStart - xskipEnd
            numSquaresHeight = height // squareSize - yskipStart - yskipEnd

            # Initiliazes numpy array that later holds the intensity values for
            # every speckle. Weird notation: simply creates a numpy array
            # with dimensions of number of squares, every single element
            # being an empty list.
            speckleInt = np.empty((numSquaresWidth, numSquaresHeight),
                                  dtype=np.object_)
            speckleInt.fill([])
            speckleInt = np.frompyfunc(list, 1, 1)(speckleInt)

            # writes header for log data. Array filled with empty lists.
            # Log data is not meant to be human readable, but rather for use
            # with table calculation programs such as origin
            if logging:

                # log data for time intensity of every speckle
                numSpeckles = numSquaresWidth*numSquaresHeight
                logfilename = directory + ".asc"
                with open(logfilename, "w+") as log:
                    speckleString = "\t".join(["Speckle %d" % i
                                               for i in range(numSpeckles)])
                    log.write("Im. No." + "\t" + speckleString + "\n")
                firstFlag = False

                # initializing finished
                firstFlag = False

# -----------------------------------------------------------------------------

        # prepares list of intensities so writing to log is easier
        intensityList = []

        # divides the frame into squares and writes
        # the mean intensity of the square into the speckleInt matrix
        for x in range(xskipStart, numSquaresWidth - xskipEnd):
            for y in range(yskipStart, numSquaresHeight - yskipEnd):
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
    speckleIAKFS = []

    print("Creating Speckles...")

    for x in range(xskipStart, numSquaresWidth - yskipEnd):
        for y in range(yskipStart, numSquaresHeight - yskipEnd):
            speck = Speckle(speckleInt[x, y])
            speckleList.append(speck)

            if logging:
                speckleIAKFS.append(ut.list2string(speck.getTimeIAKF()))

    # print("Writing logs...")
    # if logging:
    #     # log data for IAKF of every speckle
    #     logfilenameIAKF = directory + "IAKF.asc"
    #     with open(logfilenameIAKF, "w+") as log:
    #         speckleString = "\t".join(["Speckle %d" % i
    #                                    for i in range(numSpeckles)])
    #         log.write("Im. No." + "\t" + speckleString + "\n")
    #         numbering = [str(i) for i in range(len(speckleIAKFS[0]))]
    #         speckleIAKFS.insert(0, numbering)
    #         log.write(ut.alternateWrite(speckleIAKFS))

    print("Creating Ensemble...")
    ens = Ensemble()
    ens.addSpeckle(speckleList)

    print("Calculating Ensemble AKFs...")
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


# folder = input("Folder to open: ")
# ensA = readFramesSquare(folder)
# ensA.createTimeKey([10000, 10000], [0.015, 0.1])
# ensA.log("ensA.asc")
#
#
# ensB = ensA.findExtremeSpeckles(0.4, best=True, worst=False,
#                                 sortFunc=Speckle.getTimeAverage)
# ensB.log("ensB.asc")
#
#
# ensC = readFramesSquare("frames2", skipStart=(0,8), skipEnd=(0, 12))
# ensC.createTimeKey([10000, 10000], [0.015, 0.1])
# ensC.log("ensC.asc")
#
# ensD = ensA.findExtremeSpeckles(0.2, best=True, worst=False,
#                                 sortFunc=Speckle.getTimeAverage)
# ensD.log("ensD.asc")
#
# # ensA.printStats()
# # ensB.printStats()
# # ensC.printStats()
# ensD.printStats()
#
# ensE = readFramesSquare("frames2", squareSize=2)
# ensE.createTimeKey([10000, 10000], [0.015, 0.1])
# ensE.logIAKF("specklesAR20", 1000)
# ensE.log("ensE.asc")

# ensF = readFramesSquare("frames160x120_400fps", squareSize=1)
# ensF.createTimeKey([3999], [0.0025])
# ensF.logIAKF("160x120_400fps", 1000)
# ensF.log("ensF.asc")
#
# ensG = readFramesSquare("frames320x240_200fps", squareSize=2)
# ensG.createTimeKey([2500], [0.005])
# ensG.logIAKF("320x240_200fps", 1000)
# ensG.log("ensG.asc")
#
# ensH = readFramesSquare("frames640x480_200fps", squareSize=4)
# ensH.createTimeKey([1999], [0.005])
# ensH.logIAKF("640x480_200fps", 1000)
# ensH.log("ensH.asc")

# ensI = readFramesSquare("frames640x480_200fps", squareSize=2)
# ensI.createTimeKey([1999], [0.005])
# # ensI.logIAKF("640x480_200fps", 1000)
# ensI.log("ensI.asc")

ensJ = readFramesSquare("framesLangzeit", squareSize=2, logging=False)
ensJ.createTimeKey([86400], [1])
ensJ.log("ensJ.asc")

























#------------------------------------------------------------------------------
#Testing Area
def randIntList(num):
    return [np.random.normal() for x in range(num)]

#
#dictDur = datetime.now()
#
##sets seed for testing
#np.random.seed(0)
#
##interactive Test
##numImg = int(input("Anzahl Bilder: "))
##numSpeckles = int(input("Anzahl Speckles: "))
#numImg = 100
#numSpeckles = 5
#
##gives out random normal distribution
#speckList = [Speckle(np.random.random_sample(numImg)*np.random.normal()) for x in range(numSpeckles)]
#
##Uniform random distribution
##speckList = [Speckle(randIntList(numImg)) for x in range(numSpeckles)]
#
##makes speed test for image number
#start = datetime.now()

#intList = []
#first = True
#with open("testGolde.txt", "r") as dat:
#    for line in dat:
#        if first:
#            sp = line.split("\t")
#            for k in range(len(sp)):
#                intList.append([])
#            first = False
#        splitLine = line.split("\t")
#        for i in range(len(splitLine)):
#            intList[i].append(float(splitLine[i].strip("\n")))
#
#speckList = []
#
#for lst in intList:
#    speckList.append(Speckle(lst))
#ens = Ensemble()
#ens.addSpeckle(speckList)
#ens.updateEnsemble()

#end = datetime.now()

#prints results of speed tests.
#print("Algorithm speed test results for", numImg, "Images and", numSpeckles, "Speckles.")
#print("Time needed for IAKF and List-making:", start-dictDur)
#print("Time needed for ensemble:", end-start)
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
