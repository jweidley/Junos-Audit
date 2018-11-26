#!/usr/bin/python
# Purpose: Run predefined audit checks on Junos Configuration files that are in 'set' format.
# Version: 0.11
#####################################################################################################################

############################################
## Modules
############################################
import ConfigParser
import sys
import io
import os
import re
import shutil
from checkModules import *

############################################
## Read in configuration file
############################################
print "\n#################################################################################################"
print "# J U N O S  A U D I T "
print "#################################################################################################"
sys.stdout.write("+ Reading configuration file......................")

############################################
## Read in junosAudit.ini configuration file
############################################
try:
	with open('junosAudit.ini') as f:
		junosAudit_config = f.read()
		config = ConfigParser.RawConfigParser(allow_no_value=True)
		config.readfp(io.BytesIO(junosAudit_config))
        print " SUCCESS"
except IOError:
	print " FAILED!"
	print "\n\nERROR: Could not find configuration file: junosAudit.ini\n"
	exit()

# Check if necessary directories exist
sys.stdout.write("+ Working Directory Exists........................")
if os.path.exists(config.get('global', 'workDir')):
	print " SUCCESS"
else:
	print " FAILED!"
	print "\nERROR: Working directory Does NOT exist: " + config.get('global', 'workDir')
	exit()

sys.stdout.write("+ HTML Directory Exists...........................")
if os.path.exists(config.get('global', 'htmlDir')):
	print " SUCCESS"
else:
	print " FAILED!"
	print "\nERROR: HTML directory Does NOT exist: " + config.get('global', 'htmlDir')
	exit()

sys.stdout.write("+ Template Directory Exists.......................")
if os.path.exists(config.get('global', 'templateDir')):
	print " SUCCESS"
else:
	print " FAILED!"
	print "\nERROR: Template directory Does NOT exist: " + config.get('global', 'templateDir')
	exit()

sys.stdout.write("+ Configuration Directory Exists..................")
if os.path.exists(config.get('global', 'configDir')):
	print " SUCCESS"
	filenames = os.listdir(config.get('global', 'configDir'))
	filenames.remove('README')	## Remove the README file from processing

else:
	print " FAILED!"
	print "\nERROR: Configuration Directory Does NOT exist: " + config.get('global', 'configDir')
	exit()

##################################################################################
## Functions
##################################################################################
def buildIndex(filenames,config):
	htmlDir = config.get('global', 'htmlDir')
	indexFile = "%s/index.html" % (htmlDir)

	# Create file
	index = open(indexFile, "w")
	index.write("<html><head><title>Index</title></head><body><pre>\n")

	for i in filenames:
		index.write(i)
		index.write("\n")

	index.write("\n</pre></body></html>")
	index.close()

def preStaging(filenames,config):
	sys.stdout.write("+ Copying configurations to working directory.....")
	configDir = config.get('global', 'configDir')
	workDir = config.get('global', 'workDir')

	for file in filenames:
		deviceFile = "%s/%s" % (configDir,file)
		workFile = "%s/%s" % (workDir,file) 
	
		shutil.copy(deviceFile, workFile)

		# Add corrective action footer to each working file
		file = open(workFile, "a")
		file.write("<br><hr><h4>Corrective Actions</h4><hr>\n")
		file.close()

	print " SUCCESS"

def finalize(filenames,config):
	sys.stdout.write("\n+ Finalizing Device Reports.......................")
	workDir = config.get('global', 'workDir')
	htmlDir = config.get('global', 'htmlDir')
	if config.has_option('site', 'customer'):
		customerName = config.get('site', 'customer')
	else:
		print "\n\t!WARNING: site/customer name NOT set in junosAudit.ini. Setting customer to NOT-SET\n"
		customerName = "NOT-SET"

	# Build HTML output files from working files
	for filename in filenames:
		workFile = "%s/%s" % (workDir,filename) 
		htmlFile = "%s/%s.html" % (htmlDir,filename) 

		# Read workfile into memory
		with open(workFile, "r") as file:
			lines = [line.strip() for line in file]
		file.close()

		# Create html outfile
		file = open(htmlFile, "w")
		file.write("<html>\n<style>\n")
		file.write(".greentip {\n")
		file.write("       position: relative;\n")
		file.write("       display: inline-block;\n")
		file.write("       color: green;\n")
		file.write("       border-bottom: 1px dotted black; \n}\n")
		file.write(".greentip .greentiptext {\n")
		file.write("       visibility: hidden;\n")
		file.write("       width: 260px;\n")
		file.write("       background-color: green;\n")
		file.write("       color: #fff;\n")
		file.write("       text-align: center;\n")
		file.write("       border-radius: 6px;\n")
		file.write("       padding: 5px 0;\n")
		file.write("       position: absolute;\n")
		file.write("       z-index: 1;\n")
		file.write("       bottom: 150%;\n")
		file.write("       left: 50%;\n")
		file.write("       margin-left: -60px;\n}\n")
		file.write(".greentip .greentiptext::after {\n")
		file.write("       content: "";\n")
		file.write("       position: absolute;\n")
		file.write("       top: 100%;\n")
		file.write("       left: 50%;\n")
		file.write("       margin-left: -5px;\n")
		file.write("       border-width: 5px;\n")
		file.write("       border-style: solid;\n")
		file.write("       border-color: black transparent transparent transparent;\n}\n")
		file.write(".greentip:hover .greentiptext {\n")
		file.write("       visibility: visible;\n}\n")
		file.write(".redtip {\n")
		file.write("       position: relative;\n")
		file.write("       display: inline-block;\n")
		file.write("       color: red;\n")
		file.write("       border-bottom: 1px dotted black; \n}\n")
		file.write(".redtip .redtiptext {\n")
		file.write("       visibility: hidden;\n")
		file.write("       width: 260px;\n")
		file.write("       background-color: red;\n")
		file.write("       color: #fff;\n")
		file.write("       text-align: center;\n")
		file.write("       border-radius: 6px;\n")
		file.write("       padding: 5px 0;\n")
		file.write("       position: absolute;\n")
		file.write("       z-index: 1;\n")
		file.write("       bottom: 150%;\n")
		file.write("       left: 50%;\n")
		file.write("       margin-left: -60px;\n}\n")
		file.write(".redtip .redtiptext::after {\n")
		file.write("       content: "";\n")
		file.write("       position: absolute;\n")
		file.write("       top: 100%;\n")
		file.write("       left: 50%;\n")
		file.write("       margin-left: -5px;\n")
		file.write("       border-width: 5px;\n")
		file.write("       border-style: solid;\n")
		file.write("       border-color: black transparent transparent transparent;\n}\n")
		file.write(".redtip:hover .redtiptext {\n")
		file.write("       visibility: visible;\n}\n")
		file.write("h1 span {\n")
		file.write("       background: grey;\n")
		file.write("       color: #fff;\n")
		file.write("       padding: 0 20px;\n")
		file.write("       display: inline-block;\n}\n")
		file.write("</style><head><title>Junos Audit Results: " + filename + " </title></head><body><pre>\n")
		file.write("<h1><span>Junos Config Audit: " + customerName + ": " + filename + "</span></h1>\n")

		for line in lines:
			file.write(line)
			file.write("\n")

		file.write("\n</pre></body></html>\n")
		file.close()

		# Remove working files
		os.remove(workFile)

	print " SUCCESS"

############################################
## main
############################################
preStaging(filenames,config)

# Run checks on configuration files
sys.stdout.write("+ Running Audit Checks: ")
for file in filenames:
	checkJunosVersion(file,config)
	checkCLIs(file,config)
	checkPartial(file,config)
	checkSNMP(file,config)
	checkTraceoptions(file,config)
	checkAccounts(file,config)
	checkNTP(file,config)

finalize(filenames,config)
#buildIndex(filenames,config)

## end of file ##
