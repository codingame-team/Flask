# coding: utf-8
import os
import re
import sys
import locale
import time
from math import radians, sin, cos, sqrt, atan2, pi
from datetime import datetime
from typing import TextIO
from pytz import timezone
from gpxpy import parse
from gpxpy.gpx import GPX
from common import get_strava_path, resource_path


class PositionGPS:
	def __init__(self, latitude, longitude, lieu_dit):
		self.latitude = float(latitude)
		self.longitude = float(longitude)
		self.lieu_dit = lieu_dit

	def calculate_distance_vol_oiseau(self, other) -> float:
		"""Calculate great-circle distance between two points using Haversine formula."""
		R = 6371.0  # Earth radius in km
		lat1, lon1 = map(radians, (self.latitude, self.longitude))
		lat2, lon2 = map(radians, (other.latitude, other.longitude))
		a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
		return 2 * R * atan2(sqrt(a), sqrt(1 - a))


def gpx_covid_regulations_check_compliance(gpx_file: TextIO, domicile: PositionGPS):
	d_max = 1.0
	d_runner = 0.0
	gpx: GPX = parse(gpx_file)
	moving_data = gpx.get_moving_data()
	max_speed_kmh = moving_data.max_speed * 3600 / 1000

	for track in gpx.tracks:
		for segment in track.segments:
			for point in segment.points:
				gps_pos = PositionGPS(point.latitude, point.longitude, "")
				distance = domicile.calculate_distance_vol_oiseau(gps_pos)
				#print(f'{point} - Distance from home: {distance:.3f} km')
				d_runner = max(d_runner, distance)

	locale.setlocale(locale.LC_TIME, 'fr_FR')
	start_time = gpx.get_time_bounds().start_time.astimezone(timezone('Europe/Paris'))
	end_time = gpx.get_time_bounds().end_time.astimezone(timezone('Europe/Paris'))
	day, hour = start_time.strftime('%A %d %B %Y'), start_time.strftime('%Hh%M')
	elapsed_time = gpx.get_duration()
	distance3d = gpx.length_3d() / 1000

	exceeded_distance = max(0, d_runner - d_max)
	exceeded_time = max(0, elapsed_time - 3600)
	amende = exceeded_distance > 0 or exceeded_time > 0

	return day, hour, amende, distance3d, elapsed_time, exceeded_distance, exceeded_time, max_speed_kmh


def display_message(filename, day, hour, elapsed_time, distance, exceeded_distance, exceeded_time, max_speed_kmh) -> str:
	elapsed_hours, elapsed_minutes = divmod(elapsed_time / 60, 60)
	message = (f"Le {day}, vous avez débuté une activité sportive intitulée \"{filename.split('.')[0]}\" à {hour} et parcouru une distance "
			   f"de {distance:.1f} km pour une durée de {int(elapsed_hours)}h{round(elapsed_minutes)}mn, et atteint la vitesse maximale de {max_speed_kmh:.2f} km/h.")

	if exceeded_distance > 0:
		message += f" Vous avez dépassé le périmètre autorisé de {exceeded_distance:.3f} km!"
	if exceeded_time > 0:
		exceeded_minutes, exceeded_seconds = divmod(exceeded_time, 60)
		message += f" Vous avez dépassé la durée autorisée de {round(exceeded_minutes)} minutes et {round(exceeded_seconds)} secondes!"

	return message


def main():
	gpx_strava_path = get_strava_path()
	# print(f"Strava path: {gpx_strava_path}")
	os.makedirs(gpx_strava_path, exist_ok=True)


	domicile = PositionGPS(43.683708, 7.179375, "Domicile")
	total_distance = total_duration = nombre_infractions = 0

	print("-" * 80)
	print("Analyse des fichiers GPX dans le répertoire courant")
	for filename in sorted(os.listdir(gpx_strava_path)):
		if filename.endswith('.gpx'):
			print("-" * 80)
			with open(resource_path(f'{gpx_strava_path}/{filename}'), 'r') as gpx_file:
				data = gpx_covid_regulations_check_compliance(gpx_file, domicile)
				jour, heure, amende, distance, elapsed_time, exceeded_distance, exceeded_time, max_speed_kmh = data
				print(display_message(filename, jour, heure, elapsed_time, distance, exceeded_distance, exceeded_time, max_speed_kmh))

				if amende:
					nombre_infractions += 1
				total_distance += distance
				total_duration += elapsed_time

	print("-" * 80)
	if nombre_infractions > 0:
		print(f"Vous avez commis un total de {nombre_infractions} infraction(s), montant dû: {nombre_infractions * 135}€")
	else:
		print("Félicitations, vous avez respecté les directives!")
	print("-" * 80)


if __name__ == '__main__':
	main()
