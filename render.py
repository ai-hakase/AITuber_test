from dataclasses import dataclass
from typing import Tuple

@dataclass
class FrameData:
    character_name: str
    subtitle_line: str
    reading_line: str
    reading_speed: float
    selected_model: Tuple[str, str, str]
    voice_style: str
    voice_style_strength: float
    audio_file: str
    emotion_shortcut: str
    motion_shortcut: str
    explanation_media_path: str
    whiteboard_image_path: str
    subtitle_image_path: str
    preview_image: str
    audio_duration: float = 0.0,
    frame_clips = None,
    bgm_path: str = None,
    background_media_path: str = None,
