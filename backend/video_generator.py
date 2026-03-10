# CineWorld Studio's - Video Generation System
# Generates ceremony recap videos using FFmpeg (free)

import os
import asyncio
import base64
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import tempfile
import shutil

async def generate_ceremony_video(
    ceremony_data: Dict[str, Any],
    audio_clips: List[Dict[str, Any]],
    output_path: str,
    language: str = 'it'
) -> Optional[str]:
    """
    Generate a video recap of the ceremony using FFmpeg.
    
    Args:
        ceremony_data: Festival/ceremony information
        audio_clips: List of {audio_base64, text, winner_name, category_name, duration}
        output_path: Where to save the final video
        language: Language for subtitles
    
    Returns:
        Path to generated video or None if failed
    """
    temp_dir = tempfile.mkdtemp(prefix='ceremony_video_')
    
    try:
        # Create temporary files for audio clips
        audio_files = []
        subtitle_entries = []
        current_time = 0
        
        for i, clip in enumerate(audio_clips):
            # Save audio to temp file
            audio_data = base64.b64decode(clip['audio_base64'])
            audio_path = os.path.join(temp_dir, f'audio_{i}.mp3')
            with open(audio_path, 'wb') as f:
                f.write(audio_data)
            audio_files.append(audio_path)
            
            # Calculate duration (estimate 3 seconds per 10 words)
            text = clip.get('text', '')
            word_count = len(text.split())
            duration = max(3, word_count * 0.3)  # At least 3 seconds
            
            # Create subtitle entry (SRT format)
            start_time = format_srt_time(current_time)
            end_time = format_srt_time(current_time + duration)
            subtitle_entries.append(f"{i+1}\n{start_time} --> {end_time}\n{text}\n")
            
            current_time += duration + 1  # 1 second pause between announcements
        
        # Write subtitle file
        subtitle_path = os.path.join(temp_dir, 'subtitles.srt')
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(subtitle_entries))
        
        # Create audio list file for FFmpeg concat
        audio_list_path = os.path.join(temp_dir, 'audio_list.txt')
        with open(audio_list_path, 'w') as f:
            for audio_path in audio_files:
                f.write(f"file '{audio_path}'\n")
        
        # Concatenate all audio files
        combined_audio_path = os.path.join(temp_dir, 'combined_audio.mp3')
        concat_cmd = f"ffmpeg -y -f concat -safe 0 -i {audio_list_path} -c copy {combined_audio_path}"
        
        process = await asyncio.create_subprocess_shell(
            concat_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg audio concat failed: {stderr.decode()}")
            # Try alternative method
            combined_audio_path = audio_files[0] if audio_files else None
        
        if not combined_audio_path or not os.path.exists(combined_audio_path):
            logging.error("No audio file available")
            return None
        
        # Create background image (gradient with text)
        bg_image_path = os.path.join(temp_dir, 'background.png')
        festival_name = ceremony_data.get('festival_name', 'Awards Ceremony')
        
        # Generate background with FFmpeg
        bg_cmd = (
            f"ffmpeg -y -f lavfi -i 'color=c=0x1a1a1a:s=1920x1080:d=1' "
            f"-vf \"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"text='{festival_name}':fontcolor=gold:fontsize=72:x=(w-text_w)/2:y=100,"
            f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"text='Award Ceremony':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=200\" "
            f"-frames:v 1 {bg_image_path}"
        )
        
        process = await asyncio.create_subprocess_shell(
            bg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        # If background generation failed, create a simple black background
        if not os.path.exists(bg_image_path):
            simple_bg_cmd = f"ffmpeg -y -f lavfi -i 'color=c=black:s=1920x1080:d=1' -frames:v 1 {bg_image_path}"
            process = await asyncio.create_subprocess_shell(
                simple_bg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        
        # Get audio duration
        probe_cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {combined_audio_path}"
        process = await asyncio.create_subprocess_shell(
            probe_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        audio_duration = float(stdout.decode().strip()) if stdout else 60
        
        # Generate final video with background, audio, and subtitles
        video_cmd = (
            f"ffmpeg -y -loop 1 -i {bg_image_path} -i {combined_audio_path} "
            f"-vf \"subtitles={subtitle_path}:force_style='FontSize=28,Alignment=2,MarginV=50,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2'\" "
            f"-c:v libx264 -tune stillimage -c:a aac -b:a 192k "
            f"-pix_fmt yuv420p -shortest -t {audio_duration + 2} {output_path}"
        )
        
        process = await asyncio.create_subprocess_shell(
            video_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logging.error(f"FFmpeg video generation failed: {stderr.decode()}")
            # Try simpler version without subtitles
            simple_video_cmd = (
                f"ffmpeg -y -loop 1 -i {bg_image_path} -i {combined_audio_path} "
                f"-c:v libx264 -tune stillimage -c:a aac -b:a 192k "
                f"-pix_fmt yuv420p -shortest -t {audio_duration + 2} {output_path}"
            )
            process = await asyncio.create_subprocess_shell(
                simple_video_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        
        if os.path.exists(output_path):
            logging.info(f"Ceremony video generated: {output_path}")
            return output_path
        else:
            logging.error("Video file not created")
            return None
            
    except Exception as e:
        logging.error(f"Video generation error: {e}")
        return None
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass


def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


async def cleanup_old_videos(db, days: int = 3):
    """Remove videos older than specified days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Find old ceremony videos
    old_videos = await db.ceremony_videos.find({
        'created_at': {'$lt': cutoff.isoformat()}
    }).to_list(100)
    
    deleted_count = 0
    for video in old_videos:
        video_path = video.get('video_path')
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
                deleted_count += 1
            except:
                pass
        
        await db.ceremony_videos.delete_one({'id': video['id']})
    
    logging.info(f"Cleaned up {deleted_count} old ceremony videos")
    return deleted_count
