# [FR] Compresseur vidéo discord


Ce programme en python sert a compresser des vidéos/clips pour qu'il fassent moins de 25Mo pour pouvoir les envoyer sur discord

Il utilise les librairies suivantes:

- **subprocess**
- **pymediainfo**
- **datetime**
- **os**

Vous avez besoin d'avoir ffmpeg d'installé, ou l'executable de ffmpeg.exe à la racine du programme

## Version Classique
Interface CMD, en français, avec choix de la qualité, nom et dossier de sortie

## Version CLI
Arguments et syntaxe:
- `-q --quality` : Qualité de la vidéo entre 1 et 3 (Définit la résolution de sortie : 720p, 900p, 1080p)
- `-f --fluid` : Séléctionne 60fps
- `-on --output-name` : Permet de définir un nom de sortie pour la vidéo
- `-od --output-dir` : Permet de choisir un répertoire de sortie
- `-y` : Ré-écrit le fichier de sortie s'il existe déjà

# [EN] Discord video compressor

This python program is used to compress videos/clips to make them under 25Mb to be sent on discord


It uses the following libraries:

- **subprocess**
- **os**
- **datetime**
- **os**

You need to have ffmpeg installed, or the ffmpeg.exe executable in the program's root directory

## Classic Version
CMD interface, in French, with choice of quality, output name and directory

## CLI Version
Arguments and syntax:
- `-q --quality` : Video quality betwin 1 and 3 (Sets the output resolution : 720p, 900p, 1080p)
- `-f --fluid` : Selects 60fps
- `-on --output-name` : Allows you to set an output name
- `-od --output-dir` : Allows you to set an output director
- `-y` : Overwrites output file if it allready exists