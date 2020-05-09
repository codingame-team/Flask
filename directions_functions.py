# coding: utf-8
from mapbox import Directions
import requests
import sys
import pprint
import math
from geojson import Feature, Point

def calculateDistanceVolOiseau(from_location, to_location):
    earth_radius = 6371
    longA = (math.pi / 180) * from_location.longitude
    latA = (math.pi / 180) * from_location.latitude
    longB = (math.pi / 180) * to_location.longitude
    latB = (math.pi / 180) * to_location.latitude
    X = (longB - longA) * math.cos(((latA + latB) / 2));
    Y = latB - latA;
    distance = math.sqrt(X * X + Y * Y) * earth_radius;
    return distance

#
# Some basic tutorial on using Directions Mapbox API :-)
#   - https://github.com/mapbox/mapbox-sdk-py/blob/master/docs/directions.md#directions
# et une doc plus générale pour décrire les différentes fonctionalités exploitables par l'API:
#   - https://docs.mapbox.com/help/how-mapbox-works/directions/
#
# Paramètres d'entrée: Location Object Source, Location Object Destination, Mapbox API key
#         N.B. en fait on a besoin seulement des attributs (Longitude, Latitude).
#              On utilise ici le module geojson pour créer nos objets de type Feature GEOJSON et accessoirement pour extraire plus aisément (ou pas) les données en sortie :-D
#               Consultable ici: https://pypi.org/project/geojson/
# Paramètres de sortie: JSON Object {'distance': 9176.91, 'duration': 1263.044} ou code d'erreur HTTP si pas d'objet JSON retourné par l'API Mapbox
#
def get_Directions_Mapbox(from_location, to_location, api_key):
    service = Directions(access_token=api_key)
    origin = Feature(geometry=Point((from_location.longitude, from_location.latitude)))
    destination = Feature(geometry=Point((to_location.longitude, to_location.latitude)))
    #my_profile = 'mapbox/driving'
    my_profile = 'mapbox/driving-traffic'
    response = service.directions([origin, destination], profile=my_profile, geometries=None, annotations=['duration', 'distance'])
    driving_routes = response.geojson()
    #print("JSON Object: ", driving_routes, file=sys.stderr)
    #new_json = driving_routes['features'][0]['properties']
    #pprint.pprint(new_json)
    if response.status_code == 200:
        return driving_routes['features'][0]['properties']
    else:
        return response.status_code