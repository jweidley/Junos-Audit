#!/usr/bin/python
# Purpose: This file contains all of the check functions that are called from the junosAudit.py script
# Version: 0.6
#####################################################################################################################################

############################################
## Modules
############################################
import os
import re
import sys

######################################################################################################################################
# checkJunosVersion Function
# Used to check the correct version of Junos is installed on each platform type. This function relies on the
# [junosVersion] section of the junosAudit.ini file, so ensure it is up to date and accurate.
######################################################################################################################################
def checkJunosVersion(file,config):
	sys.stdout.write(".")
	checkResult = ""
	devModel = ""
	devVer = ""
	approvedJunos = ""
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	
	# Read working file into a list
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Find Platform model & Junos version
	for line in lines:
		# Find platform model from 'show version' output
		if re.match(r'^Model:\s.*',line):
			shoVerLine = re.split('\s+',line)
			devModel = shoVerLine[1]

		# Find Junos version from 'show version' output
		elif re.match(r'^Junos:\s.*',line):
			shoVerLine = re.split('\s+',line)
			devVer = shoVerLine[1]


	# Set value based on model from the ini file
	if config.has_option('junosVersion', devModel) :
		approvedJunos = config.get('junosVersion', devModel)
	else:
		approvedJunos = "UNKNOWN"

	# Create new working file
	file = open(workFile, "w")
	for line in lines:

		# Find version in the configuration
		if re.match(r'set version .*',line):
			confVerLine = re.split('\s+',line)
			confVer = confVerLine[2]
			if (confVerLine[2] == approvedJunos):
				checkResult = "pass"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Matched: " + approvedJunos + "</span></div>")
				file.write("\n")
			elif approvedJunos == "UNKNOWN":
				checkResult = "error"
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">OS Version NOT Found!</span></div>")
				file.write("\n")
			else:
				checkResult = "fail"
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">OS Upgrade Required!</span></div>")
				file.write("\n")
		else:
			file.write(line)
			file.write("\n")

	if (checkResult == "fail"):
		file.write("<font color=red>")
		file.write("# Junos Upgrade Required!")
		file.write("</font>\n")
	elif (checkResult == "error"):
		file.write("<font color=orange>")
		file.write("# Check junosVersion value in junosAudit.ini file!")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkCLIs Function
# With the number of checks that need to be done there needs to be a quick and concise way to match bulk CLI commands. The downside 
# to this method is that in the SvcLists you have to list the EXACT command since its not using regular expressions!! The badCliList 
# and requiredCliList should only list the EXACT CLIs that should/should not be in the configuration. Anything that requires more
# intelligent processing needs a separate function that uses the Regex module.
######################################################################################################################################
def checkCLIs(file,config):
	sys.stdout.write(".")
	fixCommands = [] 
	badCliList = [
			"set routing-options source-routing ip",
			"set routing-options source-routing ipv6",
			"set system license autoupdate url https://ae1.juniper.net/junos/key_retrieval",
			"set system services ssh protocol-version v1", 
			"set system services ssh root-login allow" 
	]
	requiredCliList = [
			"set system no-redirects", 
			"set system no-ping-record-route", 
			"set system no-ping-time-stamp", 
			"set system internet-options tcp-drop-synfin-set", 
			"set system internet-options no-source-quench", 
			"set system internet-options icmpv4-rate-limit packet-rate 50", 
			"set system internet-options icmpv6-rate-limit packet-rate 50", 
			"set system internet-options no-ipv6-path-mtu-discovery", 
			"set system internet-options no-ipip-path-mtu-discovery", 
			"set system internet-options no-tcp-reset drop-all-tcp", 
			"set system ports console log-out-on-disconnect", 
			"set system ports console insecure", 
			"set system ports auxiliary disable", 
			"set system ports auxiliary insecure", 
			"set system login retry-options tries-before-disconnect 3", 
			"set system login retry-options backoff-threshold 1", 
			"set system login retry-options backoff-factor 5", 
			"set system login retry-options minimum-time 20", 
			"set system login retry-options maximum-time 60", 
			"set system login retry-options lockout-period 10", 
			"set system login password minimum-length 15", 
			"set system login password change-type character-sets", 
			"set system login password minimum-changes 4", 
			"set system login password minimum-numerics 2", 
			"set system login password minimum-upper-cases 2", 
			"set system login password minimum-lower-cases 2", 
			"set system login password minimum-punctuations 2", 
			"set system login password format sha512", 
			"set system services ssh protocol-version v2", 
			"set system services netconf ssh", 
			"set system services ssh ciphers aes256-ctr", 
			"set system services ssh ciphers aes256-cbc", 
			"set system services ssh ciphers aes192-ctr", 
			"set system services ssh ciphers aes192-cbc", 
			"set system services ssh ciphers aes128-ctr", 
			"set system services ssh ciphers aes128-cbc", 
			"set system services ssh macs hmac-sha2-512", 
			"set system services ssh macs hmac-sha2-256", 
			"set system services ssh macs hmac-sha1", 
			"set system services ssh macs hmac-sha1-96", 
			"set system services ssh key-exchange ecdh-sha2-nistp521", 
			"set system services ssh key-exchange ecdh-sha2-nistp384", 
			"set system services ssh key-exchange ecdh-sha2-nistp256", 
			"set system services ssh key-exchange group-exchange-sha2", 
			"set system services ssh key-exchange dh-group14-sha1", 
			"set system services ssh client-alive-count-max 3", 
			"set system services ssh client-alive-interval 10", 
			"set system services ssh connection-limit 10", 
			"set system services ssh rate-limit 4", 
			"set system services ssh max-sessions-per-connection 1", 
			"set system services ssh root-login deny", 
			"set system services ssh no-tcp-forwarding"
	]
	customerName = config.get('site', 'customer')
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)

	# Read working file into a list
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Find unauthorized CLI commands
	for cmd in badCliList:
		if (cmd) in lines:
			lines = [line.replace(cmd, 
				"<div class=\"redtip\">" + cmd + "<span class=\"redtiptext\">Check Result: FAILED</span></div>") for line in lines]
			cmd = re.sub(r'set\s',"delete ", cmd)
			fixCommands.append(cmd)

	# Find required CLI commands
	for cmd in requiredCliList:
		if (cmd) in lines:
			lines = [line.replace(cmd, 
				"<div class=\"greentip\">" + cmd + "<span class=\"greentiptext\">Check Result: Passed</span></div>") for line in lines]
		else:
			fixCommands.append(cmd)

	file = open(workFile, "w")
	for line in lines:
		file.write(line)
		file.write("\n")
			
	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")

        file.close()

######################################################################################################################################
# checkPartial Function
# This function should be used to check for partial commands in a configuration line.
######################################################################################################################################
def checkPartial(file,config):
	sys.stdout.write(".")
	fixCommands = []
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	
	# Read working file into memory
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Create new working file
	file = open(workFile, "w")
	for line in lines:

		# Find IP directed broadcast
		if re.match(r'set\sinterfaces\s.*\sunit\s.*\sfamily\sinet\stargeted-broadcast',line):
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			line = re.sub('set\s',"delete ", line)
			fixCommands.append(line)

		# Find insecure services query configuration
		elif re.match(r'set system services (dns|finger|ftp|outbound-ssh|telnet|tftp-server|rest|xnm-clear|xnm-ssl|webapi|web-management).*',line):
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			line = re.sub('set\s',"delete ", line)
			fixCommands.append(line)

		else:
			file.write(line)
			file.write("\n")

	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkSNMP Function
######################################################################################################################################
def checkSNMP(file,config):
	sys.stdout.write(".")
	fixCommands = []
	snmpv3 = ""
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	
	# Read working file into memory
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Create new working file
	file = open(workFile, "w")
	for line in lines:

		# Find SNMPv2 query configuration
		if re.match(r'set\ssnmp\scommunity\s.*',line):
			community = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			if ("delete snmp community " + community[3]) not in fixCommands:
				fixCommands.append("delete snmp community " + community[3])

		# Find SNMPv2 trap configuration
		elif re.match(r'set\ssnmp\strap-group\s.*',line):
			trapLine = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			if ("delete snmp trap-group " + trapLine[3]) not in fixCommands:
				fixCommands.append("delete snmp trap-group " + trapLine[3])

		# Find SNMPv3 auth and priv values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(authentication-sha|privacy-aes128)\s.*',line):
			snmpv3 = "1"
			file.write("<div class=\"greentip\">")
			file.write(line)
			file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
			file.write("\n")

		# Find unsecure SNMPv3 auth values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(authentication-none|authentication-md5)\s.*',line):
			snmpv3 = "1"
			auth = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")
			fixCommands.append("set snmp v3 usm local-engine user " + auth[6] + " authentication-sha authentication-password -PASSWORD-")

		# Find unsecure SNMPv3 priv values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(privacy-none|privacy-des|privacy-3des)\s.*',line):
			snmpv3 = "1"
			auth = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			fixCommands.append("set snmp v3 usm local-engine user " + auth[6] + " privacy-aes128 privacy-password -PASSWORD-")

		else:
			file.write(line)
			file.write("\n")

	# Is SNMPv3 configured?
	if not snmpv3:
		fixCommands.append("# SNMPv3 NOT configured. Deploy SNMPv3 template")

	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkTraceoptions Function
######################################################################################################################################
def checkTraceoptions(file,config):
	sys.stdout.write(".")
	fixCommands = []
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	
	# Read working file into memory
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Create new working file
	file = open(workFile, "w")
	for line in lines:

		# Find configured traceoptions
		if re.match(r'.*\straceoptions\s.*',line):
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			line = re.sub("set","delete", line)
			fixCommands.append(line)

		else:
			file.write(line)
			file.write("\n")

	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkAccounts Function
######################################################################################################################################
def checkAccounts(file,config):
	sys.stdout.write(".")
	fixCommands = []
	accountList = []
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	emergencyAcct = config.get('site', 'emergencyAcct')
	
	# Read working file into memory
	with open(workFile, "r") as file:
		lines = [line.strip() for line in file]
	file.close()

	# Remove working file
	os.remove(workFile)

	# Create new working file
	file = open(workFile, "w")
	for line in lines:

		# Find all configured login classes
		if re.match(r'set\ssystem\slogin\suser\s.*\sclass\s.*',line):
			classLine = re.split('\s+',line)
			accountList.append(classLine[4])

			# Find default login classes
			if classLine[6] == "super-user" or classLine[6] == "operator" or classLine[6] == "unauthorized" or classLine[6] == "read-only":
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">Status: FAILED! No idle-timeout</span></div>")
				file.write("\n")

				fixCommands.append("set system login user " + classLine[4] + " class -CUSTOM-CLASS-")

			# Only login classes
			else:
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Status: Passed!</span></div>")
				file.write("\n")

		# Find configured ssh keys
		elif re.match(r'set\ssystem\slogin\suser\s.*\sauthentication ssh-.*',line):
			sshLine = re.split('\s+',line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Status: FAILED! No ssh keys.</span></div>")
			file.write("\n")

			fixCommands.append("delete system login user " + classLine[4] + " authentication " + sshLine[6] + " " + sshLine[7])

		else:
			file.write(line)
			file.write("\n")

	# Check to see if the emergency account is configured
	if emergencyAcct:
		if emergencyAcct not in accountList:
			fixCommands.append("# Emergency Account NOT configured. Deploy account template.")
			
	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()


## end of file ##
