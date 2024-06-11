from moviepy.editor import VideoFileClip

# 動画ファイルのパス
video_path = "Asset/sample_video.mp4"

# GIFの出力パス
gif_path = "Asset/sample_video.gif"

# 動画を読み込む
clip = VideoFileClip(video_path)

# 動画をGIFに変換
clip.write_gif(gif_path, fps=16)

print(f"GIF saved to: {gif_path}")
