import argparse
import dlsprocessing as dlsp
import slsprocessing as slsp
import fitfunctions as ff
import utils
import os
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="General light scattering"
                                 + " data processor")

parser.add_argument("files", metavar="f", nargs="*",
                    help="The file names that should be analyzed together."
                    + " All the files must belong to a single sample.")
parser.add_argument("-d", "--dir", action="store_true",
                    help="If this option is enabled, directories can be"
                    + " specified as input instead of files. Every directory"
                    + " should then represent a unique sample.")
parser.add_argument("-ff", "--fitfunction", default="singleExp",
                    choices=["singleExp", "doubleExp",
                             "cum2", "cum3", "cum3b"],
                    help="Fit function that is used to during fitting."
                    + "default: %(default)s")
parser.add_argument("-st", "--start", type=int, default=0,
                    help="First data entry that is used during fitting, if "
                    + "fitting should start at a later point.")
parser.add_argument("-fo", "--falloff", type=float, default=0,
                    help="Can be used to set a premature end to the fit after "
                    + "the point whose value is lower than the start*falloff.")
parser.add_argument("-r", "--recursive", action="store_true",
                    help="Reserved for future use.")
parser.add_argument("-l", "--log", action="store_true",
                    help="Saves some stats in a txt file.")
parser.add_argument("-sls", action="store_true",
                    help="Uses SLS mode for data evaluation."
                    + "Only -pmcr, -cmp work.")
parser.add_argument("-pcr", "--plotcorr", action="store_true",
                    help="Plots (logy) autocorrelation function against q^2.")
parser.add_argument("-pmcr", "--plotmeanCR", action="store_true",
                    help="Plots mean correlation against angle.")
parser.add_argument("-pcf", "--plotcoherencefactor", action="store_true",
                    help="Plots coherence factor against angle.")
parser.add_argument("-pg", "--plotgamma", action="store_true",
                    help="Plots Gamma against angle and prints Hydrodynamic"
                    + " radius by linear fitting.")
parser.add_argument("-cmp", "--compareCR", action="store", nargs=2,
                    help="Compares two mean countrates by diving them against"
                    + " each other and plotting the result over the angle."
                    + " The first value is divided by the second, the "
                    + "plots get saved in the folder of the first sample.")
parser.add_argument("-pm", "--plotmode", default="lin",
                    choices=["xlog", "ylog", "loglog", "lin"],
                    help="Sets plot mode for the plotting flags.")
parser.add_argument("-phr", "--plotradius", action="store_true",
                    help="Plots hydrodynamic radius for every angle.")
args = parser.parse_args()

# Recognizes the plotmode that was put in and assigns it to a plotting function
plotdict = {
                "xlog": plt.semilogx,
                "ylog": plt.semilogy,
                "loglog": plt.loglog,
                "lin": plt.plot
}

plotmode = plotdict[args.plotmode]

# Enables use of . operators.
if args.files == ["."]:
    files = [os.getcwd()]
    args.dir = True
elif args.files == [".."]:
    files = [os.path.dirname(os.getcwd())]
    args.dir = True

# DLS plotting branch
if not args.sls:
    fitfunc = eval("ff.%s" % args.fitfunction)

    if args.compareCR is not None:
        dlsp.compareCRs(args.compareCR[0], args.compareCR[1], plotmode)

    if args.dir:
        for file in args.files:

            dlsp.dlsplot(file, fitfunc, args.start, args.falloff, args.log,
                         plotCorr=args.plotcorr, plotMeanCR=args.plotmeanCR,
                         plotCoherence=args.plotcoherencefactor,
                         plotGamma=args.plotgamma, plotHydroR=args.plotradius,
                         plotmode=plotmode)
    else:
        files = args.files
        dlsp.dlsplot(files, fitfunc, args.start, args.falloff, args.log,
                     plotCorr=args.plotcorr, plotMeanCR=args.plotmeanCR,
                     plotCoherence=args.plotcoherencefactor,
                     plotHydroR=args.plotradius, plotGamma=args.plotgamma,
                     plotmode=plotmode)


# SLS Processing branch
else:
    if args.dir:
        for file in args.files:
            if args.plotmeanCR:
                ddict = slsp.readElementsAndProcess(file)
                slsp.plotMeanCRs(ddict, plotmode)

    else:
        if args.plotmeanCR:
            ddict = slsp.readElementsAndProcess(args.files)
            print(args.files)
            slsp.plotMeanCRs(ddict, plotmode)

    if args.compareCR is not None:
        slsp.compareCRs(args.compareCR[0], args.compareCR[1], plotmode)

if __name__ == "__main__":
    pass
