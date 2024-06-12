# AI Tuber 動画編集プログラム

このプロジェクトは、CSVファイルに記述されたキャラクターとセリフの情報を元に、感情分析を行い、表情や動作のショートカットキーを自動的に入力することで、AI Tuberの動画を生成するプログラムです。

## 最終的な出力イメージ

![sample_video](Asset/chrome-capture-2024-6-12.gif)

## スクリーンショット

![プロジェクトのスクリーンショット1](Asset/sample_image(1).png)

![プロジェクトのスクリーンショット2](Asset/sample_image(2).png)


## 設計書

[https://xmind.app/m/FQAkZ2/](https://xmind.app/m/FQAkZ2)
![プロジェクトのスクリーンショット1](Asset/sample_image(1).png)

![プロジェクトのスクリーンショット2](Asset/sample_image(2).png)


## 設計書

[https://xmind.app/m/FQAkZ2/](https://xmind.app/m/FQAkZ2)

## 機能

- CSVファイルからキャラクターとセリフの情報を読み込む
- 感情分析を行い、セリフに合った表情や動作のショートカットキーを選択する
- 読み上げ音声ファイルを生成する
- 解説画像を生成する
- 選択されたBGMと背景動画を使用して、最終的な動画ファイルを生成する
- ユーザーインターフェースを提供し、設定の変更や動画生成の実行が可能

## 必要条件

- Python 3.x
- PyTorch
- transformers
- gradio
- pyautogui
- pygame
- requests

## インストール

1. リポジトリをクローンまたはダウンロードします。
```
git clone https://github.com/ai-hakase/AITuber_test.git
```

2. 必要なPythonパッケージをインストールします。
```
python -m venv myenv
python -m venv myenv
venv\Scripts\activate
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
<!-- または pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -->
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
<!-- または pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -->
pip install -r requirements.txt
```

※ 書き出し
```
pip freeze > requirements.txt
```

※ 書き出し
```
pip freeze > requirements.txt
```

## 使用方法

1. `main.py`ファイルを開き、必要に応じて設定を変更します。
   - `TALK_CHARACTER`: メインキャラクターの名前
   - `DEFAULT_SETTING_FOLDER`: 設定ファイルの保存先フォルダ
   - `DEFAULT_SETTING_FILE`: デフォルトの設定ファイルのパス

2. `python main.py`を実行して、Gradioアプリケーションを起動します。

3. Webブラウザで`http://127.0.0.1:7860`にアクセスします。

4. CSVファイル、BGMファイル、背景動画ファイルを選択します。

5. Live2D立ち上げ、00FF00 に背景を設定。API、バーチャルカメラを有効化しメインキャラクター名と音声合成モデルを選択します。
5. Live2D立ち上げ、00FF00 に背景を設定。API、バーチャルカメラを有効化しメインキャラクター名と音声合成モデルを選択します。

6. 必要に応じて、感情とアクションのショートカットキーを更新します。

7. 動画出力フォルダを指定します。

8. 「動画生成」ボタンをクリックして、動画の生成を開始します。

9. 生成された動画ファイルが指定されたフォルダに保存されます。

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 貢献

プルリクエストや改善提案は歓迎します。問題やバグがある場合は、Issueを作成してください。

## Memo

OBS Studioの設定

OBS Studioを起動します。
シーンを作成し、必要なソース（背景画像、動画、音声）をシーンに追加します。
音声ソースは入力のみで出力しない設定にしておきます。


OBS WebSocketの設定

OBS StudioにWebSocketプラグインをインストールします。
WebSocketサーバーのIPアドレス、ポート、パスワードを設定します。
PythonスクリプトからOBS StudioのWebSocketサーバーに接続します。
https://github.com/obsproject/obs-websocket/releases


## Memo

OBS Studioの設定

OBS Studioを起動します。
シーンを作成し、必要なソース（背景画像、動画、音声）をシーンに追加します。
音声ソースは入力のみで出力しない設定にしておきます。


OBS WebSocketの設定

OBS StudioにWebSocketプラグインをインストールします。
WebSocketサーバーのIPアドレス、ポート、パスワードを設定します。
PythonスクリプトからOBS StudioのWebSocketサーバーに接続します。
https://github.com/obsproject/obs-websocket/releases

