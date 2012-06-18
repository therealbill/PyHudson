#!/usr/bin/python

import urllib2
from pprint import pprint
import datetime
import sys
import HudsonConnector
from optparse import OptionParser

def runAllJobsForView(hbase,viewname):
	view = hbase.getViewByName(viewname)

	if view is None:
		print "no view named '%s' was found" % viewname
		return

	print "Running all jobs for",view.name
	count_failed = 0
	for j in view.jobs.values():
		if j.inQueue:
			print j.name.ljust(40),"Already in queue, skipping"
			continue
			
		if j.buildable:
			buildurl = j.url+"/build?delay=0"
			result = urllib2.urlopen(buildurl)
			print j.name.ljust(40),"queued"
			continue
		else:
			print j.name.ljust(40),"Job is DISABLED, skipping"
			continue
					
def runAllFailedJobsForView(hbase,viewname):
	#hbase = HudsonConnector.HudsonConnector(baseUrl)
	view = hbase.getViewByName(viewname)

	if view is None:
		print "no view named '%s' was found" % viewname
		return

	print "Running all FAILED jobs for",view.name
	count_failed = 0
	for j in view.jobs.values():
		#print
		#print j.name
		#print j.url

		if j.inQueue:
			print "Already in queue, skipping"
			continue
			
		if j.buildable:
			try:
				last = j.lastBuild
				lb = HudsonConnector.HudsonObject( hbase.getDataFromUrl(last.url) )
				if lb.result == "FAILURE":
					buildurl = j.url+"/build?delay=0"
					print "Calling:", buildurl
					result = urllib2.urlopen(buildurl)
					count_failed+=1
					continue
			except:
				raise
		else:
			print "Job is DISABLED, skipping"
			continue
	print
	print "Found %i jobs to execute:" % count_failed
	print
					


if __name__ ==  "__main__":

	usage_statement = "Usage: %s (-l|-b|-f) -v <server name/list> [--help] [-u]\nSee --help for details"  % sys.argv[0]

	parser = OptionParser(usage_statement)
	parser.add_option("-l","--list", action="store_true", dest="listonly", help="Display a comma separated list of available views")
	parser.add_option("-f","--runfailed", action="store_true", dest="runfailed", help="Run all failed projects on the view or views in --views")
	parser.add_option("-b","--runbuildable", action="store_true", dest="runbuildable", help="Run all buildable projects on the view or views specified in --views")
	parser.add_option("-v","--views", dest="executeon",help="Comma separated list of views to report on",metavar="VIEWLIST")
	parser.add_option("-u","--url", dest="serverURL", help="The baseURL for the Hudson server", default="http://ci:8080/")
	(options, args) = parser.parse_args()
	print

	if len(args) ==1:
		print "I need you to use either --runall <svrlist> or --runfailed <svrlist"
		print "where <svrlist> is either a single server (view) name, or is a comma-separated list"
		print "without spaces, or angle brackets"


	if ( options.runfailed and options.runbuildable):
		print "Mutually exclusive options '--runbuildable' and 'runall' found."
		print "For clarity, please use only one."
		parser.error()

	if options.listonly:
		conn = HudsonConnector.HudsonConnector(options.serverURL)
		print "The server knows of these Views:"
		print "\t",",".join(conn.getPossibleViews())
		sys.exit(0)

	elif options.runbuildable:
		if options.executeon is None:
			parser.error("Need Server/View List")
		else:
			servers = options.executeon.split(",")
			conn = HudsonConnector.HudsonConnector(options.serverURL,servers)
			for svr in servers:
				runAllJobsForView(conn,svr)

	elif options.runfailed:
		if options.executeon is None:
			parser.error("Need Server/View List")
		else:
			servers = options.executeon.split(",")
			conn = HudsonConnector.HudsonConnector(options.serverURL,servers)
			for svr in servers:
				runAllFailedJobsForView(conn,svr)

	else:
		parser.print_help()
		sys.exit(-1)


	
	

#showReport(servers)
#runAllJobsForView('qa6')



