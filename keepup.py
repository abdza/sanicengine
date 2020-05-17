#!/usr/bin/env python3
from urllib.request import urlopen
import subprocess

gotpage = False
try:
    portal = urlopen('https://visitor.cbmyportal.org')
    mainpage = portal.read()
    if(str(mainpage).find('Welcome to CIMB Visitor')>0):
        gotpage = True
except:
    print("Not up")

if not gotpage:
    subprocess.run(["/opt/visitor/restart.sh",])
    f = open("/opt/visitor/restart.log","a+")
    f.write(str(timestamp))
    f.close()
    print("System restarted")
else:
    print("System intact")
