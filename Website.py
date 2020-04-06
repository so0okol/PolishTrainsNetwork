from bs4 import BeautifulSoup
from urllib import request
from time import sleep
import pandas as pd
from datetime import timedelta, datetime
from StationCode import *
import Station
from Line import Line
import numpy as np
import re


# create url address from given criteria
def createUrl(station_from, station_to, datetime_from):
    url = "https://beta.bilkom.pl/podroz?poczatkowa="
    url += str(station_from)
    url += "&posrednia1=&posrednia2=&docelowa="
    url += str(station_to)
    url += "&data="
    datetime_value = str(format(datetime_from.day, '02d')) + \
                     str(format(datetime_from.month, '02d')) + \
                     str(datetime_from.year) + \
                     str(format(datetime_from.hour, "02d")) + \
                     str(format(datetime_from.minute, "02d"))
    url += datetime_value
    url += "&directOnly=on&przyjazd=false&minChangeTime=&bilkomAvailOnly=off&_csrf="
    return url


# get data from one line of BILKOM html page
def getDataFromLine(line):
    line = str(line)
    retSeries = pd.Series()
    # arrival_date = line.split('data-arrivaldate="')
    dataArrival = line.split('data-arrival="')
    stationTo = dataArrival[1].split('"')[0]
    stationFrom = line.split('data-departure="')[1].split('"')[0]
    if isinstance(dataArrival, list):
        stationsIntermediate = line.split('data-stations="')[1].split('">')[0]
        arrivalDate = line.split('data-arrivaldate="')[1].split('"')[0]
        departureDate = line.split('data-startdate="')[1].split('"')[0]
        carrierId = line.split('data-carrierid="')[1].split('"')[0]
        trainNumber = line.split('data-number="')[1].split('"')[0]
        retSeries["carrier"] = carrierId
        retSeries["number"] = trainNumber
        retSeries["arrival"] = arrivalDate
        retSeries["departure"] = departureDate
        retSeries["intermediates"] = stationsIntermediate.replace(";", "-")
    return retSeries, stationFrom, stationTo


class Website:
    repeatNumber = 5
    urlDelay = 3
    url = ""
    soup = None

    def __init__(self, url, repeatNumber=5, urlDelay=3):
        self.repeatNumber = repeatNumber
        self.urlDelay = urlDelay
        self.url = url

    def getRequest(self, repeat=False):
        if self.soup is None or repeat:
            ii = 0
            while ii < self.repeatNumber:
                try:
                    urlRes = request.urlopen(self.url).read().decode('UTF-8')
                    ii = self.repeatNumber
                except:
                    ii += 1
                    sleep(self.urlDelay)
                    pass
            self.soup = BeautifulSoup(urlRes, features="html.parser")
        return self.soup


class BilkomWebsite(Website):
    stationFrom = None
    stationTo = None
    datetimeFrom = None

    def __init__(self, stationFrom, stationTo, datetimeFrom, repeatNumber=5, urlDelay=3):
        self.repeatNumber = repeatNumber
        self.urlDelay = urlDelay
        self.datetimeFrom = datetimeFrom
        self.stationFrom = stationFrom
        self.stationTo = stationTo
        self.url = createUrl(stationFrom, stationTo, datetimeFrom)

    def getConnections(self):
        stationFrom = self.stationFrom
        stationTo = self.stationTo
        howManyDone = 0
        while howManyDone < 2:
            if self.soup is None or howManyDone != 0:
                soup = self.getRequest()
            else:
                soup = self.soup
            carrierSoup = soup.find_all(class_="carrier-metadata")
            connection_df = pd.DataFrame()
            for line in carrierSoup:
                if '"carrier-metadata"' in str(line):
                    line_data_series, line_station_from, line_station_to = getDataFromLine(line)
                    if not line_data_series.empty and line_station_from == str(stationFrom) and line_station_to == str(
                            stationTo):
                        connection_df = connection_df.append(line_data_series, ignore_index=True)
            last_departure = ""
            if not connection_df.empty:
                last_departure = connection_df.iloc[-1]["departure"]
                howManyDone = 2
            else:
                howManyDone += 1
                sleep(0.4)
            if last_departure != "":
                last_departure_date = last_departure.split(" ")[0]
                last_departure_date_list = last_departure_date.split("-")
                last_departure_time = last_departure.split(" ")[1]
                last_departure_time_list = last_departure_time.split(":")
                last_departure = datetime(int(last_departure_date_list[2]), int(last_departure_date_list[1]),
                                          int(last_departure_date_list[0]), int(last_departure_time_list[0]),
                                          int(last_departure_time_list[1]))
            else:
                last_departure = self.datetimeFrom + timedelta(days=1)
        connection_df = connection_df.drop_duplicates(subset="number", keep="first")
        return connection_df, last_departure


class StationBazaWebsite(Website):
    bazaCode = None

    def __init__(self, data):
        if isinstance(data, Station.Station):
            self.bazaCode = str(data.bazaCode)
        elif isinstance(data, int) or isinstance(data, np.int64):
            self.bazaCode = str(data)
        elif isinstance(data, str):
            self.bazaCode = data
        else:
            raise ValueError(
                "Argument of StationBazaWebsite initializer should be either Station object, integer or string")
        self.url = r"https://www.bazakolejowa.pl/index.php?dzial=stacje&id=" + self.bazaCode + "&okno=start"

    def getStationInfo(self):
        self.getRequest()
        stationInfo = self.soup.find_all("table")[0].td.text
        return stationInfo

    def getLines(self):
        self.getRequest()
        retList = []
        for tableRow in self.soup.find_all("table")[2].find_all("tr")[2:]:
            tdList = tableRow.find_all("td")
            try:
                type = tdList[0]["title"]
                bracketList = tdList[2].text.split("(")
                number = bracketList[-1].split(")")[0]
                try:
                    number = int(number)
                except ValueError:
                    number = number.split("/")[0]
                cityFrom = bracketList[0].split("–")[0]
                cityTo = bracketList[0].split("–")[1]
                bazaCode = tdList[2].a["href"].split("id=")[1].split("&")[0]
                retList.append((Line(number, bazaCode, type=type, stationTo=cityTo, cityFrom=cityFrom),
                                float(tdList[1].text.replace(",", "."))))
            except KeyError:
                pass
        return retList


class LineBazaWebsite(Website):

    def __init__(self, data):
        if isinstance(data, Line):
            self.bazaCode = str(data.bazaCode)
        elif isinstance(data, int) or isinstance(data, np.int64):
            self.bazaCode = str(data)
        elif isinstance(data, str):
            self.bazaCode = data
        else:
            raise ValueError(
                "Argument of LineBazaWebsite initializer should be either Line object, integer or string")
        self.url = r"https://www.bazakolejowa.pl/index.php?dzial=linie&id=" + str(self.bazaCode) + "&okno=przebieg"

    def getLineData(self):
        self.getRequest()
        title = self.soup.title.text
        line = Line()
        if title == "Wykaz linii":
            return None
        stationFromToList = self.soup.title.text.replace("Linia ", "")
        if isinstance(stationFromToList, list):
            cityFrom = self.soup.title.text.replace("Linia ", "").split("–")[0]
            if cityFrom[-1] == " ":
                cityFrom = cityFrom[:-1]
            line.stationFrom = cityFrom
            cityTo = self.soup.title.text.replace("Linia ", "").split("–")[1]
            for sign in ["(", ")"]:
                if sign in cityTo:
                    cityTo = cityTo.replace(sign, "")
                if cityTo[0] == " ":
                    cityTo = cityTo[1:]
                if cityTo[-1] == " ":
                    cityTo = cityTo[:-1]
            line.stationTo = cityTo
        ret = re.search("\(([^)]*)\)[^(]*$", title)
        if ret is not None:
            try:
                number = int(ret.group(1))
            except ValueError:
                if "/" in ret.group(1):
                    number = int(ret.group(1).split("/")[0])
                else:
                    number = None
            line.number = number
        line.bazaCode = self.bazaCode
        for trElem in self.soup.find_all("table")[0].find_all("tr"):
            try:
                tdList = trElem.find_all("td")
                stationData = (tdList[1].a.text, tdList[2].input["value"], tdList[0].span["title"])
                line.stationList.append(stationData)
            except:
                pass
        return line
