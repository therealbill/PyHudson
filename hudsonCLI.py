#!/usr/bin/python

import urllib2
from pprint import pprint
import datetime
import sys
import HudsonConnector

baseURL="http://ci:8080/"

class HudsonObject:
	def __init__(self,datadict):
		self.__dict__ = datadict

	def __repr__(self):
		return self.__dict__

def getDataForUrl(url):
	if url.endswith("api/python"):
		return eval( urllib2.urlopen(url).read() )
	else:
		return eval( urllib2.urlopen(url+"api/python").read() )

def objectifyJSON(jsondict):
	"""Recursive function to convert all dictionaries to HudsonObject"""
	for k,v in jsondict.items():
		if type(v) == 'dict':
			return HudsonObject(v)


baseData = getDataForUrl(baseURL+"api/python")
#pprint(baseData.keys())
"""
print "testing objectifyJSON"
root = objectifyJSON(baseData)
print root
print "done"
sys.exit(0)
"""

SHOWKEYS_JOB=False
SHOWKEYS_VIEW=False

#sys.exit(0)

servers=['qa6']
servers=['qa4']
servers=['qa3']

jobkeys = []




def showReport(servers):
	print
	jobkeys = []
	hbase = HudsonObject(baseData)
	if servers=="All":
		servers = [v['name'] for v in hbase.views]

	print "Running report for the following views:", ",".join(servers)

	for viewdata in hbase.views:
		viewname = viewdata['name']
		view = HudsonObject(getDataForUrl(viewdata['url']))
		if viewname == "All":
			continue
		elif viewname in servers:
			print "="*40
			print "View:",viewname
			#viewdata  = getDataForUrl(view.url)
			print "Description:", view.description
			#print "view keys:", viewdata.keys()
			print "Jobs"
			print "----"
			for jobdata in view.jobs:
				job = HudsonObject(getDataForUrl(jobdata['url']))
				#print job.color, job.healthReport, job.description
				print "(%s) %s" %(viewname,job.name)
				if jobkeys==[]:
					jobkeys= job.__dict__.keys()
				if job.lastBuild is not None:
					lastbuild = HudsonObject(getDataForUrl(job.lastBuild['url']))
					#pprint(lastbuild.__dict__)
					lbtime = datetime.datetime.fromtimestamp(lastbuild.timestamp/1000)
					print "\tLast Build was at", lbtime
					if job.buildable:
						print "\tStatus:", lastbuild.result
					else:
						print "\tStatus: DISABLED"
				elif job.firstBuild is None:
					print "\tStatus: NEVER RUN"
				else:
					if job.buildable:
						print "health report:", job.color, job.healthReport, job.description
						pprint(jobdata)
						pprint(job.__dict__)
					else:
						print "\tStatus: DISABLED"
					
				print

def runAllJobsForView(viewname):
	jobkeys = []
	hbase = HudsonObject(getDataForUrl(baseURL))
	for v in hbase.views:
		if v['name'] == viewname:
			view = HudsonObject( getDataForUrl(v['url']) )
			jobs = [HudsonObject(getDataForUrl(j)) for j in [x['url'] for x in view.jobs]]
			for j in jobs:
				if jobkeys ==[]:
					jobkeys = j.__dict__.keys()

				print
				print j.name
				print j.url

				if j.inQueue:
					print "Already in queue, skipping"
					continue
					
				if j.buildable:
					buildurl = j.url+"/build?delay=0"

					print "Calling:", buildurl
					result = urllib2.urlopen(buildurl)
					continue
				else:
					print "Job is DISABLED, skipping"
					continue
					
	print
	print "Job keys:",jobkeys



if __name__ ==  "__main__":
	args = sys.argv

	if len(args) ==1:
		showReport("All")	

	if args[1] == "--runall":
		servers = args[2].split(",")
		for svr in servers:
			print "Running all jobs for",svr
			runAllJobsForView(svr)

	if args[1] == "--report":
		servers = args[2].split(",")
		showReport(servers)


	
	

#showReport(servers)
#runAllJobsForView('qa6')



