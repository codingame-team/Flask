# coding: utf-8
import sys
import math
import email
# import urllib  as URLLIB, urllib3 , urllib_ext , urllib_parse_ParseResult_overloaded, urllib5
import os
import os.path
from urllib import request, parse
import json
#import requests
import re
from email import policy
from email.parser import BytesParser
# My modules
import geocoding_functions as geocoding_api
import directions_functions as direction_api
import text_functions as txt_func
from dotenv import load_dotenv
import datetime


#
# Created by philRG on 26/04/2020.
# Copyright © 2020 philRG. All rights reserved.
#

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
    def __init__(self, id, name, id_location, list_id_courses):
        self.id = id
        self.name = name
        self.id_location = id_location
        self.list_id_courses = list()
        self.liste_id_courses = list_id_courses # Liste des ids des courses

    def __str__(self):
        return "{} (id:{}), name:{}, id_location:{}, liste_id_courses:{}".format(self.__class__.__name__, self.id, self.name, self.id_location, self.liste_id_courses)

class Location(object):
    #   Constructeur de la classe Location
    #   Paramètres d'initialisation:
    #       - Id (géré par l'application)
    #       - Adresse postale (obligatoire)
    #       - Latitude (obligatoire?)
    #       - Longitude (obligatoire?)
    #       - Code secteur (facultatif)
    #       - Type d'emplacement (obligatoire) (adresse taxi, adresse de ramassage "pick-up" ou de destination): "T", "P", "D"
    def __init__(self, id, street, city, latitude, longitude, sector_code, location_type):
        self.id = id
        self.street = street
        self.city = city
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.sector_code = sector_code
        self.location_type = location_type
        #print(self)

    def __str__(self):
        return "{} (id:{}), postal_address:{} {}, latitude:{}, longitude:{}, sector_code:{}, location_type:{}".format(self.__class__.__name__, self.id, self.street, self.city, self.latitude, self.longitude, self.sector_code, self.location_type)

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
        self.taxi_no = -1 # Par défaut pas de taxi affecté
        #print(self)

    def calculateDuration(self):
        duration = "15"
        return duration

    def calculateDistance(self):
        duration = "15"
        return distance

    def __str__(self):
        return "{} id: {}, time: {}, from_location_id: {}, to_location_id: {}, contact_name: {}, first_phone_no: {}, second_phone_no: {}, payment_info: {}".format(
            self.__class__.__name__, self.id + 1, self.time, self.from_location_id, self.to_location_id, self.contact_name,
            self.first_phone_no, self.second_phone_no, self.payment_info)

# Classe d'accès aux données GPS (locales ou distantes)
class DAO_Toolbox(object):
    def __init__(self, chemin, api_key, taxis_filename, gps_locations_filename, courses_list):
        self.chemin = chemin
        self.api_key = api_key
        self.taxis_filename = taxis_filename
        self.gps_locations_filename = gps_locations_filename
        self.taxis_list = self.loadTaxis(taxis_filename)
        self.gps_locations_list = self.loadGPSLocations(gps_locations_filename)
        if self.gps_locations_list == None:
            self.gps_locations_list = []
        self.gps_locations_count = len(self.gps_locations_list) if self.gps_locations_list != None else 0
        #self.gps_locations_count = len(self.gps_locations_list)
        self.courses_list = self.loadCourses(courses_list)
        #print(self.gps_locations_list)

    #
    # Création du planning de courses pour les taxis
    # Entrée: La liste structurées des courses (liste d'objets de type "Course") et la liste des taxis (liste d'objets de type "Taxi"
    # Sortie: planning des courses et affactation aux taxis
    #
    def calculatePlanning(self, courses_object_list, taxi_object_list):
        time_interval = datetime.timedelta(hours=0, minutes=30) # par défaut, on suppose un délai de 30' entre 2 courses
        time_km_vol_oiseau = datetime.timedelta(hours=0, minutes=3, seconds=30)
        #
        # Algorithme de sélection de la première course
        #   - Affectation aux taxis de la liste une 1ère course
        #   - Mise à jour de la nouvelle localisation et heure d'arrivée du taxi après avoir déposé le client à sa destination
        #
        for i in range(len(taxi_object_list)):
            courses_object_list[i].taxi_no = i
            taxi_object_list[i].id_location = courses_object_list[i].to_location_id
            time_pickup_course = datetime.datetime.strptime(courses_object_list[i].time, "%Hh%M")
            taxi_object_list[i].available_time = time_pickup_course + time_interval
        # Affectation de la 2ème course
        # Création de la nouvelle liste de candidats
        new_courses_list = [course for course in courses_object_list if courses_object_list[i].taxi_no == -1]
        print("new_courses_list", new_courses_list, file=sys.stderr)
        #
        # Algorithme de sélection de la deuxième course
        #   - Pour chaque course restante:
        #       - Déterminer la liste de taxis disponibles susceptibles de prendre les courses restantes
        #       - Pour chaque taxi de cette liste:
        #           - Calculer la distance à parcourir jusqu'au client
        #           - Calculer le temps d'attente arrivé à destination
        #   - Pour chaque taxi identifié, il va choisir le temps d'attente le moins éloigné
        #
        for course in new_courses_list:
            course.liste_available_taxis = []
            heure_depart_course = datetime.datetime.strptime(course.time, "%Hh%M")
            pickup_location = self.gps_locations_list[course.from_location_id]  # Localisation du client à aller chercher
            for taxi_id in len(taxi_object_list):
                taxi_location = self.gps_locations_list[taxi_object_list[taxi_id].id_location]  # Localisation du taxi après la première course
                distance_vol_oiseau = direction_api.calculateDistanceVolOiseau(taxi_location, pickup_location) / 1000 # distance du taxi à parcourir (à vol d'oiseau)
                # geojson_object_prop = direction_api.get_Directions_Mapbox(from_location, to_location, MAPBOX_API_KEY)
                # distance = geojson_object_prop['distance']
                # duration = geojson_object_prop['duration']
                heure_estimee_arrivee_taxi = taxi_object_list[i].available_time +  time_km_vol_oiseau * distance_vol_oiseau
                if heure_estimee_arrivee_taxi < heure_depart_course:
                    temps_attente = heure_depart_course - heure_estimee_arrivee_taxi
                    course.liste_available_taxis.append((taxi_id, distance_vol_oiseau, temps_attente))
            course.temps_attente_moyen = avg([taxi[1] for taxi in course.liste_available_taxis])
            course.distance_taxi_moyenne = avg([taxi[0] for taxi in course.liste_available_taxis])
            print("attente moy: {}, distance moy: {} -> {}".format(course.temps_attente_moyen, course.distance_taxi_moyenne, course), file=sys.stderr)

        # for course in new_courses_list:
        #     taxi_found = False
        #         for taxi_id, distance_vol_oiseau, temps_attente in course.liste_available_taxis:
        #             if not taxi_found:
        #                 if temps_attente < course.temps_attente_moyen and distance_vol_oiseau < course.distance_taxi_moyenne:
        #                     taxi_found = True

                # On prend le taxi le plus proche de la liste et qui soit à moins de 10'
        #
        return True

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
    # Entrée: nom de fichier ("data\\taxis.csv")
    #           Structure: "Id taxi";"Nom";"Id_Location";"Liste Id courses" (exemple: 0;15;2,7,8)
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
                    list_id_courses = [course for course in taxi[3].split(',')] if taxi[3] != '' else None
                    taxi_object = Taxi(id_taxi, nom, id_location, list_id_courses)
                    if re.match(r'\d', id_taxi):
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
            gps_loc_count = len([gpsloc for gpsloc in gps_locations_file])-1
            if gps_loc_count == 0:
                print("Fichier {} vide!".format(gps_locations_filename))
                gps_locations_file.close()
                return None
            else:
                print("Chargement de {} position(s) GPS".format(gps_loc_count))
                gps_locations_object_list = []
                gps_locations_file.seek(0)
                for line in gps_locations_file:
                    gps_location = line.split(";")
                    id_location = gps_location[0]
                    street = gps_location[1]
                    city = gps_location[2]
                    latitude = gps_location[3]
                    longitude = gps_location[4]
                    sector_code = gps_location[5]
                    location_type = gps_location[6]
                    if re.match(r'\d', id_location):
                        location_object = Location(id_location, street, city, latitude, longitude, sector_code, location_type)
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
                gps_location_csv = "{};{};{};{};{};{};{}".format(gpsloc.id, gpsloc.street, gpsloc.city, gpsloc.latitude, gpsloc.longitude, gpsloc.sector_code, gpsloc.location_type)
                output_txt += "\n{}".format(gps_location_csv)
            print("Ecriture du fichier {} - {} nouvelles localisations GPS créées".format(gps_locations_filename, end_index-start_index))
            gps_locations_file.write(output_txt)
        gps_locations_file.close()


    #
    # Retourne un "id_location"
    #   Si ID de localisation pas déjà enregistré localement, on va créér une nouvel ID et interroger la base Mapbox pour créér un nouvel objet Location et le rajouter à la liste gps_locations_list de la classe courante
    # Entrée: Adresse postale
    # Sortie: "id_location" ou "None" si l'API Mapbox n'a pas localisé l'adresse
    #
    def getLocationId(self, street, city, sector_code, location_type):
        gps_locations_file = open(gps_locations_filename, "a")
        if len(self.gps_locations_list) > 0:
            #print(self.gps_locations_list, file=sys.stderr)
            for gps_location_object in self.gps_locations_list:
                #print(gps_location_object.postal_address)
                pattern_street = re.compile(gps_location_object.street, re.I)
                pattern_city = re.compile(gps_location_object.city, re.I)
                #print(gps_location_object)
                if pattern_street.match(street) and pattern_city.match(city):
                    gps_locations_file.close()
                    return gps_location_object.id
        result = geocoding_api.get_GPS_Coordinates_Mapbox(street, city, self.api_key)
        if len(result) == 1:
            print("Erreur de géolocalisation! Service Mapbox (code erreur HTTP {})".format(result))
            return None
        else:
            #id_location = len(self.gps_locations_list) if self.gps_locations_list != None else 0
            id_location = len(self.gps_locations_list)
            longitude = result[0]
            latitude = result[1]
            # Création de l'objet en mémoire
            location_object = Location(id_location, street, city, latitude, longitude, sector_code, location_type)
            self.gps_locations_list.append(location_object)
            # Ecriture de la nouvelle localisation sur disque (au cas où Mapbox se plante)
            gps_location_csv = "\n{};{};{};{};{};{};{}".format(location_object.id, location_object.street, location_object.city, location_object.latitude, location_object.longitude, location_object.sector_code, location_object.location_type)
            print("Ecriture dans fichier {} - 1 nouvelle localisation GPS créée".format(gps_locations_filename, location_object))
            gps_locations_file.write(gps_location_csv)
            gps_locations_file.close()
            return id_location


    # méthode de création d'un objet de type "Course" à partir de données d'entrées
    def createCourse(self, id_course, course):
        pattern = r'(\(.*\))\s*'
        tab = re.split(pattern, course)
        # Supression du délimiteur - dans le champ (NOM PRENOM)
        tab[1] = tab[1].replace("-", "")
        course = " ".join(tab)
        course = txt_func.conversion_accents(course)
        course = re.sub(regex_special_chars, ' ', course)
        #print(course, file=sys.stderr)
        # template = "09H20 - (MARTIN JUSTINE (ADO)) Saint-Laurent-du-Var - 14 Avenue Jean Mermoz - RESIDENCE ST FIACRE BAT 7 - 06 00 00 00 00  - 06 00 00 00 01 PERE DEST Nice 20 Rue Vivien / CPJA <<EXO OUI BT SERIE SI HOMME PRENDS COURSE, NE PAS PARLER A JUSTINE"
        tab_1 = course.split("<<")
        # payment info -> EXO OUI BT SERIE SI HOMME PRENDS COURSE, NE PAS PARLER A JUSTINE"
        payment_info = tab_1[1].strip()
        # tab_2 -> template = "09H20 - (MARTIN JUSTINE (ADO)) Saint-Laurent-du-Var - 14 Avenue Jean Mermoz - RESIDENCE ST FIACRE BAT 7 - 06 00 00 00 00  - 06 00 00 00 01 PERE DEST Nice 20 Rue Vivien / CPJA
        tab_2 = tab_1[0]
        tab_3 = tab_2.split(" DEST ")
        # Extraction adresse destination de la course
        # tab_4 -> template = "Nice 2 Rue Raynardi / CPJA "
        # tab_4 -> template = "S20 Nice  CYCLOTRON - CAL - 214 Avenue de la Pioche "
        tab_4 = tab_3[1]
        tab_4_tmp = tab_4.split(" ")
        is_sector_code = True if re.match(regex_code_secteur, tab_4_tmp[0]) else False
        sector_code = tab_4_tmp[0].strip() if is_sector_code else ""
        to_city = tab_4_tmp[1] if is_sector_code else tab_4_tmp[0]
        to_street = " ".join(tab_4_tmp[2:len(tab_4_tmp)]).strip() if sector_code else " ".join(tab_4_tmp[1:len(tab_4_tmp)])
        to_street = to_street.split("/")[0].strip()
        pattern = r'(\(.*\))\s*'
        to_street = re.sub(pattern, '', to_street)
        #to_postal_address = to_street.strip() + " " + to_city.strip()
        # Extraction informations client, heure et adresse de ramassage
        # tab_5 -> template = "09H20 - (MARTIN JUSTINE (ADO)) Saint-Laurent-du-Var - 14 Avenue Jean Mermoz - RESIDENCE ST FIACRE BAT 7 - 06 00 00 00 00  - 06 00 00 00 01 PERE
        # tab_5 -> template = "09H15 - (ROBERT CLAUDE) NICE - 145 RUE DES MIMOSAS - MAISON EN FACE DE L ARCHE- PRES DU COURS MAXIME - 06 00 00 00 00 - 06 00 00 00 01  "
        # tab_5 -> template = "09H00 - (DUPONT SEBASTIEN - BASTIA) NICE -  NICE AEROPORT 2 - BASTIA - 06 00 00 00 00  DEST S22 NICE  HOPITAL ARCHET 1"
        tab_5 = tab_3[0]
        tab_6 = tab_5.split(" - ")
        time = tab_6[0].strip()
        # Nom contact et ville
        # template = "(MARTIN JUSTINE (ADO)) Saint-Laurent-du-Var"
        # template = "(DUPONT SEBASTIEN - BASTIA) NICE"
        tab_field_2 = tab_6[1].strip()
        tab_field_2_tmp = tab_field_2.strip().split(" ")
        from_city = tab_field_2_tmp[-1]
        contact_name_tmp = " ".join(tab_field_2_tmp[0:len(tab_field_2_tmp) - 1])
        contact_name = contact_name_tmp[1:len(contact_name_tmp) - 1].strip()
        # Adresse et complément d'adresse
        from_street = tab_6[2]
        #from_postal_address = from_street.strip() + " " + from_city.strip()
        # Numéros de tél de contact
        phone_list = []
        for field in tab_6:
            if re.match(regex_phone_number, field):
                phone_number = re.sub('[a-zA-Z]', '', field)
                phone_list.append(phone_number)
        first_phone_no = phone_list[0]
        second_phone_no = phone_list[1] if len(phone_list) == 2 else ""
        position_fin_adresse = len(tab_6) - len(phone_list)
        from_address_info = " - ".join(tab_6[3:position_fin_adresse])

        # pattern = r'(\(.*\))\s*'
        # tab = re.split(pattern, from_street)
        # tab[1] = tab[1].replace("-", " ")
        # from_street = " ".join(tab)
        # tab = re.split(pattern, to_street)
        # tab[1] = tab[1].replace("-", " ")
        # to_street = " ".join(tab)

        from_street = re.sub(regex_special_chars_sup, ' ', from_street).strip()
        to_street = re.sub(regex_special_chars_sup, ' ', to_street).strip()

        from_street = re.sub(r'\s{2,}', ' ', from_street)
        to_street = re.sub(r'\s{2,}', ' ', to_street)

        from_location_id = self.getLocationId(from_street, from_city, sector_code, 'P')
        to_location_id = self.getLocationId(to_street, to_city, sector_code, 'D')
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
#       6 - Ecriture du nouveau planning dans un fichier text "Planning.txt"
#       7 - Mise à jour des nouvelles destinations dans le fichier "data\\locations_gps.csv"
#
########################################################################################################################################################################################################################################

if __name__ == '__main__':
    #
    #   Paramètres globaux du programme
    #

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
    input_filename = os.path.join(uploads_dir, "Mail des resas.eml")
    output_filename = os.path.join(uploads_dir, "Planning.txt")
    gps_locations_filename = os.path.join(uploads_dir, "locations_gps.csv")
    taxis_filename = os.path.join(uploads_dir, "taxis.csv")
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
    print("Nombre courses: {}".format(nombre_courses))
    liste_Courses = []
    #
    # for course in courses_tab:
    #     print(course)

    # Création de l'objet DAO pour charger la structure de données en mémoire
    DAO_Toolbox = DAO_Toolbox(uploads_dir, MAPBOX_API_KEY, taxis_filename, gps_locations_filename, courses_tab)

    taxis_object_list = DAO_Toolbox.taxis_list
    courses_object_list = DAO_Toolbox.courses_list
    gps_locations_object_list = DAO_Toolbox.gps_locations_list

    #
    #   Début de l'algorithme (pour l'instant rien du tout :-DD)
    #

    # Ecriture du fichier de sortie ( A implémenter )
    # DAO_Toolbox.createPlanning()
    output_txt = ""
    for course in courses_tab:
        i = courses_tab.index(course)
        course = txt_func.conversion_accents(course).strip()
        course = re.sub(regex_special_chars, ' ', course)
        course_object = courses_object_list[i]
        from_location = gps_locations_object_list[int(course_object.from_location_id)]
        to_location = gps_locations_object_list[int(course_object.to_location_id)]
        distance_vol_oiseau = direction_api.calculateDistanceVolOiseau(from_location, to_location)
        geojson_object_prop = direction_api.get_Directions_Mapbox(from_location, to_location, MAPBOX_API_KEY)
        course_object.distance = geojson_object_prop['distance']
        course_object.duration = geojson_object_prop['duration']
        elapsed_hours = course_object.duration / 3600
        elapsed_minutes = (elapsed_hours - int(elapsed_hours)) * 60
        output_txt += "Course #{} - {:0.1f} km - {} km - {}h{}mn - {}\n".format(i+1, distance_vol_oiseau, round(course_object.distance/1000, 1), int(elapsed_hours), round(elapsed_minutes), course)
    planning_txt = DAO_Toolbox.calculatePlanning(courses_object_list, taxis_object_list)
    fichier = open(output_filename, "w")
    print("Ecriture du fichier {} - {} nouvelles courses créées".format(fichier.name, nombre_courses))
    fichier.write(output_txt)
    #fichier.write(planning_txt)
    fichier.close()

    # Enregistrement des nouvelles destinations (désactivé pour l'instant, la maj des nouvelles destinations se fait au début du traitement ligne par ligne dans le cas où l'API Mapbox retourne une erreur
    #DAO_Toolbox.updateGPSLocations()
