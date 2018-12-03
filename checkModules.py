#!/usr/bin/python
# Purpose: This file contains all of the check functions that are called from the junosAudit.py script
# Version: 0.10
#####################################################################################################################################

############################################
## Modules
############################################
import os
import re
import sys

######################################################################################################################################
# deployTemplate Function
# templateFile is passed in from another function which indicates the file that contains the Junos configuration to be added as a 
# corrective actions list.
######################################################################################################################################
def deployTemplate(templateFile,fixCommands):
	# Does templateFile exist?
	if not os.path.isfile(templateFile):
		print "\n\tERROR Template File does not exist: " + templateFile
		exit()
	else: 	
		# Read working file into a list
		with open(templateFile, "r") as file:
			templateCommands = [line.strip() for line in file]
		file.close()

		# Merge fixCommands with template commands
		fixCommands = fixCommands + templateCommands

		return(fixCommands)

######################################################################################################################################
# checkJunosVersion Function
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
	fixCommands = [] 
	badCliList = []
	requiredCliList = []
	templateDir = config.get('global', 'templateDir')
	unauthFile = "%s/%s" % (templateDir,"unauthorized-cli-commands.txt")
	requiredFile = "%s/%s" % (templateDir,"required-cli-commands.txt")

	# Check for required template files
	if not os.path.isfile(unauthFile):
		sys.stdout.write("\n\t+ Checking for Unauthorize cli commands file ........................")
		print " FAILED!"
		print "\nERROR: Does NOT exist: " + unauthFile
		exit()
	else:
		# Read unauthorized clis into a list
		with open(unauthFile, "r") as ucfile:
			badCliList = [ucline.strip() for ucline in ucfile]
		ucfile.close()

		# Some sanity checking on read in data (empty, space, tab) 
		badCliList = filter(None, badCliList)

	if not os.path.isfile(requiredFile):
		sys.stdout.write("\n\t+ Checking for Required cli commands file ........................")
		print " FAILED!"
		print "\nERROR: Does NOT exist: " + requiredFile
		exit()
	else:
		# Read required clis into a list
		with open(requiredFile, "r") as rcfile:
			requiredCliList = [rcline.strip() for rcline in rcfile]
		rcfile.close()

		# Some sanity checking on read in data (empty, space, tab)
		requiredCliList = filter(None, requiredCliList)

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
		if cmd in lines:
			sys.stdout.write(".")
			lines = [line.replace(cmd,
				"<div class=\"redtip\">" + cmd + "<span class=\"redtiptext\">Check Result: FAILED</span></div>") for line in lines]
			cmd = re.sub(r'set\s',"delete ", cmd)
			fixCommands.append(cmd)

	# Find required CLI commands
	for cmd in requiredCliList:
		if cmd in lines:
			sys.stdout.write(".")
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
# This function should be used to check for partial commands in a configuration line. Current checks are:
# - targeted-broacast (IP directed broadcast) - should not be configured on any interface
# - insecure/unneccessary services - currently set to dns,finger,outbound-ssh,telnet,tftp-server,rest,xnm-clear|ssl,webapi&web-mgmt
# - proxy-arp - masks configuration errors, should only be a temperory solution.
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
			sys.stdout.write(".")
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			line = re.sub('set\s',"delete ", line)
			fixCommands.append(line)

		# Find insecure services query configuration
		elif re.match(r'set system services (dns|finger|ftp|outbound-ssh|rsh|rlogin|telnet|tftp-server|rest|xnm-clear|xnm-ssl|webapi|web-management).*',line):
			sys.stdout.write(".")
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
			file.write("\n")

			line = re.sub('set\s',"delete ", line)
			fixCommands.append(line)

		# Find proxy-arp
		elif re.match(r'set\sinterfaces\s.*\sunit\s.*\sproxy-arp.*',line):
			sys.stdout.write(".")
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">FAILED! Proxy-arp not recommended</span></div>")
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
# Performs the following checks related to SNMP:
# - SNMP community - Flagged as a failure due to insecure passing of community string 
# - SNMP trap groups - Flagged as a failure due to insecure passing of community string
# - SNMPv3 user auth & priv algorithms should be set to the strongest
# - SNMPv3 VACM security-to-group configured and set to usm
# - SNMPv3 VACM access configured and set to usm
# - SNMPv3 target security-model set to usm
# - SNMPv3 target security-level set to privacy
# - SNMPv3 target message model v3
######################################################################################################################################
def checkSNMP(file,config):
	sys.stdout.write(".")
	fixCommands = []
	v3Auth = ""
	v3VacmGroup = ""
	v3VacmAccess = ""
	targetSecModel = ""
	targetSecLevel = ""
	targetMsgModel = ""
	templateFile = ""
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)
	
	# Check if the snmpv3 template value is set in junosAudit.ini
	if config.has_option('site', 'snmpv3Template'):
		templateDir = config.get('global', 'templateDir')
		templateName = config.get('site', 'snmpv3Template')
		templateFile = "%s/%s" % (templateDir,templateName)
	
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
			sys.stdout.write(".")
			community = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">FAILED! Insecure: clear text.</span></div>")
			file.write("\n")

			if ("delete snmp community " + community[3]) not in fixCommands:
				fixCommands.append("delete snmp community " + community[3])

		# Find SNMPv2 trap configuration
		elif re.match(r'set\ssnmp\strap-group\s.*',line):
			sys.stdout.write(".")
			trapLine = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">FAILED! Insecure: clear text.</span></div>")
			file.write("\n")

			if ("delete snmp trap-group " + trapLine[3]) not in fixCommands:
				fixCommands.append("delete snmp trap-group " + trapLine[3])

		# Find strong SNMPv3 auth and priv values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(authentication-sha|privacy-aes128)\s.*',line):
			sys.stdout.write(".")
			v3Auth = "1"
			file.write("<div class=\"greentip\">")
			file.write(line)
			file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
			file.write("\n")

		# Find unsecure SNMPv3 auth values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(authentication-none|authentication-md5)\s.*',line):
			sys.stdout.write(".")
			v3Auth = "1"
			auth = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">FAILED! Weak auth algorithm.</span></div>")
			file.write("\n")
			fixCommands.append("set snmp v3 usm local-engine user " + auth[6] + " authentication-sha authentication-password -PASSWORD-")

		# Find unsecure SNMPv3 priv values
		elif re.match(r'set\ssnmp\sv3\susm\slocal-engine\suser\s.*\s(privacy-none|privacy-des|privacy-3des)\s.*',line):
			sys.stdout.write(".")
			v3Auth = "1"
			auth = re.split("\s", line)
			file.write("<div class=\"redtip\">")
			file.write(line)
			file.write("<span class=\"redtiptext\">FAILED! Weak privacy algorithm.</span></div>")
			fixCommands.append("set snmp v3 usm local-engine user " + auth[6] + " privacy-aes128 privacy-password -PASSWORD-")

		# Find SNMPv3 vacm security
		elif re.match(r'set\ssnmp\sv3\svacm\ssecurity-to-group\ssecurity-model\s.*',line):
			sys.stdout.write(".")
			vacmGroupLine = re.split("\s",line)
			if vacmGroupLine[6] == "usm":
				v3VacmGroup = "1"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")
			else:
				v3VacmGroup = ""
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">FAILED! Security model not USM</span></div>")
				file.write("\n")

		# Find SNMPv3 vacm access
		elif re.match(r'set\ssnmp\sv3\svacm\saccess\sgroup\s.*',line):
			sys.stdout.write(".")
			vacmAccessLine = re.split("\s",line)
			if vacmAccessLine[9] == 'usm':
				v3VacmAccess = "1"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")
			else:
				v3VacmAccess = ""
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">FAILED! Security model not USM</span></div>")
				file.write("\n")

		# Find SNMPv3 target-parameters security-model usm
		elif re.match(r'set\ssnmp\sv3\starget-parameters\s.*\sparameters\ssecurity-model\s.*',line):
			sys.stdout.write(".")
			targetSecModelLine = re.split("\s",line)
			if targetSecModelLine[7] == 'usm':
				targetSecModel = "1"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")
			else:
				targetSecModel = ""
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">FAILED! Security model not USM</span></div>")
				file.write("\n")
				fixCommands.append("set snmp v3 target-parameters " + targetSecModelLine[4] + " parameters security-model usm")

		# Find SNMPv3 target-parameters security-level privacy
		elif re.match(r'set\ssnmp\sv3\starget-parameters\s.*\sparameters\ssecurity-level\s.*',line):
			sys.stdout.write(".")
			targetSecLevelLine = re.split("\s",line)
			if targetSecLevelLine[7] == 'privacy':
				targetSecLevel = "1"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")
			else:
				targetSecLevel = ""
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">FAILED! Sec level not privacy</span></div>")
				file.write("\n")
				fixCommands.append("set snmp v3 target-parameters " + targetSecModelLine[4] + " parameters security-level privacy")

		# Find SNMPv3 target-parameters messsage-processing-model
		elif re.match(r'set\ssnmp\sv3\starget-parameters\s.*\sparameters\smessage-processing-model\s.*',line):
			sys.stdout.write(".")
			targetMsgModelLine = re.split("\s",line)
			if targetMsgModelLine[7] == 'v3':
				targetMsgModel = "1"
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")
			else:
				targetMsgModel = ""
				file.write("<div class=\"redtip\">")
				file.write(line)
				file.write("<span class=\"redtiptext\">FAILED! Msg model not v3</span></div>")
				file.write("\n")
				fixCommands.append("set snmp v3 target-parameters " + targetSecModelLine[4] + " parameters message-processing-model v3")

		else:
			file.write(line)
			file.write("\n")

	# Is SNMPv3 configured?
	if not v3Auth or not v3VacmGroup or not v3VacmAccess:
		# If template file is not configured, print general statement.
		if templateFile == "":
			fixCommands.append("# SNMPv3 NOT configured correctly.")
		else:
			fixCommands = deployTemplate(templateFile,fixCommands)

	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkTraceoptions Function
# Traceoptions puts a strain on device resources and it should only be enabled for troubleshooting purposes and then disabled. This
# function will flag any configured traceoptions as something that should be disabled.
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
			file.write("<span class=\"redtiptext\">FAILED! Unneccessary debugging.</span></div>")
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
# This function checks the following:
# - Default login classes - Default login classes do not have idle-timeouts and shouldnt be used in production
# - Accounts configured with ssh keys - SSH keys pose a risk if the keys are not properly protected.
# - Emergency account - This is a local account that is used in the event the radius/tacplus server is unavailable.
######################################################################################################################################
def checkAccounts(file,config):
	sys.stdout.write(".")
	fixCommands = []
	accountList = []
	templateFile = ""
	workDir = config.get('global', 'workDir')
	workFile = "%s/%s" % (workDir,file)

	# Check if the emergency account template value is set in junosAudit.ini
	if config.has_option('site', 'emergencyAcctTemplate'):
		templateDir = config.get('global', 'templateDir')
		templateName = config.get('site', 'emergencyAcctTemplate')
		templateFile = "%s/%s" % (templateDir,templateName)
	
	# Check existance of emergencyAcct, otherwise set it to something so it doesnt fail
	if config.has_option('site', 'emergency'):
		emergencyAcct = config.get('site', 'emergencyAcct')
	else:
		emergencyAcct = "VALUE-NOT-SET"
	
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
			sys.stdout.write(".")
			classLine = re.split('\s+',line)
			accountList.append(classLine[4])

			# Find default login classes
			if classLine[6] == "super-user" or classLine[6] == "operator" or classLine[6] == "unauthorized" or classLine[6] == "read-only":
				sys.stdout.write(".")
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
		#elif re.match(r'set\ssystem\slogin\suser\s.*\sauthentication ssh-.*',line):
		#	sys.stdout.write(".")
		#	sshLine = re.split('\s+',line)
		#	file.write("<div class=\"redtip\">")
		#	file.write(line)
		#	file.write("<span class=\"redtiptext\">Status: FAILED! No ssh keys.</span></div>")
		#	file.write("\n")
                #
		#	fixCommands.append("delete system login user " + classLine[4] + " authentication " + sshLine[6] + " " + sshLine[7])

		else:
			file.write(line)
			file.write("\n")

	# If template file is defined, deploy the template
	if templateFile is None:
		fixCommands.append("# Emergency account NOT configured")
	elif templateFile:
		fixCommands = deployTemplate(templateFile,fixCommands)
		
	# Add Corrective Actions
	if (len(fixCommands) > 0):
		file.write("<font color=red>")
		for i in fixCommands:
			file.write(i + "\n")
		file.write("</font>\n")
	file.close()

######################################################################################################################################
# checkNTP Function
# - Checks ntp/servers from junosAudit.ini are configured
#   + flags servers not listed in junosAudit.ini as possible unauthorized
# - Checks configured key ids
# - Checks key type values
#   + md5 flagged as failed and fixCommand is set to sha256
# - Checks configured trusted keys
# - Check boot-server to ensure it matches value in junosAudit.ini
######################################################################################################################################
def checkNTP(file,config):

	# Verify the ntp options are set, otherwise fail
	if not config.has_option('site', 'ntp_servers'):
		print "\n\t ! ERROR: checkNTP module ntp_server value not configured in junosAudit.ini\n"
		exit()

	elif not config.has_option('site', 'ntp_boot_server'):
		print "\n\t ! ERROR: checkNTP module ntp_boot_server value not configured in junosAudit.ini\n"
		exit()

	else:
		sys.stdout.write(".")
		fixCommands = []
		ntpConfigured = ""
		ntpAuthKeyList = []
		templateFile = ""
		workDir = config.get('global', 'workDir')
		workFile = "%s/%s" % (workDir,file)
		ntpSvrList = config.get('site', 'ntp_servers')
	
		# Check if the ntp template value is set in junosAudit.ini
		if config.has_option('site', 'ntpTemplate'):
			templateDir = config.get('global', 'templateDir')
			templateName = config.get('site', 'ntpTemplate')
			templateFile = "%s/%s" % (templateDir,templateName)

		# Read working file into memory
		with open(workFile, "r") as file:
			lines = [line.strip() for line in file]
		file.close()

		# Remove working file
		os.remove(workFile)


		# Find the configured ntp auth keys
		for line in lines:
			if re.match(r'set\ssystem\sntp\sauthentication-key\s.*\svalue\s',line):
				ntpAuthKeyLine = re.split('\s+', line)
				ntpAuthKeyList.append(ntpAuthKeyLine[4])


		# Create new working file
		file = open(workFile, "w")
		for line in lines:

			# Find configured traceoptions
			if re.match(r'set\ssystem\sntp\sserver\s.*\s',line):
				ntpConfigured = "1"
				ntpSvrLine = re.split('\s+', line)
				
				# Verify configured ntp server to configuration file
				if (ntpSvrLine[4]) in ntpSvrList:
					file.write("<div class=\"greentip\">")
					file.write(line)
					file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
					file.write("\n")
				else:
					fixLine = re.sub("set","delete", line)
					fixLine = fixLine + " <============= Possible unauthorized server"
					fixCommands.append(fixLine)


				# ntp auth configured?
				if ntpSvrLine > 4:
					if (ntpSvrLine[5]) == "key":
						if (ntpSvrLine[6]) in ntpAuthKeyList:
							file.write("<div class=\"greentip\">")
							file.write(line)
							file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
							file.write("\n")
						else:
							file.write("<div class=\"redtip\">")
							file.write(line)
							file.write("<span class=\"redtiptext\">Check Status: FAILED!</span></div>")
							file.write("\n")

			# Find Key values. Just changes the color to acknowledge we've seen it.
			elif re.match(r'set\ssystem\sntp\sauthentication-key\s.*\svalue\s',line):
				file.write("<div class=\"greentip\">")
				file.write(line)
				file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
				file.write("\n")

			# Find key type
			elif re.match(r'set\ssystem\sntp\sauthentication-key\s.*\stype\s',line):
				ntpTypeLine = re.split('\s+', line)

				# Test key type
				if (ntpTypeLine[6]) == "md5":
					file.write("<div class=\"redtip\">")
					file.write(line)
					file.write("<span class=\"redtiptext\">FAILED! Stronger types available</span></div>")
					file.write("\n")
					fixLine = re.sub("md5","sha256", line)
					fixCommands.append(fixLine)

				elif (ntpTypeLine[6]) == "sha1" or (ntpTypeLine[6]) == "sha256":
					file.write("<div class=\"greentip\">")
					file.write(line)
					file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
					file.write("\n")

			# Find trusted-keys
			elif re.match(r'set\ssystem\sntp\strusted-key\s.*',line):
				ntpTrustLine = re.split('\s+', line)
				
				# Check if the trusted key is configured
				if (ntpTrustLine[4]) in ntpAuthKeyList:
					file.write("<div class=\"greentip\">")
					file.write(line)
					file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
					file.write("\n")
				else:
					file.write("<div class=\"redtip\">")
					file.write(line)
					file.write("<span class=\"redtiptext\">FAILED! trusted key not configured</span></div>")
					file.write("\n")

					fixLine = re.sub("set","delete", line)
					fixCommands.append(fixLine)

			# Find boot server
			elif re.match(r'set\ssystem\sntp\sboot-server\s.*',line):
				ntpBootSvrLine = re.split('\s+', line)

				if (ntpBootSvrLine[4]) == config.get('site', 'ntp_boot_server'):
					file.write("<div class=\"greentip\">")
					file.write(line)
					file.write("<span class=\"greentiptext\">Check Status: Passed!</span></div>")
					file.write("\n")
				else:
					file.write("<div class=\"redtip\">")
					file.write(line)
					file.write("<span class=\"redtiptext\">FAILED! Incorrect boot server</span></div>")
					file.write("\n")

					fixCommands.append("set system ntp boot-server " + config.get('site', 'ntp_boot_server'))

			else:
				file.write(line)
				file.write("\n")

		# Is NTP configured?
		if not ntpConfigured:
			if templateFile == "":
				fixCommands.append("# NTP not configured.")
			else:
				fixCommands = deployTemplate(templateFile,fixCommands)
				
		# Add Corrective Actions
		if (len(fixCommands) > 0):
			file.write("<font color=red>")
			for i in fixCommands:
				file.write(i + "\n")
			file.write("</font>\n")
		file.close()

## end of file ##
