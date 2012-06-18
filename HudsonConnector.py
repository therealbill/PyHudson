#!/usr/bin/python

import urllib2
try:
	import json
except:
	import simplejson as json

import datetime
from pprint import pprint


__doc__= """
	HudsonConnector is a class that utilizes the Hudson remote JSON API to
	retrieve information from Hudson as well as issue commands.

"""
__author__ = "Bill Anderson <therealbill@me.com>"
__version__="$Revision: 1.5 $".split()[1]



__todos__= """
	* Need to subclass to create HudsonJob and HudsonView
	* Need to convert Connector loader to lazy load Views (and hence Jobs)
"""
class HudsonObject:
	"""
	Base Class for Hudson interface objects.
	Essentially it is initialized by a dictionary and will build
	a small DB of views and jobs.
	"""
	def __init__(self,datadict):
		for k,v in datadict.items():
			if type(v) == type({}):
				datadict[k] = self.objectifyDictionary(v)
		self.__dict__.update(datadict)
		if datadict.has_key(u"views"):
			self.objectifyViews()

		self._keys = datadict.keys()


	def objectifyViews(self):
		objectviews = []
		newviewsdict = {}
		for view in self.views:
			view_object = self.objectifyDictionary(view)

			newviewsdict[view_object.name] = self.objectifyJobs(view_object)
		self.views = HudsonObject(newviewsdict)

	def objectifyJobs(self,view):
		if view.name !="All":
			data = json.loads( urllib2.urlopen(view.url+"api/json").read() )
			jobs={}
			for j in data['jobs']:
				job = HudsonObject(j)
				jobs[job.name] = job
			view.jobs = HudsonObject(jobs)
			return view

	def values(self):
		return [v for k,v in self.__dict__.items() if k in self._keys]

	def items(self):
		return [[k,v] for k,v in self.__dict__.items() if k in self._keys]

	def keys(self):
		return self._keys

	def objectifyDictionary(self,data):
		hasDicts = False
		for v in data.values():
			if type(v) == type({}):
				hasDicts=True
				pass

		if hasDicts:
			for k,v in data.items():
				if type(v) == 'dict':
					data[k] = self.objectifyDictionary(v)

		else:
			return HudsonObject(data)

class HudsonConnector:
	"""
		A class serving as an interface to the Hudson Python RPC API
	"""


	def __init__(self,baseurl,viewlist=[],init=False):
		""" Initialize the connection and retrieve the root data"""
		self.baseURL = baseurl
		self.auto_init=init
		self.onviews=viewlist
		self.allviews={}

		self.getRootData()

	def getPossibleViews(self):
		return [ v['name'] for v in self.getDataFromUrl(self.baseURL)['views'] ]


	def getDataFromUrl(self,url):
		"""
			Given an item's URL, this method will return the necessary
			objects loaded from JSON. If the URL is raw (as in does not have an
			api/lang ending) it will append the needed "api/json" URL parts
			to ensure it only reads in JSON data.
			It will return a python representation of the data, such as a
			dictionary or list. Most often Hudson gives a dictionary that can
			have sub-dicts or lists, etc..
		"""
		if url.endswith("json"):
			return json.loads( urllib2.urlopen(url).read() )
		else:
			return json.loads( urllib2.urlopen(url+"api/json").read() )

	def getRootData(self):
		"""
			Opens a connection to Hudson and retrieves the data from the
			baseurl member variable.
		"""

		#hdict = json.loads( urllib2.urlopen(self.baseURL).read() )
		hdict = self.getDataFromUrl(self.baseURL)
		for k,v in hdict.items():
			if type(v) == type({}):
				hdict[k] = HudsonObject(v)

			self.__dict__.update(hdict)
			self._keys = hdict.keys()

		if self.auto_init:
			self.onviews = [v['name'] for v in self.views]

		self.initializeViews()

	def initializeViews(self):
		"""Initialize the views from the list"""

		""" Save original data away, as we will be overwriting self.views """
		for view in self.views:
			self.allviews[ view['name'] ] = view

		rawviews={}
		for vname in self.onviews:
			try:
				vd = self.allviews[vname]
				view = self.objectifyJobs( HudsonObject(vd) )
				rawviews[vd['name']] = view
			except KeyError:
				print "VIEW '%s' NOT FOUND" % vname
		self.views = rawviews

	def objectifyJobs(self,view):
		"""
			Given a view object this method will return a HudsonObject
			(or HudsonJob when implemented) representing the jobs for it.
		"""

		#if view.name != "All":
		data = json.loads( urllib2.urlopen(view.url+"api/json").read() )
		jobs={}
		for j in data['jobs']:
			j.update(self.getDataFromUrl(j['url']))
			job = HudsonObject(j)
			jobs[job.name] = job
		view.jobs = HudsonObject(jobs)
		return view

	def getViewByName(self,vname):
		"""
			Given the name of a view return it, or None if not found.
		"""
		try:
			return self.views[vname]
		except KeyError:
			return None

	def runBaseTesting(self,vnames):
		"""
			Basic testing sequence to validate the functionality of the class.
			Given the name of a view to test against it will output the name, description
			(if any), and list of jobs with the results of their last build - as implemented
			in showDataView(view).
		"""
		for vname in vnames:
			view = self.getViewByName(vname)
			if view is None:
				print "No view with name '%s' was found" % vname
				print "Known views are:"
				print ",".join( self.getPossibleViews() )
				#print ", ".join(self.views.keys())
				return False

			#print "Running Test on view '%s'" % view.name
			self.showViewData(view)


	def showViewData(self,view):
		"""
			Intended to be called by runBaseTesting(vname) ths method takes
			a view object and will print out the details of the view.
		"""
		print "\n\n"
		print "#"*80
		print "View Name:".ljust(15),view.name.rjust(30)
		print "#"*80
		print


		print "Job data"
		print "Job Name".ljust(29),"Last Run".ljust(24),"Result or Status"
		print "-"*72

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
						print job.name.ljust(29),"Has Not Ran".ljust(24),"Pending",'*'
						count_inqueue+=1
					else:
						print job.name.ljust(29),"Has Not Ran".ljust(24),"NOT RUN",'*'
					attention.append(job)
				else:
					print job.name.ljust(29),"Has Not Ran".ljust(24),"Disabled"
					count_disabled+=1
				continue

			try:
				lb = HudsonObject( self.getDataFromUrl(last.url) )
				stamp = datetime.datetime.fromtimestamp(lb.timestamp/1000)
			except:
				print "ERROR on ",job.name

				print dir(job)
				pprint(job.items())
				raise


			if not job.buildable:
				print job.name.ljust(29),str(stamp).ljust(24),"Disabled"
				count_disabled+=1
			else:
				count_buildable+=1
				if lb.result == "SUCCESS":
					print job.name.ljust(29),str(stamp).ljust(24),lb.result.capitalize()
					count_succesful+=1
				else:
					print job.name.ljust(29),str(stamp).ljust(24),lb.result,'*'
					attention.append(job)
					if lb.result == 'ABORTED':
						count_aborted+=1
					else:
						count_failed_buildable+=1

		print
		print " [Job Status Summary] ".center(70,"=").center(80)
		print "Total Jobs:".ljust(40),count_total
		print "Buildable Jobs:".ljust(40),count_buildable
		print "Disabled Jobs:".ljust(40),count_disabled
		print "Jobs in Queue:".ljust(40),count_inqueue
		print
		print "Successful Jobs:".ljust(40),count_succesful
		print "Aborted Jobs:".ljust(40),count_aborted
		print "Failed Buildable Jobs:".ljust(40),count_failed_buildable

		def getHealthRating():
			maxhealth = 5*count_total
			rating = (count_succesful*5) + (count_disabled*4) + (count_inqueue*3) + (count_aborted*2)
			health_pct =  rating/float(maxhealth)
			return (rating,maxhealth,health_pct)

		hr = getHealthRating()
		healthstring = "%i / %i" % (hr[0],hr[1])
		healthstring = "%.2f%%" % (hr[2]*100)
		print "Health Rating:".ljust(40), healthstring


		if len(attention) >0:
			print "\n"*3
			print " [ATTENTION ON JOBS] ".center(50,'*').center(80)
			for  job in attention:
				print job.name

		print "\n"*2




if __name__=='__main__':
	"""
		This is only called if Module is run as a script.
	"""

	print "\n"
	print " [Testing Connector] ".center(70,"*").center(80)
	print "\n"*2
	print "Version:".ljust(40),__version__

	import sys
	args = sys.argv

	test_targets = []
	try:
		test_targets = args[1].split(',')
	except:
		pass

	import time

	url = "http://hudsonserver:hudsonport/api/json"
	print "initializing connector...    ",
	start = time.time()
	conn = HudsonConnector(url,test_targets)
	stop = time.time()
	elapsed = stop - start

	print "initialized in %.2f seconds" % elapsed

	conn.runBaseTesting(test_targets)

