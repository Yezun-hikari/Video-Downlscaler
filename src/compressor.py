import os
import subprocess
import re
import imageio_ffmpeg

def get_ffmpeg_path():
    return imageio_ffmpeg.get_ffmpeg_exe()

def get_video_info(input_path):
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [ffmpeg_exe, "-i", input_path]
    result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    # Parse duration
    duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2}\.\d+)", result.stderr)
    duration = 0
    if duration_match:
        hours, minutes, seconds = duration_match.groups()
        duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)

    # Parse video stream for resolution
    # Stream #0:0(und): Video: h264 (High) (avc1 / 0x31637661), yuv420p, 1920x1080 [SAR 1:1 DAR 16:9], 3236 kb/s, 24 fps, 24 tbr, 24k tbn, 48 tbc
    resolution_match = re.search(r"Stream #.*Video:.*, (\d{3,5})x(\d{3,5})", result.stderr)
    width = 0
    height = 0
    if resolution_match:
        width = int(resolution_match.group(1))
        height = int(resolution_match.group(2))

    return duration, width, height

def parse_time_str(time_str):
    # time=00:00:05.12
    try:
        parts = time_str.split(':')
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2])
        return h * 3600 + m * 60 + s
    except:
        return 0

def compress_video(input_path, output_path, target_size_mb, progress_callback=None):
    ffmpeg_exe = get_ffmpeg_path()
    duration, width, height = get_video_info(input_path)

    if duration == 0:
        raise ValueError("Could not determine video duration")

    # Calculate target bitrate
    # target_size_mb = size in MB
    # size_in_bits = target_size_mb * 8 * 1024 * 1024
    # bitrate = size_in_bits / duration

    target_total_bitrate = (target_size_mb * 8 * 1024 * 1024) / duration

    # Audio bitrate (fixed 128k for stereo, or 96k if tight)
    audio_bitrate = 128 * 1024

    video_bitrate = target_total_bitrate - audio_bitrate

    # If video bitrate is too low, reduce audio or scale down
    if video_bitrate < 100 * 1024: # Less than 100k for video
        audio_bitrate = 64 * 1024 # Reduce audio to 64k
        video_bitrate = target_total_bitrate - audio_bitrate

    if video_bitrate < 1000:
         raise ValueError("Target size is too small for this video length.")

    # Downscaling heuristic
    # Calculate Bits Per Pixel (BPP) assuming 30fps if unknown
    # BPP = bitrate / (width * height * fps)
    # If BPP < 0.1, we should scale down.
    # Let's target a BPP of around 0.1 for decent quality H.264

    target_pixel_count = video_bitrate / (0.1 * 30)
    current_pixel_count = width * height

    scale_filter = []

    if target_pixel_count < current_pixel_count:
        scale_factor = (target_pixel_count / current_pixel_count) ** 0.5
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)

        # Ensure dimensions are even
        if new_width % 2 != 0: new_width -= 1
        if new_height % 2 != 0: new_height -= 1

        # Don't scale down below 320x240 just to hit bitrate, it will look like a stamp.
        # But user wants "under filesize", so we prioritize file size.
        if new_width < 320:
             new_width = 320
             new_height = int(320 * height / width)
             if new_height % 2 != 0: new_height -= 1

        scale_filter = ["-vf", f"scale={new_width}:{new_height}"]

    video_bitrate_kb = int(video_bitrate / 1000)
    audio_bitrate_kb = int(audio_bitrate / 1000)

    print(f"Target Video Bitrate: {video_bitrate_kb}k, Audio: {audio_bitrate_kb}k")
    if scale_filter:
        print(f"Scaling to {scale_filter[1]}")

    # Pass 1
    # On Windows NUL, others /dev/null
    outfile_null = "NUL" if os.name == 'nt' else "/dev/null"

    pass1_cmd = [
        ffmpeg_exe, "-y", "-i", input_path,
        "-c:v", "libx264", "-b:v", f"{video_bitrate_kb}k", "-pass", "1",
        "-an", # No audio for pass 1
        "-f", "mp4"
    ] + scale_filter + [outfile_null]

    # Run pass 1
    if progress_callback:
        progress_callback(0, "Running Pass 1...")

    subprocess.run(pass1_cmd, check=True)

    # Pass 2
    pass2_cmd = [
        ffmpeg_exe, "-y", "-i", input_path,
        "-c:v", "libx264", "-b:v", f"{video_bitrate_kb}k", "-pass", "2",
        "-c:a", "aac", "-b:a", f"{audio_bitrate_kb}k"
    ] + scale_filter + [output_path]

    # Run pass 2 and capture progress
    if progress_callback:
        progress_callback(50, "Running Pass 2...")

    process = subprocess.Popen(pass2_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True)

    # ffmpeg outputs to stderr
    while True:
        line = process.stderr.readline()
        if not line:
            break
        # Parse "time=..."
        if "time=" in line:
            time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d+)", line)
            if time_match:
                current_time_str = time_match.group(1)
                current_seconds = parse_time_str(current_time_str)
                if duration > 0:
                    percent = (current_seconds / duration) * 50 + 50 # Pass 2 is the second 50%
                    if progress_callback:
                        progress_callback(int(percent), f"Compressing... {int(percent)}%")

    process.wait()

    # Cleanup logs
    try:
        if os.path.exists("ffmpeg2pass-0.log"): os.remove("ffmpeg2pass-0.log")
        if os.path.exists("ffmpeg2pass-0.log.mbtree"): os.remove("ffmpeg2pass-0.log.mbtree")
    except:
        pass

    if progress_callback:
        progress_callback(100, "Done!")
