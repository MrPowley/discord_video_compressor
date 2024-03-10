import subprocess
from pymediainfo import MediaInfo
from datetime import datetime
from os import mkdir, listdir
from os.path import isdir
import re
from tqdm import tqdm


def nvidia():
    try:
        subprocess.check_output('nvidia-smi')
        return True
    except Exception:
        return False

def amd():
    try:
        subprocess.check_output(["clinfo"], stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

def ffmpeg_process(ffmpeg, input_file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, codec, gpu, duration):
    ffmpeg_command = f'{ffmpeg} {gpu} -i "{input_file}" {audio_settings} -map 0:v -c:v {codec} -b:v {video_bitrate} -maxrate {video_bitrate} -minrate {video_bitrate} -vf "scale={resolution}:-1" -r {framerate} "{output_dir}/{output_file}"'

    with tqdm(total=100, desc=f'Processing ', unit='%', position=0, leave=True) as pbar:
        try:
            process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
            for line in process.stdout:
                if line.startswith("frame"):
                    time_match = re.search(r'time=(\d+:\d+:\d+\.\d+)', line)
                    time_value = time_match.group(1)

                    time_object = datetime.strptime(time_value, "%H:%M:%S.%f")
        
                    seconds = time_object.second + time_object.minute * 60 + time_object.hour * 3600 + time_object.microsecond / 1e6

                    completion = seconds/duration*100
                    add = round(completion - pbar.n)

                    if completion >= 100:
                        pbar.update(100-completion)
                    else:
                        pbar.update(add)
        except subprocess.CalledProcessError as e:
            # En cas d'erreur, affiche le message d'erreur
            print(f"Error processing: {e.output.decode()}")

def get_video():
    file = input("Fichier ou dossier: ")
    file = file.replace("\\", "/")
    file = file.replace('"', '')
    file = file.replace("'", "")
    return file

def get_metadata(file):
    metadata = MediaInfo.parse(file)
    duration = metadata.tracks[0].duration / 1000
    audio_track_count = 0
    tracks_bitrates = []
    for track in metadata.tracks:
        if track.track_type == "Audio":
            audio_track_count += 1
            try:
                track_bitrate = track.to_data()["bit_rate"]
                tracks_bitrates.append(track_bitrate)
            except KeyError:
                tracks_bitrates.append(92000)
    if audio_track_count == 0:
        return duration, None, None
    max_bitrate = max(tracks_bitrates)

    return duration, audio_track_count, max_bitrate

def choose_quality(duration):
    if duration == -1:
        quality = int(input("""Liste de vidéos
1 - Meilleure Qualité, résolution basse
2 - Très bonne qualité, résolution basse, fluide
3 - Très bonne qualité, résolution moyenne
4 - Bonne qualité, résolution moyenne, fluide
5 - Bonne qualité, haute résolution
6 - Moyenne qualité, haute résolution, fluide\n"""))
        match quality:
            case 1:
                return 1280, 30
            case 2:
                return 1280, 60
            case 3:
                return 1600, 30
            case 4:
                return 1600, 60
            case 5:
                return 1920, 30
            case 6:
                return 1920, 60
            
    elif duration < 35:
        quality = int(input("""Vidéo de moins de 30sec
1 - Qualité parfaite, résolution moyenne
2 - Qualité très bonne, résolution moyenne, fluide
3 - Qualité très bonne, haute résolution
4 - Qualité bonne, haute résolution, fluide\n"""))
        match quality:
            case 1:
                return 1600, 30
            case 2:
                return 1600, 60
            case 3:
                return 1920, 30
            case 4:
                return 1920, 60
    elif duration < 65:
        quality = int(input("""Vidéo de moins de 1min
1 - Qualité parfaite, résolution basse
2 - Qualité très bonne, résolution basse, fluide
3 - Qualité très bonne, résolution moyenne
4 - Qualité bonne, résolution moyenne, fluide
5 - Qualité bonne, haute résolution
6 - Qualité moyenne, haut résolution, fluide\n"""))
        match quality:
            case 1:
                return 1280, 30
            case 2:
                return 1280, 60
            case 3:
                return 1600, 30
            case 4:
                return 1600, 60
            case 5:
                return 1920, 30
            case 6:
                return 1920, 60
    elif duration < 125:
        quality = int(input("""Vidéo de moins de 2min
1 - Qualité bonne, résolution basse
2 - Qualité moyenne, résolution basse, fluide
3 - Qualité moyenne, résolution moyenne
4 - Qualité mauvaise, résolution moyenne, fluide
5 - Qualité mauvaise, haute résolution
6 - Qualité très mauvaise, haute résolution, fluide\n"""))
        match quality:
            case 1:
                return 1280, 30
            case 2:
                return 1280, 60
            case 3:
                return 1600, 30
            case 4:
                return 1600, 60
            case 5:
                return 1920, 30
            case 6:
                return 1920, 60
    else:
        quality = int(input("""Vidéo de plus de 2min
1 - Qualité moyenne, résolution basse
2 - Qualité mauvaise, résolution basse, fluide
3 - Qualité mauvaise, résolution moyenne
4 - Qualité très mauvaise, résolution moyenne, fluide
5 - Qualité très mauvaise, haute résolution
6 - Qualité exécrable, haute résolution, fluide\n"""))
        match quality:
            case 1:
                return 1280, 30
            case 2:
                return 1280, 60
            case 3:
                return 1600, 30
            case 4:
                return 1600, 60
            case 5:
                return 1920, 30
            case 6:
                return 1920, 60

def get_output(is_dir):
    if is_dir:
        output_dir = input("Répertoire de sortie (laisser vide pour le répertoire par défaut): ")
        return None, output_dir
    else:
        output_name = input("Nom du fichier final (laisser vide pour le nom par défaut): ")
        output_dir = input("Répertoire de sortie (laisser vide pour le répertoire par défaut): ")
        return output_name, output_dir

def process(file, resolution, framerate, output_file, output_dir, is_dir):
    duration, audio_track_count, max_audio_bitrate = get_metadata(file)
    if audio_track_count == None and max_audio_bitrate == None:
        audio_settings = ""
    else:
        audio_settings = f'-filter_complex "[0:a]amerge=inputs={audio_track_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map "[aout]" -c:a mp3 -b:a 96k'
    
    # Audio bitrate set to 96kb/s
    audio_size = 96000 * duration
    video_bitrate = int((config["target_size"] - audio_size) / duration)

    if not is_dir:
        resolution, framerate = choose_quality(duration)

    ffmpeg_process(config["ffmpeg"], file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, config["codec"], config["gpu"], duration)

def main(config):
    path = get_video()
    
    if isdir(path):
        is_dir = True
        resolution, framerate = choose_quality(-1)
        output_name, output_dir = get_output(is_dir)

        if not output_dir:
            setup()
            output_dir = "output/"

        
        for file in listdir(path):
            if file.endswith(config["extensions"]):
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                output_file = f'{now}_output.mp4'
                file = path + "/" + file
                process(file, resolution, framerate, output_file, output_dir, is_dir)
    else:
        is_dir = False
        output_name, output_dir = get_output(is_dir)

        if not output_dir:
            setup()
            output_dir = "output/"
        
        if output_name:
            output_file = output_name + ".mp4"
        else:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_file = f'{now}_output.mp4'

        process(path, None, None, output_file, output_dir, is_dir)

def setup():
    try:
        mkdir("./output")
    except Exception:
        pass

def get_config():
    config = {}
    try:
        output = subprocess.check_output('ffmpeg -h', text=True, stderr=subprocess.STDOUT)
        config["ffmpeg"] = "ffmpeg"
    except Exception:
        config["ffmpeg"] = "ffmpeg.exe"

    if nvidia():
        config["codec"] = "h264_nvenc"
        config["gpu"] = "-hwaccel cuda"
    elif amd():
        config["codec"] = "h264_amf"
        config["gpu"] = "-hwaccel cuda"
    else:
        config["codec"] = "h264 -preset veryfast"
        config["gpu"] = ""
    
    config["target_size"] = 25 * 1024 * 1024 * 8 * 0.97

    config["extensions"] = video_extensions = (".mp4", ".mkv", ".mov")

    return config
    

if __name__ == "__main__":
    config = get_config()
    main(config)