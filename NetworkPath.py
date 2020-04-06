import os
from os.path import join, isdir, isfile
import numpy as np
from datetime import timedelta, datetime
from Station import *
import copy

class NetworkPath(dict):
    stationList = StationList()
    trainsDict = {}

    def __init__(self, path: str=None, citySep: str = ".", fileSep: str = "_") -> None:
        """

        :param path: path where network structure is saved. It contains folders with csv files
        :param citySep: separator of city (instead space), e.g. "Warszawa Centralna" to "Warszawa.Centralna"
        :param fileSep: separator of file name. It concatenates city name and city bilkomCode, e.g. "Siemiatycze_5103355"
        """
        super().__init__()
        if path is not None:
            for cityFromFile in os.listdir(path):
                if isdir(join(path, cityFromFile)):
                    cityFromFileSep = cityFromFile.split(fileSep)
                    cityFrom = cityFromFileSep[0].replace(citySep, " ")
                    codeFrom = cityFromFileSep[1]
                    cityCodeFrom = Station(cityFrom, codeFrom)
                    self.stationList.append(cityCodeFrom)
                    self[cityFrom] = {}
                    for cityToFile in os.listdir(join(path, cityFromFile)):
                        cityToFilePath = join(path, cityFromFile, cityToFile)
                        if isfile(cityToFilePath):
                            cityToFileSep = cityToFile.split(fileSep)
                            cityTo = cityToFileSep[0].replace(citySep, " ")
                            codeTo = cityToFileSep[1]
                            cityCodeTo = Station(cityTo, codeTo)
                            self.stationList.append(cityCodeTo)
                            self[cityFrom][cityTo] = pd.read_csv(cityToFilePath)

    def __copy__(self):
        clone = NetworkPath()
        clone = self
        return clone


    def getAllTrains(self):
        for cityFrom in self.keys():
            for cityTo, df in self[cityFrom].items():
                for index, row in df.iterrows():
                    trainNumber = row["number"]
                    trainIntemediates = row["intermediates"].split("-")
                    trainIntermediatesLen = len(trainIntemediates)
                    if trainNumber in self.trainsDict.keys():
                        if max(self.trainsDict[trainNumber][0], trainIntermediatesLen) == trainIntermediatesLen:
                            self.trainsDict[trainNumber] = (trainIntermediatesLen, trainIntemediates)
                    else:
                        self.trainsDict[trainNumber] = (trainIntermediatesLen, trainIntemediates)
        return self.trainsDict

    def getTrainData(self, trainNumber, intermediatesList=[]):
        trainNumber = str(trainNumber)
        trainDf = pd.DataFrame()
        maxNumTrains = 0
        intemediatesCntList = []
        dataSeriesList = []
        for cityFrom in self.keys():
            cityFromCode = self.stationList.getCode(cityFrom)
            if len(intermediatesList) == 0 or cityFromCode == intermediatesList[0]:
                pass
            else:
                continue
            for cityTo, df in self[cityFrom].items():
                if len(intermediatesList) == 0 or self.stationList.getCode(cityTo) == intermediatesList[-1]:
                    pass
                else:
                    continue
                for index, row in df.iterrows():
                    trainNumberTemp = str(row["number"])
                    if trainNumberTemp == trainNumber:
                        newNumTrains = len(row["intermediates"].split("-"))
                        maxNumTrains = max(maxNumTrains, newNumTrains)
                        intemediatesCntList.append(len(row["intermediates"].split("-")))
                        dataSeriesList.append(row)
                        # if trainDf.empty:
                        #     trainDf = pd.DataFrame(row).transpose()
                        # elif maxNumTrains == newNumTrains:
                        #     trainDf = trainDf.append(row)
        return dataSeriesList[np.argmax(intemediatesCntList)]

    def createNetworkDf(self, carrierId=["KM"]):
        networkDf = pd.DataFrame()
        for cityFrom in self.keys():
            for cityTo, df in self[cityFrom].items():
                if not carrierId[0] == "all":
                    df = df[df["carrier"].isin(carrierId)]
                num_connections = df.shape[0]
                counter = 0
                travel_time = timedelta()
                for row in df.iterrows():
                    counter += 1
                    if "CET" in row[1].arrival:
                        arrival = row[1].arrival.replace(" CET", "")
                    else:
                        arrival = row[1].arrival.replace(" CEST", "")
                    if "CET" in row[1].departure:
                        departure = row[1].departure.replace(" CET", "")
                    else:
                        departure = row[1].departure.replace(" CEST", "")
                    arrival_datetime = datetime.strptime(arrival, "%d-%m-%Y %H:%M")
                    departure_datetime = datetime.strptime(departure, "%d-%m-%Y %H:%M")
                    travel_time += arrival_datetime - departure_datetime
                if num_connections != 0:
                    travel_time /= counter
                    citySeries = pd.Series()
                    citySeries["city_from"] = self.stationList.getCode(cityFrom)
                    citySeries["city_from_name"] = cityFrom
                    citySeries["city_to"] = self.stationList.getCode(cityTo)
                    citySeries["city_to_name"] = cityTo
                    citySeries["num_connections"] = num_connections
                    citySeries["avg_time"] = travel_time
                    networkDf = networkDf.append(citySeries, ignore_index=True)
        return networkDf
