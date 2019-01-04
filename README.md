# lseval.py

## What does it do?
lseval.py serves as a small tool to perform perform evaluations and calculations on light-scattering data obtained from commercial machines, namely ALV-machines. The ALV-Correlator software produces a file in a specific format that this script can work with. Additionally, the tool can be used to perform multi-speckle-correlation given a stack of images, and also analysis of static light scattering data (experimental).

Example features:
* Read in an arbitrary amount of input data
* Output particle radius, coherence factor, mean countrate from sample data
* Use different fitting methods to obtain results (single exponential, double exponential...)

## How do I use it?

At the moment, lseval is still a command-line tool. You can see the help and further use by executing the script with an additional --help flag.

### Windows
1. Download the release.
2. Unzip the release.
3. Open up the cmd and switch to the "dist/lseval" directory (via the cd command).
4. Enter "lseval.exe", followed by any flags you need (for example --help).

### Linux
1. Download the Codebase.
2. Install pipenv.
3. Switch into the directory of your downloaded codebase, run "pipenv shell", then "pipenv install" (or install dependencies directly).
4. Run commands from pipenv, for example "lseval.py --help".

## To-Do
- Specify file structure for static light scattering
- Test further and fix various bugs
- Add setup.py to codebase
- Build graphical application for Text-interface
