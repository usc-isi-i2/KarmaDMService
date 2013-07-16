from __future__ import division
import csv
from collections import defaultdict
from fileinfo import filename, files

# filename = "test/sample/sample_data_%d.txt"
# filename = "../extracted_data/860173015670486/sample/sample_data_%d.txt"
# files = range(1, 25)
# filename = "../extracted_data/863101010131862/sample/sample_data_%d.txt"
# files = range(1, 5)
# filename = "../extracted_data/863101010249847/sample/sample_data_%d.txt"
# files = range(1, 6)
# filename = "../extracted_data/863101010336255/sample/sample_data_%d.txt"
# files = range(1, 7)
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
        #self.counts_uni['$'] = len(train_files)
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
    #####################################
    # print "Unigram Counts:"
    # print
    # for t in self.counts_uni:
    #     print t, self.counts_uni[t]
    # print
    # print "Bigram Counts:"
    # print
    # for t in self.counts_bi:
    #     print t, self.counts_bi[t]
    # print
    #####################################
    
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
            # for e in self.counts_uni:
            # print e, self.counts_uni[e]
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

def find_accuracy():
    sum = 0
    filenames = ["../extracted_data/860173015670486/sample/sample_data_%d.txt", "../extracted_data/863101010131862/sample/sample_data_%d.txt", "../extracted_data/863101010249847/sample/sample_data_%d.txt", "../extracted_data/863101010336255/sample/sample_data_%d.txt"]
    files = [range(1, 25), range(1, 5), range(1, 6), range(1, 7)]
    for i in range(4):
        model = LocationPrecitionModel(files[i], filenames[i], latLabel, longLabel, dirLabel, originalTextLabel, gridScale, shouldIgnoreRepetitions, shouldIgnoreAddedOnly, verbose=False)
        model.readFiles()
        maxAccuracy, bestSet, avgAccuracy = model.crossValidate(sequential=True)
        sum = sum + avgAccuracy
        print avgAccuracy
    print sum/4

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
#model.printUniqueLocations()
#model.printData()

if __name__ == '__main__':
    main()