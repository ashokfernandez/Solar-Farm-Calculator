import os
home = os.path.expanduser("~")
filename = os.path.join(home, ".foo.txt")
print filename
f = open(filename, 'w+')