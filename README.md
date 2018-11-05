# Junos-Audit
Junos Audit is a Python script that will allow you to audit your Junos devices for security and organization baseline compliance. You have to customize the parts of the script to tell Junos Audit what to look for and then it will check the configurations, report corrective actions and generate a color coded HTML file for easy viewing.

# Prerequisites
1. Python. I test with Python 2.7
2. Junos device configuration files (in 'set' format)
3. Have some kind of idea what you want to look for in the configuration. There are some standard checks that are supplied for example
   purposes but really its up to you to customize it for your useage.

# Running Junos Audit
1. download Junos Audit and put it in a directory
2. Unpack the archive
   - tar zxvf junosAudit-xxxx.tar.gz
3. Create an 'Output' directory for your HTML results
4. Create a Working directory for the script to put scratch files and other transient files
5. Edit junosAudi.ini:
   - Update the configDir path to reflect your environment
   - Update the htmlDir path to reflect your environment
   - Update the workDir path to reflect your environment
6. Populate the configuration directory with Junos device configuration files
   - Each file should contain the output of 2 Junos commands:
     + show version | no-more
     + show configuration | display set | no-more
7. Edit junosAudi.ini:
   - Update the key value pairs in the [junosVersion] section
     + The left side should be the model number of the device obtained from the 'show version' output
     + The right side should be the recommended version of code for that platform
     ! This section is important to update so the script can tell the correct version of code for each platform
8. Run the script
   - ./junosAudit.py
   - Watch the onscreen output to ensure the script proceeds successfully
   - The HTML output files are placed in the htmlDir (as defined in the junosAudit.ini file.

# Customizing the checks
The check functions are located in the checkModles.py file. The function name gives you a clue as to its purpose. There are 2 general
purpose functions for adding simple custom checks:
  - checkCLIs: Has two lists that contain EXACT CLI commands. It is a simple should be there or shouldn't be there kind of check. This
    function does *NOT* use regular expressions and thats why the CLI must match exactly.
 
    + badCliList is for commands that should NOT be in the configuration file (i.e. "set system services ssh root-login allow"). Entries 
      in the badCliList will be flagged as failed (colored red) and added to the Corrective Actions section of the HTML file. 

    + requiredCliList is for commands that SHOULD be in the configuration file (i.e. "set system services ssh root-login deny"). Entries 
      in the requiredCliList will be flagged (colored green) as passed.

  - checkPartial: This function uses regular expressions so you can match keywords or partial CLI commands. Adding new checks is as 
    simple as adding a new 'elif' condition inside the for loop.

For more complex checking you can add a new function in the checkModules.py file and then call it from junosAudi.py.

