# coding: utf-8
from mapbox import Geocoder
import requests
import sys

#
# Fonction MapBox de "forward geocoding" pour récupérer les coordonnées GPS d'une adresse donnée
#   Se base sur des services commerciaux (mais gratuit pour 100.000 requêtes HTTP par mois)
# https://docs.mapbox.com/api/search/#geocoding
# Marche nickel, nécessite une clé API, 100.000 requêtes par mois (payant au delà!)
# https://www.mapbox.com/pricing/#search
#
# Pour installer le package SDK: https://github.com/mapbox/mapbox-sdk-py
#
# Paramètres d'entrée: Adresse postale
#           Structure: "Id_Location";"Adresse Postale";"Latitude";"Longitude";"Code secteur";"Type Location"
# Paramètres de sortie: tableau indexé [longitude, latitude] ou code d'erreur HTTP si pas d'objet JSON retourné par l'API Mapbox
#
def get_GPS_Coordinates_Mapbox(street, city, api_key):
    print(street, file=sys.stderr)
    print(api_key, file=sys.stderr)
    endpoint_full = "mapbox.places-permanent"  # utilisé pour des fonctions avancées payantes (on n'utilise pas!)
    endpoint = "mapbox.places"
    geocoder = Geocoder(access_token=api_key)
    postal_address = street + " " + city
    response = geocoder.forward(postal_address)
    # print(response,file=sys.stderr)
    # print(postal_address,file=sys.stderr)
    debug = response.geojson()
    # print(debug,file=sys.stderr)
    first = response.geojson()['features'][0]
    if response.status_code == 200:
        return [round(coord, 5) for coord in first['geometry']['coordinates']]
    else:
        return response.status_code

def get_Postal_Address_Mapbox(longitude, latitude, api_key):
    endpoint_full = "mapbox.places-permanent"  # utilisé pour des fonctions avancées payantes (on n'utilise pas!)
    endpoint = "mapbox.places"
    geocoder = Geocoder(access_token=api_key)
    response = geocoder.reverse(lon=longitude, lat=latitude)
    first = response.geojson()['features'][0]
    if response.status_code == 200:
        return first['place_name']
    else:
        return response.status_code

#
# Les fonctions de géolocalisation pour OpenStreetMap, GoogleMaps (non utilisées dans ce programme)
#   (N.B.: j'ai choisi Mapbox cf classe DAO_Toolbox plus bas... (100.000 requêtes gratuites par mois) car GoogleMaps API est devenu payant et OpenStreetMap peu exploitable
#
# OpenStreet Map (données OpenData)
# https://nominatim.openstreetmap.org/search?q=17+Strada+Pictor+Alexandru+Romano%2C+Bukarest&format=geojson
# API Documentation: https://nominatim.org/release-docs/develop/api/Search/
# Fonction OpenStreet Map pour récupérer les coordonnées GPS d'une adresse donnée
# Imprécis! Ne localise pas le numéro de rue :-(
# Pas besoin de clé API
def get_GPS_Coordinates_OpenStreet_Map(postal_address, city):
    formatted_PA = postal_address.replace(" ", "+") + parse.quote(",") + "+" + city
    #print(formatted_PA)
    # url_address = parse.urlencode(formatted_PA)
    # url_address = parse.quote(formatted_PA)
    # print(url_address)
    # url_openstreetmap_api = "https://nominatim.openstreetmap.org/search?q=" + url_address + "&key=" + MAPBOX_API_KEY
    url_openstreetmap_api = "https://nominatim.openstreetmap.org/search?q=" + formatted_PA + "&format=geojson"
    #print(url_openstreetmap_api)
    # Request data from link as 'str'
    data = requests.get(url_openstreetmap_api).text
    # convert 'str' to Json
    data = json.loads(data)
    return data

# (Non utilisée) Récupérer une clé d'API pour la géolocalisation Google Maps (nécessite une CB, crédit de 200$ par mois): https://developers.google.com/maps/documentation/geocoding/get-api-key
def get_GPS_Coordinates_Google_API(postal_address, api_key):
    formatted_PA = postal_address
    url_address = parse.urlencode({'address': formatted_PA})
    url_google_map_api = "https://maps.googleapis.com/maps/api/geocode/json?address=" + url_address + "&key=" + api_key
    # Request data from link as 'str'
    data = requests.get(url_google_map_api).text
    # convert 'str' to Json
    data = json.loads(data)
    # data = requests.get(url=url_google_map_api)
    # binary = data.content
    # output = json.loads(binary)
    # result = json.load(urllib.urlopen(url_google_map_api))
    return data