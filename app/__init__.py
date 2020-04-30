# app/__init__.py

from flask import Flask, render_template, request
from app import gpx_strava_check as gpx
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.utils import secure_filename
import os.path
from flask import send_file
from var_dump import var_dump
import logging

def create_app():
    app = Flask(__name__)

    app.config.update(
        DEBUG=True,
        SECRET_KEY='d66HR8dç"f_-àgjYYic*dh'
    )
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

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

    # @app.route('/hello/')
    # @app.route('/hello/<name>/')
    # def hello(name='Anonyme'):
    #     return render_template('hello.html', name=name)


    @app.route('/resultat', methods=['POST'])
    def resultat():
        try:
            result = request.form
            gpx_file = request.files["gpx_file"]
            securedFilename = secure_filename(gpx_file.filename)
            securedFilename = os.path.join(uploads_dir, securedFilename)
            gpx_file.save(securedFilename)
            Domicile = gpx.Position_GPS(43.683708, 7.179375, "Domicile")
            gpx_file = open(securedFilename, 'r')
            jour, heure, amende, distance, elapsed_time, distance_not_OK, duration_not_OK, exceeded_time, exceeded_distance = gpx.gpx_covid_regulations_check_compliance(
                gpx_file, Domicile)
            gpx_file.close()
            total_duration_hours = elapsed_time / 3600
            total_duration_minutes = (total_duration_hours - int(total_duration_hours)) * 60
            exceeded_minutes = exceeded_time / 3600
            exceeded_seconds = (exceeded_minutes - int(exceeded_minutes)) * 60
            n = result['nom']
            p = result['prenom']
            return render_template("resultat.html", nom=n, prenom=p, jour=jour, heure=heure, amende=amende, distance=round(distance, 1),
                                   elapsed_time=round(elapsed_time), distance_KO=distance_not_OK,
                                   duration_KO=duration_not_OK, total_duration_hours=round(total_duration_hours), total_duration_minutes=round(total_duration_minutes), exceeded_minutes=round(exceeded_minutes),
                                   exceeded_seconds=round(exceeded_seconds), exceeded_distance=round(exceeded_distance,3))
        except Exception as e:
            return render_template("errors/error_fileupload.html", error_message=e, filename=gpx_file.filename)

    return app
