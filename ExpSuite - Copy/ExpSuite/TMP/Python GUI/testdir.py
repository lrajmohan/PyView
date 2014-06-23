import os
currDir = os.getcwd()
print currDir
dirs = currDir.split('\\')
dirs.pop()
print dirs
currDir = '\\'.join(dirs)
print currDir
directory = currDir+'\\Time Stamps\\'
print directory
