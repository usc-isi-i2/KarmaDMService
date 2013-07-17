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

import urllib
import csv
import json
import math
import time
import datetime
from decodePolylineGoogle import decode_line

oppositeDirection = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E', 'NE': 'SW', 'SW': 'NE',
                        'SE': 'NW', 'NW': 'SE', 'stat': '--'}

def getDirection(lat1, long1, lat2, long2):
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

def filter(points, latA, longA, latB, longB):
    # a more precise filter required (180 degrees difference in direction?)
    dirAB = getDirection(latA, longA, latB, longB)
    if dirAB == 'stat':
        return []
    dirBA = oppositeDirection[dirAB]
    i = 0
    while i < len(points) and \
        dirAB == oppositeDirection[getDirection(latA, longA, points[i][0], points[i][1])]:
        i = i + 1
    j = len(points) - 1
    while j >= 0 and \
        dirBA == oppositeDirection[getDirection(latB, longB, points[j][0], points[j][1])]:
        j = j - 1
    return points[i:(j + 1)]

threshold = 120 * 60000  # 120min or 2hr
req = "http://maps.googleapis.com/maps/api/directions/json?origin=%s,%s&destination=%s,%s&sensor=false"
n1 = raw_input("Enter start file_number: ")
n2 = raw_input("Enter end file_number: ")
for n in range(int(n1), int(n2) + 1):
    f = open("converted/converted_data_" + str(n) + ".txt")
    outputFile = open("populated/populated_data_" + str(n) + ".txt", 'w')
    table = []
    latIdx = 0
    longIdx = 0
    tsIdx = 0
    dayIdx = 0
    hrIdx = 0

    with f:
        contents = csv.reader(f, delimiter=',')
        first = True
        for row in contents:
            if first:
                first = False
                tsIdx = row.index('timestamp')
                latIdx = row.index('latitude')
                longIdx = row.index('longitude')
                hrIdx = row.index('hour_of_day')
                dayIdx = row.index('day_of_week')
            else:
                table.append(row)

    filled_table = []
    last = len(table) - 1
    print "Creating populated/populated_data_" + str(n) + ".txt",
    for i in range(last):
        filled_table.append([table[i][tsIdx], table[i][hrIdx], table[i][dayIdx], table[i][latIdx], table[i][longIdx], '1'])
        ts = int(table[i][tsIdx])
        timegap = int(table[i+1][tsIdx]) - ts
        if timegap <= threshold:
            req1 = urllib.urlopen(req % (table[i][latIdx], table[i][longIdx],
                                         table[i+1][latIdx], table[i+1][longIdx]))
            req2 = urllib.urlopen(req % (table[i+1][latIdx], table[i+1][longIdx],
                                         table[i][latIdx], table[i][longIdx]))
            route1 = req1.read()
            route2 = req2.read()
            j1 = json.loads(route1)
            j2 = json.loads(route2)
            j = j1
            if j2['routes'][0]['legs'][0]['distance']['value'] < j['routes'][0]['legs'][0]['distance']['value']:
                j = j2
            polyline = j['routes'][0]['overview_polyline']['points']
            points = decode_line(polyline)
            filtered_points = filter(points, float(table[i][latIdx]), float(table[i][longIdx]), float(table[i+1][latIdx]), float(table[i+1][longIdx]))
            step = timegap / (len(filtered_points) + 1)
            t = ts + step
            for point in filtered_points:
                dt = (datetime.datetime.fromtimestamp(float(t)/1000.0) + datetime.timedelta(hours=16))
                ds_hour = dt.strftime("%H")
                ds_day = dt.strftime("%A")
                filled_table.append([str(t), ds_hour, ds_day, str(point[0]), str(point[1]), '0'])
                t = t + step
            print '.',
            time.sleep(2)
    filled_table.append([table[last][tsIdx], table[last][hrIdx], table[last][dayIdx], table[last][latIdx], table[last][longIdx], '1'])
    print 'done'

    with outputFile:
        csvwriter = csv.writer(outputFile, delimiter=',')
        csvwriter.writerow(['timestamp', 'hour_of_day', 'day_of_week', 'latitude', 'longitude', 'original-data'])
        for row in filled_table:
            csvwriter.writerow(row)
        print outputFile.name, "created."