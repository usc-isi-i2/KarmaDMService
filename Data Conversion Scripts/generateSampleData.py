###############################################################################


# Copyright 2013 University of Southern California
#


# Licensed under the Apache License, Version 2.0 (the "License");


# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at


#
# 	http://www.apache.org/licenses/LICENSE-2.0


#
# Unless required by applicable law or agreed to in writing, software


# distributed under the License is distributed on an "AS IS" BASIS,


# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and


# limitations under the License.
#


# This code was developed by the Information Integration Group as part


# of the Karma project at the Information Sciences Institute of the
# University of Southern California.  For more information, publications,


# and related projects, please see: http://www.isi.edu/integration


###############################################################################

########################################################################################################
###
### DESCRIPTION:
###
### This script takes the GPS data files created by populateData.py (populated/populated_data_<i>.txt)
### [where i represents the day number for a particular user]
### and adds direction-of-movement feature to it
###
### NOTE: The scripts can be merged into a single script but I divided them to keep the conversions
###       separate.
###
########################################################################################################

import urllib
import csv
import json
import math

def getDirection(lat1, long1, lat2, long2):
    """Returns the direction from point (lat1, long1) to point (lat2, long2)"""
    
    direction = ''
    if lat1 == lat2 and long1 == long2:
        direction = 'stat'
    else:
        deg = math.degrees(math.atan2((long2 - long1), (lat2 - lat1)))
        if deg < 0.0:
            deg = 180.0 - deg
        if 22.5 <= deg < 67.5:
            direction = 'NE'
        elif 67.5 <= deg < 112.5:
            direction = 'N'
        elif 112.5 <= deg < 157.5:
            direction = 'NW'
        elif 157.5 <= deg < 202.5:
            direction = 'W'
        elif 202.5 <= deg < 247.5:
            direction = 'SW'
        elif 247.5 <= deg < 292.5:
            direction = 'S'
        elif 292.5 <= deg < 337.5:
            direction = 'SE'
        else:
            direction = 'E'
    return direction

n1 = raw_input("Enter start file_number: ")
n2 = raw_input("Enter end file_number: ")
for n in range(int(n1), int(n2) + 1):
    f = open("populated/populated_data_" + str(n) + ".txt")
    outputFile = open("sample/sample_data_" + str(n) + ".txt", 'w')
    with f, outputFile:
        contents = csv.reader(f, delimiter=',')
        first = True
        table = []
        latIdx = 0
        longIdx = 0
        timeIdx = 0
        lastLat = None
        lastLong = None
        for row in contents:
            if first:
                first = False
                tsIdx = row.index('timestamp')
                latIdx = row.index('latitude')
                longIdx = row.index('longitude')
                hrIdx = row.index('hour_of_day')
                dayIdx = row.index('day_of_week')
                origIdx = row.index('original-data')
            else:
                direction = '$'
                lat = float(row[latIdx])
                long = float(row[longIdx])
                if not lastLat is None:
                    direction = getDirection(lastLat, lastLong, lat, long)
                table.append([row[tsIdx], row[hrIdx], row[dayIdx], row[latIdx], row[longIdx], row[origIdx], direction])
                lastLat = lat
                lastLong = long
        csvwriter = csv.writer(outputFile, delimiter=',')
        csvwriter.writerow(['timestamp', 'hour_of_day', 'day_of_week', 'latitude', 'longitude', 'original-data', 'direction_of_movement'])
        for row in table:
            csvwriter.writerow(row)
        print outputFile.name, "created and filled."