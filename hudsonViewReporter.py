#!/usr/bin/python

import HudsonConnector
from optparse import OptionParser
import sys
from pprint import pprint
import datetime
from cStringIO import StringIO
import ConfigParser

__doc__="""
A command line app that will output view information for specified views, 
show current state of all jobs run in the last specified hours, or list all
known views """ 

__author__ = "Bill Anderson"
__author_email__ = "Bill Anderson bill.anderson@bodybuilding.com"
__version__ = "$Revision: 1.1 $".split()[1]


def getAllJobsReportLastXHours(conn,hours,allbuilds=False):
	Report = StringIO()
	hours = float(hours)
	now = datetime.datetime.now()
	starter = now - datetime.timedelta(hours=hours)
	vname = 'All'
	view = conn.getViewByName(vname)
	count_failed = 0
	count_aborted = 0
	count_total = 0
	count_succesful = 0
	counts = { "FAILURE":0, "SUCCESS":0, "ABORTED":0, "INQUEUE":0 }
	final_counts = { "FAILURE":0, "SUCCESS":0, "ABORTED":0, "INQUEUE":0 }

	print >>Report,"#"*80
	print >>Report, "Report run at".ljust(39), str(now).rjust(40)
	print >>Report, "Most recent results for jobs run since".ljust(39), str(starter).rjust(40)
	print >>Report, "Report type:".ljust(39),
	if allbuilds:
		print >>Report, "All Jobs".rjust(40)
	else:
		print >>Report, "Current state of run Jobs".rjust(40)

	print >>Report,"#"*80
	print >>Report, ""
	print >>Report, "Job Name".ljust(29),"Last Run".ljust(24),"Result or Status"
	print >>Report, "-"*80

	testx=0

	if not view:	
		print >>Report, "view not found: '%s'" % vname
		Report.seek(0)
		return Report.read()

	jobslist = view.jobs.keys()
	jobslist.sort()
	for jobname in jobslist:
		job = view.jobs.__dict__[jobname]
		have_latest_result = False
		if job.buildable:
			if allbuilds:
				for build_i in job.builds:
					bo = HudsonConnector.HudsonObject( conn.getDataFromUrl(build_i['url']) )
					stamp = datetime.datetime.fromtimestamp(bo.timestamp/1000)
					if stamp >starter:
						if bo.result is None:
							bo.result = "INQUEUE"
						count_total+=1
						testx+=1
						runname = job.name+" #%d" % bo.number
						try:
							print >>Report, runname.ljust(29),  str(stamp).ljust(24), bo.result.capitalize()
						except AttributeError:
							print >>Report, runname.ljust(29),  str(stamp).ljust(24), "Unknown"
						counts[bo.result]+=1
						if not have_latest_result:
							final_counts[bo.result] += 1
							have_latest_result = True
					else:
						continue
					print >>Reporter,""

			else:
				last = job.lastBuild
				count_total+=1
				try:
					lb = HudsonConnector.HudsonObject( conn.getDataFromUrl(last.url) )
					stamp = datetime.datetime.fromtimestamp(lb.timestamp/1000)
					if stamp > starter:
						if lb.result is None:
							lb.result = "INQUEUE"
						print >>Report, job.name.ljust(29), str(stamp).ljust(24), lb.result.capitalize()
						counts[lb.result]+=1
				except:
					pass

	
	section_hdr = ""
	if allbuilds:
		section_hdr = "State Summary for all jobs run in the last %.2f hours" % hours
	else:
		section_hdr = "Current State Summary for jobs run in the last %.2f hours" % hours
	print >>Report, ""
	print >>Report, section_hdr.center(80)
	total = 0
	for k in ("SUCCESS","FAILURE","ABORTED","INQUEUE"):
		print >>Report,k.ljust(40), str(counts[k]).rjust(20)
		total += counts[k]
	if allbuilds:
		print >>Report, "Unresolved failures".ljust(40), str(final_counts['FAILURE']).rjust(20)
	Report.seek(0)
	return Report.read()

def getReportForView(conn,vname):
	"""
		Given a HudsonConnection and a view name, print out the details of the view.
	"""

	Report = StringIO()
	view = conn.getViewByName(vname)
	if view is None:
		print >>Report, "View '%s' not found" % vname
		return Report
	print >>Report, "#"*80
	print >>Report, "View Name:".ljust(15),view.name.rjust(50)
	print >>Report, "Report Run At:".ljust(15), str(datetime.datetime.now()).rjust(50)
	print >>Report, "#"*80
	print  >>Report, ""
	print >>Report, "Job Name".ljust(29),"Last Run".ljust(24),"Result or Status"
	print >>Report, "-"*80
	attention = []
	count_buildable = 0
	count_failed_buildable = 0
	count_disabled = 0
	count_aborted = 0
	count_succesful = 0
	count_total=0
	count_inqueue=0

	for job in view.jobs.values():
		last = job.lastBuild
		count_total+=1
		if last is None:
			if job.buildable:
				count_buildable+=1
				if job.inQueue:
					print >>Report, job.name.ljust(29),"Has Not Ran".ljust(24),"Pending",'*'
					count_inqueue+=1
				else:
					print >>Report, job.name.ljust(29),"Has Not Ran".ljust(24),"NOT RUN",'*'
				attention.append(job)
			else:
				print >>Report, job.name.ljust(29),"Has Not Ran".ljust(24),"Disabled"
				count_disabled+=1
			continue
		try:
			lb = HudsonConnector.HudsonObject( conn.getDataFromUrl(last.url) )
			stamp = datetime.datetime.fromtimestamp(lb.timestamp/1000)
		except:
			print >>Report, "ERROR on ",job.name
			print dir(job)
			pprint(job.items())
			raise
		if not job.buildable:
			print >>Report, job.name.ljust(29),str(stamp).ljust(24),"Disabled"
			count_disabled+=1
		else:
			count_buildable+=1
			if lb.result == "SUCCESS":
				print >>Report, job.name.ljust(29),str(stamp).ljust(24),lb.result.capitalize()
				count_succesful+=1
			else:
				print >>Report, job.name.ljust(29),str(stamp).ljust(24),lb.result,'*'
				attention.append(job)
				if lb.result == 'ABORTED':
					count_aborted+=1
				else:
					count_failed_buildable+=1

	print >>Report, ""
	print >>Report, "[ Job Status Summary ]".center(80,"=")
	print >>Report, "Total Jobs:".ljust(40),count_total
	print >>Report, "Buildable Jobs:".ljust(40),count_buildable
	print >>Report, "Disabled Jobs:".ljust(40),count_disabled
	print >>Report, "Jobs in Queue:".ljust(40),count_inqueue
	print >>Report, ""
	print >>Report, "Successful Jobs:".ljust(40),count_succesful
	print >>Report, "Aborted Jobs:".ljust(40),count_aborted
	print >>Report, "Failed Buildable Jobs:".ljust(40),count_failed_buildable

	def getHealthRating():
		maxhealth = 5*count_total
		rating = (count_succesful*5) + (count_disabled*4) + (count_inqueue*3) + (count_aborted*2) 
		health_pct =  rating/float(maxhealth)
		return (rating,maxhealth,health_pct)

	hr = getHealthRating()
	healthstring = "%d / %d" % (hr[0],hr[1])
	healthstring = "%.2f%%" % (hr[2]*100)
	print >>Report, "Health Rating:".ljust(40), healthstring

	if len(attention) >0:
		print >>Report, "\n"
		print >>Report, "[ ATTENTION ON JOBS ]".center(80,'*').center(80)
		for  job in attention:
			print >>Report, job.name

	print >>Report, "\n"
	Report.seek(0)
	finished_report = Report.read()
	return finished_report


def deliverReport(options,report,view=""):
	if options.mailto:
		subject=""
		if options.doJobsReport:
			if options.doAllJobs:
				subject = "[Hudson] All Jobs Report for the last %s hours" % options.hours
			else:
				subject = "[Hudson] Jobs Report for the last %s hours" % options.hours
		elif options.reporton:
			subject = "[Hudson] View Report for %s" % view
		import email
		import smtplib
		msg = email.message_from_string(report)
		msg['To'] = options.mailto
		Sender = "HudsonViewReporter <donotreply@bodybuilding.com"
		msg['From'] = Sender
		msg['Subject'] = subject
		svr = smtplib.SMTP("exchgstore.body.local")
		svr.sendmail(Sender,options.mailto.split(","),msg.as_string())
	else:
		print report


if __name__=='__main__':
	parser = OptionParser()
	parser.add_option("-l","--list", action="store_true", dest="listonly", help="Display a comma separated list of available views")
	parser.add_option("-u","--url", dest="serverURL", help="The baseURL for the Hudson server", default="http://ci:8080/")
	parser.add_option("-v","--views", dest="reporton",help="Comma separated list of views to report on",metavar="VIEWLIST")
	parser.add_option("-m","--mailto", dest="mailto", help="Sends an email to the specified address", metavar="EMAILADDRESS")
	parser.add_option("-t","--hours", dest="hours", help="In conjunction with --jobs/-j, specify the hours to go back. Default is 1 hour", metavar="HOURS", default=1)
	parser.add_option("-j","--jobs", dest="doJobsReport", action="store_true", help="Run a report showing *current* status of all jobs run. Requires -t/--hours option" )
	parser.add_option("-a","--alljobs", dest="doAllJobs", action="store_true", help="Run a report showing status of every job run in the window specified by -t/--hours. Requires -t/--hours option" )

	(options,args) = parser.parse_args()

	if options.listonly:
		conn = HudsonConnector.HudsonConnector(options.serverURL)
		print "The server knows of these Views:"
		print "\t",",".join(conn.getPossibleViews())
		sys.exit(0)

	if options.doJobsReport:
		conn = HudsonConnector.HudsonConnector(options.serverURL,['All'])
		report = getAllJobsReportLastXHours(conn,options.hours,options.doAllJobs)
		deliverReport(options,report)
		sys.exit(0)

	if options.reporton:
		views  = options.reporton.split(",")
		conn = HudsonConnector.HudsonConnector(options.serverURL,views)
		for view in views:
			report =  getReportForView(conn,view)
			deliverReport(options,report,view)

		
