# -*- coding: utf-8 -*-
"""
Created on Mon May 28 17:59:23 2018

@author: AGSchoepe
"""

import os
import re

def changeValues(path, setting, replace):
    """
    Input: 
        path: string, (full path, defautlt current folder)
        setting: regex, pattern to replace
        replace: regex, replacement
    """
    with open(path, "r") as f:
        content = f.read()
        
    newcontent = re.sub(setting, replace, content)
    with open(path, 'w') as f:
        f.write(newcontent)
        
    return

def changeForAll(filepattern, setting, replace, dirpath = os.getcwd(),):
    """
    Input: 
        dirpath: path to directory
        filepatter: regex the file name matches to
    rest see changeValues
    """
    names = os.listdir(os.getcwd())
    
    
    regex = re.compile(filepattern)
    for name in names:
        matchobj = regex.match(name)
        if not matchobj == None:
            print(dirpath + "\\" + name)
            changeValues(dirpath + "\\" + name, setting, replace)
    return

#for testing
testpath = 'C:\\Users\\AGSchoepe\\OneDrive\\Alex\\Bachelor Thesis\\Messdaten\\20182805 First-Test\\'
setting = r"632.0*\n"
replace = r"532.0000\n"
filepattern = r"DLS.*\.txt"

"test"