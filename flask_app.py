# coding: utf-8

from flask import Flask, render_template, request
import gpx_strava_check as gpx
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename
import os
import os.path
import logging
import sys
import geocoding_functions as gps_api
from dotenv import load_dotenv
import datetime
from pytz import timezone
import re
from email import policy
from email.parser import BytesParser
import text_functions as txt_func
import taxi as tax
import pprint

app = Flask(__name__)

#logging.basicConfig(level=logging.DEBUG)
load_dotenv(os.path.join(app.instance_path, '.env'))

app.config.update(
    DEBUG=True,
    SECRET_KEY=os.getenv("SECRET_KEY"),
    MAPBOX_API_KEY=os.getenv("MAPBOX_API_KEY")
    # SECRET_KEY="c'est bien caché :-),
    # MAPBOX_API_KEY="et là aussi :-)"
)
toolbar = DebugToolbarExtension(app)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
MAPBOX_API_KEY = app.config['MAPBOX_API_KEY']
SECRET_KEY = app.config['SECRET_KEY']

# print(app.instance_path, file=sys.stderr)
# print(SECRET_KEY, file=sys.stderr)
# print(MAPBOX_API_KEY, file=sys.stderr)

# Create a directory in a known location to save files to.
uploads_dir = os.path.join(app.instance_path, 'uploads')
os.makedirs(uploads_dir, exist_ok = True)

@app.route('/')
def homepage():
    logging.warning("See this message in Flask Debug Toolbar!")
    return render_template('index.html')

@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/taxi/')
def taxi():
    logging.warning("See this message in Flask Debug Toolbar!")
    return render_template('taxi.html')

@app.route('/planning', methods=['POST'])
def planning():
    try:
        logging.warning("See this message in Flask Debug Toolbar!")
        regex_dsup_delimiter = '>> ?\d{1,2} *'
        regex_cr_lf = '[\n\r]'
        regex_libelle_societe = "^-- {}".format(os.getenv("LIBELLE_SOCIETE"))
        regex_code_secteur = 'S\d{1,2}'
        regex_special_chars = '[^A-Za-z0-9 \-()<<\/]'
        regex_special_chars_sup = '\s+[\-\/]\s+'
        regex_phone_number = '([0-9]{2} ){4}'

        INSTANCE_PATH = "instance"

        # ma clé d'API sur Mabox: https://account.mapbox.com/
        #MAPBOX_API_KEY = "c'est bien caché :-)"
        load_dotenv(os.path.join(INSTANCE_PATH, '.env'))
        MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")
        # print(MAPBOX_API_KEY, file=sys.stderr)
        # print(os.getenv("LIBELLE_SOCIETE"), file=sys.stderr)

        # Create a directory in a known location to save files to.
        uploads_dir = os.path.join(INSTANCE_PATH, 'data')
        os.makedirs(uploads_dir, exist_ok=True)

        # Chemins d'accès aux fichiers sur le PC
        # input_filename = os.path.join(uploads_dir, "Mail des resas.eml")
        # output_filename = os.path.join(uploads_dir, "Planning.txt")
        gps_locations_filename = os.path.join(uploads_dir, "locations_gps.csv")
        taxis_filename = os.path.join(uploads_dir, "taxis.csv")
        #
        # Chargement des informations de courses dans notre base d'objets locaux
        #
        paris = timezone('Europe/Paris')
        today = datetime.datetime.now(paris)
        tomorrow = today + datetime.timedelta(days=1)
        today_str = today.strftime('%Y-%m-%d')
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        result = request.form
        nom = result['nom']
        prenom = result['prenom']
        # Lecture du fichier d'entrée (EML) - fichier binaire de messagerie à décrypter et vérifier le type d'encodage de caractères
        eml_file = request.files["eml_file"]
        # Sauvegarde locale du fichier avant analyse...
        if eml_file.filename.endswith('.eml'):
            new_filename = eml_file.filename.split(".eml")[0] + "_" + nom.upper() + "_" + prenom[0].upper() + prenom[1:] + "_" + today_str + ".eml"
            securedFilename = secure_filename(new_filename)
            securedFilename = os.path.join(uploads_dir, securedFilename)
            eml_file.save(securedFilename)
        elif eml_file.filename == '':
            raise Exception("Fichier EML manquant!")
        else:
            raise Exception("Extension du fichier {} invalide, doit être un fichier EML!".format(eml_file.filename))

        ##########
        ### OK ###
        ##########
        #eml_file_local = open(securedFilename, "rb")
        msg = BytesParser(policy=policy.default).parse(eml_file)
        #eml_file_local.close()

        # texte_courses = msg.get_body(preferencelist=("plain")).get_content() # version qui semble marcher aussi donc pas de nécessité d'utiliser les fonctions codées localement get_charset() et get_body()
        texte_courses = txt_func.get_body(msg)
        #print(texte_courses)
        # Extraction des données utiles à partir du délimiteur >>
        # Enregistrement des données dans un tableau indexé "courses_tab" non structuré
        patron = re.compile(regex_dsup_delimiter)
        courses_tab = patron.split(texte_courses)

        # Suppression du libellé Taxi Médical à la fin
        # ces 2 ligne marchaient au tout début... pas chercher à comprendre :-D
        # libelle_societe = [course for course in courses_tab if re.match(regex_libelle_societe, course)][0]
        # courses_tab.remove(libelle_societe)
        courses_tab.remove(courses_tab[-1])
        nombre_courses = len(courses_tab)
        #print("Nombre courses: {}".format(nombre_courses))
        liste_Courses = []

        # Création de l'objet DAO pour charger la structure de données en mémoire
        DAO_Toolbox = tax.DAO_Toolbox(uploads_dir, MAPBOX_API_KEY, taxis_filename, gps_locations_filename, courses_tab)

        taxis_object_list = DAO_Toolbox.taxis_list
        courses_object_list = DAO_Toolbox.courses_list
        gps_locations_object_list = DAO_Toolbox.gps_locations_list

        for taxi in taxis_object_list:
            app.logger.info("testing info log: {}".format(taxi))

        for course in courses_object_list:
            app.logger.info("testing info log: {}".format(course))

        for location in gps_locations_object_list:
            app.logger.info("testing info log: {}".format(location))

        #
        #   Début de l'algorithme (pour l'instant rien du tout :-DD)
        #

        # Ecriture du fichier de sortie ( A implémenter )
        # DAO_Toolbox.createPlanning()
        output_txt = ""
        print("FIFI")
        for course in courses_tab:
            i = courses_tab.index(course)
            course = txt_func.conversion_accents(course).strip()
            course = re.sub(regex_special_chars, ' ', course)
            course_object = courses_object_list[i]
            from_location = gps_locations_object_list[int(course_object.from_location_id)]
            to_location = gps_locations_object_list[int(course_object.to_location_id)]
            distance_vol_oiseau = direction_api.calculateDistanceVolOiseau(from_location, to_location)
            geojson_object_prop = direction_api.get_Directions_Mapbox(from_location, to_location, MAPBOX_API_KEY)
            courses_object_list[i].distance = geojson_object_prop['distance']
            courses_object_list[i].duration = geojson_object_prop['duration']
            elapsed_hours = course_object.duration / 3600
            elapsed_minutes = (elapsed_hours - int(elapsed_hours)) * 60
            output_txt += "Course #{} - {:0.1f} km - {} km - {}h{}mn - {}\n".format(i + 1, distance_vol_oiseau, round(course_object.distance / 1000, 1), int(elapsed_hours), round(elapsed_minutes), course)
        DAO_Toolbox.calculatePlanning()
        planning_filename = "Planning" + "_" + tomorrow_str + ".txt"
        print(planning_filename, file=sys.stderr)
        planning_filename = os.path.join(uploads_dir, planning_filename)
        planning_file = open(planning_filename, "w")
        print("Ecriture du fichier {} - {} nouvelles courses créées".format(fichier.name, nombre_courses))
        planning_file.write(output_txt)
        planning_file.close()

        return render_template('planning.html', output_txt=output_txt, nom=nom, prenom=nom, today=today_str, tomorrow=tomorrow_str)

    except Exception as e:
        return render_template("errors/error_fileupload.html", error_message=e, filename=eml_file.filename)

@app.route('/resultat', methods=['POST'])
def resultat():
    try:
        result = request.form
        nom = result['nom']
        prenom = result['prenom']
        adresse = result['adresse']
        ville = result['ville']
        #postal_address = adresse + " " + ville
        fw_geocoding_result = gps_api.get_GPS_Coordinates_Mapbox(adresse, ville, MAPBOX_API_KEY)
        if len(result) == 1:
            raise Exception("Erreur de géolocalisation! Service Mapbox (code erreur HTTP {})".format(result))
        else:
            longitude = fw_geocoding_result[0]
            latitude = fw_geocoding_result[1]
            rev_geocoding_result = gps_api.get_Postal_Address_Mapbox(longitude, latitude, MAPBOX_API_KEY)
            Domicile = gpx.Position_GPS(longitude, latitude, "Domicile")
            Domicile = gpx.Position_GPS(longitude, latitude, "Domicile")
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
            jour, heure, amende, distance, elapsed_time, distance_OK, duration_OK, exceeded_time, exceeded_distance = gpx.gpx_covid_regulations_check_compliance(gpx_file, Domicile)
            gpx_file.close()
            total_duration_hours = elapsed_time / 3600
            total_duration_minutes = (total_duration_hours - int(total_duration_hours)) * 60
            exceeded_minutes = exceeded_time / 3600
            exceeded_seconds = (exceeded_minutes - int(exceeded_minutes)) * 60
            # app.logger.warning('testing warning log')
            # app.logger.error('testing error log')
            # app.logger.info(str(Domicile.latitude))
            return render_template("resultat.html", found_postal_address=rev_geocoding_result, nom=nom, prenom=prenom, jour=jour, heure=heure, amende=amende, distance=round(distance, 1),
                                   elapsed_time=round(elapsed_time), distance_OK=distance_OK,
                                   duration_OK=duration_OK, total_duration_hours=int(total_duration_hours), total_duration_minutes=round(total_duration_minutes), exceeded_minutes=int(exceeded_minutes),
                                   exceeded_seconds=round(exceeded_seconds), exceeded_distance=round(exceeded_distance,3))
    except Exception as e:
        return render_template("errors/error_fileupload.html", error_message=e, filename=gpx_file.filename)


if __name__ == "__main__":
    app.run()