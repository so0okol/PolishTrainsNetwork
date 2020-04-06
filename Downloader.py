from Station import StationList
import pandas as pd
from datetime import timedelta
from Website import BilkomWebsite
import os
from os.path import exists, join
from datetime import datetime, time


class DataDownloader(StationList):
    saveDir = None
    citySep = None
    fileSep = None

    def __init__(self, saveDir: str, citySep: str = ".", fileSep: str = "_") -> object:
        """
        A class to download train connection data into files from beta.bilkom.pl website
        :param saveDir: path where network structure is saved
        :param citySep: separator of city (instead space), e.g. "Warszawa Centralna" to "Warszawa.Centralna"
        :param fileSep: separator of file name. It concatenates city name and city bilkomCode, e.g. "Siemiatycze_5103355"
        """
        super().__init__()
        self.saveDir = saveDir
        self.citySep = citySep
        self.fileSep = fileSep
        if not exists(saveDir):
            os.makedirs(saveDir)

    def getConnectionsRange(self, datetimeFrom: datetime, datetimeTo: datetime) -> None:
        """
        Function that gets connection files for a given period of time.
        It saves data in list of folders (departure station) containing csv files (arrival station).
        :param datetimeFrom: datetime object. Specify a minimal departure date and time
        :param datetimeTo: datetime object. Specify a maximal departure date and time
        """
        def getConnection(stationFrom, stationTo, datetimeFrom, datetimeTo):
            datetimeTemp = datetimeFrom
            connectionDf = pd.DataFrame()
            if datetimeTo > datetimeFrom:
                while datetimeTemp < datetimeTo:
                    web = BilkomWebsite(stationFrom.bilkomCode, stationTo.bilkomCode, datetimeTemp)
                    oneConnectionDf, lastDeparture = web.getConnections()
                    connectionDf = connectionDf.append(oneConnectionDf, ignore_index=True)
                    datetimeTemp = lastDeparture + timedelta(minutes=1)
            connectionDf = connectionDf.drop_duplicates(subset="number", keep="first")
            return connectionDf
        for ii in range(len(self)):
            fromPath = join(self.saveDir, self[ii].name + self.fileSep + self[ii].bilkomCode)
            if not exists(fromPath):
                os.makedirs(fromPath)
            for jj in range(ii, len(self)):
                toName = join(fromPath,
                              self[jj].name + self.fileSep + self[jj].bilkomCode + ".csv")
                connDf = getConnection(self[ii], self[jj], datetimeFrom, datetimeTo)
                if not connDf.empty:
                    connDf.to_csv(toName)

    def getConnections(self, dateDay : datetime.date):
        """
        Function that gets connection files for a given day.
        It saves data in list of folders (departure station) containing csv files (arrival station).
        :param dateDay: date object. A date that we search connections for.
        """
        datetimeFrom = datetime.combine(dateDay, time(0,0))
        datetimeTo = datetime.combine(dateDay, time(23,59))
        self.getConnectionsRange(datetimeFrom, datetimeTo)
