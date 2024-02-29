import subprocess
from pymediainfo import MediaInfo
from datetime import datetime
from os import mkdir
from argparse import ArgumentParser, Namespace

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

def process(ffmpeg, input_file, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, overwrite, codec, gpu):
    ffmpeg_command = f'{ffmpeg} {gpu} -i "{input_file}" {audio_settings} -map 0:v -c:v {codec} -b:v {video_bitrate} -maxrate {video_bitrate} -minrate {video_bitrate} -vf "scale={resolution}:-1" -r {framerate} "{output_dir}/{output_file}" {overwrite}'
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

def choose_quality(quality: int):
    match quality:
        case 1:
            return 1280
        case 2:
            return 1600
        case 3:
            return 1920

def main(video, quality, fluid, output_name, output_dir, overwrite):
    try:
        subprocess.check_output("ffmpeg -h")
        ffmpeg = "ffmpeg"
    except Exception:
        ffmpeg = "ffmpeg.exe"
    
    duration, audio_track_count, max_audio_bitrate = get_metadata(video)

    if audio_track_count == None and max_audio_bitrate == None:
        audio_settings = ""
    else:
        audio_settings = f'-filter_complex "[0:a]amerge=inputs={audio_track_count},loudnorm=I=-16:TP=-5:LRA=11[aout]" -map "[aout]" -c:a mp3 -b:a 96k'
    
    if not quality:
        resolution = choose_quality(1)
    else:
        resolution = choose_quality(quality)
    
    if fluid:
        framerate = 60
    else:
        framerate = 30
    
    if overwrite:
        overwrite = "-y"
    else:
        overwrite = ""

    if not output_dir:
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
    
    process(ffmpeg, video, video_bitrate, resolution, framerate, audio_settings, output_file, output_dir, overwrite, codec, gpu)

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("file", help="Video path")
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

    main(args.file, args.quality, args.fluid, args.output_name, args.output_dir, args.y)