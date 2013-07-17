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

from __future__ import division
import csv
from collections import defaultdict
from fileinfo import filename, files

shouldIgnoreRepetitions = True
shouldIgnoreAddedOnly = True
shouldPrintPredictions = False
verbose = True
latLabel = 'latitude'
longLabel = 'longitude'
dirLabel = 'direction_of_movement'
originalTextLabel = 'original-data'
gridScale = 100

class LocationPrecitionModel:
    
    def __init__(self, files, filename, latLabel, longLabel, dirLabel, originalTextLabel, gridScale, shouldIgnoreRepetitions, shouldIgnoreAddedOnly, verbose):
        self.files = files
        self.filename = filename
        self.mostFrequentlyVisited = ''
        self.counts_uni = defaultdict(int)
        self.counts_bi = defaultdict(int)
        self.next = defaultdict(set)
        self.data = []
        self.fileDataDict = {}
        self.dataFileDict = {}
        self.indices = []
        self.shouldIgnoreRepetitions = shouldIgnoreRepetitions
        self.verbose = verbose
        self.latLabel = latLabel
        self.longLabel = longLabel
        self.dirLabel = dirLabel
        self.originalTextLabel = originalTextLabel
        self.shouldIgnoreAddedOnly = shouldIgnoreAddedOnly
        self.gridScale = gridScale
    
    def predict(self, x, direction):
        maxProb = 0
        r = ''
        for y in self.next[x]:
            P = (self.counts_bi[(x, y, direction)] + 1) / (self.counts_uni[(x, direction)] + len(self.next[x]))
            if P > maxProb:
                maxProb = P
                r = y
        if maxProb == 0:
            r = self.mostFrequentlyVisited
        return r, maxProb
    
    def train(self, train_files):
        last = '$'
        d = []
        for file in train_files:
            d = d + self.data[file]
        for e in d:
            if e[0] == "---":
                last = '$'
            else:
                self.counts_uni[(e[0], e[1])] = self.counts_uni[(e[0], e[1])] + 1
                self.counts_bi[(last, e[0], e[1])] = self.counts_bi[(last, e[0], e[1])] + 1
                self.next[last].add(e[0])
                last = e[0]
        maxCount = -1
        for e in self.counts_uni:
            if self.counts_uni[e] > maxCount:
                self.mostFrequentlyVisited = e[0]
                maxCount = self.counts_uni[e]
    
    def test(self, test_files):
        t = []
        for file in test_files:
            t = t + self.data[file]
        total = len(t) - 2
        correct = 0
        for i in range(total):
            predicted, P = self.predict(t[i][0], t[i][1])
            if predicted == t[i+1][0]:
                correct = correct + 1
            if shouldPrintPredictions:
                print t[i][0], t[i+1][0], "-->", predicted
        if total == 0:
            accuracy = 0.0
        else:
            accuracy = correct / total
        return accuracy
    
    def readFiles(self):
        j = 0
        for i in self.files:
            d = []
            with open(self.filename % i) as file1:
                sr = csv.reader(file1, delimiter=',')
                first = True
                last = ''
                labelIdx = -1
                for r in sr:
                    if first:
                        first = False
                        latIdx = r.index(self.latLabel)
                        longIdx = r.index(self.longLabel)
                        dirIdx = r.index(self.dirLabel)
                        origIdx = r.index(self.originalTextLabel)
                    else:
                        label = self.getLabel(r[latIdx], r[longIdx])
                        direction = r[dirIdx]
                        if shouldIgnoreRepetitions and last == label:
                            if not self.shouldIgnoreAddedOnly or r[origIdx] == '0':
                                continue
                        d.append([label, direction])
                        last = label
            d.append(["---", "---"])
            self.data.append(d)
            self.fileDataDict[i] = j
            self.dataFileDict[j] = i
            j = j + 1
        self.indices = [self.fileDataDict[i] for i in self.files]
    
    def getLabel(self, latitude, longitude):
        x = int(float(latitude) * self.gridScale) / gridScale
        y = int(float(longitude) * self.gridScale) / gridScale
        label = 'LAT' + str(x) + 'LON' + str(y)
        return label
    
    def resetTrainedModel(self):
        self.counts_uni = defaultdict(int)
        self.counts_bi = defaultdict(int)
        self.next = defaultdict(set)
        self.mostFrequentlyVisited = ''
    
    def crossValidate(self, sequential=False):
        maxAccuracy = -1
        bestSet = []
        sets = []
        if sequential:
            sets = [(self.indices[:i], [self.indices[i]]) for i in range(len(self.indices))]
        else:
            sets = [(self.indices[:i] + self.indices[i+1:], [self.indices[i]]) for i in range(len(self.indices))]
        passNum = 1
        total = 0.0
        for train_files, test_files in sets:
            self.resetTrainedModel()
            self.train(train_files)
            accuracy = self.test(test_files)
            if accuracy > maxAccuracy:
                maxAccuracy = accuracy
                bestSet = (train_files, test_files)
            total = total + accuracy
            if self.verbose:
                print "Pass no.:", passNum, "| Accuracy:", accuracy
            passNum = passNum + 1
        bestSetFiles = ([self.dataFileDict[i] for i in bestSet[0]], [self.dataFileDict[i] for i in bestSet[1]])
        cases = passNum - 1
        if sequential:
            cases = cases - 1
        avgAccuracy = total / cases
        return maxAccuracy, bestSetFiles, avgAccuracy
    
    def printData(self):
        i = 1
        for d in self.data:
            print i
            i = i + 1
            print "######################"
            j = 1
            for x in d:
                print j, x
                j = j + 1
            print
            print "######################"
    
    def printUniqueLocations(self):
        l = []
        for d in self.data:
            l = l + d
        s = set(l)
        print "Unique Locations:\n"
        c = sorted(s)
        for x in c:
            print x
        print "\nTotal:", len(c)

def main():
    model = LocationPrecitionModel(files, filename, latLabel, longLabel, dirLabel, originalTextLabel, gridScale, shouldIgnoreRepetitions, shouldIgnoreAddedOnly, verbose)
    model.readFiles()
    print
    print "1 test file and remaining all training files:"
    print
    maxAccuracy, bestSet, avgAccuracy = model.crossValidate(sequential=False)
    print
    print "Maximum accuracy:", maxAccuracy
    print "Training files:", bestSet[0]
    print "Test files:", bestSet[1]
    print "Average accuracy:", avgAccuracy
    print
    print "1 test file and all preceding it as training files:"
    print
    maxAccuracy, bestSet, avgAccuracy = model.crossValidate(sequential=True)
    print
    print "Maximum accuracy:", maxAccuracy
    print "Training files:", bestSet[0]
    print "Test files:", bestSet[1]
    print "Average accuracy [excluding first day's predictions]:", avgAccuracy
    print

if __name__ == '__main__':
    main()