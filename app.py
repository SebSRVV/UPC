import osmnx as ox
import networkx as nx
import folium
from flask import Flask, render_template, request
from geopy.geocoders import Nominatim

# Configuración de OSMnx
ox.config(use_cache=True, log_console=True)

app = Flask(__name__)

# Función para calcular la ruta
def calculate_route(origin, destination, transport_mode):
    geolocator = Nominatim(user_agent="route_planner")
    
    # Obtener la ubicación de origen y destino
    origin_point = geolocator.geocode(origin)
    destination_point = geolocator.geocode(destination)

    if not origin_point or not destination_point:
        return None, None, None
    
    origin_coords = (origin_point.latitude, origin_point.longitude)
    destination_coords = (destination_point.latitude, destination_point.longitude)
    
    # Obtener el grafo según el modo de transporte
    if transport_mode == "driving":
        graph = ox.graph_from_point(origin_coords, dist=10000, network_type="drive")
    elif transport_mode == "walking":
        graph = ox.graph_from_point(origin_coords, dist=10000, network_type="walk")
    elif transport_mode == "bicycle":
        graph = ox.graph_from_point(origin_coords, dist=10000, network_type="bike")

    # Obtener los nodos más cercanos
    orig_node = ox.distance.nearest_nodes(graph, origin_coords[1], origin_coords[0])
    dest_node = ox.distance.nearest_nodes(graph, destination_coords[1], destination_coords[0])

    # Calcular la ruta más corta
    route = nx.shortest_path(graph, orig_node, dest_node, weight="length")
    
    return route, graph, origin_coords

# Ruta principal
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        origin = request.form["origin"]
        destination = request.form["destination"]
        transport_mode = request.form["transport_mode"]
        
        route, graph, origin_coords = calculate_route(origin, destination, transport_mode)
        
        if route is None:
            return render_template("index.html", error="No se pudo calcular la ruta. Por favor, verifica los datos ingresados.")
        
        # Crear un mapa centrado en el origen
        m = folium.Map(location=origin_coords, zoom_start=14)
        
        # Obtener coordenadas de la ruta
        route_coords = [(graph.nodes[node]['y'], graph.nodes[node]['x']) for node in route]
        
        # Añadir la ruta al mapa
        folium.PolyLine(route_coords, color="blue", weight=5, opacity=0.7).add_to(m)
        
        # Guardar el mapa en un archivo HTML
        m.save("templates/map.html")
        
        return render_template("map.html")
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
