#!/usr/bin/env python3

#Copyright (c) 2018, Hannu Vuolasaho 

#Permission is hereby granted, free of charge, to any person obtaining a 
#copy of this software and associated documentation files (the "Software"), 
#to deal in the Software without restriction, including without limitation 
#the rights to use, copy, modify, merge, publish, distribute, sublicense, 
#and/or sell copies of the Software, and to permit persons to whom the 
#Software is furnished to do so, subject to the following conditions: 

#The above copyright notice and this permission notice shall be included in 
#all copies or substantial portions of the Software. 

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL 
#THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING 
#FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER 
#DEALINGS IN THE SOFTWARE.

import ujson
import json
import sys
import threading
from datetime import datetime

logPath = ""
beaconTimer = None
beaconInterval = 0
beaconData = { 'start_time' : datetime.now().astimezone().isoformat(timespec='seconds'),
               'lines' : 0, 'passed' : 0, 'dropped' : 0, 'inserted' : 0 }


def matching(data, matchObj):
    if type(matchObj) == type(''): #string
        if matchObj in data:
            return True
    elif type(matchObj) == type({}): #object
        for dataKey, dataValue in data.items():
            if dataKey in matchObj and matchObj[dataKey] == dataValue:
                return True
    return False
def timeStamp():
    str = datetime.now().astimezone().isoformat(timespec='seconds')
    return {'filter_time' : str}

def filtering(data):
    if not "filter" in conf:
        return
    filterList = conf["filter"]

    for filterObj in filterList:
        if 'match' in filterObj:
            matchList = filterObj['match']
            matchMade = True
            for matchObj in matchList:
                if not matching(data, matchObj):
                    matchMade = False
                    break
            if matchMade:
                outData = data
                printIt = True
                if 'drop' in filterObj:
                    dropList = filterObj['drop']
                    for dropItem in dropList:
                        if dropItem in outData:
                            del outData[dropItem]
                            beaconData['dropped'] += 1
                if 'pass' in filterObj:
                    passList = filterObj['pass']
                    outData = {}
                    for passItem in passList:
                        if passItem in data:
                            outData[passItem] = data[passItem]
                            beaconData['passed'] += 1
                if 'insert' in filterObj:
                    outData.update(filterObj['insert'])
                    beaconData['inserted'] += 1
                if 'filter_time' in filterObj and filterObj['filter_time'] == True:
                    outData.update(timeStamp())
                if 'report' in filterObj and filterObj['report'] == True:
                    printIt = False
                    print(ujson.dumps(outData), file=sys.stderr )
                if 'file' in filterObj:
                    printIt = False
                    logFileName = logPath + filterObj['file']
                    try:
                        logFile = open(logFileName, 'a')
                        print(ujson.dumps(outData), file=logFile )
                        logFile.close()
                    except IOError as inst:
                            print(f'Logfile {logFileName} open failed: {inst.strerror}',
                                  file=sys.stderr )
                if 'print' in filterObj:
                    printIt = filterObj['print']
                if printIt:
                    print(ujson.dumps(outData))


def beacon():
    beaconData.update(timeStamp())
    print(ujson.dumps(beaconData))
    
def confCheck():
    global logPath
    global beaconInterval
    global beaconTimer
    # Set up log path
    if 'log_path' in conf:
        logPath = conf['log_path'] + "/"
    else:
        logPath = "./"
    print (logPath)
    # Check if there are filtering rules
    if not "filter" in conf:
        print("WARNING: No filter rule in config", file=sys.stderr)
    else:
        filterList = conf["filter"]
    for filterObj in filterList:
        # Check for rules with pass and drop
        if 'pass' in filterObj and 'drop' in filterObj:
            print(f"WARNING: Pass and Drop in {filterObj}", file=sys.stderr)
        # Check for rules without match
        if not 'match' in filterObj:
            print(f"WARNING: Match missing in {filterObj}", file=sys.stderr)
        elif type(filterObj['match']) != type([]): # type checks
            print(f"ERROR: Match is not array in {filterObj}", file=sys.stderr)
        if 'pass' in filterObj and type(filterObj['pass']) != type([]):
            print(f"ERROR: Pass is not array in {filterObj}", file=sys.stderr)
        if 'drop' in filterObj and type(filterObj['drop']) != type([]):
            print(f"ERROR: Drop is not array in {filterObj}", file=sys.stderr)
        if 'insert' in filterObj and type(filterObj['insert']) != type({}):
            print(f"ERROR: Insert is not object in {filterObj}", file=sys.stderr)
        if 'report' in filterObj and type(filterObj['report']) != type(True):
            print(f"ERROR: Report is not bool in {filterObj}", file=sys.stderr)
        if 'print' in filterObj and type(filterObj['print']) != type(True):
            print(f"ERROR: Print is not bool in {filterObj}", file=sys.stderr)
        if 'filter_time' in filterObj and type(filterObj['filter_time']) != type(True):
            print(f"ERROR: Filter_time is not bool in {filterObj}", file=sys.stderr)
        if 'file' in filterObj and type(filterObj['file']) != type(''):
            print(f"ERROR: File is not string in {filterObj}", file=sys.stderr)
            
        # Check for unknown keys
        tmp = filterObj.copy()
        for key in  ['match', 'drop', 'pass', 'insert', 'file', 'report', 'print', 'filter_time']:
            if key in tmp:
                del tmp[key]

        if len(tmp):
            print(f"WARNING: Unknown keys\n{tmp}\nin filter\n{filterObj}")

    # Check for beacon and set it up
    if 'beacon' in conf:
        interval = conf['beacon']
        if 'interval_seconds' in interval:
            beaconInterval = interval["interval_seconds"]
        if beaconInterval > 0:
            beaconTimer = threading.Timer(beaconInterval, beacon)
            beacon()
            beaconTimer.start()


def main():
    global conf
    try:
        [fileName] = sys.argv[1:]
    except ValueError:
        print(f"Usage: {sys.argv[0]} config_file.json", file=sys.stderr)
        exit(1)
    try:    
        confFile = open(fileName)
        #with open('rtl_433_filter_conf.json') as conf_file:
        conf = json.load(confFile)
        confFile.close()
    except IOError as inst:
        print(f'Config file {fileName} open failed: {inst.strerror}',
              file=sys.stderr )
        exit(2)
    confCheck()
    line = sys.stdin.readline()
    while line:
        data = ujson.loads(line)
        filtering(data)
        beaconData['lines'] += 1
        line = sys.stdin.readline()
    beaconTimer.cancel()

if __name__ == '__main__':
    main()
