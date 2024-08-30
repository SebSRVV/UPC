import osmnx as ox
from osmnx import distance
import networkx as nx
import folium
from flask import Flask, render_template, request, jsonify
from geopy.geocoders import Nominatim

#OSMX Config
ox.config(use_cache=True, log_console=True)

app = Flask(__name__)

#Heuristica para A*
def heuristic(u, v, graph):
    #distancia euclidiana entre los nodos
    ux, uy = graph.nodes[u]['x'], graph.nodes[u]['y']
    vx, vy = graph.nodes[v]['x'], graph.nodes[v]['y']
    return ((ux - vx) ** 2 + (uy - vy) ** 2) ** 0.5

#calcular la ruta usando A*
def calculate_route(origin, destination, transport_mode):
    geolocator = Nominatim(user_agent="route_planner")

    #ubicacion y destino
    origin_point = geolocator.geocode(origin)
    destination_point = geolocator.geocode(destination)

    if not origin_point or not destination_point:
        return None, None, None

    origin_coords = (origin_point.latitude, origin_point.longitude)
    destination_coords = (destination_point.latitude, destination_point.longitude)

    #modo de transporte
    modo = {"driving" : "drive", "walking" : "walk", "bicycle" : "bike"}
    graph = ox.graph_from_point(origin_coords, dist=10000, network_type=modo[transport_mode], simplify=False)

    #nodos mas cercanos
    orig_node = ox.distance.nearest_nodes(graph, origin_coords[1], origin_coords[0])
    dest_node = ox.distance.nearest_nodes(graph, destination_coords[1], destination_coords[0])

    #ruta más corta usando A*
    route = nx.astar_path(graph, orig_node, dest_node, weight='length', heuristic=lambda u, v: heuristic(u, v, graph))

    return route, graph, origin_coords

#Ruta principal
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        origin = request.form["origin"]
        destination = request.form["destination"]
        transport_mode = request.form["transport_mode"]

        route, graph, origin_coords = calculate_route(origin, destination, transport_mode)

        if route is None:
            return render_template("index.html", error="No se pudo calcular la ruta. Por favor, verifica los datos ingresados.")

        #crear un mapa centrado en el origen
        estilo = "cartodb positron"
        m = folium.Map(location=origin_coords, zoom_start=14, tiles=estilo)

        #obtener coordenadas de la ruta
        route_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in route]

        #añadir la ruta al mapa
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)

        #guardar el mapa en un archivo HTML
        m.save("templates/map.html")

        return render_template("map.html")

    return render_template("index.html")

if __name__ == "__main__":
     app.run(host='0.0.0.0', port=5000)
