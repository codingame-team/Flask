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
        SECRET_KEY='d66HR8dç"f_-àgjYYic*dh',
        UPLOAD_FOLDER='data',
    )
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

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
            var_dump(result)
            gpx_file = request.files["gpx_file"]
            if gpx_file:
                securedFilename = secure_filename(gpx_file.filename)
                print(securedFilename)
                print(os.path.join(app.config["UPLOAD_FOLDER"], securedFilename))
                gpx_file.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], securedFilename)
                )
            Domicile = gpx.Position_GPS(43.683708, 7.179375, "Domicile")
            jour, heure, amende, distance, elapsed_time, distance_not_OK, duration_not_OK, exceeded_time, exceeded_distance = gpx.gpx_covid_regulations_check_compliance(
                gpx_file, Domicile)
            exceeded_minutes = exceeded_time / 3600
            exceeded_seconds = (exceeded_minutes - int(exceeded_minutes)) * 60
            gpx_file.close()
            n = result['nom']
            p = result['prenom']
            return render_template("resultat.html", nom=n, prenom=p, amende=amende, distance=round(distance, 1),
                                   elapsed_time=round(elapsed_time), distance_KO=distance_not_OK,
                                   duration_KO=duration_not_OK, exceeded_minutes=round(exceeded_minutes),
                                   exceeded_seconds=round(exceeded_seconds), exceeded_distance=round(exceeded_distance))
        except Exception as e:
            return render_template("errors/error_fileupload.html", error_message=e, file="toto")

    return app
