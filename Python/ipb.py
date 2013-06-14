#! /usr/bin/env python

'''
    This script does bulk update changes to the IP address of your zone, by reading in a CSV file,
    then Publishing the Zones that were updated trough the DynECT API.
    
    The format of the csv file is "Zone Name", "Old IPv4 Address", "New IPv4 Address",

    The credentials are read in from a configuration file in 
    the same directory. 
    
    The file is named credentials.cfg in the format:
    
    [Dynect]
    user: user_name
    customer: customer_name
    password: password
    
    Usage: %python ipb.py [-F]

    Options
        -h, --help              Show this help message and exit
        -F, FILE, --File=FILE   Add CSV file to search through for bulk IP address change.

    The Dynect API library is available at:
    https://github.com/dyninc/Dynect-API-Python-Library
'''
import sys
import os
import csv
import ConfigParser
from optparse import OptionParser
from DynectDNS import DynectRest

# Create an instance of the api reference library to use.
dynect = DynectRest()

def login(cust, user, pwd):
    '''
    This method will do a dynect login

    @param cust: customer name
    @type cust: C{str}

    @param user: user name
    @type user: C{str}

    @param pwd: password
    @type pwd: C{str}

    @return: The function will exit the script on failure to login
    @rtype: None

    '''

    arguments = {
            'customer_name': cust,
            'user_name': user,
            'password': pwd,
    }

    response = dynect.execute('/Session/', 'POST', arguments)

    if response['status'] != 'success':
        sys.exit("Incorrect Credentials")
    elif response['status'] == 'success':
        print 'Logged In'

def publish(zone):
    '''
    Publish a Zone
   
    @param zone: zone name
    @type zone: C{str}

    @return: Failed or Published
    '''

    arguments = {
            'publish': 'True'
    }
    response = dynect.execute('/Zone/' + zone + "/", 'PUT', arguments)
    
    if response['status'] != 'success':
        print '\t' + zone + ' Failed to Publish!'
    elif response['status'] == 'success':
        print '\t' + zone + ' Published!'


def updateIP(path):
    '''
    This method goes through a csv file and pulls out the domain name and IP address to be updated
    on the DynECT system.

    @param path: csv file path
    @type path: C{str}

    @return: None (status is printed inline)

    '''
    with open(path, 'rb') as csvfile:
        zone = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in zone:
            # name the 3 pieces of data from the csv
            zone_name = row[0]
            new = row[2]
            old = row[1]
            
            #setup the new ip for the row
            data = {'rdata' : {'address' : new }}
            
            #get all the records in the zone
            records_response = dynect.execute('/REST/AllRecord/' + zone_name, 'GET')
            
            #loop the records and check for A records
            if records_response['status'] == 'success':
                #check each record in the zone to see if it is an A record
                for record in records_response['data']:
                    if '/ARecord/' in record:
                        # get the details of the A record
                        arecord_response = dynect.execute(record, 'GET', data)
                        if arecord_response['status'] == 'success':
                            # see if the A record has rdata that we need to update
                            if arecord_response['data']['rdata']['address'] == old:
                                #do the update
                                response = dynect.execute(record, 'PUT', data)
                                if response['status'] == 'success':
                                    print zone_name + ' Updated!'
                                    #publish the zone if we updated it
                                    publish(zone_name)
                                else:
                                    print zone_name + " did NOT Update!"
                                    printresponse['msgs']
                        else:
                            print "Failed to get A Record details for " + record
                            print arecord_response['msgs']            
            else:
                print "Failed to get All Records for zone " + zone_name
                print records_response['msgs']

# main entry for script
usage = "Usage: %python ipb.py [-F] [options]"
parser = OptionParser(usage=usage)
parser.add_option("-F", "--File", action="store", dest="File", default=False, help="csv file with zone ip pairs")
(options, args) = parser.parse_args()

if not options.File:
    parser.error("Your must provide a csv file.")
    
# Now read in the DynECT user credentials
config = ConfigParser.ConfigParser()

#read in the configuration data
user = None
cust = None
pwd = None
try:
    config.read('credentials.cfg')
    user = config.get('Dynect', 'user', 'none')
    cust = config.get('Dynect', 'customer', 'none')
    pwd = config.get('Dynect', 'password', 'none')
except Exception, ex:
    print str(ex)
    sys.exit("Error Reading Config File")

#login
login(cust, user, pwd)

#update the IP based on the csv file
updateIP(options.File)

# Log out, to be polite
dynect.execute('/Session/', 'DELETE')
print "Logged out"

print "Script has finished executing"