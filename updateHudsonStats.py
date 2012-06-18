#!/usr/bin/python


import bpgsql
from optparse import OptionParser
import syslog
import datetime


USER="hudsondb"
PW="hudson"
HOST="ito-tools-dev1"
DBASE = "hudsondb"

__doc__="""
A command line app that will retreive job status for jobs since last invocation and upload them to the db.
"""

__author__ = "Bill Anderson"
__author_email__ = "Bill Anderson bill.anderson@bodybuilding.com"
__version__ = "$Revision: 1.1 $".split()[1]




if __name__=='__main__':
	
