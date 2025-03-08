# coding: utf-8
import re
import os.path
import sys
from typing import TextIO
from math import radians, sin, cos, sqrt, atan2, pi

from gpxpy import parse
# import gpxpy
# import gpxpy.gpx
from gpxpy.gpx import GPX
import locale
import time
from datetime import datetime
from pytz import timezone

from common import get_strava_path, resource_path


#
# Created by Philippe Mourey on 27/04/2020.
# Copyright © 2020 philRG. All rights reserved.
#
#   https://pypi.org/project/gpxpy/
#
# Classes métier "Position_GPS"
#
class Position_GPS(object):
    def __init__(self, latitude, longitude, lieu_dit):
        self.longitude = float(longitude)
        self.latitude = float(latitude)
        self.lieu_dit = lieu_dit
        #print(float(self.longitude), float(self.latitude))

    def calculateDistanceVolOiseau_old(self, other):
        earth_radius = 6371
        longA = (pi / 180) * self.longitude
        latA = (pi / 180) * self.latitude
        longB = (pi / 180) * other.longitude
        latB = (pi / 180) * other.latitude
        X = (longB - longA) * cos(((latA + latB) / 2))
        Y = latB - latA
        D = sqrt(X * X + Y * Y) * earth_radius
        return D

    def calculateDistanceVolOiseau(self, other) -> float:
        """Calculate great-circle distance between two points using Haversine formula."""
        R = 6371.0  # Earth radius in km
        lat1, lon1 = map(radians, (self.latitude, self.longitude))
        lat2, lon2 = map(radians, (other.latitude, other.longitude))

        a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
        return 2 * R * atan2(sqrt(a), sqrt(1 - a))


#
# Fonction d'analyse d'un fichier GPX par rapport aux règles de confinement (durée d'1h et ne pas dépasser un rayon de 1km autour du domicile)
#   Paramètre de sortie: (Boolean, running_distance, running_duration)
def gpx_covid_regulations_check_compliance(gpx_file: TextIO, domicile: Position_GPS):
    d_max = 1.0
    d_runner = 0.0
    gpx: GPX = parse(gpx_file)
    moving_time, stopped_time, moving_distance, stopped_distance, max_speed_ms = gpx.get_moving_data()
    max_speed_kmh = max_speed_ms * 60 ** 2 / 1000
    print(f'max_speed= {max_speed_kmh} km/h')
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                gps_pos = Position_GPS(point.longitude, point.latitude, "")
                distance = domicile.calculateDistanceVolOiseau(gps_pos)
                if distance > d_runner:
                    d_runner = distance

    #
    # Quelques rappels sur les timezones et conversions de timestamps créés avec une timezone UTC
    #   But de cette manipulation: pas trouvé de documentation sur le package GpxPi pour changer la timezone...
    #   et données Strava utilisent UTC comme Timezone et Paris est à UTC+2 (GMT+1)
    #   donc on utilse la fonction astimezone de la classe datetime :-)
    #
    utc = timezone('UTC')
    paris = timezone('Europe/Paris')
    berlin = timezone('Europe/Berlin')
    tokyo = timezone('Asia/Tokyo')
    new_york = timezone('America/New_York')
    los_angeles = timezone('America/Los_Angeles')
    paris_time = datetime.now(paris)
    berlin_time = datetime.now(berlin)
    tokyo_time = datetime.now(tokyo)
    new_york_time = datetime.now(new_york)
    los_angeles_time = datetime.now(los_angeles)
    utc_time = datetime.now(utc)
    # print("UTC Time", utc_time)
    # print("Europe/Paris", paris_time.strftime('%Y-%m-%d_%H-%M-%S'))
    # print("Europe/Berlin", berlin_time.strftime('%Y-%m-%d_%H-%M-%S'))
    # print("Asia/Tokyo", tokyo_time.strftime('%Y-%m-%d_%H-%M-%S'))
    # print("America/New_York", new_york_time.strftime('%Y-%m-%d_%H-%M-%S'))
    # print("America/Los_Angeles", los_angeles_time.strftime('%Y-%m-%d_%H-%M-%S'))

    locale.setlocale(locale.LC_TIME, 'fr_FR')
    time_bound = gpx.get_time_bounds()
    #print("Old Timezone", time_bound.start_time.tzinfo)
    start_time = time_bound.start_time.astimezone(paris)
    #print("New Timezone", start_time.tzinfo)
    end_time = time_bound.end_time.astimezone(paris)
    day = start_time.strftime('%A %d %B %Y')
    hour = start_time.strftime('%Hh%M')
    elapsed_time = gpx.get_duration()
    distance2d = gpx.length_2d() / 1000
    distance3d = gpx.length_3d() / 1000
    duration_OK = True
    distance_OK = True
    amende = False
    exceeded_time = 0
    exceeded_distance = 0

    if d_runner > d_max:
        distance_OK = False
        exceeded_distance = d_runner - d_max
    if elapsed_time > 3600:
        duration_OK = False
        exceeded_time = elapsed_time - 3600

    if not (duration_OK and distance_OK):
        amende = True

    return day, hour, amende, distance3d, elapsed_time, distance_OK, duration_OK, exceeded_time, exceeded_distance


def afficherMessage(day, hour, amende, elapsed_time, distance, distance_OK, duration_OK, exceeded_time, exceeded_distance):
    elapsed_hours = elapsed_time / 3600
    elapsed_minutes = (elapsed_hours - int(elapsed_hours)) * 60
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    print("Le {}, vous avez débuté une activité sportive à {} et parcouru une distance autour de votre domicile de {:0.1f} km pour une durée de {}h{}mn".format(day, hour, distance, int(elapsed_hours), round(elapsed_minutes)))
    if not distance_OK:
        print("Vous avez dépassé le périmètre autorisé d'1km autour de votre domicile de: {:0.3f} km!".format(exceeded_distance))
    if not duration_OK:
        exceeded_minutes = exceeded_time / 3600
        exceeded_seconds = (exceeded_minutes - int(exceeded_minutes)) * 60
        print("Vous avez dépassé la durée autorisée d'1h autour de votre domicile de: {} minutes et {} secondes!".format(round(exceeded_minutes), round(exceeded_seconds)))
    if amende == True:
        print("Vous devez payer une amende de 135€!")
    else:
        print("Félicitations {}, vous avez correctement suivi les directives de confinement pendant cette activité sportive!")

if __name__ == '__main__':
    # Paramètres globaux de l'application
    path = os.path.dirname(__file__)
    abspath = os.path.abspath(path)
    gpx_strava_path = get_strava_path()
    if gpx_strava_path and not os.path.exists(gpx_strava_path):
        os.makedirs(gpx_strava_path)

    domicile: Position_GPS = Position_GPS(43.683708, 7.179375, "Domicile")

    #
    # Analyse après relevé manuel des points les plus éloignés dans Google Maps
    #
    A = Position_GPS(43.696342, 7.174842, "Montaleigne")
    B = Position_GPS(43.687953, 7.173538, "Chemin des Mauberts")
    C = Position_GPS(43.676365, 7.175073, "Garage Melani")

    print("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    print("Données de test de la fonction de calcul de distance à vol d'oiseau")
    for point in list([A,B,C]):
        distance = domicile.calculateDistanceVolOiseau(point)
        print("Distance vol d'oiseau {} -> {} = {:0.3f} km".format(domicile.lieu_dit, point.lieu_dit, distance))

    nombre_infractions = 0
    total_distance = 0
    total_duration = 0
    elapsed_hours = 0
    elapsed_minutes = 0
    print("-------------------------------------------------------------------------------------------------------------------------------------------------------")
    print("Analyse des fichiers GPX dans le répertoire courant")
    for filename in sorted(os.listdir(gpx_strava_path)):
        if filename.endswith('.gpx'):
            with open(resource_path(f'{gpx_strava_path}/{filename}'), 'r') as gpx_file:
                jour, heure, amende, distance, elapsed_time, distance_OK, duration_OK, exceeded_time, exceeded_distance = gpx_covid_regulations_check_compliance(gpx_file, domicile)
            afficherMessage(jour, heure, amende, elapsed_time, distance, distance_OK, duration_OK, exceeded_time, exceeded_distance)
            if amende:
                nombre_infractions += 1
            total_distance += distance
            total_duration += elapsed_time
            elapsed_hours = elapsed_time / 3600
            elapsed_minutes = (elapsed_hours - int(elapsed_hours)) * 60
            print("Félicitations! Vous avez couru un total de {:0.1f} km pour une durée de {}h{}mn".format(distance, int(elapsed_hours), round(elapsed_minutes)))

    print("-------------------------------------------------------------------------------------------------------------------------------------------------------")

    total_duration_hours = total_duration / 3600
    total_duration_minutes =  (total_duration_hours - int(total_duration_hours)) * 60
    total_amendes = nombre_infractions * 135

    print("Félicitations! Vous avez couru un total de {:0.1f} km pour une durée de {}h{}mn".format(total_distance, int(total_duration_hours), int(total_duration_minutes)))
    print("Cependant, vous avez commis un total de {} infractions aux règles de confinement et devez règler un montant de {}€ au trésor public!".format(nombre_infractions,total_amendes))

    print("-------------------------------------------------------------------------------------------------------------------------------------------------------")
