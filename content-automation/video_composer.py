from pathlib import Path
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from frame_generator import (
    create_title_frame, create_point_frame, create_hook_frame, create_outro_frame,
)
from config import OUTPUT_DIR, CHANNEL_NAME, FPS


TITLE_DURATION = 8     # seconds for title card
HOOK_DURATION = 12     # seconds for hook card
OUTRO_DURATION = 10    # seconds for outro
MIN_POINT_DURATION = 15  # minimum seconds per key point card


def compose_video(audio_path: str, script_data: dict, output_path: str) -> str:
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    audio = AudioFileClip(audio_path)
    total = audio.duration
    key_points: list[str] = script_data["key_points"]

    # Distribute remaining time evenly across key point slides
    fixed_time = TITLE_DURATION + HOOK_DURATION + OUTRO_DURATION
    point_time = max((total - fixed_time) / len(key_points), MIN_POINT_DURATION)

    slides: list[tuple[str, float]] = []

    # Title slide
    title_path = f"{OUTPUT_DIR}/slide_title.png"
    create_title_frame(script_data["title"], CHANNEL_NAME, title_path)
    slides.append((title_path, TITLE_DURATION))

    # Hook slide (first attention-grabbing point)
    hook_path = f"{OUTPUT_DIR}/slide_hook.png"
    create_hook_frame(script_data["hook"], CHANNEL_NAME, hook_path)
    slides.append((hook_path, HOOK_DURATION))

    # Key point slides
    for i, point in enumerate(key_points):
        frame_path = f"{OUTPUT_DIR}/slide_point_{i}.png"
        create_point_frame(i + 1, point, CHANNEL_NAME, frame_path)
        slides.append((frame_path, point_time))

    # Outro slide
    outro_path = f"{OUTPUT_DIR}/slide_outro.png"
    create_outro_frame(CHANNEL_NAME, outro_path)
    slides.append((outro_path, OUTRO_DURATION))

    # Build video clips
    clips = [ImageClip(path).with_duration(dur) for path, dur in slides]
    video = concatenate_videoclips(clips)

    # Trim to match audio exactly
    if video.duration > total:
        video = video.subclipped(0, total)

    final = video.with_audio(audio)
    final.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4,
        logger=None,
    )

    audio.close()
    final.close()

    print(f"  Video composed: {output_path}")
    return output_path
