import subprocess
from pymediainfo import MediaInfo


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

def gpu():
    if amd() or nvidia():
        return True
    else:
        return False


def nvidia_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count, resolution, framerate, ffmpeg):
    ffmpeg_command = f'{ffmpeg} -hwaccel cuda -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale={resolution}:-1" -c:v h264_nvenc -b:v {video_bitrate} -maxrate {video_bitrate} -c:a mp3 -b:a {audio_bitrate} -r {framerate} "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def amd_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count, resolution, framerate, ffmpeg):
    ffmpeg_command = f'{ffmpeg} -hwaccel cuda -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale={resolution}:-1" -c:v h264_amf -b:v {video_bitrate} -maxrate {video_bitrate} -c:a mp3 -b:a {audio_bitrate} -r {framerate} "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def cpu_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count, resolution, framerate, ffmpeg):
    ffmpeg_command = f'{ffmpeg} -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale={resolution}:-1" -c:v h264 -b:v {video_bitrate} -maxrate {video_bitrate} -preset veryfast -c:a mp3 -b:a {audio_bitrate} -r {framerate} "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def process(input_file, output_file, video_bitrate, audio_bitrate, audio_count, resolution, framerate):
    
    try:
        subprocess.check_output("ffmpeg -h")
        ffmpeg = "ffmpeg"
    except Exception:
        ffmpeg = "ffmpeg.exe"
    
    if nvidia():
        nvidia_process(output_file, video_bitrate, audio_bitrate, input_file, audio_count, resolution, framerate, ffmpeg)
    elif amd():
        amd_process(output_file, video_bitrate, audio_bitrate, input_file, audio_count, resolution, framerate, ffmpeg)
    else:
        cpu_process(output_file, video_bitrate, audio_bitrate, input_file, audio_count, resolution, framerate, ffmpeg)

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

def main():
    video = get_video()
    duration, audio_track_count, max_audio_bitrate = get_metadata(video)
    
    resolution, framerate = choose_quality(duration)

    # Theoretical audio bitrate
    t_audio_bitrate = 92000
    # Mesured output bitrate
    e_audio_bitrate = 95261

    audio_size = e_audio_bitrate * duration

    total_output_target_size = 25 * 1024 * 1024 * 8 * 0.95
    video_bitrate = int((total_output_target_size - audio_size) / duration)

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f'{now}_output.mp4'

    process(video, output_file, video_bitrate, max_audio_bitrate, audio_track_count, resolution, framerate)

def setup():
    from os import mkdir
    try:
        mkdir("./output")
    except Exception:
        pass



if __name__ == "__main__":
    setup()
    main()