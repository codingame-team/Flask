# Flask
Projet pour porter sur le web mes scripts Python. Comme ils sont développés en couches, cela rend la tâche plus facile. 
Avec les framework web, il faut y aller progressivement, et commencer simplement.

Un bon tutoriel ultra-simpliste (mais pas superflu) pour se familiariser à l'environnement: https://www.kaherecode.com/tutorial/demarrer-avec-flask-un-micro-framework-python

Cela suppose de connaître quelques bases sur l'HTML/CSS, le protocole HTTP et les CGI, ainsi que quelques bases sur le fonctionnement des moteurs de template HTML (Jinja dans ce cas pour Flask).

N.B.: ce projet n'inclut pas de base de données (pour lequel on pourrait utiliser SQL Alchemy comme ORM), mais utilise quelques fonctionalités intéressantes (la transmission de fichiers sécurisée ainsi que l'utilisation de la Debug Toolbar)

Un outil en ligne pour construire et vérifier ses feuilles CSS (on pourra s'inspirer de modèles CSS glanés sur le web), rien de pire qu'un IDE avec des centaines de menus et d'options pour décourager: https://codepen.io/
Un bon système de template permet notamment de ne plus avoir à se préoccuper du front-end mais seulement du back-end. Le système des routes rendant de plus la navigation entre pages très facile à maintenir.

L'intérêt pédagogique de ce projet est multiple:
- Il réutilise des fonctions communes utilisées dans la version initiale du programme exécuté en ligne de commande en utilisant les propriétés intrinsèques du langages python (organisation des codes en modules, et définition du programme principal par la fonction __main__)
- Il montre les différentes couches utilisées (Front-End et Back-End) et met en valeur les caractéristiques de chacun de ces métiers.
- Il permet aussi d'intégrer des algorithmes de calcul et de s'y concentrer de manière indépendante sans avoir à s'occuper des autres couches.
