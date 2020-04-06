from NetworkPath import *
from GetNetwork import convert_string_timedelta, convert_time
import networkx as nx
from networkx import Graph
from Station import *
import matplotlib.pyplot as plt
from bokeh.io import show, output_file
from bokeh.models import Plot, Range1d, MultiLine, Circle, HoverTool, BoxZoomTool, ResetTool, PanTool, WheelZoomTool, \
    SaveTool
from bokeh.layouts import row
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.models.graphs import from_networkx


def plotGraph(graph, title=None, graphSavePath=None, networkPath=None):
    for k, adjacencies in zip(list(graph.nodes.keys()), graph.adjacency()):
        graph.nodes[k]["degree"] = len(adjacencies[1])
    if networkPath is not None:
        for city in graph.nodes():
            graph.nodes[city]["code"] = graph.networkPath.stationList.getCode(city)
    plot_height = 700
    plot = Plot(plot_width=900, plot_height=plot_height,
                x_range=Range1d(-1.1, 1.1), y_range=Range1d(-1.1, 1.1))
    plot.title.text = title
    node_hover_tool = HoverTool(
        tooltips=[("Miasto", "@index"), ("Kod miasta", "@code"), ("Stopien wierzcholka", "@degree")])
    plot.add_tools(WheelZoomTool(), PanTool(), SaveTool(), node_hover_tool, BoxZoomTool(), ResetTool())  # , TapTool())
    graph_renderer = from_networkx(graph, nx.spring_layout, scale=1, center=(0, 0))
    graph_renderer.node_renderer.glyph = Circle(size=12, fill_color="yellow")
    graph_renderer.node_renderer.selection_glyph = Circle(size=15, fill_color="blue")
    graph_renderer.node_renderer.hover_glyph = Circle(size=15, fill_color="red")
    graph_renderer.edge_renderer.glyph = MultiLine(line_color="green", line_alpha=0.3, line_width=1)
    graph_renderer.edge_renderer.selection_glyph = MultiLine(line_color="blue", line_width=1.2)
    graph_renderer.edge_renderer.hover_glyph = MultiLine(line_color="red", line_width=1.2)
    plot.renderers.append(graph_renderer)
    columnCities = ColumnDataSource(data=dict(city=list(graph.nodes.keys())))
    columnsNetwork = [TableColumn(field="city", title="Miasto"), ]
    table = DataTable(source=columnCities, columns=columnsNetwork, width=155, height=plot_height)
    layout = row(plot, table)
    if graphSavePath is not None:
        output_file(graphSavePath, title)
    show(layout)

def compareGraphs(G1, G2):
    nodeG2List = list(G2.nodes)
    nodeDiffList = []
    for node in G1.nodes:
        if node not in nodeG2List:
            nodeDiffList.append(node)
    edgeG2List = list(G2.edges)
    edgeDiffList = []
    for edge in G1.edges:
        if edge not in edgeG2List:
            edgeDiffList.append(edge)
    return nodeDiffList, edgeDiffList

class ChangesGraph(Graph):
    shortestPathsDict = {}
    networkPath = None
    stopsGraph = None

    def __init__(self, networkObject, carrierId=["KM"], **kwargs):
        """

        :type networkObject: NetworkPath object
        :param carrierId: list of String: names of carriers that we want to have in network
        :type *kwargs: arguments of networkx.Graph object and optional arguments self.fromDataFrame function
        """
        super().__init__(self)
        if isinstance(networkObject, pd.DataFrame):
            networkDf = networkObject.copy()
        else:
            networkDf = networkObject.createNetworkDf(carrierId)
            self.networkPath = networkObject
        source = "city_from_name"
        if "source" in kwargs.keys():
            source = kwargs["source"]
        target = "city_to_name"
        if "target" in kwargs.keys():
            target = kwargs["target"]
        self.fromDataFrame(networkDf, source, target, **kwargs)

    def fromDataFrame(self, df, source, target, weights=[], weightsFun={}):
        """

        :param df: pandas.DataFrame object
        :param source: string: name of column where edge begins
        :param target: string: name of column where edge ends
        :param weights: list: list of columns that we want to use as edge data
        :param weightsFun: dictionary: dictionary that show functions (dicts's values) used to transform column (dict's key)
        """
        if not isinstance(weights, list):
            raise ValueError(
                "weights should be an instance of list but they are of type " + str(type(weights)) + ": " + str(
                    weights))
        dfCopy = df.copy()
        for col, fun in weightsFun.items():
            dfCopy[col] = dfCopy[col].apply(fun)
        for index, row in dfCopy.iterrows():
            self.add_edge(row[source], row[target], **dict(row[weights]))

    def addOneConnection(self, stationFrom, stationTo):
        if self.has_edge(stationFrom, stationTo):
            self[stationFrom][stationTo]["num_connections"] += 1
        else:
            raise ValueError(
                    "stopsGraph should be given, because connection from {0} to {1} does not exist in this graph. Define self.stopsGraph as StopsGraph object".format(
                        str(stationFrom), str(stationTo)))

    def addConnection(self, stationList):
        #if not self.has_edge(stationList, stationTo) and self.stopsGraph is None:
        #    raise ValueError("stopsGraph should be given if such connection does not exist in graph. Define self.stopsGraph as StopsGraph object.")
        for ii in range(1, len(stationList)):
            stationFrom = stationList[ii-1]
            for jj in range(ii, len(stationList)):
                stationTo = stationList[jj]
                self.addOneConnection(stationFrom, stationTo)

    def getShortestPathsList(self, weight):
        pathList = []
        for city, stations in nx.shortest_path_length(self, weight=weight):
            for v in stations.values():
                if v != 0:
                    pathList.append(v)
        return pathList

    def getShortestPaths(self, weights=None, replace=False):
        shortestPathsList = []
        if weights is None or isinstance(weights, str):
            weights = [weights]
        for weight in weights:
            if weight not in self.shortestPathsDict.keys() or replace:
                shortestPath = nx.shortest_path(self, weight=weight)
                shortestPathsList.append(shortestPath)
                self.shortestPathsDict[weight] = shortestPath
        return shortestPathsList

    def plotNodeHistogram(self, retSequence=False, **histParams):
        degreeDict = dict(nx.degree(self))
        sequence = sorted(degreeDict.values(), reverse=True)  # degree sequence
        plt.hist(x=sequence, **histParams)
        if retSequence:
            return sequence

    def plotShortestPathHistogram(self, weight, **histParams):
        pathsList = nx.shortest_path_length(self, weight=weight)
        lenList = []
        for paths in pathsList:
            for length in paths[1].values():
                if length != 0:
                    lenList.append(length)
        plt.hist(lenList, **histParams)


class TransferGraph(ChangesGraph):
    networkObject = None

    def __init__(self, networkObject, df=None, **kwargs):
        if not isinstance(networkObject, NetworkPath):
            raise ValueError("networkObject should be instance of NetworkPath but it is of type " + str(
                type(networkObject)) + ": " + str(networkObject))
        self.networkObject = networkObject
        weightsFun = {"avg_time": convert_string_timedelta}
        if "weightsFun" in kwargs.keys():
            if "avg_time" in kwargs["weightsFun"].keys():
                weightsFun = kwargs["weightsFun"]
            else:
                weightsFun = {**weightsFun, **kwargs["weightsFun"]}
        weights = ["avg_time", "num_connections"]
        if "weights" in kwargs.keys():
            if "avg_time" in kwargs["weights"]:
                weights = kwargs["weights"]
            else:
                weights.extend(kwargs["weights"])
        networkData = None
        if df is None:
            networkData = networkObject
        else:
            networkData = df.copy()
        super().__init__(networkData, weights=weights, weightsFun=weightsFun, **kwargs)
        self.addTransferFactorToEdges(**kwargs)

    def addConnection(self, stationList):
        for ii in range(1, len(stationList)):
            stationFrom = stationList[ii-1]
            for jj in range(ii, len(stationList)):
                stationTo = stationList[jj]
                self.addOneConnection(stationFrom, stationTo)
                transferTime = self.nodes[stationFrom][stationTo]
                numConn = self[stationFrom][stationTo]["num_connections"]
                self.nodes[stationFrom][stationTo] = transferTime*(numConn-1)/numConn
                self.nodes[stationTo][stationFrom] = transferTime*(numConn-1)/numConn
                self[stationFrom][stationTo]["travel_time"] = self[stationFrom][stationTo]["avg_time"]+self.nodes[stationFrom][stationTo]

    def setTransferFactor(self, source: str, target: str) -> float:
        transfer_factor = None
        try:
            df = self.networkObject[source][target]
        except KeyError:
            df = self.networkObject[target][source]
        departures = df["departure"].apply(convert_time)
        mean_transfer = str(departures.diff().mean())
        if mean_transfer is "NaT":
            transfer_factor = 12 * 60
        else:
            transfer_factor = convert_string_timedelta(mean_transfer) / 2
        self.nodes[source][target] = transfer_factor
        return transfer_factor

    def addTransferFactorToEdges(self, **kwargs):
        for node in self.nodes:
            for neighbor in self[node]:
                self.edges[(node, neighbor)]["travel_time"] = self.edges[(node, neighbor)]["avg_time"] + self.setTransferFactor(node, neighbor)


class StationsGraph(Graph):

    def __init__(self, lineList, stationsFilter=None, networkPath=None, changesGraphCarriers=["KM"], allInLine=True):
        """
        :type networkObject: NetworkPath object
        :param carrierId: list of String: names of carriers that we want to have in network
        :type *kwargs: arguments of networkx.Graph object and optional arguments self.fromDataFrame function
        """
        super().__init__(self)
        if stationsFilter is not None:
            if isinstance(stationsFilter, list) and isinstance(stationsFilter[0], Station):
                stationsFilter = [s.name for s in stationsFilter]
            elif isinstance(stationsFilter, list) and isinstance(stationsFilter[0], str):
                pass
            else:
                raise ValueError("StationsFilter should be type of list of string or list of Station objects")
        changesGraph = None
        if networkPath is not None:
            if isinstance(networkPath, NetworkPath):
                changesGraph = ChangesGraph(networkPath, changesGraphCarriers, weights=["avg_time"],
                                            weightsFun={"avg_time": lambda x: convert_string_timedelta(x) / 60})
            else:
                raise ValueError("networkPath should be type of ChangesGraph object")

        def checkCondition(line, ii):
            lastData = line.stationList[ii - 1]
            data = line.stationList[ii]
            retValue = False
            if stationsFilter is None:
                retValue = True
            elif allInLine:
                for stationName in line.getStationNames():
                    if stationName in stationsFilter:
                        retValue = True
                        break
            elif data[0] in stationsFilter and lastData[0] in stationsFilter:
                retValue = True
            return retValue

        for line in lineList:
            for ii in range(1, len(line.stationList)):
                lastData = line.stationList[ii - 1]
                data = line.stationList[ii]
                if checkCondition(line, ii):
                    distance = 0
                    try:
                        distance = float(data[1]) - float(lastData[1])
                    except:
                        pass
                    self.add_edge(data[0], lastData[0], km=distance)
                    if "lines" in self.nodes[data[0]].keys():
                        self.nodes[data[0]]["lines"].append(line)
                    else:
                        self.nodes[data[0]]["lines"] = [line]
                    if data[0] in stationsFilter:
                        self.nodes[data[0]]["type"] = "in"
                    else:
                        self.nodes[data[0]]["type"] = "out"
                    if changesGraph is not None:
                        try:
                            self[data[0]][lastData[0]]["speed"] = self[data[0]][lastData[0]]["km"] / \
                                                                  changesGraph[data[0]][lastData[0]]["avg_time"]
                        except KeyError:
                            self[data[0]][lastData[0]]["speed"] = 0

    def getDistance(self, stationFrom: str, statonTo: str) -> float:
        short_path = nx.shortest_path(self, stationFrom, statonTo, "km")
        distance = 0
        for ii in range(1, len(short_path)):
            stationFromTemp = short_path[ii-1]
            statonToTemp = short_path[ii]
            distance += self[stationFromTemp][statonToTemp]["km"]
        return distance
