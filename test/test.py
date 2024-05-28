# git clone https://github.com/turboderp/exllamav2
# cd exllamav2
# pip install -r requirements.txt
# pip install .
# pip install exllamav2
# pip uninstall -y transformers
# pip install git+https://github.com/huggingface/transformers

from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache_Q4,
    ExLlamaV2Tokenizer,
)

from exllamav2.generator import ExLlamaV2BaseGenerator, ExLlamaV2Sampler


batch_size = 1
cache_max_seq_len = -1

# model_directory = "/Volumes/training/llm/model_snapshots/models--bartowski--Phi-3-medium-4k-instruct-exl2-6.5/"
model_directory = r"C:\Users\okozk\Test\Gradio\test\Phi-3-medium-4k-instruct-exl2-6.5"

config = ExLlamaV2Config(model_directory)

model = ExLlamaV2(config)
print("Loading model: " + model_directory)

cache = ExLlamaV2Cache_Q4(
    model,
    lazy=True,
    batch_size=batch_size,
    max_seq_len=cache_max_seq_len,
) 
model.load_autosplit(cache)

tokenizer = ExLlamaV2Tokenizer(config)
generator = ExLlamaV2BaseGenerator(model, cache, tokenizer)

# サンプリングの設定
settings = ExLlamaV2Sampler.Settings()
settings.temperature = 0.0
settings.top_k = 50
settings.top_p = 0.9
settings.token_repetition_penalty = 1.05

max_new_tokens = 400

# 今回推論する内容
prompts = [
    """「今回は、VTube Studioを使ってAI Tuberを作る方法ということで」の文章の数字と英語表記の文字部分を、全てカタカナ表記の読みに直してください。

# 例
（訂正前）Amazon Sagemakerで Stable Diffusion を動かす方法を解説します。 
（訂正後）アマゾンセージメーカーで ステイブル ディフュージョン を動かす方法を解説します。 
※（訂正後）の文章のみを出力すること。""",
]

# パディングを最小化するために文字列サイズでソート
s_prompts = sorted(prompts, key=len)

# プロンプトを整形
def format_prompt(sp, p):
    return f"<|user|>\n{sp}{p} <|end|>\n<|assistant|>"


# 適当
system_prompt = "あなたは日本語を話すAIアシスタントです。"

f_prompts = [format_prompt(system_prompt, p) for p in s_prompts]

# 生計済みプロンプトをバッチに分割
batches = [f_prompts[i : i + batch_size] for i in range(0, len(prompts), batch_size)]

collected_outputs = []
for b, batch in enumerate(batches):
    print(f"Batch {b + 1} of {len(batches)}...")

    outputs = generator.generate_simple(
        batch,
        settings,
        max_new_tokens,
        seed=1234,
        add_bos=True,
        completion_only=True,
    )

    collected_outputs += outputs

# 結果出力
for q, a in zip(s_prompts, collected_outputs):
    print("---------------------------------------")
    print("Q: " + q)
    print("A: " + a.strip())
