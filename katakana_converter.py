import sys
import os
import json
import pykakasi
import re
from pygtrie import CharTrie
from cachetools import cached, TTLCache
from constants import DEFAULT_SETTING_FILE


# キャッシュの設定 (有効期限1週間)
cache = TTLCache(maxsize=100, ttl=604800)  # 最大100個のキャッシュを保持


class KatakanaConverter:
    def __init__(self):

        # self.trie = None
        self.registered_words_table = self.split_words()  # 辞書を更新
        self.trie = CharTrie(self.registered_words_table)  # Trie木を作成

        # pykakasi
        self.kakasi = pykakasi.kakasi()
        self.kakasi.setMode("H", "K")  # Hiragana to Katakana
        self.kakasi.setMode("J", "K")  # Kanji to Katakana
        self.converter = self.kakasi.getConverter()



    def split_words(self):
        """半角スペースで区切られた単語を分割し、重複を避けて辞書に追加・設定ファイルを更新する関数"""

        # 設定ファイルの読み込み
        with open(DEFAULT_SETTING_FILE, "r", encoding="utf-8") as f:
            self.settings = json.load(f)
            words_table = self.settings["dics"]
    
        # 辞書を取得
        for words, katakana in words_table.copy().items():  # 辞書のコピーに対してループ
            if " " in katakana:  # カタカナ表記にスペースが含まれている場合
                katakana_list = katakana.split()  # カタカナ表記を分割
                words_list = words.split()  # アルファベット表記を分割

                if len(katakana_list) == len(words_list):  # 分割された要素数が一致する場合のみ処理
                    for word, kana in zip(words_list, katakana_list):
                        if word not in words_table:  # 重複を避ける
                            words_table[word] = kana

                    del words_table[words]  # 元のキーを削除

        self.update_dics(words_table)
        return words_table


    def update_dics(self, words_table):
        """辞書を更新する関数"""
        with open(DEFAULT_SETTING_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        settings["dics"] = words_table  # 辞書部分を更新

        # 設定ファイルを更新
        with open(DEFAULT_SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        # self.registered_words_table = words_table
        self.registered_words_table = words_table
        self.trie = CharTrie(words_table)  # Trie木を作成


    def add_word_reading(self, word_input, word_reading_input):
        """
        単語と読み方を辞書に追加し、設定ファイルを更新する関数
        """
        # 入力チェック
        if not word_input or not word_reading_input:
            print("単語と読み方を両方入力してください。")

        with open(DEFAULT_SETTING_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        # 辞書に単語と読み方を追加
        settings["dics"][word_input] = word_reading_input
        # print(f'settings["dics"]: {settings["dics"]}')

        # 設定ファイルを更新
        with open(DEFAULT_SETTING_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)

        # return f"単語 '{word_input}' と読み方 '{word_reading_input}' を追加しました。"



    @cached(cache)
    def translate_to_katakana(self, text):
        """アルファベットの連続した部分をカタカナに変換する関数 (pykakasi)"""

        def replace_alphabet(match):
            word = match.group()
            return self.trie.longest_prefix(word).value or self.converter.do(word)

        return re.sub(r'[a-zA-Z]+', replace_alphabet, text)  # アルファベットの連続を置換