# -*- coding: utf-8 -*-
"""
Created on Fri May 11 11:04:44 2018

@author: Alexander Conzelmann | lexan@kabelbw.de
"""
import numpy as np
from datetime import datetime
from scipy import signal
import matplotlib.pyplot as plt

def xcorr(x, y, scale='none', SciPy = True):
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
        #does convolution with one array turned around
        corr = signal.fftconvolve(x, y[::-1], mode = 'full')
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
    Class of speckle object. 
    """
    def __init__(self, timeInt):
        """
        Can take in an intensity list which maps specific points in
        measurement time (images) to the intensity that the speckle held at this point.
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
        Getter method for time Intensity Autocorrelation Function of the speckle.
        """
        return self.timeIAKF
    
    def getTimeFAKF(self):
        """
        Getter method for Field Autocorrelation Function of the speckle.
        """
        return self.timeFAKF
    
    def addInt(self, timeInt, update = True):
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
        #unnormalized autocorrelation function
        unnAKF = xcorr(intArr, intArr, 'unbiased', True)[0]
        
        #Weird indexing is because of how the function xcorr produces its array
        self.timeIAKF = unnAKF[(len(intArr)-1):(2*len(intArr))] / (self.timeAvg)**2
        return
    
    def calcTimeFAKF(self):
        self.timeFAKF = (abs((self.timeIAKF-1) / \
                                 (self.timeIAKF[0]-1)))**(1/2)
    
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
    def __init__(self, speckles = []):
        self.speckles = []
        self.numSpeckles = 0
    
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
            except:
                eIAKF = speck.timeIAKF * speck.timeAvg**2
        ensembleIAKF = eIAKF/(len(self.speckles) * self.ensembleAvg**2)
        self.ensembleIAKF = ensembleIAKF
        return
    
    def calcEnsembleFAKF(self):
        """
        Calculates field autocorrelation function (FAKF, g1, f_E (dynamic structure factor))
        for the ensemble, based on the ensemble IAKF. 
        """
        self.ensembleFAKF = (abs((self.ensembleIAKF-1) / \
                                 (self.ensembleIAKF[0]-1)))**(1/2)
        return 
    
    def updateEnsemble(self):
        """
        Updates Ensemble by calculating Intensity Average, IAKF, FAKF.
        """
        self.calcEnsembleAvg()
        self.calcEnsembleIAKF()
        self.calcEnsembleFAKF()
        return
    
    def findExtremeSpeckles(self, percent, corrImg = 0, best=True, \
                            worst=True, sortFunc = Speckle.getTimeIAKF):
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
            raise IndexError("Correlation image higher than number of total images")
        
        if not (best or worst):
            print("Either fast or slow must be set to True!")
            return
        
        numExtremeSpeckles = int(percent*self.numSpeckles)        
        
        #copies speckle list to not modify the origial
        speckles = self.speckles[:]
        
        # Sorts speckles by intensity at positiong (image) corrImg.
        # Index error means that an integer was produced by the sort function,
        # in which case we catch the error and use an unsubscripted sortFunc.
        try:
            speckles.sort(key = lambda x: sortFunc(x)[corrImg])
        except IndexError:
            speckles.sort(key = lambda x: sortFunc(x))
        
        extremeSpeckles = []
        if best:
            extremeSpeckles += speckles[:numExtremeSpeckles]
        if worst:
            extremeSpeckles += speckles[-numExtremeSpeckles:]

        ens = Ensemble()
        ens.addSpeckle(extremeSpeckles)
        return ens

#------------------------------------------------------------------------------
#Testing Area
def randIntList(num):
    return [np.random.normal() for x in range(num)]


dictDur = datetime.now()

#sets seed for testing
np.random.seed(0)

#interactive Test
#numImg = int(input("Anzahl Bilder: "))
#numSpeckles = int(input("Anzahl Speckles: "))
numImg = 10000
numSpeckles = 500

#gives out random normal distribution
speckList = [Speckle(np.random.random_sample(numImg)*np.random.normal()) for x in range(numSpeckles)]

#Uniform random distribution
#speckList = [Speckle(randIntList(numImg)) for x in range(numSpeckles)]

#makes speed test for image number
start = datetime.now()


ens = Ensemble()
ens.addSpeckle(speckList)
ens.updateEnsemble()

end = datetime.now()

#prints results of speed tests.
print("Algorithm speed test results for", numImg, "Images and", numSpeckles, "Speckles.")
print("Time needed for IAKF and List-making:", start-dictDur)
print("Time needed for ensemble:", end-start)

compImg = 10

#compares histograms and tests extreme speckles method.
arr = []
for k in range(len(ens.speckles)):
    arr.append(ens.speckles[k].getTimeIAKF()[compImg])
arr = np.array(arr)
plt.hist(arr, label = "Normal Speckles")

ensext = ens.findExtremeSpeckles(0.1, compImg, worst = True, sortFunc = Speckle.getTimeIAKF)
arr2 = []
for k in range(ensext.numSpeckles):
    arr2.append(ensext.speckles[k].getTimeIAKF()[compImg])
arr2 = np.array(arr2)
plt.hist(arr2, label = "Extreme Speckles")
plt.legend(loc = "best")

#for use in the shell
#input("Finished. Press enter to exit.")
#------------------------------------------------------------------------------
