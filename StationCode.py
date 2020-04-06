from journeys import *
import pandas as pd
from datetime import datetime
from parms import excel_path


def get_intermediate_stations(url, datetime):
    def get_website(url):
        ii = 0
        soup = ""
        while ii < repeat_number:
            try:
                url_res = request.urlopen(url).read().decode('UTF-8')
                ii = repeat_number
                soup = BeautifulSoup(url_res, features="html.parser")
            except:
                ii += 1
                sleep(url_delay)
                pass
        return soup

    def create_url(station_from, station_to, datetime_from):
        url = "https://beta.bilkom.pl/podroz?poczatkowa="#A%3D1%40L%3D"
        url += str(station_from)
        url += "&posrednia1=&posrednia2=&docelowa="#"%40B%3D1%40&posrednia1=&posrednia2=&docelowa=A%3D1%40L%3D"
        url += str(station_to)
        url += "&data="# "%40B%3D1%40&data="
        print(str(format(datetime_from.minute, '02d'))+str(format(datetime_from.month,'02d')))
        datetime_value = str(format(datetime_from.day, '02d')) + \
                         str(format(datetime_from.month,'02d')) + \
                         str(datetime_from.year) + \
                         str(format(datetime_from.hour, "02d")) + \
                         str(format(datetime_from.minute, "02d"))
        url += datetime_value
        url += "&directOnly=on&przyjazd=false&minChangeTime=&bilkomAvailOnly=off&_csrf="
        return url

    data_from, data_to = get_codes_from_url(url)
    url_new = create_url(data_from[1], data_to[1], datetime)
    soup = get_website(url_new)
    json_path = soup.find_all(class_="jsonPath")
    station_list = str(json_path).split("A=1@O=")
    stations_df = pd.DataFrame(columns=["code"])
    for ii in range(1,len(station_list)):
        station_data = station_list[ii]
        station_data_list = station_data.split("@")
        city = station_data_list[0]
        code = station_data_list[4].replace("L=", "")
        stations_df = stations_df.append(pd.Series([code], name=city, index=["code"]))
    stations_df = stations_df.drop_duplicates()
    return stations_df

def get_intermediate_stations_from_list(list_path):
    df = pd.read_csv(list_path)
    all_stations_df = pd.DataFrame()
    for row in df.iterrows():
        series = row[1]
        datetime_val = datetime(series.year, series.month, series.day, series.hour, series.minute)
        url = series.link
        stations_df = get_intermediate_stations(url, datetime_val)
        all_stations_df = all_stations_df.append(stations_df)
    all_stations_df = all_stations_df.drop_duplicates()
    all_stations_df = all_stations_df.rename_axis("station")
    all_stations_df = all_stations_df.sort_index(ascending=False)
    return all_stations_df

def get_city_code_from_excel(city):#, excel_path="..//python_files//stacjeKM.xlsx"):
    path = excel_path
    df = pd.read_excel(path, index_col=0)
    if city in list(df.index.values):
         ret_value = df.loc[[city]]
         ret_value = ret_value.values[0][0]
    else:
        ret_value = "ERROR " + city + " nie jest w pliku " + path
    return str(ret_value)

def get_city_name_from_excel(code):
    code = int(code)
    path = excel_path
    df = pd.read_excel(path, index_col=1)
    if code in list(df.index.values):
        ret_value = df.loc[[code]]
        ret_value = ret_value.values[0][0]
    else:
        ret_value = "ERROR " + str(code) + " is not in file " + path
    return ret_value
