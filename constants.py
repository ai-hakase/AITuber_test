import os

TALK_CHARACTER = "〇〇"
TALKING = "話し方"
WAITING = "待機"
EMOTIONS = ['joy、うれしい', 'sadness、悲しい', 'anticipation、期待', 'surprise、驚き', 'anger、怒り', 'fear、恐れ', 'disgust、嫌悪', 'trust、信頼']
DEFAULT_SETTINGS_FOLDER = "settings"
DEFAULT_SETTING_FILE = os.path.join(DEFAULT_SETTINGS_FOLDER, "default_setting.json")
DEFAULT_OUTPUTS_FOLDER = "outputs"
BGM_FOLDER = "bgm"
BACKGROUND_VIDEO_FOLDER = "background_video"
DEFAULT_BGM = "bgm\default_bgm.wav"
DEFAULT_BACKGROUND_VIDEO = "background_video\default_video.mp4"
VTUBE_STUDIO_URI = "ws://127.0.0.1:8001"
# VTUBE_STUDIO_URI = "ws://localhost:8001"
PLUGIN_NAME = "AI Tuber Test Program"
PLUGIN_DEVELOPER = "AI-Hakase"
