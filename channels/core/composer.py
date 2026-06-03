"""
FFmpeg-based video composer.
Combines audio + video clips into a final branded video.
"""
import subprocess
import tempfile
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{result.stderr[-2000:]}")


def _loop_clip_to_duration(clip: str, audio: str, out: Path) -> None:
    """Loop/trim a video clip to exactly match the audio duration, with no audio."""
    _run([
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", clip,
        "-i", audio,
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(out),
    ])


def _concat_segments(segment_paths: list[Path], out: Path) -> None:
    """Concatenate multiple video segments into one file."""
    list_file = out.parent / "concat_list.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in segment_paths))
    _run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy",
        str(out),
    ])


def _add_branding(
    video: str,
    out: Path,
    channel_name: str,
    is_short: bool,
    primary_hex: str = "#00C864",
    text_hex: str = "#FFFFFF",
) -> None:
    """Overlay channel name watermark at bottom of video."""
    font = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    fallback = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    fontsize = 28 if is_short else 36
    x = "(w-text_w)/2"
    y = "h-80" if is_short else "h-60"

    # Clean hex colours for ffmpeg (strip #)
    bg = primary_hex.lstrip("#")
    fg = text_hex.lstrip("#")

    drawtext = (
        f"fontfile={font}:text='{channel_name}':"
        f"fontsize={fontsize}:fontcolor=0x{fg}:"
        f"x={x}:y={y}:"
        f"box=1:boxcolor=0x{bg}AA:boxborderw=12"
    )

    _run([
        "ffmpeg", "-y", "-i", video,
        "-vf", f"drawtext={drawtext}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "copy",
        str(out),
    ])


def compose_short(scenes: list[dict], config, out_dir: Path) -> Path:
    """
    Compose a YouTube Short from scene dicts that each have:
      clip_path, audio_path, actual_duration, narration, visual_prompt
    Returns path to the final branded MP4.
    """
    segments_dir = out_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    segment_paths = []

    for i, scene in enumerate(scenes):
        seg = segments_dir / f"seg_{i:02d}.mp4"
        _loop_clip_to_duration(scene["clip_path"], scene["audio_path"], seg)
        segment_paths.append(seg)
        print(f"  composed segment {i} ({scene['actual_duration']:.1f}s)")

    raw = out_dir / "raw_concat.mp4"
    _concat_segments(segment_paths, raw)

    branded = out_dir / "final.mp4"
    _add_branding(
        str(raw), branded,
        channel_name=config.CHANNEL_NAME,
        is_short=True,
        primary_hex=config.PRIMARY_HEX,
    )
    print(f"  ✓ Short composed: {branded}")
    return branded


def compose_long(sections: list[dict], config, out_dir: Path) -> Path:
    """
    Compose a long-form video from section dicts, each having:
      heading, audio_path, audio_duration, clip_paths (list)
    Returns path to final branded MP4.
    """
    segments_dir = out_dir / "segments"
    segments_dir.mkdir(parents=True, exist_ok=True)
    segment_paths = []

    for i, section in enumerate(sections):
        clips = section["clip_paths"]
        audio = section["audio_path"]
        audio_dur = section["audio_duration"]

        # Interleave clips to cover the full audio duration
        # Simple strategy: loop all clips equally across the section
        clips_per_section = len(clips)
        clip_dur = audio_dur / clips_per_section

        sub_segs = []
        for j, clip in enumerate(clips):
            sub_audio_dir = out_dir / f"sub_audio_{i}_{j}"
            sub_audio_dir.mkdir(exist_ok=True)
            sub_audio = sub_audio_dir / "slice.wav"
            # Trim audio slice for this sub-clip
            start = j * clip_dur
            _run([
                "ffmpeg", "-y",
                "-i", audio,
                "-ss", str(start), "-t", str(clip_dur),
                "-c:a", "copy",
                str(sub_audio),
            ])
            sub_seg = segments_dir / f"sec_{i:02d}_clip_{j:02d}.mp4"
            _loop_clip_to_duration(clip, str(sub_audio), sub_seg)
            sub_segs.append(sub_seg)

        seg = segments_dir / f"section_{i:02d}.mp4"
        if len(sub_segs) == 1:
            sub_segs[0].rename(seg)
        else:
            _concat_segments(sub_segs, seg)
        segment_paths.append(seg)
        print(f"  composed section {i}: {section['heading']} ({audio_dur:.0f}s)")

    raw = out_dir / "raw_concat.mp4"
    _concat_segments(segment_paths, raw)

    branded = out_dir / "final.mp4"
    _add_branding(
        str(raw), branded,
        channel_name=config.CHANNEL_NAME,
        is_short=False,
        primary_hex=config.PRIMARY_HEX,
    )
    print(f"  ✓ Long-form composed: {branded}")
    return branded
