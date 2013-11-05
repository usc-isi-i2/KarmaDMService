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

# 2nd order Markov Chain

from __future__ import division
import csv
from collections import defaultdict
import datetime
from fileinfo import filename, files

shouldIgnoreRepetitions = True  # decides whether to ignore consecutive repetition in generated labels
shouldIgnoreAddedOnly = False  # decides whether only the repetition in points added by the routing service is to be ignored
shouldPrintPredictions = False  # decides whether predictions are printed to the screen during the test phase
shouldSegmentData = False  # decides whether to segment the data for each day into trips based on the concept of stationary locations
segmentTimeThreshold = 60 * 60000  # 60min or 1hr threshold for segmenting data into trips
verbose = True  # decides whether to print the accuracy in each fold of cross-validation
latLabel = 'latitude'
longLabel = 'longitude'
timestampLabel = 'timestamp'
originalTextLabel = 'original-data'
gridScale = 100  # 100 is equivalent to truncating the lat/long values to the second place after decimal

class LocationPrecitionModel:
    
    def __init__(self, files, filename, latLabel, longLabel, timestampLabel, originalTextLabel, gridScale, shouldIgnoreRepetitions, shouldSegmentData, shouldIgnoreAddedOnly, segmentTimeThreshold, verbose):
        self.files = files
        self.filename = filename
        self.mostFrequentlyVisited = ''
        self.counts_uni = defaultdict(int)
        self.counts_bi = defaultdict(int)
        self.counts_tri = defaultdict(int)
        self.next = defaultdict(set)
        self.data = []
        self.fileDataDict = {}
        self.dataFileDict = {}
        self.indices = []
        self.shouldIgnoreRepetitions = shouldIgnoreRepetitions
        self.verbose = verbose
        self.latLabel = latLabel
        self.longLabel = longLabel
        self.timestampLabel = timestampLabel
        self.originalTextLabel = originalTextLabel
        self.gridScale = gridScale
        self.shouldSegmentData = shouldSegmentData
        self.segmentTimeThreshold = segmentTimeThreshold
        self.accuracyList = []
        self.shouldIgnoreAddedOnly = shouldIgnoreAddedOnly
    
    def predict(self, z, x):
        """Predicts the next grid-id based on the current and the previous grid-ids."""
        
        maxProb = 0
        r = ''
        # the following code calculates the probablity of each candidate next grid-id and finds the one with the maximum probability
        for y in self.next[x]:
            P = 0
            if self.counts_bi[(x, y)] != 0:
                P = self.counts_tri[(z, x, y)] / self.counts_bi[(x, y)]
            if P > maxProb:
                maxProb = P
                r = y
        if maxProb == 0:  # 1st fallback --> 1st order markov chain
            for y in self.next[x]:
                P = self.counts_bi[(x, y)] / self.counts_uni[x]
                if P > maxProb:
                    maxProb = P
                    r = y
            if maxProb == 0:  # 2nd fallback
                r = self.mostFrequentlyVisited
        return r, maxProb
    
    def train(self, train_files):
        """Trains the location prediction model with the training set provided as argument.
        
        train_files is a list. Each element of train_files is a list of type location-labels.
        
        """
        
        last = '$'
        last2 = '$'
        d = []
        for file in train_files:
            d = d + self.data[file]
        # the following code calculates the counts required by the prediction model
        # to calculate probabilities of candidate locations and make predictions
        for e in d:
            if e == "---":
                last = '$'
                last2 = '$'
            else:
                self.counts_uni[e] = self.counts_uni[e] + 1
                self.counts_bi[(last, e)] = self.counts_bi[(last, e)] + 1
                self.counts_tri[(last2, last, e)] = self.counts_tri[(last2, last, e)] + 1
                self.next[last].add(e)
                last2 = last
                last = e
        maxCount = -1
        for e in self.counts_uni:
            if self.counts_uni[e] > maxCount:
                self.mostFrequentlyVisited = e
                maxCount = self.counts_uni[e]
    
    def test(self, test_files):
        """Returns the accuracy of the location prediction model once it has been trained."""
        
        t = []
        for file in test_files:
            t = t + self.data[file]
        total = len(t) - 3
        correct = 0
        for i in range(total):
            predicted, P = self.predict(t[i], t[i+1])
            if predicted == t[i+2]:
                correct = correct + 1
            if shouldPrintPredictions:
                print t[i+1], t[i+2], "-->", predicted
        if total <= 5:  # days with not more than 5 points are not considered
            return None
        accuracy = correct / total
        return accuracy
    
    def readFiles(self):
        """Reads the data files, extracts lat/long values from each row, and adds the data to the class."""
        
        j = 0
        for i in self.files:
            d = []
            with open(self.filename % i) as file1:
                sr = csv.reader(file1, delimiter=',')
                first = True
                last = ''
                labelIdx = -1
                tsIdx = -1
                origIdx = -1
                lastTime = None
                for r in sr:
                    if first:
                        first = False
                        latIdx = r.index(self.latLabel)
                        longIdx = r.index(self.longLabel)
                        tsIdx = r.index(self.timestampLabel)
                        origIdx = r.index(self.originalTextLabel)
                    else:
                        label = self.getLabel(r[latIdx], r[longIdx])
                        if self.shouldIgnoreRepetitions and last == label:
                            if not self.shouldIgnoreAddedOnly or r[origIdx] == '0':
                                continue
                        if self.shouldSegmentData:
                            Time = float(r[tsIdx])
                            if lastTime is None:
                                lastTime = Time
                            if (Time - lastTime) >= self.segmentTimeThreshold:
                                d.append("---")
                            lastTime = Time
                        d.append(label)
                        last = label
            d.append("---")
            self.data.append(d)
            self.fileDataDict[i] = j
            self.dataFileDict[j] = i
            j = j + 1
        self.indices = [self.fileDataDict[i] for i in self.files]
    
    def getLabel(self, latitude, longitude):
        """Returns a string label for latitude-longitude values after truncating the values using the grid-scale"""
        
        x = int(float(latitude) * self.gridScale) / gridScale
        y = int(float(longitude) * self.gridScale) / gridScale
        label = 'LAT' + str(x) + 'LON' + str(y)
        return label
    
    def resetTrainedModel(self):
        """Resets the prediction model so that it can be trained again using a different dataset."""
        
        self.counts_tri = defaultdict(int)
        self.counts_uni = defaultdict(int)
        self.counts_bi = defaultdict(int)
        self.next = defaultdict(set)
        self.mostFrequentlyVisited = ''
    
    def crossValidate(self, sequential=False):
        """Runs a leave-one-out or a sequential cross-validation for the prediction algorithm on the dataset.
        
        sequential = False: leave-one-out cross-validation
        sequential = True: for the xth day, use data from 1...(x-1) days for training the model and tha from the xth day for testng
        
        """
        
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
            if not accuracy is None:
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
    model = LocationPrecitionModel(files, filename, latLabel, longLabel, timestampLabel, originalTextLabel, gridScale, shouldIgnoreRepetitions, shouldSegmentData, shouldIgnoreAddedOnly, segmentTimeThreshold, verbose)
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