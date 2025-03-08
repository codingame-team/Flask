import os
import sys
from pathlib import Path


def resource_path(relative_path):
    """ Get the absolute path to a resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        # Running as bundled executable
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Running in development environment
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Navigate up to the project root (assuming this file is in a subdirectory)
        project_root = os.path.dirname(current_dir)

        # Join the project root with the relative path
        return os.path.join(project_root, relative_path)

# nicola: Dans Linusque, tu peux utiliser f'{Path.home()}/.config/{folder_name}'.
def get_strava_path(folder_name="Strava"):
    """
    Retourne le chemin d'un dossier pour sauvegarder les jeux en cours en fonction du système d'exploitation.

    :param folder_name: Nom du sous-dossier pour les sauvegardes (optionnel).
    :return: Chemin absolu du dossier de sauvegarde.
    """
    # Récupère le dossier utilisateur en fonction du système d'exploitation
    if os.name == 'nt':  # Système Windows
        save_path = f'{Path.home()}/Documents/{folder_name}'
    elif os.name == 'posix':  # Systèmes Unix-like (Linux, macOS)
        save_path = f'{Path.home()}/{folder_name}'
    else:
        raise OSError("Système d'exploitation non supporté")

    return save_path