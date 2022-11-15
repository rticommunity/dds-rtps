#!/usr/bin/python

import os
from qos import names
from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error
from datetime import date

today = date.today()
#d4 = today.strftime("%b-%d-%Y")
d4 = today.strftime('%Y%m%d-%H:%M:%S')
name = d4+'.xml'
xml = JUnitXml()
xml.write(name)
for k1 in names:
    for k2 in names:
        print('Testing -P %s -S %s' %(k1, k2))
        os.system('python interoperability_report.py -P %s -S %s -o %s' %(k1, k2, name))
        

