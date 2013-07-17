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

import datetime
n1 = raw_input("Enter start file_number: ")
n2 = raw_input("Enter end file_number: ")
for n in range(int(n1), int(n2) + 1):
    f = open("project_gps_edited_" + str(n) + ".txt")
    outputFile = open("converted/converted_data_" + str(n) + ".txt", 'w')
    with f, outputFile:
        contents = f.read()
        lines = contents.splitlines()
        nlines = len(lines)
        j = 1
        outputFile.write('index,timestamp,hour_of_day,day_of_week,GPS_timestamp,latitude,longitude,altitude,Accuracy,bearing,speed')
        for i in range(nlines):
            line = lines[i]
            if line.count('|') == 7:
                newline = line.replace('|', ',')
                idx = newline.find(',')
                timestamp = newline[:idx]
                dt = (datetime.datetime.fromtimestamp(float(timestamp)/1000.0) + datetime.timedelta(hours=16))
                ds_hour = dt.strftime("%H")
                ds_day = dt.strftime("%A")
                # ts = dt.strftime("%H:%M:%S %d/%m/%Y")
                d = timestamp + ',' + ds_hour + ',' + ds_day
                newline = '\n' + str(j) + ',' + d + newline[idx:]
                outputFile.write(newline)
                j = j + 1