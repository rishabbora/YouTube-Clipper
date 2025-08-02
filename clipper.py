import sys
import subprocess
import os
import tempfile
import re
from pathlib import Path

# auto-install dependencies
for module, pkg in [('yt_dlp','yt-dlp'),('moviepy','moviepy'),('imageio_ffmpeg','imageio-ffmpeg')]:
    try:
        __import__(module)
    except ImportError:
        subprocess.check_call([sys.executable,'-m','pip','install',pkg])

import yt_dlp
from moviepy.video.io.VideoFileClip import VideoFileClip


def validate_url(url: str) -> bool:
    # basic pattern check; yt-dlp will catch deeper issues
    return bool(re.match(r'https?://(www\.)?youtube\.com/watch\?v=[\w-]+', url))


def parse_time(ts: str) -> float:
    # strict HH:MM:SS, no negatives
    if not re.match(r'^[0-9]{2}:[0-5][0-9]:[0-5][0-9]$', ts):
        raise ValueError('Timestamp must be HH:MM:SS')
    h, m, s = map(int, ts.split(':'))
    return h*3600 + m*60 + s


def format_hms(sec: float) -> str:
    t = int(sec)
    h = t//3600; m = (t%3600)//60; s = t%60
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_validated_inputs():
    # URL
    while True:
        url = input('Enter YouTube link: ').strip()
        if validate_url(url):
            break
        print('Invalid YouTube link. Private, age-restricted, or malformed videos cannot be clipped.')

    # start/end timestamps
    while True:
        try:
            start_ts = input('Start time (HH:MM:SS): ').strip()
            start = parse_time(start_ts)
            end_ts = input('End time (HH:MM:SS): ').strip()
            end = parse_time(end_ts)
        except ValueError as e:
            print(f'Error: {e}. Please use HH:MM:SS and non-negative values.')
            continue
        if end <= start:
            print('Error: end time must be after start time. Please re-enter times.')
            continue
        if (end - start) < 5:
            print('Error: clip length must be at least 5 seconds. Please re-enter times.')
            continue
        return url, start, end


def download_video(url: str, path: str):
    opts = {'format':'mp4', 'outtmpl':path, 'quiet':True, 'no_warnings':True, 'username': 'rishabbora93@gmail.com', 'password': 'Csd62295'}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def clip_and_save(url: str, start: float, end: float, out_path: Path, audio_only=False):
    print(f'Downloading from {url}…')
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'video.mp4')
    download_video(url, tmpfile)
    clip_full = VideoFileClip(tmpfile)
    dur = clip_full.duration
    # Safety re-check
    if start >= dur or end > dur:
        print(f'Error: video duration is {format_hms(dur)}, requested {format_hms(start)}–{format_hms(end)} incompatible.')
        clip_full.close()
        sys.exit(1)
    print(f'Clipping {format_hms(start)}→{format_hms(end)}…')
    clip = clip_full.subclipped(start, end)
    try:
        if audio_only:
            clip.audio.write_audiofile(str(out_path))
        else:
            clip.write_videofile(str(out_path), codec='libx264')
        print(f'Successfully saved at {out_path}')
    finally:
        clip_full.close()
        clip.close()
        # cleanup
        try:
            os.remove(tmpfile)
            os.rmdir(tmpdir)
        except:
            pass


if __name__ == '__main__':
    url, start, end = get_validated_inputs()

    # mode selection
    while True:
        mode = input('Enter 0 for audio only or 1 for audio+video: ').strip()
        if mode in ('0','1'):
            break
        print('Invalid selection. Please enter 0 or 1.')

    # filename
    while True:
        base = input('Enter output filename (without extension): ').strip()
        if base:
            break
        print('Filename cannot be empty. Please enter a name.')

    # prepare output path
    dl = Path.home() / 'Downloads'
    dl.mkdir(exist_ok=True)
    ext = '.mp3' if mode=='0' else '.mp4'
    out = dl / (Path(base).stem + ext)

    clip_and_save(url, start, end, out, audio_only=(mode=='0'))