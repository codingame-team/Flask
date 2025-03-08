from __future__ import annotations

from flask import Flask, render_template, jsonify, request
from extensions import db, migrate
import secrets
from itsdangerous import URLSafeSerializer
from logging import basicConfig, DEBUG
import locale
import os

import geocoding_functions as gps_api
import gpx_strava_check as gpx
from werkzeug.utils import secure_filename


def create_app():
	app = Flask(__name__, static_folder='static', static_url_path='/static')

	# Set the secret key
	app.secret_key = secrets.token_bytes(32).hex()

	# Create serializer
	app.serializer = URLSafeSerializer(app.secret_key)

	# Config
	app.config.from_object('config.Config')

	# Initialize extensions
	db.init_app(app)
	migrate.init_app(app, db)

	# Locale settings
	locale.setlocale(locale.LC_TIME, 'fr_FR')
	basicConfig(level=DEBUG)

	# Create a directory in a known location to save files to.
	uploads_dir = os.path.join(app.instance_path, 'uploads')
	os.makedirs(uploads_dir, exist_ok=True)

	@app.route('/')
	def welcome():
		return render_template('index.html')

	@app.route('/about/')
	def about():
		return render_template('about.html')

	@app.route('/resultat', methods=['POST'])
	def resultat():
		try:
			# logging.DEBUG(request)
			app.logger.debug(request)
			result = request.form
			nom = result['nom']
			prenom = result['prenom']
			adresse = result['adresse']
			ville = result['ville']
			# postal_address = adresse + " " + ville
			fw_geocoding_result = gps_api.get_GPS_Coordinates_Mapbox(adresse, ville, app.config['MAPBOX_API_KEY'])
			if len(result) == 1:
				raise Exception("Erreur de géolocalisation! Service Mapbox (code erreur HTTP {})".format(result))
			else:
				longitude = fw_geocoding_result[0]
				latitude = fw_geocoding_result[1]
				rev_geocoding_result = gps_api.get_Postal_Address_Mapbox(longitude, latitude, app.config['MAPBOX_API_KEY'])
				domicile = gpx.Position_GPS(latitude, longitude, "domicile")
				gpx_file = request.files["gpx_file"]
				# Sauvegarde locale du fichier avant analyse...
				if gpx_file.filename.endswith('.gpx'):
					new_filename = gpx_file.filename.split(".gpx")[0] + "_" + nom.upper() + "_" + prenom[0].upper() + prenom[1:] + "_long" + str(longitude) + "_lat" + str(latitude) + ".gpx"
					securedFilename = secure_filename(new_filename)
					securedFilename = os.path.join(uploads_dir, securedFilename)
					gpx_file.save(securedFilename)
				elif gpx_file.filename == '':
					raise Exception("Fichier GPX manquant!")
				else:
					raise Exception("Extension du fichier {} invalide, doit être un fichier GPX!".format(gpx_file.filename))
				gpx_file = open(securedFilename, 'r')
				jour, heure, amende, distance, elapsed_time, distance_OK, duration_OK, exceeded_time, exceeded_distance = gpx.gpx_covid_regulations_check_compliance(gpx_file, domicile)
				gpx_file.close()
				total_duration_hours = elapsed_time / 3600
				total_duration_minutes = (total_duration_hours - int(total_duration_hours)) * 60
				exceeded_minutes = exceeded_time / 3600
				exceeded_seconds = (exceeded_minutes - int(exceeded_minutes)) * 60
				# app.logger.warning('testing warning log')
				# app.logger.error('testing error log')
				# app.logger.info(str(domicile.latitude))
				return render_template("resultat.html", found_postal_address=rev_geocoding_result, nom=nom, prenom=prenom, jour=jour, heure=heure, amende=amende, distance=round(distance, 1), elapsed_time=round(elapsed_time), distance_OK=distance_OK, duration_OK=duration_OK, total_duration_hours=int(total_duration_hours), total_duration_minutes=round(total_duration_minutes), exceeded_minutes=int(exceeded_minutes), exceeded_seconds=round(exceeded_seconds), exceeded_distance=round(exceeded_distance, 3))
		except Exception as e:
			return render_template("errors/error_fileupload.html", error_message=e, filename=gpx_file.filename)

	return app
