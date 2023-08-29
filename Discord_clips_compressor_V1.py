import subprocess
import os
import datetime
from threading import Thread


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
    
def get_video_duration(input_file_path):
    command = [
        'ffprobe.exe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_file_path
    ]
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        duration = float(output)
        return duration
    except subprocess.CalledProcessError as e:
        print("Error:", e.output)
        return None

def get_audio_track_count(video_path):
    command = [
        'ffprobe.exe',
        '-v', 'error',
        '-select_streams', 'a',
        '-show_entries', 'stream=codec_type',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)
        audio_count = output.count('audio')
        return audio_count
    except subprocess.CalledProcessError as e:
        print("Error:", e.output)
        return None

def get_file_size(input_file_path):
    size = os.path.getsize(input_file_path)
    return size

def nvidia_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count):
    ffmpeg_command = f'ffmpeg.exe -hwaccel cuda -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale=1280:-1" -c:v h264_nvenc -b:v {video_bitrate} -maxrate {video_bitrate} -c:a mp3 -b:a {audio_bitrate} -r 30 "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def amd_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count):
    ffmpeg_command = f'ffmpeg.exe -hwaccel cuda -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale=1280:-1" -c:v h264_amf -b:v {video_bitrate} -maxrate {video_bitrate} -c:a mp3 -b:a {audio_bitrate} -r 30 "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def cpu_process(output_file, video_bitrate, audio_bitrate, input_file_path, audio_count):
    ffmpeg_command = f'ffmpeg.exe -i "{input_file_path}" -filter_complex "[0:a]amerge=inputs={audio_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map 0:v -map "[aout]" -vf "scale=1280:-1" -c:v h264 -b:v {video_bitrate} -maxrate {video_bitrate} -preset veryfast -c:a mp3 -b:a {audio_bitrate} -r 30 "output/{output_file}" -y'
    subprocess.run(ffmpeg_command)

def process(input_file):
    duration = get_video_duration(input_file)
    end_audio_bitrate = 95261
    audio_bitrate = 92000
    audio_size = end_audio_bitrate * duration
    target_size = 25 * 1024 * 1024 * 8
    video_bitrate = int((target_size - audio_size) / duration / 1.07)

    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f'{now}_output.mp4'

    audio_count = get_audio_track_count(input_file)
    os.mkdir("./output")

    if nvidia():
        Tnvidia = Thread(target=nvidia_process, args=(output_file, video_bitrate, audio_bitrate, input_file, audio_count))
        Tnvidia.start()
    elif amd():
        Tamd = Thread(target=amd_process, args=(output_file, video_bitrate, audio_bitrate, input_file, audio_count))
        Tamd.start()
    else:
        Tcpu = Thread(target=cpu_process, args=(output_file, video_bitrate, audio_bitrate, input_file, audio_count))
        Tcpu.start()

file = input("Fichier: ")
file = file.replace("\\", "/")
file = file.replace('"', '')
file = file.replace("'", "")

process(file)