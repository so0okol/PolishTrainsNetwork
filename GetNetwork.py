#!/usr/bin/env python
# coding: utf-8

# In[5]:


import networkx as nx
import pandas as pd
from os import listdir
from os.path import join, isfile, sep
from datetime import datetime

# # Pobranie grafów
# G1 - graf nieważony
# G2 - graf ważony iloscią połączeń
# G3 - graf ważony średnim czasem połączenia

file_name_sep = "_"
city_name_sep = "."
excel_path = "..//python_files//stacjeKM.xlsx"

def get_city_code_from_excel(city, excel_path="..//python_files//stacjeKM.xlsx"):
    path = excel_path
    df = pd.read_excel(path, index_col=0)
    if city in list(df.index.values):
         ret_value = df.loc[[city]]
         ret_value = ret_value.values[0][0]
    else:
        ret_value = "ERROR " + city + " nie jest w pliku " + path
        raise Exception(ret_value)
    return str(ret_value)

def get_avg_connection_time(path):
    avg_connection_dict = {}
    for city_from in listdir(path):
        city_from_name = city_from.split("_")[0]
        avg_connection_dict[city_from_name] = {}
        for city_to in listdir(join(path, city_from)):
            city_to_name = city_to.split("_")[0]
            df = pd.read_csv(join(path, city_from, city_to))
            avg_connection_dict[city_from_name][city_to_name] = time_value_series.mean()
    return avg_connection_dict


# In[7]:
def convert_string_timedelta(time_value):
    time = str(time_value).split(" ")[2].split(".")[0]
    time_value_temp = time.split(":")
    time_value_temp = int(time_value_temp[0])*60+int(time_value_temp[1])+int(time_value_temp[2])/60.
    #time_value_list.append(time_value_temp)
    return time_value_temp

def convert_time(string_time):
    return datetime.strptime(string_time.replace(" CET", ""), "%d-%m-%Y %H:%M")

def get_transfer_factor(node, neighbor, conn_G=None, conn_G_weight=None, files_path=None):
    transfer_factor = None
    if files_path is not None:
        node = node.replace("Warszawa Młynów d Koło", "Warszawa Młynów d.Koło")
        neighbor = neighbor.replace("Warszawa Młynów d Koło", "Warszawa Młynów d.Koło")
        city_from = node.replace(" ",city_name_sep)+file_name_sep+get_city_code_from_excel(node, excel_path)
        travel_date = files_path.split(sep)[-2]
        city_to = neighbor.replace(" ",city_name_sep)+file_name_sep
        city_to += get_city_code_from_excel(neighbor, excel_path)+file_name_sep+travel_date
        if not isfile(join(files_path, city_from, city_to+".csv")):
            city_to = node.replace(" ",city_name_sep)+file_name_sep
            city_to += get_city_code_from_excel(node, excel_path)+file_name_sep+travel_date
            city_from = neighbor.replace(" ",city_name_sep)+file_name_sep+get_city_code_from_excel(neighbor, excel_path)
        df = pd.read_csv(join(files_path, city_from, city_to+".csv"))
        departures = df["departure"].apply(convert_time)
        mean_transfer = str(departures.diff().mean())
        if mean_transfer is "NaT":
            transfer_factor = 12*60
        else:
            transfer_factor = convert_string_timedelta(mean_transfer)
    else:
        transfer_factor = 24/conn_G.get_edge_data(node, neighbor)[conn_G_weight]
    return transfer_factor/2

def get_transfer_graph(time_G, files_path=None, conn_G=None, weight = "weight"):
    if conn_G is None and files_path is None:
        raise Exception("Either conn_G or files_path (path to network's files) has to be defined")
    G = time_G.copy()
    for node in G.nodes:
        for neighbor in G[node]:
            transfer_factor = get_transfer_factor(node, neighbor, conn_G, weight, files_path)
            G.nodes[node][neighbor] = transfer_factor
            G.edges[(node,neighbor)][weight] += transfer_factor
    return G

def get_graphs_from_path(network_path):
    df = pd.read_csv(network_path)
    network_df = df[["city_from_name", "city_to_name", "num_connections"]]
    num_connections_series = df["num_connections"]
    network_df = network_df.rename(columns={"num_connections" : "weight"})
    conn_graph = nx.from_pandas_edgelist(network_df, "city_from_name", "city_to_name", "weight")
    network_df = df[["city_from_name", "city_to_name", "avg_time"]]
    network_df = network_df.rename(columns={"avg_time" : "weight"})
    # time_value_list = []
    # for time_value in network_df["weight"]:
    #     time = time_value.split(" ")[2].split(".")[0]
    #     time_value_temp = time.split(":")
    #     time_value_temp = int(time_value_temp[0])*60+int(time_value_temp[1])+int(time_value_temp[2])/60.
    #     time_value_list.append(time_value_temp)
    # time_value_series = pd.Series(time_value_list)
    network_df["weight"] = network_df["weight"].apply(convert_string_timedelta)# = time_value_series
    time_value_series = network_df["weight"]
    time_graph = nx.from_pandas_edgelist(network_df, "city_from_name", "city_to_name", "weight")
    #network_df["weight"] = num_connections_series*time_value_series
    network_df["weight"] = time_value_series/num_connections_series
    connxtime_graph = nx.from_pandas_edgelist(network_df, "city_from_name", "city_to_name", "weight")
    network_df = df[["city_from_name", "city_to_name"]]
    unweighted_graph = nx.from_pandas_edgelist(network_df, "city_from_name", "city_to_name")
    graph_tuple = unweighted_graph, conn_graph, time_graph, connxtime_graph
    return graph_tuple
