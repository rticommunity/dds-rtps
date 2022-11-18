#!/usr/bin/python

import os
from qos import names
from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Error
from datetime import datetime

#add option -verbose
now = datetime.now()
date_time = now.strftime('%Y%m%d-%H:%M:%S')
name = date_time+'.xml'
xml = JUnitXml()
xml.write(name)
for k1 in names:
    for k2 in names:
        print('Testing -P %s -S %s' %(k1, k2))
        os.system('python interoperability_report.py -P %s -S %s -o %s' %(k1, k2, name))
        

