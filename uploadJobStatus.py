#!/usr/bin/python

import HudsonConnector
from optparse import OptionParser
import sys
from pprint import pprint
import datetime
from cStringIO import StringIO
import ConfigParser
import bpgsql
from os import path
import cPickle


STATEFILE = "/var/lib/hudsondb/lastrunat"

USER="hudsondb"
PW="hudson"
HOST="ito-tools-dev1"
DBASE = "hudsondb"

__doc__="""
A command line app that will retreive job status for jobs since last invocation and upload them to the db.
"""

__author__ = "Bill Anderson"
__author_email__ = "Bill Anderson therealbill@me.com"
__version__ = "$Revision: 1.1 $".split()[1]

serverURL = "http://ci:8080/"


class Application:
	def __init__(self):
		self.hudson = HudsonConnector.HudsonConnector(serverURL,['All'])
		self.db = bpgsql.Connection(dbname=DBASE,host=HOST,username=USER,password=PW)
		self.runtime = datetime.datetime.now()
		self.state={}
		self.loadState()

	def saveState(self):
		self.state['lastrun'] = self.runtime
		sfile = open(STATEFILE,'w')
		cPickle.dump(self.state,sfile)

	def loadState(self):
		"""Load last saved state from the statefile. State is a dictionary."""
		if not path.exists(STATEFILE):
			print "No previous statefile, assuming first run"
			self.state['lastrun'] = datetime.datetime.now()-datetime.timedelta(days=365)
		else:
			sfile = open(STATEFILE,'r')
			self.state = cPickle.load(sfile)
		self.lastrun = self.state['lastrun']

	def uploadJobState(self,jobdata):
		"""Uploads the results from a given job result set"""
		sql = "INSERT INTO jobresults(jobname,viewname,started,ended,result) VALUES (%s,%s,%s,%s,%s)"
		data = ( jobdata['name'], jobdata['view'], jobdata['start'], jobdata['end'],jobdata['result'] )
		csr = self.db.cursor()
		res = csr.execute(sql,data)
		print "Uploaded a build for %(name)s to the DB" % jobdata

	def getJobListFromDB(self):
		"""Returns a list of all current known jobs from the DB"""
		sql = "SELECT jobname from hudson_jobs"
		csr = self.db.cursor()
		csr.execute(sql)
		data = [ x[0] for x in csr.fetchall() ]
		return data

	def addJobToDb(self,jobname):
		"""Adds a job to the db"""
		sql = "INSERT INTO hudson_jobs(jobname) VALUES (%s)"
		csr = self.db.cursor()
		csr.execute(sql,[jobname])

	def getViewListFromDB(self):
		"""Returns a list of all current known views from the DB"""
		sql = "SELECT viewname from hudson_views"
		csr = self.db.cursor()
		csr.execute(sql)
		data = [ x[0] for x in csr.fetchall() ]
		return data

	def addViewToDb(self,name):
		"""Adds a view to the db"""
		sql = "INSERT INTO hudson_views(viewname) VALUES (%s)"
		csr = self.db.cursor()
		csr.execute(sql,[name])

	def getJobHistory(self,jobname):
		"""Return a multi-level dictionary containing the history of a given job"""
		pass

	def main(self):
		"""Application Point of Entry"""
		print "Retreiving view 'All",
		view_all = self.hudson.getViewByName('All')
		print "Done"
		print "iterating over jobs"
		for job in view_all.jobs.values():
			viewname = job.name.split(".")[0]
			if job.name not in self.getJobListFromDB():
				self.addJobToDb(job.name)
			if viewname not in self.getViewListFromDB():
				self.addViewToDb(viewname)
			for build in job.builds:
				bo = HudsonConnector.HudsonObject( self.hudson.getDataFromUrl(build['url']) )
				stamp = datetime.datetime.fromtimestamp(bo.timestamp/1000)
				if stamp > self.lastrun:
					if bo.result is None:
						runname = job.name+" #%d" % bo.number
						try:
							print runname.ljust(29),  str(stamp).ljust(24), bo.result.capitalize()
						except AttributeError:
							print runname.ljust(29),  str(stamp).ljust(24), "Unknown"
					else:
						jobdata = { 'name':job.name, 'view':job.name.split(".")[0], 'start':stamp, 
									'end':stamp  + datetime.timedelta(seconds=bo.duration),
									'duration':bo.duration,
									'result':bo.result
									}
						self.uploadJobState(jobdata)
		self.saveState()

if __name__ == '__main__':
	app = Application()
	app.main()

