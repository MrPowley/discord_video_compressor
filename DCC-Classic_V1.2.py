import subprocess
from pymediainfo import MediaInfo
from datetime import datetime
from os import mkdir

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

def process(ffmpeg, input_file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, codec, gpu):
    ffmpeg_command = f'{ffmpeg} {gpu} -i "{input_file}" {audio_settings} -map 0:v -c:v {codec} -b:v {video_bitrate} -maxrate {video_bitrate} -minrate {video_bitrate} -vf "scale={resolution}:-1" -r {framerate} "{output_dir}/{output_file}"'
    subprocess.run(ffmpeg_command)

def get_video():
    file = input("Fichier: ")
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
        else:
            # FIXME Ramplacer la ligne dans le cas ou la vidéo est sans son
            tracks_bitrates.append(64000)
    max_bitrate = max(tracks_bitrates)

    return duration, audio_track_count, max_bitrate

def choose_quality(duration):
    if duration < 35:
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

def get_output():
    output_name = input("Nom du fichier final (laisser vide pour le nom par défaut): ")
    output_dir = input("Répertoire de sortie (laisser vide pour le répertoire par défaut): ")
    return output_name, output_dir

def main():
    try:
        output = subprocess.check_output('ffmpeg -h', text=True, stderr=subprocess.STDOUT)
        ffmpeg = "ffmpeg"
    except Exception:
        ffmpeg = "ffmpeg.exe"

    video = get_video()
    duration, audio_track_count, max_audio_bitrate = get_metadata(video)
    
    if audio_track_count == None and max_audio_bitrate == None:
        audio_settings = ""
    else:
        audio_settings = f'-filter_complex "[0:a]amerge=inputs={audio_track_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map "[aout]" -c:a mp3 -b:a 96k'

    resolution, framerate = choose_quality(duration)

    output_name, output_dir = get_output()
    
    if not output_dir:
        setup()
        output_dir = "output/"

    if output_name:
        output_file = output_name + ".mp4"
    else:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f'{now}_output.mp4'

    audio_bitrate = 96000
    audio_size = audio_bitrate * duration

    total_output_target_size = 25 * 1024 * 1024 * 8 * 0.97
    video_bitrate = int((total_output_target_size - audio_size) / duration)

    if nvidia():
        codec = "h264_nvenc"
        gpu = "-hwaccel cuda"
    elif amd():
        codec = "h264_amf"
        gpu = "-hwaccel cuda"
    else:
        codec = "h264 -preset veryfast"
        gpu = ""
    
    print(gpu)
    process(ffmpeg, video, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, codec, gpu)

def setup():
    try:
        mkdir("./output")
    except Exception:
        pass

if __name__ == "__main__":
    main()