import os
import sys
import html.parser
import json
import time
from enum import Enum

class NoaaParseState(Enum):
    start = 0
    inArea = 1
    inStation = 2
    captureName = 3
    captureDate = 4


class StationListParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(self)
        self.stations = {}
        self.current = None
        self.status = NoaaParseState.start
        self.area = ''

    def parse(self, inFileName):
        with open(inFileName) as f:
            self.feed(f.read())

    def handle_starttag(self, tag, attrs):
        if tag in ['br', 'hr', 'img']:
            return

        da = {x[0]:x[1] for x in attrs}
        if 'class' in da and 'areaheader' in da['class']:
            self.enterArea(da)
        elif 'class' in da and 'station' in da['class']:
            self.enterStation(da)
        elif tag == 'a' and self.status == NoaaParseState.inStation:
            self.enterCapturingName()
        elif 'class' in da and 'datefield' in da['class']:
            self.enterCapturingDate()
    
    def handle_endtag(self, tag):
        if self.status == NoaaParseState.inStation and tag == 'div':
            self.exitStation()

    def handle_data(self, data):
        if self.status == NoaaParseState.captureDate:
            self.exitCapturingDate(data)
        elif self.status == NoaaParseState.captureName:
            self.exitCapturingName(data)

    def enterArea(self, da):
        self.area = da['id']
        self.status = NoaaParseState.inArea

    def enterStation(self, da):
        assert self.status == NoaaParseState.inArea
        self.current = {}
        self.current['station_id'] = da['id']
        self.current['area'] = self.area
        self.status = NoaaParseState.inStation

    def exitStation(self):
        self.stations[self.current['station_id']] = self.current
        self.current = None
        self.status = NoaaParseState.inArea

    def enterCapturingName(self):
        assert self.status == NoaaParseState.inStation
        self.status = NoaaParseState.captureName

    def exitCapturingName(self, data):
        self.current['name'] = data
        self.status = NoaaParseState.inStation

    def enterCapturingDate(self):
        assert self.status == NoaaParseState.inStation
        self.status = NoaaParseState.captureDate

    def exitCapturingDate(self, data):
        start, end = data.split('-')
        inFormat = '%b %d, %Y'
        iso8601 = '%Y-%m-%d'

        startDate = None if not start else time.strptime(start.strip(), inFormat)
        endDate = None if 'present' in end else time.strptime(end.strip(), inFormat)

        self.current['start_date'] = '' if not startDate else time.strftime(iso8601, startDate)
        self.current['end_date'] = '' if not endDate else time.strftime(iso8601, endDate)
        self.current['active'] = not endDate
        self.status = NoaaParseState.inStation

#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

INPUT = '../../data/noaa_station_list.html'
OUTPUT = '../../data/noaa_station_list.json'

if __name__ == '__main__':
    # where is this script?
    thisScriptDir = os.path.dirname(__file__)

    # load the input file
    print('Loading HTML')
    fn = os.path.join(thisScriptDir, INPUT)
    parser = StationListParser()
    parser.parse(fn)

    # determine maxes for schema def
    for col in ['name', 'area', 'station_id']:
        lengths = [len(v[col]) for k,v in parser.stations.items()]
        print('Max',col,'length', max(lengths))

    # save as JSON
    print('Saving as JSON')
    fn = os.path.join(thisScriptDir, OUTPUT)
    with open(fn, 'w') as f:
        json.dump(parser.stations, f, indent=2)