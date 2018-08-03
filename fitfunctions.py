import numpy as np


def singleExp(x, a, b):
        """
        Fit function for single exponential autocorrelation function.

        Assumes ergodic samples, for which the siegert relation is valid:
            g2 = 1 + g1^2
            g2 - 1 = a * e^-2*Gamma*tau (g2 - 1 = akf)
        and
            Gamma = Ds*q^2
        """
        return a * np.exp(-2*b*x)


def doubleExp(x, a1, a2, b1, b2):
    """
    Double exponential autocorrelation function.a1

    Assumes: g2 - 1 = a1 * e^(-2*Gamma*tau)
    """
    return a1*np.exp(-2*b1*x) + a2*np.exp(-2*b2*x)


def cum2(x, a, gammaMean, mu2):
    """
    Cumulant with three cumulants:
        g1 = a* exp(-gammaMean (x - mu2/2*x**2)
    """
    return a*np.exp(-gammaMean*(x - mu2/2*x**2))


def cum3(x, a, gammaMean, mu2, mu3):
    """
    Cumulant with three cumulants:
        g1 = a* exp(-gammaMean (x - mu2/2*x**2 + mu3/6*x**3))
    """
    return a*np.exp(-gammaMean*(x - mu2/2*x**2 + mu3/6*x**3))


def nameOf(function):
    nameDict = {
        singleExp: "Single Exponential",
        doubleExp: "Double Exponential",
        cum2: "2-Cumulant",
        cum3: "3-Cumulant"
    }
    return nameDict[function]
