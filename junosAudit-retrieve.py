#!/usr/bin/python
# Purpose: Grab device model & version and configuration (set format). This script can be used to automate the 
# 	configuration retrieval for junosAudit.
# Version: 0.2
##############################################################################################################

#################################
# Variables
#################################
# configDir is where the output will be written
configDir = "./Configs"

# Devices is a list of IP addresses of the devices to grab configs from.
devices = [
	'192.168.3.1',
	'192.168.3.101'
	]

#################################
# Modules
#################################
import sys
from getpass import getpass
from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree

#################################
# Main
#################################
print "\n#############################################################################"
print " Junos Audit: Retrieve Required Information"
print "#############################################################################"
print "Enter Credentials for all devices"

username = raw_input("Username: ")
passwd = getpass()

# Loop through devices and gather information
for device in devices:

	# Open file for writing
	fileName = configDir + "/" + device + "-config.txt"
	file = open(fileName, "w")

	# Login to the device and grab the neccessary information
	dev = Device(host=device, user=username, password=passwd)

	try: 
		dev.open()

		print "Fetching data for " + device

		file.write("############ Device Facts ################\n")
		file.write("Model: " + dev.facts['model'])
		file.write("\n")
		file.write("Version: " + dev.facts['version'])
		file.write("\n\n")

		# Junos OS set format
		data = dev.rpc.get_config(options={'format':'set'})
		file.write("############ Configuration ################\n")
		file.write(etree.tostring(data))
		file.write("\n\n")
		file.close()

	except ConnectError as err:
		print ("Cannot connect to device: {0}".format(err))

	except Exception as err:
		print (err)

	dev.close()

## End of Script ##
