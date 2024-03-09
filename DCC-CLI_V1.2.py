import subprocess
from pymediainfo import MediaInfo
from datetime import datetime
from argparse import ArgumentParser, Namespace
from os import mkdir, listdir
from os.path import isdir

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

def ffmpeg_process(ffmpeg, input_file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, codec, gpu):
    ffmpeg_command = f'{ffmpeg} {gpu} -i "{input_file}" {audio_settings} -map 0:v -c:v {codec} -b:v {video_bitrate} -maxrate {video_bitrate} -minrate {video_bitrate} -vf "scale={resolution}:-1" -r {framerate} "{output_dir}/{output_file}"'
    subprocess.run(ffmpeg_command)

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

def set_audio_settings(audio_track_count, max_audio_bitrate):
    if audio_track_count == None and max_audio_bitrate == None:
        return ""
    else:
        return f'-filter_complex "[0:a]amerge=inputs={audio_track_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map "[aout]" -c:a mp3 -b:a 96k'

def process(config, file, resolution, framerate, output_file, output_dir):
    duration, audio_track_count, max_audio_bitrate = get_metadata(file)
    audio_settings = set_audio_settings(audio_track_count, max_audio_bitrate)
    
    audio_size = 96000 * duration
    video_bitrate = int((config["target_size"] - audio_size) / duration)

    ffmpeg_process(config["ffmpeg"], file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, config["codec"], config["gpu"])

def choose_quality(quality: int):
    if quality:
        match quality:
            case 1:
                return 1280
            case 2:
                return 1600
            case 3:
                return 1920
    else:
        return 1280

def choose_framerate(fluid: bool):
    if fluid:
        return 60
    else:
        return 30

def choose_overwrite(overwrite: bool):
    if overwrite:
        return "-y"
    else:
        return ""

def choose_output_dir(output_dir: str):
    if output_dir:
        return output_dir
    else:
        return "output/"

def choose_output_name(output_name):
    if output_name:
        return output_name + ".mp4"
    else:
        now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f'{now}_output.mp4'

def main(config, path, quality, fluid, output_name, output_dir, overwrite):
    if isdir(path):

        resolution = choose_quality(quality)
        framerate = choose_framerate(fluid)
        output_dir = choose_output_dir(output_dir)
        
        for file in listdir(path):
            if file.endswith(config["extensions"]):
                now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                output_file = f'{now}_output.mp4'
                file = path + "/" + file
                process(config, file, resolution, framerate, output_file, output_dir)
    else:
        resolution = choose_quality(quality)
        framerate = choose_framerate(fluid)
        output_dir = choose_output_dir(output_dir)
        
        overwrite = choose_overwrite(overwrite)
        output_name = choose_output_name(output_name)
        
        process(config, file, resolution, framerate, output_file, output_dir)



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

    config["extensions"] = (".mp4", ".mkv", ".mov", ".webm")

    return config

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("path", help="Video or directory path")
    parser.add_argument("-q", "--quality",
                        help="Video quality 1-3 (Sets the resolution : 720p, 900p, 1080p). Note that a higher resolution results in a lower global quality. The lower the setting, the higher the global video quality.",
                        type=int, choices=[1,2,3])
    parser.add_argument("-f", "--fluid",
                        help="Choose to have a higher framerate (With : 60fps, without : 30fps). Note that a higher framerate will negatively impact the video quality.",
                        action="store_true")
    parser.add_argument("-on", "--output-name",
                        help="Set an output name for the video")
    parser.add_argument("-od", "--output-dir",
                        help="Select an output directory for the video")
    parser.add_argument("-y",
                        help="Overwrite file if it allready exists")

    args: Namespace = parser.parse_args()

    config = get_config()
    main(config, args.path, args.quality, args.fluid, args.output_name, args.output_dir, args.y)