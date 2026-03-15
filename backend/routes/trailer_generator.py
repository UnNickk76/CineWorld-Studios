"""
CineWorld Trailer Generator
Creates cinematic trailers from film poster + metadata using MoviePy/FFmpeg
"""
import os
import uuid
import tempfile
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Video settings
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280  # Vertical (mobile-friendly)
FPS = 24
FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"

UPLOAD_DIR = "/app/backend/static/trailers"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def download_poster(poster_url: str) -> Image.Image:
    """Download poster image and return as PIL Image."""
    resp = requests.get(poster_url, timeout=15)
    resp.raise_for_status()
    img = Image.open(BytesIO(resp.content)).convert("RGB")
    return img


def create_frame_black(text_lines, alpha=255):
    """Create a black frame with centered text."""
    frame = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(frame)

    y_offset = VIDEO_HEIGHT // 2 - (len(text_lines) * 40)
    for line, size, color in text_lines:
        try:
            font = ImageFont.truetype(FONT_PATH, size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        # Apply alpha to color
        r, g, b = color
        a = alpha / 255.0
        final_color = (int(r * a), int(g * a), int(b * a))
        draw.text((x, y_offset), line, font=font, fill=final_color)
        y_offset += size + 15

    return frame


def create_poster_frame(poster: Image.Image, zoom=1.0, offset_y=0):
    """Create a frame with the poster, zoom effect, and cinematic bars."""
    # Resize poster to fill width with zoom
    aspect = poster.height / poster.width
    new_w = int(VIDEO_WIDTH * zoom)
    new_h = int(new_w * aspect)

    resized = poster.resize((new_w, new_h), Image.LANCZOS)

    # Center crop
    frame = Image.new("RGB", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0))
    x = (VIDEO_WIDTH - new_w) // 2
    y = (VIDEO_HEIGHT - new_h) // 2 + offset_y
    frame.paste(resized, (x, y))

    # Add cinematic letterbox bars
    draw = ImageDraw.Draw(frame)
    bar_h = 80
    draw.rectangle([(0, 0), (VIDEO_WIDTH, bar_h)], fill=(0, 0, 0))
    draw.rectangle([(0, VIDEO_HEIGHT - bar_h), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(0, 0, 0))

    # Add vignette effect
    vignette = Image.new("L", (VIDEO_WIDTH, VIDEO_HEIGHT), 255)
    vdraw = ImageDraw.Draw(vignette)
    for i in range(60):
        alpha = int(255 * (i / 60))
        vdraw.rectangle([(i, i), (VIDEO_WIDTH - i, VIDEO_HEIGHT - i)], outline=alpha)
    frame = Image.composite(frame, Image.new("RGB", frame.size, (0, 0, 0)), vignette)

    return frame


def create_text_overlay_frame(poster: Image.Image, text_lines, zoom=1.0):
    """Create a poster frame with text overlay at the bottom."""
    frame = create_poster_frame(poster, zoom)

    # Dark gradient overlay at bottom
    draw = ImageDraw.Draw(frame)
    gradient_h = 400
    for i in range(gradient_h):
        alpha = int(220 * (i / gradient_h))
        y = VIDEO_HEIGHT - gradient_h + i
        draw.line([(0, y), (VIDEO_WIDTH, y)], fill=(0, 0, 0, alpha))

    # Draw text
    y_offset = VIDEO_HEIGHT - 200
    for line, size, color in text_lines:
        try:
            font = ImageFont.truetype(FONT_PATH, size)
        except Exception:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (VIDEO_WIDTH - tw) // 2
        # Shadow
        draw.text((x + 2, y_offset + 2), line, font=font, fill=(0, 0, 0))
        draw.text((x, y_offset), line, font=font, fill=color)
        y_offset += size + 8

    return frame


def generate_trailer(film: dict) -> str:
    """
    Generate a cinematic trailer video for a film.
    Returns the path to the generated MP4 file.
    """
    from moviepy import VideoClip

    title = film.get("title", "Untitled")
    genre = film.get("genre", "Drama").upper()
    director_name = film.get("director_name", "")
    cast_names = film.get("cast_names", [])[:4]  # Top 4 actors
    quality = film.get("quality_score", 0)
    poster_url = film.get("poster_url", "")
    studio_name = film.get("studio_name", "CineWorld Studio's")

    # Download poster
    if poster_url:
        try:
            poster = download_poster(poster_url)
        except Exception:
            poster = Image.new("RGB", (720, 1080), (20, 20, 30))
    else:
        poster = Image.new("RGB", (720, 1080), (20, 20, 30))

    clips = []

    # Scene 1: Studio name fade in (1.5s)
    frames_s1 = []
    for i in range(36):  # 1.5s at 24fps
        alpha = min(255, int(255 * (i / 18)))
        frame = create_frame_black([
            (studio_name, 28, (200, 170, 100)),
            ("PRESENTA", 18, (150, 150, 150)),
        ], alpha=alpha)
        frames_s1.append(frame)
    # Hold for 1s
    for _ in range(24):
        frames_s1.append(frames_s1[-1])
    # Fade out 0.5s
    for i in range(12):
        alpha = max(0, int(255 * (1 - i / 12)))
        frame = create_frame_black([
            (studio_name, 28, (200, 170, 100)),
            ("PRESENTA", 18, (150, 150, 150)),
        ], alpha=alpha)
        frames_s1.append(frame)

    # Scene 2: Poster with slow zoom in (3s)
    frames_s2 = []
    total_s2 = 72  # 3s
    for i in range(total_s2):
        t = i / total_s2
        zoom = 1.0 + (t * 0.15)  # Slow zoom from 1.0 to 1.15
        alpha = min(255, int(255 * (i / 18)))  # Fade in first 0.75s
        frame = create_poster_frame(poster, zoom)
        if alpha < 255:
            black = Image.new("RGB", frame.size, (0, 0, 0))
            mask = Image.new("L", frame.size, alpha)
            frame = Image.composite(frame, black, mask)
        frames_s2.append(frame)

    # Scene 3: Genre flash (0.8s)
    frames_s3 = []
    for i in range(19):
        t = i / 19
        if t < 0.2:
            alpha = int(255 * (t / 0.2))
        elif t > 0.7:
            alpha = int(255 * ((1 - t) / 0.3))
        else:
            alpha = 255
        frame = create_frame_black([
            (genre, 48, (230, 190, 70)),
        ], alpha=alpha)
        frames_s3.append(frame)

    # Scene 4: Poster with title overlay (3s)
    frames_s4 = []
    total_s4 = 72
    title_lines = [(title.upper(), 36, (255, 255, 255))]
    if director_name:
        title_lines.append((f"Diretto da {director_name}", 18, (200, 200, 200)))
    for i in range(total_s4):
        t = i / total_s4
        zoom = 1.15 + (t * 0.1)
        alpha = min(255, int(255 * (i / 12)))
        frame = create_text_overlay_frame(poster, title_lines, zoom)
        if alpha < 255:
            black = Image.new("RGB", frame.size, (0, 0, 0))
            mask = Image.new("L", frame.size, alpha)
            frame = Image.composite(frame, black, mask)
        frames_s4.append(frame)

    # Scene 5: Cast names (2s)
    frames_s5 = []
    if cast_names:
        cast_text = [(name, 22, (220, 220, 220)) for name in cast_names]
        for i in range(48):
            t = i / 48
            if t < 0.15:
                alpha = int(255 * (t / 0.15))
            elif t > 0.85:
                alpha = int(255 * ((1 - t) / 0.15))
            else:
                alpha = 255
            frame = create_frame_black(cast_text, alpha=alpha)
            frames_s5.append(frame)

    # Scene 6: Final poster zoom out with quality (2s)
    frames_s6 = []
    total_s6 = 48
    quality_str = f"Quality Score: {quality:.0f}/100" if quality else ""
    final_lines = [(title.upper(), 32, (255, 215, 0))]
    if quality_str:
        final_lines.append((quality_str, 20, (200, 200, 200)))
    final_lines.append(("PROSSIMAMENTE", 24, (180, 150, 80)))
    for i in range(total_s6):
        t = i / total_s6
        zoom = 1.25 - (t * 0.15)  # Zoom out
        frame = create_text_overlay_frame(poster, final_lines, zoom)
        # Fade to black at end
        if t > 0.75:
            fade = int(255 * ((1 - t) / 0.25))
            black = Image.new("RGB", frame.size, (0, 0, 0))
            mask = Image.new("L", frame.size, fade)
            frame = Image.composite(frame, black, mask)
        frames_s6.append(frame)

    # Combine all frames
    all_frames = frames_s1 + frames_s2 + frames_s3 + frames_s4 + frames_s5 + frames_s6

    # Convert PIL images to numpy arrays
    import numpy as np
    frame_arrays = [np.array(f) for f in all_frames]

    # Create video from frames
    duration = len(frame_arrays) / FPS

    def make_frame(t):
        idx = min(int(t * FPS), len(frame_arrays) - 1)
        return frame_arrays[idx]

    video = VideoClip(make_frame, duration=duration)
    video = video.with_fps(FPS)

    # Output file
    trailer_id = str(uuid.uuid4())
    output_path = os.path.join(UPLOAD_DIR, f"{trailer_id}.mp4")

    video.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="ultrafast",
        threads=2,
        logger=None
    )

    video.close()

    return trailer_id, output_path
