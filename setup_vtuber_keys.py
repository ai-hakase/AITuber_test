import torch
import random

from transformers import AutoTokenizer, LukeConfig, AutoModelForSequenceClassification
from constants import TALKING, WAITING, EMOTIONS


# デバイスの設定
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {DEVICE}")

# 感情分析モデルの準備
tokenizer = AutoTokenizer.from_pretrained("Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime")
config = LukeConfig.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', output_hidden_states=True)
model = AutoModelForSequenceClassification.from_pretrained('Mizuiro-sakura/luke-japanese-large-sentiment-analysis-wrime', config=config)
model.to(DEVICE)


class SetupVtuberKeys:

    def __init__(self):
        self.previous_motion_shortcut = None
        self.sub_previous_motion_shortcut = None


    # 感情分析を行う関数
    def analyze_sentiment(self, text):
        # テキストの感情分析を行い、感情ラベルを返す
        token = tokenizer(text, truncation=True, max_length=512, padding="max_length")
        input_ids = torch.tensor(token['input_ids']).unsqueeze(0).to(DEVICE)
        attention_mask = torch.tensor(token['attention_mask']).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            output = model(input_ids, attention_mask)
        max_index = torch.argmax(output.logits)
        return EMOTIONS[max_index]


    # ランダムにキーを選択する関数
    def press_random_key(self, action_list, last_key):
        """
        同じキーを続けて押さないように、ランダムにキーを選択する関数
        """
        keys = [key for _, key in action_list]
        if len(keys) > 1 and last_key in keys:
            keys.remove(last_key)
        return random.choice(keys) if keys else last_key


    # 感情分析を行い、表情と動作のショートカットキーを取得。ショートカットキーをランダムに選択する関数
    def get_shortcut_key(self, emotion_shortcuts, actions, character, line):
        """
        ショートカットキーをランダムにキーを選択する関数
        """
        if character == "葉加瀬あい":
        # if character == self.main_character:
            emotion = self.analyze_sentiment(line)
            emotion_shortcut = emotion_shortcuts.get(emotion)#EX ->  "anger、怒り": ["angry","cheekpuff"],

            # 感情ラベルに対応するショートカットキーをランダムに選択
            selected_emotion_shortcut = random.choice(emotion_shortcut)

            # # 前回の感情と同じならNoneを追加
            # if selected_emotion_shortcut != previous_emotion_shortcut:
            #     previous_emotion_shortcut = selected_emotion_shortcut
            # else:
            #     selected_emotion_shortcut = None


            motion_shortcut = actions[TALKING]# ["Motion_1","Motion_2","Motion_3","Motion_default"],

            selected_motion_shortcut = random.choice(motion_shortcut)
            if selected_motion_shortcut != self.previous_motion_shortcut:
                self.previous_motion_shortcut = selected_motion_shortcut
            else:
                selected_motion_shortcut = None  # 前回と同じならNoneを追加

            # motion_shortcut = self.press_random_key(actions[TALKING], self.last_motion_shortcut[self.main_character])
            # self.last_motion_shortcut[self.main_character] = motion_shortcut

            # if line in "バイバイ" or "またね" or "ばいばい" or "さようなら" or "バイバーイ" or "さよなら":
            #     motion_shortcut = actions[BAYBAY]
            # else:
                # motion_shortcut = actions[TALKING]
                
            # motion_shortcut = self.press_random_key(actions[TALKING], self.last_motion_shortcut[self.main_character])
            # self.last_motion_shortcut[self.main_character] = motion_shortcut

        else:
            # selected_emotion_shortcut = emotion_shortcuts.get('anticipation、期待')
            selected_emotion_shortcut = None
            motion_shortcut = actions[WAITING]
            # motion_shortcut = self.press_random_key(actions[WAITING], self.last_motion_shortcut["other"])
            # self.last_motion_shortcut["other"] = motion_shortcut

            selected_motion_shortcut = random.choice(motion_shortcut)
            if selected_motion_shortcut != self.sub_previous_motion_shortcut:
                self.sub_previous_motion_shortcut = selected_motion_shortcut
            else:
                selected_motion_shortcut = None  # 前回と同じならNoneを追加


        return selected_emotion_shortcut, selected_motion_shortcut
