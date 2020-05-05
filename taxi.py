# coding: utf-8
import sys
import math
import email
# import urllib  as URLLIB, urllib3 , urllib_ext , urllib_parse_ParseResult_overloaded, urllib5
import os.path
from urllib import request, parse
import json
#import requests
import re
from email import policy
from email.parser import BytesParser
from email.iterators import typed_subpart_iterator
import geocoding_functions as gps_api


#
# Created by philRG on 26/04/2020.
# Copyright © 2020 philRG. All rights reserved.
#


#
# Quelques fonctions de vérification de l'encodage de caractères utilisé dans le mail (au cas où) - Peut-être à supprimer (car double emploi)
#
def get_charset(message, default="ascii"):
    """Get the message charset"""

    if message.get_content_charset():
        return message.get_content_charset()

    if message.get_charset():
        return message.get_charset()

    return default


def get_body(message):
    """Get the body of the email message"""

    if message.is_multipart():
        # get the plain text version only
        text_parts = [part for part in typed_subpart_iterator(message, 'text', 'plain')]
        body = []
        for part in text_parts:
            charset = get_charset(part, get_charset(message))
            body.append(str(part.get_payload(decode=True), charset, "replace"))

        return u"\n".join(body).strip()

    else:  # if it is not multipart, the payload will be a string
        # representing the message body
        body = str(message.get_payload(decode=True), get_charset(message), "replace")
        return body.strip()


#
# Quelques fonctions de manipulation de chaînes de caractères
#
regex_dsup_delimiter = '>> ?\d{1,2} *'
regex_cr_lf = '[\n\r]'
regex_libelle_societe = '^-- TAXI MEDICAL NICE'
regex_code_secteur = 'S\d{1,2}'
regex_special_chars = '[^A-Za-z0-9 \-()<<\/]'
regex_phone_number = '([0-9]{2} ){4}'

def conversion_accents(chaine):
    converter = {'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'ç': 'c'}
    result = ""
    for c in chaine:
        if c in converter:
            c = converter[c]
        result += c
    return result


#
# Description des classes métier et d'accès aux données
#   Objectif de l'abstraction: s'affranchir de la source de données, structurer des données provenant d'un système tiers, et séparer les différentes couches applicatives
#
#
# Classes métier "Location", "Taxi" et "Courses"
#
class Taxi(object):
    #   Constructeur de la classe Taxi
    #   Paramètres d'initialisation:
    #       - Id (géré par l'application)
    #       - Nom (obligatoire?)
    #       - Id de localisation (géré par l'application)
    def __init__(self, id, name, id_location):
        self.id = id
        self.name = name
        self.id_location = id_location

    def __str__(self):
        return "{} (id:{}), name:{}, id_location:{}".format(self.__class__.__name__, self.id, self.name,
                                                            self.id_location)

class Location(object):
    #   Constructeur de la classe Location
    #   Paramètres d'initialisation:
    #       - Id (géré par l'application)
    #       - Adresse postale (obligatoire)
    #       - Latitude (obligatoire?)
    #       - Longitude (obligatoire?)
    #       - Code secteur (facultatif)
    #       - Type d'emplacement (obligatoire) (adresse taxi, adresse de ramassage "pick-up" ou de destination): "T", "P", "D"
    def __init__(self, id, postal_address, latitude, longitude, sector_code, location_type):
        self.id = id
        self.postal_address = postal_address
        self.latitude = latitude
        self.longitude = longitude
        self.sector_code = sector_code
        self.location_type = location_type
        print(self)

    def __str__(self):
        return "{} (id:{}), postal_address:{}, latitude:{}, longitude:{}, sector_code:{}, location_type:{}".format(self.__class__.__name__, self.id, self.postal_address, self.latitude, self.longitude, self.sector_code, self.location_type)

class Course(object):
    #   Constructeur de la classe Course
    #   Paramètres d'initialisation:
    #       - Id (généré par l'application)
    #       - Id de localisation GPS de l'adresse de "pick-up"
    #       - Id de localisation GPS de l'adresse destination
    #       - Nom du contact (obligatoire)
    #       - Numéro de téléphone principale (obligatoire)
    #       - Numéro de téléphone secondaire (facultatif)
    #       - Information de paiement (obligatoire?)
    #
    def __init__(self, id, time, from_location_id, to_location_id, contact_name, first_phone_no, second_phone_no,
                 payment_info):
        self.id = id
        self.time = time
        self.from_location_id = from_location_id
        self.to_location_id = to_location_id
        self.contact_name = contact_name
        self.first_phone_no = first_phone_no
        self.second_phone_no = second_phone_no
        self.payment_info = payment_info
        self.duration = self.calculateDuration()
        self.distance = self.calculateDistance()
        print(self)

    def calculateDistanceVolOiseau(self):
        earth_radius = 6371
        longA = (math.pi / 180) * self.from_location_id.longitude
        latA = (math.pi / 180) * self.from_location_id.latitude
        longB = (math.pi / 180) * self.to_location_id.longitude
        latB = (math.pi / 180) * self.to_location_id.latitude
        X = (longB - longA) * math.cos(((latA + latB) / 2));
        Y = latB - latA;
        D = math.sqrt(X * X + Y * Y) * earth_radius;

    def calculateDuration(self):
        duration = "15"
        return duration

    def calculateDistance(self):
        duration = "15"
        return duration

    def __str__(self):
        return "{} id: {}, time: {}, from_location_id: {}, to_location_id: {}, contact_name: {}, first_phone_no: {}, second_phone_no: {}, payment_info: {}".format(
            self.__class__.__name__, self.id, self.time, self.from_location_id, self.to_location_id, self.contact_name,
            self.first_phone_no, self.second_phone_no, self.payment_info)

# Classe d'accès aux données GPS (locales ou distantes)
class DAO_Toolbox(object):
    def __init__(self, chemin, api_key, taxis_filename, gps_locations_filename, courses_list):
        self.chemin = chemin
        self.api_key = api_key
        self.taxis_filename = taxis_filename
        self.gps_locations_filename = gps_locations_filename
        self.taxi_list = self.loadTaxis(taxis_filename)
        self.gps_locations_list = self.loadGPSLocations(gps_locations_filename)
        self.gps_locations_count = len(self.gps_locations_list) if self.gps_locations_list != None else 0
        self.courses_list = self.loadCourses(courses_list)
        print(self.gps_locations_list)

    #
    # Création du planning de courses pour les taxis
    # Entrée: à définir
    # Sortie: nom de fichier output_file
    #
    # def createPlanning(self):
    #     output_file = open(os.path.join(chemin, output_file), "r")
    #     output_file = []
    #     taxis_list.append([ligne.split(";", 4) for ligne in output_file])
    #     taxis_file.close()
    #     taxi_object_list = []
    #     for taxi in taxis_list:
    #         id_taxi = taxi[0]
    #         nom = taxi[1]
    #         id_location = taxi[2]
    #         taxi_object = Taxi(id_taxi, nom, id_location)
    #         taxi_object_list.append(taxi_object)
    #     return taxi_object_list

    #
    # Chargement en mémoire du tableau d'objets Courses
    # Entrée: tableau non formatté provenant du fichier d'entrée EML
    # Sortie: liste d'objets de type Courses
    #
    def loadCourses(self, courses_list):
        courses_object_list = []
        for course in courses_list:
            course_object = self.createCourse(courses_list.index(course), course)
            courses_object_list.append(course_object)
        return courses_object_list

    #
    # Chargement en mémoire du tableau d'objets Taxi
    # Entrée: nom de fichier ("data\\taxis.txt")
    #           Structure: "Id taxi";"Nom";"Id_Location"
    # Sortie: liste d'objets de type taxi ou "None" si fichier vide
    #
    def loadTaxis(self, taxis_filename):
        try:
            taxis_file = open(taxis_filename, "r")
            taxi_count = len([taxi for taxi in taxis_file])
            taxis_file.seek(0)
            if taxi_count == 0:
                print("Fichier {} vide!".format(taxis_filename))
                taxis_file.close()
                return None
            else:
                print("Chargement de {} taxi(s)".format(taxi_count))
                taxi_object_list = []
                for line in taxis_file:
                    taxi = line.split(";")
                    id_taxi = taxi[0]
                    nom = taxi[1]
                    id_location = taxi[2]
                    taxi_object = Taxi(id_taxi, nom, id_location)
                    taxi_object_list.append(taxi_object)
                taxis_file.close()
                return taxi_object_list
        except FileNotFoundError:
            print("Pas de fichier {} trouvé!".format(taxis_filename))
            return None
        except (ValueError, KeyError):
            print("Erreur inattendue lecture fichier {}: ValueError {}, KeyError {}".format(taxis_filename, ValueError, KeyError))
            return None

    #
    # Chargement en mémoire du tableau d'objets Locations connues à partir du fichier des localisations gps.
    #   Les données GPS des adresses précédentes de ramassage ne sont pas conservées
    # Paramètres d'entrée: nom de fichier ("data\\locations_gps.txt")
    #           Structure: "Id_Location";"Adresse Postale";"Latitude";"Longitude";"Code secteur";"Type Location"
    # Paramètres de sortie: liste d'objets de type "Location" ou "None" si fichier vide
    #
    def loadGPSLocations(self, gps_locations_filename):
        try:
            gps_locations_file = open(gps_locations_filename, "r")
            gps_loc_count = len([gpsloc for gpsloc in gps_locations_file])
            gps_locations_file.seek(0)
            if gps_loc_count == 1:
                print("Fichier {} vide!".format(gps_locations_filename))
                gps_locations_file.close()
                return None
            else:
                gps_locations_file.seek(1)
                print("Chargement de {} position(s) GPS".format(gps_loc_count))
                gps_locations_object_list = []
                for line in gps_locations_file:
                    gps_location = line.split(";")
                    id_location = gps_location[0]
                    postal_address = gps_location[1]
                    latitude = gps_location[2]
                    longitude = gps_location[3]
                    sector_code = gps_location[4]
                    location_type = gps_location[5]
                    location_object = Location(id_location, postal_address, latitude, longitude, sector_code, location_type)
                    gps_locations_object_list.append(location_object)
                gps_locations_file.close()
                return gps_locations_object_list
        except IOError:
            print("Pas de fichier {} trouvé!".format(gps_locations_filename))
            return None
        except (ValueError, KeyError):
            print("Erreur inattendue lecture fichier {}: ValueError {}, KeyError {}".format(gps_locations_filename, ValueError, KeyError))
            return None



    #
    # Mise à jour des nouvelles localisations GPS dans le fichier "data\\locations_gps.txt"
    #           Structure: "Id_Location";"Adresse Postale";"Latitude";"Longitude";"Code secteur";"Type Location"
    #
    def updateGPSLocations(self):
        gps_locations_filename = os.path.join(self.chemin, self.gps_locations_filename)
        gps_locations_file = open(gps_locations_filename, "a")
        gps_locations_newcount = len(self.gps_locations_list)
        start_index = self.gps_locations_count
        end_index = gps_locations_newcount
        if start_index == end_index:
            print("Pas de nouvelles position GPS à écrire dans le fichier {}!".format(gps_locations_filename))
        else:
            output_txt = ""
            for gpsloc in self.gps_locations_list[start_index:end_index]:
                gps_location_csv = "{};{};{};{};{};{}".format(gpsloc.id, gpsloc.postal_address, gpsloc.latitude, gpsloc.longitude, gpsloc.sector_code, gpsloc.location_type)
                output_txt += "{}\n".format(gps_location_csv)
            print("Ecriture du fichier {} - {} nouvelles localisations GPS créées".format(gps_locations_filename, end_index-start_index))
            gps_locations_file.write(output_txt)
        gps_locations_file.close()


    #
    # Retourne un "id_location"
    #   Si ID de localisation pas déjà enregistré localement, on va créér une nouvel ID et interroger la base Mapbox pour créér un nouvel objet Location et le rajouter à la liste gps_locations_list de la classe courante
    # Entrée: Adresse postale
    # Sortie: "id_location" ou "None" si l'API Mapbox n'a pas localisé l'adresse
    #
    def getLocationId(self, postal_address, sector_code, location_type):
        gps_locations_filename = os.path.join(self.chemin, self.gps_locations_file)
        gps_locations_file = open(gps_locations_filename, "a")
        for gps_location_object in self.gps_locations_list:
            #print(gps_location_object.postal_address)
            pattern_pa = re.compile(gps_location_object.postal_address)
            if pattern_pa.match(postal_address):
                gps_locations_file.close()
                return gps_location_object.id
        result = gps_api.get_GPS_Coordinates_Mapbox(postal_address, self.api_key)
        if len(result) == 1:
            print("Erreur de géolocalisation! Service Mapbox (code erreur HTTP {})".format(result))
            return None
        else:
            id_location = len(self.gps_locations_list)
            longitude = result[0]
            latitude = result[1]
            # Création de l'objet en mémoire
            location_object = Location(id_location, postal_address, latitude, longitude, sector_code, location_type)
            self.gps_locations_list.append(location_object)
            # Ecriture de la nouvelle localisation sur disque (au cas où Mapbox se plante)
            gps_location_csv = "{};{};{};{};{};{}\n".format(location_object.id, location_object.postal_address, location_object.latitude, location_object.longitude, location_object.sector_code, location_object.location_type)
            print("Ecriture dans fichier {} - 1 nouvelle localisation GPS créée".format(gps_locations_filename, location_object))
            gps_locations_file.write(gps_location_csv)
            gps_locations_file.close()
            return id_location


    # méthode de création d'un objet de type "Course" à partir de données d'entrées
    def createCourse(self, id_course, course):
        course = conversion_accents(course)
        course = re.sub(regex_special_chars, ' ', course)
        #print(course)
        # template = "09H20 - (POTEZ JUSTINE (ADO)) Saint-Laurent-du-Var - 591 Avenue Jean Aicard - RESIDENCE ST MARC BAT 7 - 06 73 80 48 45  - 06 25 18 28 24 PERE DEST Nice 2 Rue Raynardi / CPJA <<EXO OUI BT SERIE SI HOMME PRENDS COURSE, NE PAS PARLER A JUSTINE"
        tab_1 = course.split("<<")
        #print(tab_1)
        # payment info -> EXO OUI BT SERIE SI HOMME PRENDS COURSE, NE PAS PARLER A JUSTINE"
        payment_info = tab_1[1].strip()
        #print("PROUT", payment_info)
        #payment_info = tab_1
        # tab_2 -> template = "09H20 - (POTEZ JUSTINE (ADO)) Saint-Laurent-du-Var - 591 Avenue Jean Aicard - RESIDENCE ST MARC BAT 7 - 06 73 80 48 45  - 06 25 18 28 24 PERE DEST Nice 2 Rue Raynardi / CPJA
        tab_2 = tab_1[0]
        tab_3 = tab_2.split(" DEST ")
        # Extraction adresse destination de la course
        # tab_4 -> template = "Nice 2 Rue Raynardi / CPJA "
        # tab_4 -> template = "S20 Nice  CYCLOTRON - CAL - 227 Avenue de la Lanterne "
        tab_4 = tab_3[1]
        tab_4_tmp = tab_4.split(" ")
        is_sector_code = True if re.match(regex_code_secteur, tab_4_tmp[0]) else False
        sector_code = tab_4_tmp[0].strip() if is_sector_code else ""
        to_city = tab_4_tmp[1] if is_sector_code else tab_4_tmp[0]
        to_street = " ".join(tab_4_tmp[2:len(tab_4_tmp)]).strip() if sector_code else " ".join(tab_4_tmp[1:len(tab_4_tmp)])
        to_street = to_street.split("/")[0].strip()
        to_postal_address = to_street.strip() + " " + to_city.strip()

        # Extraction informations client, heure et adresse de ramassage
        # tab_5 -> template = "09H20 - (POTEZ JUSTINE (ADO)) Saint-Laurent-du-Var - 591 Avenue Jean Aicard - RESIDENCE ST MARC BAT 7 - 06 73 80 48 45  - 06 25 18 28 24 PERE
        # tab_5 -> template = "09H15 - (ROBBE CLAUDE) NICE - 12 RUE DES PONCHETTES - MAISON EN FACE DE L ARCHE- PRES DU COURS SALEYA - 06 82 56 88 06 - 04 93 13 08 28  "
        # tab_5 -> template = "09H00 - (CARBONI EDMON - BASTIA) NICE -  NICE AEROPORT 2 - BASTIA - 06 45 27 30 75  DEST S22 NICE  HOPITAL ARCHET 1"
        tab_5 = tab_3[0]
        #tab_5 = re.sub('(.')
        tab_6 = tab_5.split(" - ")
        #print("Phone 1", tab_6)
        time = tab_6[0].strip()
        # Nom contact et ville
        # template = "(POTEZ JUSTINE (ADO)) Saint-Laurent-du-Var "
        # template = "(CARBONI EDMON - BASTIA) NICE"
        tab_field_2 = tab_6[1].strip()
        tab_field_2_tmp = tab_field_2.strip().split(" ")
        from_city = tab_field_2_tmp[-1]
        contact_name_tmp = " ".join(tab_field_2_tmp[0:len(tab_field_2_tmp) - 1])
        contact_name = contact_name_tmp[1:len(contact_name_tmp) - 1].strip()
        # Adresse et complément d'adresse
        from_street = tab_6[2]
        from_postal_address = from_street.strip() + " " + from_city.strip()
        # Numéros de tél de contact
        phone_list = []
        #print("Phone", tab_6)
        for field in tab_6:
            if re.match(regex_phone_number, field):
                phone_number = re.sub('[a-zA-Z]', '', field)
                phone_list.append(phone_number)
        first_phone_no = phone_list[0]
        second_phone_no = phone_list[1] if len(phone_list) == 2 else ""
        position_fin_adresse = len(tab_6) - len(phone_list)
        from_address_info = " - ".join(tab_6[3:position_fin_adresse])

        from_location_id = self.getLocationId(from_postal_address, sector_code, 'P')
        print(from_location_id)
        to_location_id = self.getLocationId(to_postal_address, sector_code, 'D')
        course_Object = Course(id_course, time, from_location_id, to_location_id, contact_name, first_phone_no, second_phone_no, payment_info)

        return course_Object


#########################################################################################################################################################################################################################################
#
#   Début du programme principal
#
#   Etapes:
#       1 - (Non utilisé dans l'algorithme) Chargement en mémoire du tableau d'objets Taxi (à partir du fichier "taxi_locations_file")
#       2 - Chargement en mémoire du tableau d'objets Locations connues (principalement les destinations) et adresses associées  (à partir du fichier "course_locations_file"). On ne stocke pas les adresses de ramassage des clients
#       3 - Reformatage des données d'entrée (fournies par les établissement de santé) et enregistrement dans un tableau d'objets structurés (dans l'éventualité d'un stockage dans une base de données): Courses et Locations
#       4 - Pour chaque feuille de route (course), on va calculer la distance et durée
#       5 - Algorithme pour les affectations des courses aux taxis disponible (on ne prend pas en compte le lieu de départ du taxi) mais seulement les enchaînements de course
#       6 - Ecriture du nouveau planning dans un fichier text "Planning.csv"
#       7 - Mise à jour des nouvelles destinations dans le fichier "data\\locations_gps.txt"
#
########################################################################################################################################################################################################################################

if __name__ == '__main__':
    #
    #   Paramètres globaux du programme
    #
    # ma clé d'API sur Mabox: https://account.mapbox.com/
    MAPBOX_API_KEY = "pk.eyJ1IjoicG1vdXJleSIsImEiOiJjazlmcW5lMmEwZTFyM2RxbXhwd3l6eDdpIn0.0AxxOZigM-4EeTORmNAndA"

    INSTANCE_PATH = "instance"
    # Create a directory in a known location to save files to.
    uploads_dir = os.path.join(INSTANCE_PATH, 'data')
    os.makedirs(uploads_dir, exist_ok=True)

    # Chemins d'accès aux fichiers sur le PC
    input_filename = os.path.join(uploads_dir, "Mail des resas.eml")
    output_filename = os.path.join(uploads_dir, "Planning.csv")
    gps_locations_filename = os.path.join(uploads_dir, "locations_gps.txt")
    taxis_filename = os.path.join(uploads_dir, "taxis.txt")
    #
    # Chargement des informations de courses dans notre base d'objets locaux
    #
    # Lecture du fichier d'entrée (EML) - fichier binaire de messagerie à décrypter et vérifier le type d'encodage de caractères
    if input_filename.endswith('.eml') == True:
        try:
            file = open(input_filename, "rb")
            msg = BytesParser(policy=policy.default).parse(file)
        except FileNotFoundError:
            print("Pas de fichier {} trouvé!".format(input_filename))
            exit(FileNotFoundError.errno)
        except (ValueError, KeyError):
            print("Erreur inattendue lecture fichier {}: ValueError {}, KeyError {}".format(input_filename, ValueError, KeyError))
            exit(FileNotFoundError.errno)
    else:
        print("Type de fichier \"{}\" incorrect, doit porter l'extension .eml".format(input_filename))
        print("Veuiller contacter l'administateur! :-)")
        exit(-1)


    # texte_courses = msg.get_body(preferencelist=("plain")).get_content() # version qui semble marcher aussi donc pas de nécessité d'utiliser les fonctions codées localement get_charset() et get_body()
    texte_courses = get_body(msg)
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
    print("Nombre courses: {}".format(nombre_courses))
    liste_Courses = []
    #
    # for course in courses_tab:
    #     print(course)

    # Création de l'objet DAO pour charger la structure de données en mémoire
    DAO_Toolbox = DAO_Toolbox(uploads_dir, MAPBOX_API_KEY, taxis_filename, gps_locations_filename, courses_tab)

    courses = DAO_Toolbox.courses_list
    gps_locations = DAO_Toolbox.gps_locations_list

    #
    #   Début de l'algorithme (pour l'instant rien du tout :-DD)
    #

    # Ecriture du fichier de sortie ( A implémenter )
    # DAO_Toolbox.createPlanning()
    output_txt = ""
    for course in courses_tab:
        course = conversion_accents(course)
        output_txt += "{}\n".format(re.sub(regex_special_chars, ' ', course))
    fichier = open(output_filename, "w")
    print("Ecriture du fichier {} - {} nouvelles courses créées".format(fichier.name, nombre_courses))
    fichier.write(output_txt)
    fichier.close()

    print("MON ADRESSE", DAO_Toolbox.getGPSLocation("1880 ROUTE DE SAINT JEANNET SAINT-LAURENT-DU-VAR"))

    # Enregistrement des nouvelles destinations (désactivé pour l'instant, la maj des nouvelles destinations se fait au début du traitement ligne par ligne dans le cas où l'API Mapbox retourne une erreur
    #DAO_Toolbox.updateGPSLocations()
