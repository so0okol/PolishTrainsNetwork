import pandas as pd
from Station import Station

class Line():
    number = None
    stationFrom = None
    stationTo = None
    bazaCode = None
    type = None
    stationList = []
    stationNames = []

    def __init__(self, number=None, bazaCode=None, type=None, stationFrom=None, stationTo=None):
        if bazaCode is not None:
            self.bazaCode =  int(bazaCode)
        if number is not None:
            self.number = int(number)
        self.stationFrom = stationFrom
        self.stationTo = stationTo
        self.type = type
        self.stationList = []

    def __repr__(self):
        return str(self.number)+" <Line object>"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.equalsData(other)

    def equalsData(self, data):
        cmpValue = data
        if isinstance(data, str):
            cmpValue = int(data)
        if isinstance(data, Line):
            cmpValue = data.number
        if self.number == cmpValue:
            return True
        else:
            return False

    def getStationNames(self):
        if len(self.stationNames) != len(self.stationList):
            self.stationNames = [stationData[0] for stationData in self.stationList]
        return self.stationNames

    def getStationData(self, station):
        if isinstance(station, Station):
            station = station.name
        return self.stationList[self.getStationNames().index(station)]

    def toSeries(self):
        series = pd.Series()
        series["number"] = self.number
        series["baza_code"] = self.bazaCode
        series["station_from"] = self.stationFrom
        series["station_to"] = self.stationTo
        stationListString = ""
        for station, km, type in self.stationList:
            stationListString += str(station)
            stationListString += str("_")
            stationListString += str(km)
            stationListString += str("_")
            stationListString += str(type)
            stationListString += "|"
        series["station_list"] = stationListString
        return series


    def fromSeries(self, series):
        self.number = series["number"]
        self.bazaCode = series["baza_code"]
        self.stationFrom = series["station_from"]
        self.stationTo = series["station_to"]
        self.stationList = []
        try:
            for stationData in series["station_list"].split("|"):
                oneStationData = stationData.split("_")
                if not oneStationData[0] is "":
                    self.stationList.append(oneStationData)
        except AttributeError:
            pass
        return self

class LineList(list):

    def __init__(self,path=None):
        if path is not None:
            df = pd.read_excel(path, index_col=0)
            for index, row in df.iterrows():
                super().append(Line().fromSeries(row))

    def getLine(self, num):
        line = None
        for lineTemp in self:
            if lineTemp == num:
                line = lineTemp
                break
        return line

    def getStationLines(self, stationData):
        stationList = []
        if isinstance(stationData, str):
            stationList = [stationData]
        elif isinstance(stationData, Station):
            stationList = [stationData.name]
        elif isinstance(stationData, list) and isinstance(stationData[0], str):
            stationList = stationData
        elif isinstance(stationData, list) and isinstance(stationData[0], Station):
            stationList = [station.name for station in stationData]
        else:
            raise ValueError("StationData should be either string, Station object, list of strings or list of Station objects")
        retLineDict = {}
        for stationName in stationList:
            retLineDict[stationName] = []
            for line in self:
                if stationName in line.getStationNames():
                    retLineDict[stationName].append(line)
        return retLineDict

