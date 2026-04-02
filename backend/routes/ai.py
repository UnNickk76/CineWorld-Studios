# CineWorld Studio's - AI / Poster / Trailer Routes
# Screenplay generation, poster generation (AI + fallback), trailer generation (Sora 2),
# translate, soundtrack description, poster serving helpers

import os
import uuid
import math
import base64
import asyncio
import random
import logging
from io import BytesIO
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from database import db
from auth_utils import get_current_user
import poster_storage

router = APIRouter()

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

# ==================== PYDANTIC MODELS ====================

class ScreenplayRequest(BaseModel):
    genre: str
    title: str
    language: str
    tone: str = 'dramatic'
    length: str = 'medium'
    custom_prompt: Optional[str] = None

class PosterRequest(BaseModel):
    title: str
    genre: str
    description: str
    style: str = 'cinematic'
    cast_names: Optional[List[str]] = None
    force_fallback: Optional[bool] = False
    production_house_name: Optional[str] = None
    is_sequel: Optional[bool] = False
    sequel_number: Optional[int] = None
    sequel_subtitle: Optional[str] = None
    sequel_parent_title: Optional[str] = None

class TranslationRequest(BaseModel):
    text: str
    source_lang: str
    target_lang: str

class SoundtrackRequest(BaseModel):
    title: str
    genre: str
    mood: str = 'epic'
    language: str = 'en'
    custom_prompt: Optional[str] = None

class TrailerRequest(BaseModel):
    film_id: str
    style: str = 'cinematic'
    duration: int = 4

# ==================== IN-MEMORY POSTER TASKS ====================

poster_tasks = {}

# ==================== POSTER CONSTANTS ====================

POSTER_GENRE_THEMES = {
    'action': [
        [(180, 40, 20), (20, 10, 5), (255, 100, 0)],
        [(200, 60, 0), (10, 5, 0), (255, 200, 0)],
        [(60, 0, 0), (0, 0, 0), (255, 50, 50)],
    ],
    'comedy': [
        [(220, 180, 50), (40, 30, 10), (255, 220, 80)],
        [(255, 150, 50), (50, 20, 0), (255, 255, 100)],
        [(200, 100, 180), (30, 10, 25), (255, 180, 220)],
    ],
    'drama': [
        [(30, 50, 90), (10, 15, 30), (120, 160, 220)],
        [(50, 30, 70), (10, 5, 15), (180, 120, 200)],
        [(20, 40, 60), (5, 5, 10), (100, 180, 200)],
    ],
    'horror': [
        [(60, 10, 30), (5, 0, 5), (150, 0, 50)],
        [(30, 0, 0), (0, 0, 0), (200, 0, 0)],
        [(0, 20, 0), (0, 0, 0), (0, 200, 50)],
    ],
    'sci_fi': [
        [(10, 40, 80), (5, 10, 25), (0, 180, 255)],
        [(0, 10, 40), (0, 0, 10), (0, 255, 200)],
        [(40, 0, 60), (5, 0, 10), (200, 0, 255)],
    ],
    'romance': [
        [(140, 40, 80), (30, 10, 20), (255, 100, 150)],
        [(180, 60, 60), (40, 10, 10), (255, 150, 180)],
        [(100, 30, 100), (20, 5, 20), (255, 120, 200)],
    ],
    'thriller': [
        [(50, 50, 50), (10, 10, 10), (200, 180, 0)],
        [(40, 30, 20), (5, 5, 5), (255, 200, 100)],
        [(20, 20, 40), (0, 0, 5), (180, 180, 255)],
    ],
    'fantasy': [
        [(60, 20, 100), (10, 5, 25), (180, 80, 255)],
        [(20, 40, 80), (5, 5, 15), (100, 200, 255)],
        [(80, 20, 60), (15, 5, 10), (255, 100, 200)],
    ],
}

POSTER_DEFAULT_THEMES = [
    [(40, 40, 50), (10, 10, 15), (180, 180, 200)],
    [(50, 40, 30), (10, 8, 5), (200, 170, 120)],
    [(30, 50, 40), (5, 10, 8), (120, 200, 160)],
]

POSTER_PATTERNS = ['circles', 'lines', 'diamonds', 'rays', 'grid', 'nebula', 'vignette']

GENRE_POSTER_IMAGES = {
    'thriller': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'thriller.jpeg'),
    'romance': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'romance.jpeg'),
    'comedy': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'comedy.jpeg'),
    'fantasy': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'fantasy.jpeg'),
    'adventure': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'adventure.jpeg'),
    'noir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'noir.jpeg'),
    'horror': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'horror.jpeg'),
    'drama': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'posters', 'drama.jpeg'),
}


# ==================== HELPER FUNCTIONS ====================

def _overlay_poster_text(img, title: str, cast_names: list):
    """Overlay film title and cast names on the poster image using Pillow."""
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    w, h = img.size

    for y in range(int(h * 0.65), h):
        alpha = int(200 * ((y - h * 0.65) / (h * 0.35)))
        alpha = min(alpha, 200)
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, alpha) if img.mode == 'RGBA' else (0, 0, 0))
    overlay = img.copy()
    overlay_draw = ImageDraw.Draw(overlay)
    for y in range(int(h * 0.65), h):
        opacity = ((y - h * 0.65) / (h * 0.35))
        opacity = min(opacity, 0.85)
        r = int(0 * opacity)
        overlay_draw.line([(0, y), (w, y)], fill=(r, r, r))
    from PIL import Image as PILImage2
    img = PILImage2.blend(img, overlay, 0.75)
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", max(28, w // 16))
        font_cast = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", max(16, w // 30))
    except Exception:
        font_title = ImageFont.load_default()
        font_cast = ImageFont.load_default()

    title_upper = title.upper()
    bbox = draw.textbbox((0, 0), title_upper, font=font_title)
    tw = bbox[2] - bbox[0]
    title_x = (w - tw) // 2
    title_y = int(h * 0.82)
    for dx, dy in [(2, 2), (-1, -1), (2, 0), (0, 2)]:
        draw.text((title_x + dx, title_y + dy), title_upper, font=font_title, fill=(0, 0, 0))
    draw.text((title_x, title_y), title_upper, font=font_title, fill=(255, 255, 255))

    if cast_names and len(cast_names) > 0:
        names_text = "  \u2022  ".join([n.upper() for n in cast_names[:4]])
        bbox2 = draw.textbbox((0, 0), names_text, font=font_cast)
        nw = bbox2[2] - bbox2[0]
        names_x = (w - nw) // 2
        names_y = title_y - int(h * 0.05)
        for dx, dy in [(1, 1), (-1, -1)]:
            draw.text((names_x + dx, names_y + dy), names_text, font=font_cast, fill=(0, 0, 0))
        draw.text((names_x, names_y), names_text, font=font_cast, fill=(220, 180, 50))

    return img


async def _generate_fallback_poster(request) -> dict:
    """Generate a diverse fallback poster using Pillow with genre-themed visuals."""
    from PIL import Image as PILImage, ImageDraw, ImageFont

    width, height = 600, 900
    genre = (request.genre or 'drama').lower()
    title = request.title or 'Film'
    production_house = getattr(request, 'production_house_name', '') or ''

    genre_image_path = GENRE_POSTER_IMAGES.get(genre)
    has_genre_image = genre_image_path and os.path.exists(genre_image_path)

    if has_genre_image:
        try:
            img = PILImage.open(genre_image_path).convert('RGB')
            img = img.resize((width, height), PILImage.LANCZOS)
        except Exception as e:
            logging.warning(f"Failed to load genre image for {genre}: {e}")
            has_genre_image = False

    if not has_genre_image:
        img = PILImage.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)

        seed = hash(title + genre) % 2**32
        import random as rng
        rng.seed(seed)

        themes = POSTER_GENRE_THEMES.get(genre, POSTER_DEFAULT_THEMES)
        theme = rng.choice(themes)
        top_color, bottom_color, accent = theme

        def jitter(color, amount=25):
            return tuple(max(0, min(255, c + rng.randint(-amount, amount))) for c in color)

        top_color = jitter(top_color, 20)
        bottom_color = jitter(bottom_color, 10)
        accent = jitter(accent, 15)

        diagonal = rng.random() < 0.4
        for y in range(height):
            for x in range(width) if diagonal else [0]:
                if diagonal:
                    ratio = (y / height * 0.7 + x / width * 0.3)
                else:
                    ratio = y / height
                r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
                g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
                b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
                if diagonal:
                    draw.point((x, y), fill=(r, g, b))
                else:
                    draw.line([(0, y), (width, y)], fill=(r, g, b))

        pattern = rng.choice(POSTER_PATTERNS)

        if pattern == 'circles':
            for _ in range(rng.randint(5, 15)):
                cx, cy = rng.randint(-50, width + 50), rng.randint(-50, height)
                r = rng.randint(30, 200)
                opacity = rng.randint(10, 40)
                col = accent + (opacity,)
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], outline=col, width=rng.randint(1, 3))
        elif pattern == 'lines':
            for _ in range(rng.randint(5, 20)):
                y_pos = rng.randint(0, height)
                opacity = rng.randint(15, 50)
                col = accent + (opacity,)
                draw.line([(0, y_pos), (width, y_pos + rng.randint(-100, 100))], fill=col, width=rng.randint(1, 4))
        elif pattern == 'diamonds':
            for _ in range(rng.randint(3, 10)):
                cx, cy = rng.randint(0, width), rng.randint(0, height * 2 // 3)
                s = rng.randint(20, 80)
                opacity = rng.randint(15, 45)
                col = accent + (opacity,)
                draw.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], outline=col, fill=None)
        elif pattern == 'rays':
            cx, cy = width // 2, height // 3
            for i in range(rng.randint(8, 24)):
                angle = (i / 24) * 2 * math.pi + rng.uniform(-0.1, 0.1)
                ex = cx + int(math.cos(angle) * 800)
                ey = cy + int(math.sin(angle) * 800)
                opacity = rng.randint(8, 30)
                col = accent + (opacity,)
                draw.line([(cx, cy), (ex, ey)], fill=col, width=rng.randint(1, 3))
        elif pattern == 'grid':
            spacing = rng.randint(40, 80)
            for x in range(0, width, spacing):
                opacity = rng.randint(8, 25)
                draw.line([(x, 0), (x, height)], fill=accent + (opacity,), width=1)
            for y in range(0, height, spacing):
                opacity = rng.randint(8, 25)
                draw.line([(0, y), (width, y)], fill=accent + (opacity,), width=1)
        elif pattern == 'nebula':
            for _ in range(rng.randint(30, 80)):
                cx, cy = rng.randint(0, width), rng.randint(0, height * 2 // 3)
                r = rng.randint(2, 40)
                opacity = rng.randint(5, 30)
                c = jitter(accent, 40) + (opacity,)
                draw.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=c)
        elif pattern == 'vignette':
            for r in range(max(width, height), 0, -3):
                opacity = max(0, min(60, int((1 - r / max(width, height)) * 60)))
                draw.ellipse(
                    [(width // 2 - r, height // 2 - r), (width // 2 + r, height // 2 + r)],
                    outline=(0, 0, 0, opacity)
                )

        for _ in range(rng.randint(10, 40)):
            x = rng.randint(0, width)
            y = rng.randint(0, height // 2)
            size = rng.randint(1, 3)
            brightness = rng.randint(100, 255)
            draw.ellipse([(x, y), (x + size, y + size)], fill=(brightness, brightness, brightness))

        bar_style = rng.choice(['top', 'bottom', 'both', 'none'])
        if bar_style in ('top', 'both'):
            bar_h = rng.randint(2, 6)
            bar_y = rng.randint(height // 5, height // 3)
            draw.rectangle([(0, bar_y), (width, bar_y + bar_h)], fill=accent)
        if bar_style in ('bottom', 'both'):
            bar_h = rng.randint(2, 6)
            bar_y = rng.randint(height * 2 // 3, height * 3 // 4)
            draw.rectangle([(0, bar_y), (width, bar_y + bar_h)], fill=accent)

    # --- Text overlay ---
    draw = ImageDraw.Draw(img)

    overlay = PILImage.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    gradient_start = int(height * 0.55)
    for y in range(gradient_start, height):
        alpha = int(220 * ((y - gradient_start) / (height - gradient_start)))
        alpha = min(alpha, 220)
        overlay_draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    img = img.convert('RGBA')
    img = PILImage.alpha_composite(img, overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 42)
        font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 22)
    except Exception:
        font_title = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()

    title_upper = title.upper()
    title_lines = []
    words = title_upper.split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip() if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font_title)
        if bbox[2] - bbox[0] > width - 40:
            if current_line:
                title_lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        title_lines.append(current_line)
    if not title_lines:
        title_lines = [title_upper]

    line_height = 50
    total_title_height = len(title_lines) * line_height
    title_start_y = int(height * 0.72) - total_title_height // 2

    for i, line in enumerate(title_lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        tx = (width - tw) // 2
        ty = title_start_y + i * line_height
        for dx, dy in [(2, 2), (-1, -1), (2, 0), (0, 2)]:
            draw.text((tx + dx, ty + dy), line, font=font_title, fill=(0, 0, 0))
        draw.text((tx, ty), line, font=font_title, fill=(255, 255, 255))

    if production_house:
        subtitle = f"un film {production_house}"
        bbox2 = draw.textbbox((0, 0), subtitle, font=font_subtitle)
        stw = bbox2[2] - bbox2[0]
        stx = (width - stw) // 2
        sty = title_start_y + total_title_height + 10
        for dx, dy in [(1, 1), (-1, -1)]:
            draw.text((stx + dx, sty + dy), subtitle, font=font_subtitle, fill=(0, 0, 0))
        draw.text((stx, sty), subtitle, font=font_subtitle, fill=(220, 180, 50))

    jpeg_buffer = BytesIO()
    img.save(jpeg_buffer, format='JPEG', quality=82, optimize=True)
    jpeg_bytes = jpeg_buffer.getvalue()

    filename = f"fb_{uuid.uuid4().hex[:12]}.jpg"
    await poster_storage.save_poster(filename, jpeg_bytes, 'image/jpeg')
    poster_file_url = f"/api/posters/{filename}"
    image_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')

    logging.info(f"Fallback poster generated for '{title}' ({genre}, genre_image={has_genre_image}): {len(jpeg_bytes)} bytes")
    return {'poster_base64': image_base64, 'poster_url': poster_file_url, 'is_fallback': True}


# ==================== BACKGROUND TASKS ====================

async def generate_trailer_task_sora2(film_id: str, style: str, duration: int, user_id: str, cost: int):
    """Generate a trailer using Sora 2 AI from film plot description."""
    try:
        from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

        os.makedirs('/app/trailers', exist_ok=True)

        film = await db.films.find_one({'id': film_id}, {'_id': 0})
        if not film:
            raise Exception("Film non trovato")

        title = film.get('title', 'Film')
        genre = film.get('genre', 'Drama')
        description = film.get('description', '')
        cast = film.get('cast_members', [])
        cast_names = ', '.join([c.get('name', '') for c in cast[:3]]) if cast else ''

        style_prompts = {
            'cinematic': 'cinematic, dramatic lighting, film grain, professional color grading',
            'action': 'dynamic camera movement, fast cuts, explosive energy, action movie style',
            'dramatic': 'emotional, slow motion, dramatic music feel, intimate close-ups',
            'comedy': 'bright and colorful, energetic, fun atmosphere, lighthearted mood',
            'horror': 'dark atmosphere, suspenseful, eerie lighting, shadows, mysterious fog'
        }
        style_desc = style_prompts.get(style, style_prompts['cinematic'])

        prompt = f"""A {genre.lower()} movie trailer for "{title}". {description[:300] if description else f'A compelling {genre.lower()} film.'} Style: {style_desc}. Widescreen cinematic format, movie trailer aesthetic with dramatic pacing."""

        logging.info(f"[TRAILER] Generating Sora 2 trailer for {film_id}, duration={duration}s")

        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise Exception("EMERGENT_LLM_KEY not configured")

        video_gen = OpenAIVideoGeneration(api_key=api_key)
        output_path = f'/app/trailers/{film_id}.mp4'

        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model="sora-2",
            size="1280x720",
            duration=duration,
            max_wait_time=600
        )

        if not video_bytes:
            raise Exception("Sora 2 non ha generato il video")

        video_gen.save_video(video_bytes, output_path)

        file_size = os.path.getsize(output_path)
        logging.info(f"[TRAILER] Sora 2 Success! Film {film_id}, {file_size} bytes")

        trailer_url = f"/api/trailers/{film_id}.mp4"

        base_bonus = {4: 3, 8: 5, 12: 8}.get(duration, 3)
        rating_bonus = max(1, int(film.get('imdb_rating', 5.0) / 2))
        quality_bonus = base_bonus + rating_bonus

        user_data = await db.users.find_one({'id': user_id}, {'_id': 0, 'production_house_name': 1})
        studio_name = user_data.get('production_house_name', '') if user_data else ''

        await db.films.update_one(
            {'id': film_id},
            {
                '$set': {
                    'trailer_url': trailer_url,
                    'trailer_generating': False,
                    'trailer_generated_at': datetime.now(timezone.utc).isoformat(),
                    'trailer_bonus': quality_bonus,
                    'trailer_duration': duration,
                    'trailer_cost': cost
                },
                '$inc': {'quality_score': quality_bonus}
            }
        )

        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'trailer_generated',
            'title': 'Trailer Pronto!',
            'message': f'Il trailer di "{title}" ({duration}s) e pronto! +{quality_bonus} bonus qualita. Costo: ${cost:,}.',
            'data': {'film_id': film_id, 'path': f'/films/{film_id}', 'type': 'film'},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })

        if user_data:
            bot_message = {
                'id': str(uuid.uuid4()),
                'room_id': 'general',
                'user_id': 'system_bot',
                'user': {
                    'id': 'system_bot',
                    'nickname': 'CineBot',
                    'avatar_url': 'https://api.dicebear.com/9.x/bottts/svg?seed=cinebot',
                    'production_house_name': 'CineWorld System'
                },
                'content': f"NUOVO TRAILER AI! \"{title}\" di {studio_name} - Trailer {duration}s generato con Sora 2!",
                'message_type': 'trailer_announcement',
                'film_id': film_id,
                'trailer_url': trailer_url,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            await db.chat_messages.insert_one(bot_message)

    except Exception as e:
        logging.error(f"[TRAILER] Sora 2 Error for {film_id}: {str(e)}")
        await db.films.update_one(
            {'id': film_id},
            {'$set': {'trailer_generating': False, 'trailer_error': str(e)[:500]}}
        )
        await db.users.update_one({'id': user_id}, {'$inc': {'funds': cost}})

        await db.notifications.insert_one({
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'type': 'trailer_error',
            'title': 'Errore Trailer',
            'message': f'Errore generazione trailer. Costo rimborsato: ${cost:,}. Errore: {str(e)[:80]}',
            'data': {'film_id': film_id, 'path': f'/films/{film_id}', 'type': 'film'},
            'read': False,
            'created_at': datetime.now(timezone.utc).isoformat()
        })


# ==================== AI ENDPOINTS ====================

@router.post("/ai/screenplay")
async def generate_screenplay(request: ScreenplayRequest, user: dict = Depends(get_current_user)):
    logging.info(f"Screenplay generation request for: {request.title}")
    logging.info(f"EMERGENT_LLM_KEY available: {bool(EMERGENT_LLM_KEY)}")

    if not EMERGENT_LLM_KEY:
        logging.warning("No EMERGENT_LLM_KEY, returning fallback")
        return {'screenplay': f"[AI Generation unavailable] Sample screenplay for '{request.title}' - A {request.genre} film..."}

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"screenplay-{uuid.uuid4()}",
            system_message=f"You are a professional screenplay consultant. Write concise guidelines in {language}. Be brief but impactful."
        ).with_model("openai", "gpt-4o-mini")

        prompt = f"""Create a BRIEF screenplay guideline (max 300 words) for a {request.genre} film titled "{request.title}".
        Tone: {request.tone}
        Language: {language}
        {f'Creative direction from the director: {request.custom_prompt}' if request.custom_prompt else ''}
        
        Provide ONLY:
        - Logline (1-2 sentences)
        - Main conflict
        - 3-4 key plot points (bullet points)
        - Suggested ending type
        - Mood/atmosphere notes
        
        {f'IMPORTANT: Follow the directors vision: {request.custom_prompt}' if request.custom_prompt else ''}
        Keep it SHORT and practical - these are guidelines for the director, not a full screenplay."""

        logging.info(f"Generating screenplay...")
        response = await chat.send_message(UserMessage(text=prompt))
        logging.info(f"Screenplay generated successfully, length: {len(response)}")
        return {'screenplay': response}
    except Exception as e:
        logging.error(f"Screenplay generation error: {type(e).__name__}: {e}")
        return {'screenplay': f"[Sample] {request.title} - A {request.genre} story about..."}


@router.post("/ai/poster/start")
async def start_poster_generation(request: PosterRequest, user: dict = Depends(get_current_user)):
    """Start poster generation asynchronously. Returns task_id for polling."""
    task_id = str(uuid.uuid4())
    poster_tasks[task_id] = {'status': 'pending', 'poster_url': '', 'error': ''}
    logging.info(f"Poster task {task_id} started for: {request.title} ({request.genre})")

    if not request.production_house_name:
        request.production_house_name = user.get('production_house_name', '')

    if not EMERGENT_LLM_KEY:
        poster_tasks[task_id] = {'status': 'error', 'poster_url': '', 'error': 'AI key not configured'}
        return {'task_id': task_id}

    async def _generate():
        max_retries = 2
        for attempt in range(max_retries):
            try:
                from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
                user_desc = request.description or request.title
                if request.is_sequel and request.sequel_number:
                    parent = request.sequel_parent_title or request.title.split(':')[0].strip()
                    sub = request.sequel_subtitle or ''
                    prompt = (
                        f"Professional cinematic movie poster for a {request.genre} sequel film. "
                        f"This is Chapter {request.sequel_number} of the \"{parent}\" saga. "
                        f"Description: {user_desc}. "
                        f"The poster MUST include the title \"{parent.upper()}\" as large stylized text at the top, "
                        f"with the number \"{request.sequel_number}\" prominently displayed, "
                        f"and the subtitle \"{sub.upper()}\" in slightly smaller text below. "
                        f"Keep the same visual style and color palette as the original film but with a slightly different scene composition. "
                        f"Style: {request.style or 'cinematic'}, dramatic lighting, sequel movie poster, consistent saga branding."
                    )
                else:
                    prompt = (
                        f"Professional cinematic movie poster for a {request.genre} film titled \"{request.title}\". "
                        f"Description: {user_desc}. "
                        f"The poster MUST include the film title \"{request.title.upper()}\" as large, stylized text integrated into the design. "
                        f"Include a genre subtitle like \"A {request.genre.upper()} FILM\" in smaller text at the bottom. "
                        f"Style: {request.style or 'cinematic'}, dramatic lighting, high quality, professional movie poster layout with typography."
                    )
                image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
                images = await image_gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1, quality="low")
                if images and len(images) > 0:
                    from PIL import Image as PILImage
                    img = PILImage.open(BytesIO(images[0])).convert('RGB')
                    jpeg_buffer = BytesIO()
                    img.save(jpeg_buffer, format='JPEG', quality=82, optimize=True)
                    jpeg_bytes = jpeg_buffer.getvalue()
                    image_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
                    filename = f"task_{task_id}.jpg"
                    await poster_storage.save_poster(filename, jpeg_bytes, 'image/jpeg')
                    poster_file_url = f"/api/posters/{filename}"
                    logging.info(f"AI Poster task {task_id} generated with text overlay, compressed: {len(jpeg_bytes)} bytes (attempt {attempt+1})")
                    poster_tasks[task_id] = {'status': 'done', 'poster_url': poster_file_url, 'error': ''}
                    return
                logging.warning(f"Poster task {task_id} attempt {attempt+1}: No image returned")
            except Exception as e:
                logging.error(f"AI Poster task {task_id} attempt {attempt+1} error: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        poster_tasks[task_id] = {'status': 'error', 'poster_url': '', 'error': 'Generazione fallita dopo i tentativi'}
        try:
            fallback = await _generate_fallback_poster(request)
            poster_tasks[task_id] = {'status': 'done', 'poster_url': fallback['poster_url'], 'error': '', 'is_fallback': True}
            logging.info(f"Poster task {task_id}: fallback poster generated successfully")
        except Exception as fb_err:
            logging.error(f"Poster task {task_id}: fallback also failed: {fb_err}")

    asyncio.create_task(_generate())
    return {'task_id': task_id}


@router.get("/ai/poster/status/{task_id}")
async def get_poster_status(task_id: str, user: dict = Depends(get_current_user)):
    """Poll poster generation status. Checks in-memory first, then MongoDB for regen tasks."""
    task = poster_tasks.get(task_id)
    if not task:
        db_task = await db.regen_tasks.find_one({'task_id': task_id}, {'_id': 0})
        if db_task:
            result = {'status': db_task.get('status', 'pending'), 'poster_url': db_task.get('poster_url', ''), 'error': db_task.get('error', ''), 'film_id': db_task.get('film_id', '')}
            if db_task.get('status') in ('done', 'error'):
                await db.regen_tasks.delete_one({'task_id': task_id})
            return result
        return {'status': 'error', 'error': 'Task not found'}
    result = {**task}
    if task['status'] in ('done', 'error'):
        poster_tasks.pop(task_id, None)
    return result


@router.post("/ai/poster")
async def generate_poster(request: PosterRequest, user: dict = Depends(get_current_user)):
    """Generate a movie poster using GPT Image 1 (OpenAI) via Emergent LLM Key."""
    logging.info(f"Poster generation request for: {request.title} ({request.genre})")

    if not request.production_house_name:
        request.production_house_name = user.get('production_house_name', '')

    if request.force_fallback:
        return await _generate_fallback_poster(request)

    if not EMERGENT_LLM_KEY:
        return await _generate_fallback_poster(request)

    max_retries = 2
    last_error = None

    for attempt in range(max_retries):
        try:
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

            user_desc = request.description or request.title
            prompt = (
                f"Professional cinematic movie poster for a {request.genre} film titled \"{request.title}\". "
                f"Description: {user_desc}. "
                f"The poster MUST include the film title \"{request.title.upper()}\" as large, stylized text integrated into the design. "
                f"Include a genre subtitle like \"A {request.genre.upper()} FILM\" in smaller text at the bottom. "
                f"Style: {request.style or 'cinematic'}, dramatic lighting, high quality, professional movie poster layout with typography."
            )

            image_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
            images = await image_gen.generate_images(
                prompt=prompt,
                model="gpt-image-1",
                number_of_images=1,
                quality="low"
            )

            if images and len(images) > 0:
                from PIL import Image as PILImage
                img = PILImage.open(BytesIO(images[0])).convert('RGB')
                jpeg_buffer = BytesIO()
                img.save(jpeg_buffer, format='JPEG', quality=82, optimize=True)
                jpeg_bytes = jpeg_buffer.getvalue()

                image_base64 = base64.b64encode(jpeg_bytes).decode('utf-8')
                filename = f"gen_{uuid.uuid4().hex[:12]}.jpg"
                await poster_storage.save_poster(filename, jpeg_bytes, 'image/jpeg')
                poster_file_url = f"/api/posters/{filename}"
                logging.info(f"AI Poster generated with text overlay, compressed: {len(jpeg_bytes)} bytes (attempt {attempt+1})")
                return {'poster_base64': image_base64, 'poster_url': poster_file_url}

            last_error = 'No image generated'
            logging.warning(f"Poster attempt {attempt+1}: No image returned")
        except Exception as e:
            last_error = str(e)
            logging.error(f"AI Poster attempt {attempt+1} error: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2)

    try:
        return await _generate_fallback_poster(request)
    except Exception:
        return {'poster_url': '', 'error': last_error or 'Generation failed after retries'}


@router.post("/ai/translate")
async def translate_text(request: TranslationRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        return {'translated_text': request.text}

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"translate-{uuid.uuid4()}",
            system_message="You are a professional translator. Translate accurately preserving meaning and tone."
        ).with_model("openai", "gpt-5.2")

        source = lang_names.get(request.source_lang, 'English')
        target = lang_names.get(request.target_lang, 'English')

        response = await chat.send_message(UserMessage(
            text=f"Translate from {source} to {target}: {request.text}"
        ))

        return {'translated_text': response}
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return {'translated_text': request.text}


@router.post("/ai/soundtrack-description")
async def generate_soundtrack_description(request: SoundtrackRequest, user: dict = Depends(get_current_user)):
    """Generate a description for the film soundtrack."""
    logging.info(f"Soundtrack generation request for: {request.title}")
    logging.info(f"EMERGENT_LLM_KEY available: {bool(EMERGENT_LLM_KEY)}")

    if not EMERGENT_LLM_KEY:
        logging.warning("No EMERGENT_LLM_KEY, returning fallback")
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        lang_names = {'en': 'English', 'it': 'Italian', 'es': 'Spanish', 'fr': 'French', 'de': 'German'}
        language = lang_names.get(request.language, 'English')

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"soundtrack-{uuid.uuid4()}",
            system_message=f"You are a film music composer consultant. Write in {language}. Be concise."
        ).with_model("openai", "gpt-4o-mini")

        prompt = f"""Create a BRIEF soundtrack concept (max 150 words) for a {request.genre} film titled "{request.title}".
        Mood: {request.mood}
        {f'Director vision: {request.custom_prompt}' if request.custom_prompt else ''}
        
        Include:
        - Main theme description (instruments, tempo)
        - Key emotional moments to score
        - 2-3 suggested track names
        
        Keep it professional and practical."""

        logging.info(f"Generating soundtrack description...")
        response = await chat.send_message(UserMessage(text=prompt))
        logging.info(f"Soundtrack generated successfully, length: {len(response)}")
        return {'description': response}
    except Exception as e:
        logging.error(f"Soundtrack generation error: {type(e).__name__}: {e}")
        return {'description': f"An original {request.mood} soundtrack for {request.title}"}


@router.post("/ai/generate-trailer")
async def generate_trailer(request: TrailerRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """Generate a video trailer for a film using Sora 2 AI."""
    if request.duration not in [4, 8, 12]:
        request.duration = 4

    film = await db.films.find_one({'id': request.film_id, 'user_id': user['id']})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    if film.get('trailer_url') and not film.get('trailer_error'):
        return {'trailer_url': film['trailer_url'], 'status': 'exists'}

    if film.get('trailer_generating'):
        return {'status': 'generating', 'message': 'Trailer in generazione...'}

    film_rating = film.get('imdb_rating', 5.0)
    base_cost = 10000
    duration_multiplier = {4: 1.0, 8: 2.5, 12: 5.0}.get(request.duration, 1.0)
    rating_multiplier = 1.0 + (film_rating / 10.0)
    trailer_cost = int(base_cost * duration_multiplier * rating_multiplier)

    if user['funds'] < trailer_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Costo trailer: ${trailer_cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -trailer_cost}})

    await db.films.update_one({'id': request.film_id}, {
        '$set': {'trailer_generating': True, 'trailer_started_at': datetime.now(timezone.utc).isoformat(), 'trailer_cost': trailer_cost},
        '$unset': {'trailer_error': ''}
    })

    background_tasks.add_task(generate_trailer_task_sora2, request.film_id, request.style, request.duration, user['id'], trailer_cost)

    return {
        'status': 'started',
        'message': f'Generazione trailer AI avviata! Costo: ${trailer_cost:,}. Ci vorranno 2-5 minuti.',
        'film_id': request.film_id,
        'cost': trailer_cost
    }


@router.get("/ai/trailer-cost")
async def get_trailer_cost(film_id: str, duration: int = 4, user: dict = Depends(get_current_user)):
    """Get the cost preview for generating a trailer."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0, 'imdb_rating': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    film_rating = film.get('imdb_rating', 5.0)
    base_cost = 10000
    duration_multiplier = {4: 1.0, 8: 2.5, 12: 5.0}.get(duration, 1.0)
    rating_multiplier = 1.0 + (film_rating / 10.0)
    cost = int(base_cost * duration_multiplier * rating_multiplier)

    return {'cost': cost, 'duration': duration, 'film_rating': film_rating}


# ==================== TRAILER SERVING/STATUS ENDPOINTS ====================

@router.get("/trailers/{film_id}.mp4")
async def get_trailer(film_id: str):
    """Serve trailer video file."""
    new_path = f'/app/backend/static/trailers/{film_id}.mp4'
    old_path = f'/app/trailers/{film_id}.mp4'

    if os.path.exists(new_path):
        return FileResponse(new_path, media_type='video/mp4')
    elif os.path.exists(old_path):
        return FileResponse(old_path, media_type='video/mp4')

    raise HTTPException(status_code=404, detail="Trailer non trovato")


@router.get("/films/{film_id}/trailer-status")
async def get_trailer_status(film_id: str, user: dict = Depends(get_current_user)):
    """Check trailer generation status."""
    film_exists = await db.films.find_one({'id': film_id}, {'_id': 0, 'id': 1})
    if not film_exists:
        raise HTTPException(status_code=404, detail="Film non trovato")

    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'trailer_url': 1, 'trailer_generating': 1, 'trailer_error': 1, 'trailer_started_at': 1})

    is_generating = film.get('trailer_generating', False) if film else False
    if is_generating and film.get('trailer_started_at'):
        started_at = datetime.fromisoformat(film['trailer_started_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) - started_at > timedelta(minutes=15):
            await db.films.update_one(
                {'id': film_id},
                {'$set': {'trailer_generating': False, 'trailer_error': 'Generazione scaduta. Puoi riprovare.'}}
            )
            is_generating = False

    return {
        'has_trailer': bool(film.get('trailer_url') if film else False),
        'trailer_url': film.get('trailer_url') if film else None,
        'generating': is_generating,
        'error': film.get('trailer_error') if film else None
    }


@router.post("/films/{film_id}/reset-trailer")
async def reset_stuck_trailer(film_id: str, user: dict = Depends(get_current_user)):
    """Reset a stuck trailer generation. Owner only."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0, 'trailer_generating': 1})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato o non sei il proprietario")

    if not film.get('trailer_generating'):
        return {'status': 'ok', 'message': 'Il trailer non era bloccato'}

    await db.films.update_one(
        {'id': film_id},
        {'$set': {'trailer_generating': False, 'trailer_error': 'Generazione resettata. Puoi riprovare.'}}
    )

    return {'status': 'ok', 'message': 'Trailer resettato. Puoi riprovare la generazione.'}


# ==================== POSTER ENDPOINTS ====================

@router.get("/films/{film_id}/poster")
async def get_film_poster(film_id: str):
    """Return film poster as binary image for efficient loading."""
    film = await db.films.find_one({'id': film_id}, {'_id': 0, 'poster_url': 1})
    if not film or not film.get('poster_url'):
        raise HTTPException(status_code=404, detail="Poster non trovato")
    poster_url = film['poster_url']
    if poster_url.startswith('data:image/'):
        header, b64data = poster_url.split(',', 1)
        media_type = header.split(':')[1].split(';')[0]
        image_bytes = base64.b64decode(b64data)
        return Response(content=image_bytes, media_type=media_type, headers={"Cache-Control": "public, max-age=86400"})
    from starlette.responses import RedirectResponse
    return RedirectResponse(url=poster_url)


@router.post("/series/{series_id}/generate-poster")
@router.post("/anime/{series_id}/generate-poster")
async def regenerate_series_poster(series_id: str, user: dict = Depends(get_current_user)):
    """Generate/regenerate poster for a series or anime."""
    series = await db.tv_series.find_one({'id': series_id, 'user_id': user['id']}, {'_id': 0})
    if not series:
        raise HTTPException(status_code=404, detail="Serie non trovata")

    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        raise HTTPException(status_code=500, detail="Servizio generazione immagini non disponibile")

    try:
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        img_gen = OpenAIImageGeneration(api_key=key)

        is_anime = series.get('type') == 'anime'
        style = "anime art style, vibrant colors, dramatic composition" if is_anime else "cinematic TV show poster style, professional photography, dramatic lighting"
        genre_name = series.get('genre_name', series.get('genre', 'drama'))
        prompt = f"TV series poster for '{series['title']}', {genre_name} {'anime' if is_anime else 'TV series'}. {style}. No text or titles in the image."

        images = await img_gen.generate_images(prompt=prompt, model="gpt-image-1", number_of_images=1)

        if images:
            from PIL import Image as PILImage
            import io
            img = PILImage.open(io.BytesIO(images[0]))
            img = img.resize((400, 600), PILImage.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, 'PNG', optimize=True)
            filename = f"series_{series_id}.png"
            await poster_storage.save_poster(filename, buf.getvalue(), 'image/png')
            poster_url = f"/api/posters/{filename}"
            await db.tv_series.update_one(
                {'id': series_id},
                {'$set': {'poster_url': poster_url, 'updated_at': datetime.now(timezone.utc).isoformat()}}
            )
            return {"poster_url": poster_url, "message": "Locandina generata!"}
        raise HTTPException(status_code=500, detail="Nessuna immagine generata")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Series poster generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore generazione poster: {str(e)}")


@router.post("/films/{film_id}/regenerate-poster")
async def regenerate_film_poster(film_id: str, user: dict = Depends(get_current_user)):
    """Start async poster regeneration using the film's screenplay/plot. Returns task_id for polling."""
    film = await db.films.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        film = await db.film_projects.find_one({'id': film_id, 'user_id': user['id']}, {'_id': 0})
    if not film:
        raise HTTPException(status_code=404, detail="Film non trovato")

    title = film.get('title', 'Film')
    genre = film.get('genre') or film.get('genre_name') or 'drama'
    screenplay = film.get('screenplay', '')
    plot_summary = screenplay[:300] if screenplay else title
    cast_names = film.get('cast_names', [])[:5] if film.get('cast_names') else []
    prod_house = user.get('production_house_name', '')

    task_id = str(uuid.uuid4())
    poster_tasks[task_id] = {'status': 'pending', 'poster_url': '', 'error': '', 'film_id': film_id}

    async def _regen():
        try:
            poster_req = PosterRequest(
                title=title, genre=genre, description=plot_summary,
                style='cinematic', cast_names=cast_names,
                production_house_name=prod_house, force_fallback=False,
                is_sequel=film.get('is_sequel', False),
                sequel_number=film.get('sequel_number'),
                sequel_subtitle=film.get('subtitle', ''),
                sequel_parent_title=film.get('sequel_parent_title', ''),
            )

            result = None
            for attempt in range(2):
                try:
                    result = await generate_poster(poster_req, user)
                    if result and result.get('poster_url'):
                        break
                    logging.warning(f"Poster gen attempt {attempt+1} returned empty, retrying...")
                except Exception as retry_err:
                    logging.warning(f"Poster gen attempt {attempt+1} failed: {retry_err}")
                    if attempt == 0:
                        await asyncio.sleep(2)

            new_url = result.get('poster_url', '') if result else ''

            if not new_url:
                logging.info("AI poster failed, using fallback...")
                try:
                    poster_req_fallback = PosterRequest(
                        title=title, genre=genre, description=plot_summary,
                        style='cinematic', cast_names=cast_names,
                        production_house_name=prod_house, force_fallback=True,
                        is_sequel=film.get('is_sequel', False),
                        sequel_number=film.get('sequel_number'),
                        sequel_subtitle=film.get('subtitle', ''),
                        sequel_parent_title=film.get('sequel_parent_title', ''),
                    )
                    fallback_result = await generate_poster(poster_req_fallback, user)
                    new_url = fallback_result.get('poster_url', '') if fallback_result else ''
                except Exception as fb_err:
                    logging.error(f"Fallback poster also failed: {fb_err}")

            if new_url:
                await db.films.update_one({'id': film_id}, {'$set': {'poster_url': new_url}})
                await db.film_projects.update_one({'id': film_id}, {'$set': {'poster_url': new_url}})
                poster_tasks[task_id] = {'status': 'done', 'poster_url': new_url, 'error': '', 'film_id': film_id}
                await db.regen_tasks.update_one({'task_id': task_id}, {'$set': {'status': 'done', 'poster_url': new_url}})
            else:
                err_msg = 'Generazione fallita dopo retry + fallback'
                poster_tasks[task_id] = {'status': 'error', 'poster_url': '', 'error': err_msg, 'film_id': film_id}
                await db.regen_tasks.update_one({'task_id': task_id}, {'$set': {'status': 'error', 'error': err_msg}})
        except Exception as e:
            logging.error(f"Regenerate poster error: {e}")
            poster_tasks[task_id] = {'status': 'error', 'poster_url': '', 'error': str(e), 'film_id': film_id}
            await db.regen_tasks.update_one({'task_id': task_id}, {'$set': {'status': 'error', 'error': str(e)}})

    await db.regen_tasks.insert_one({'task_id': task_id, 'film_id': film_id, 'status': 'pending', 'poster_url': '', 'error': ''})
    asyncio.create_task(_regen())
    return {'task_id': task_id}
