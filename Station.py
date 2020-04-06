import pandas as pd
from datetime import datetime

class Station:
    name = ""
    bilkomCode = 0
    bazaCode = None

    def __str__(self):
        return(self.name + " " + self.bilkomCode + " <Station object>")

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.equals(other)

    def __init__(self, cityName, bilkomCode):
        self.name = str(cityName)
        self.bilkomCode = str(bilkomCode)

    def equalsBilkomCode(self, code : str):
        isEqual = False
        if self.bilkomCode == code:
            isEqual = True
        return isEqual

    def equalsName(self, name : str):
        isEqual = False
        if self.name == name:
            isEqual = True
        return isEqual

    def equalsStation(self, station) -> bool:
        isEqual = False
        if self.name == station.name and self.bilkomCode == station.bilkomCode:
            isEqual = True
        return isEqual

    def equals(self, data):
        isEqual = False
        if isinstance(data, Station):
            isEqual = self.equalsStation(data)
        else:
            try:
                intData = int(data)
                isEqual = self.equalsBilkomCode(data)
            except ValueError:
                isEqual = self.equalsName(data)
        return isEqual


###########################################
from Website import BilkomWebsite
class StationList(list):

    def __init__(self, path: object = None) -> object:
        super().__init__()
        if path is not None:
            df = pd.read_excel(path)
            for index, row in df.iterrows():
                self.append(Station(str(row["station"]), str(row["code"])))

    def getFromConnFile(self, connFilepath):
        # TO DO
        df = pd.read_csv(connFilepath)
        for index, row in df.iterrows():
            date = datetime(row["year"], row["month"], row["day"], row["hour"], row["minute"])
            url = row["link"]
            print(url)
            poczatkowa = url.split("poczatkowa")[1]
            poczatkowa = poczatkowa.split("&")[0]
            try:
                codeFrom = poczatkowa.split("D00")[1].split("%")[0]
            except IndexError:
                codeFrom = poczatkowa
            docelowa = url.split("docelowa=")[1]
            codeTo = docelowa.split("&")[0]
            retWebsite = BilkomWebsite(codeFrom,codeTo,date).getConnections()
            for _, rowConn in retWebsite[0].iterrows():
                self.append(Station(rowConn["station"], rowConn["code"]))

    def append(self, data):
        if isinstance(data, Station):
            self.appendCityCode(data)

    def extend(self, dataList):
        for data in dataList:
            self.append(data)

    def appendCityCode(self, cityCode, repeatValues=False):
        if repeatValues:
            super().append(cityCode)
        elif not self.inList(cityCode):
            super().append(cityCode)

    def inList(self, newStation):
        isInList = False
        for station in self:
            if isinstance(station, Station):
                if station.equalsStation(newStation):
                    isInList = True
                    break
        return isInList

    def getName(self, bilkomCode):
        name = "name"
        for station in self:
            if station == str(bilkomCode):
                name = station.name
                break
        return name

    def getCode(self, name):
        code = ""
        for cityCode in self:
            if cityCode.name == str(name):
                code = cityCode.bilkomCode
                break
        return code

    def getData(self, data):
        retData = ""
        try:
            intData = int(data)
            retData = self.getName(intData)
        except ValueError:
            retData = self.getCode(data)
        return retData

    def getStation(self, data):
        stationObject = None
        for station in self:
            if station == data:
                stationObject = station
                break
        return stationObject

    def getCities(self, codeList):
        cityList = []
        for code in codeList:
            cityList.append(self.getName(code))
        return cityList
