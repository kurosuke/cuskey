"""
PIN コード送信キーボード
シングルクリックで登録された PIN コードを自動送信
MODE A と MODE B で 2 種類の PIN を設定可能
"""

import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# =============================================================================
# ===================== ここから設定エリア =====================
# =============================================================================

# MODE A の PIN コード（スイッチ ON の時）
# 各桁を文字列で指定。例：["1", "2", "3", "4"] = 1234
PIN_MODE_A = ["1", "2", "3", "4"]  # 変更してください

# MODE B の PIN コード（スイッチ OFF の時）
# 各桁を文字列で指定。例：["5", "6", "7", "8"] = 5678
PIN_MODE_B = ["5", "6", "7", "8"]  # 変更してください

# 各桁間の送信間隔（秒）
DIGIT_INTERVAL = 0.1

# PIN 送信前に SPACE → BACKSPACE を送信してフォーカスをリセットするか
PRE_SEND_ESCAPE = True

# SPACE/BACKSPACE 送信後の待機時間（秒）
PRE_SEND_DELAY = 1.0

# PIN コード送信後に ENTER を送信するか
POST_SEND_ENTER = False

# チャタリング防止の待機時間（秒）
DEBOUNCE_TIME = 0.05

# CPU サイクル待機時間（秒）
LOOP_DELAY = 0.01

# =============================================================================
# ===================== ここまで設定エリア =====================
# =============================================================================

# ボード設定をインポート
import cuskey_settings

#
# ボード設定の取得
#
pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

#
# USB キーボードの初期化
#
keyboard = Keyboard(usb_hid.devices)

#
# モード切替ピンの初期化
#
# モード切替用 GND ピンの設定
if pins["mode_gnd"]:
    gnd_pin = digitalio.DigitalInOut(pins["mode_gnd"])
    gnd_pin.direction = digitalio.Direction.OUTPUT
    gnd_pin.value = False  # GND（Low）に設定

# MODE_A ピンの設定
mode_a = digitalio.DigitalInOut(pins["mode_a"])
mode_a.direction = digitalio.Direction.INPUT
mode_a.pull = digitalio.Pull.UP

#
# ボタンピンの初期化
#
# ボタン用 GND ピンの設定
if pins["button_gnd"]:
    button_gnd = digitalio.DigitalInOut(pins["button_gnd"])
    button_gnd.direction = digitalio.Direction.OUTPUT
    button_gnd.value = False  # GND（Low）に設定

# ボタン入力ピンの設定
button = digitalio.DigitalInOut(pins["button"])
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

#
# 状態管理変数の初期化
#
last_button_state = True  # プルアップなので通常は True


def send_pin(pin_code, mode_label):
    """PIN コードを送信する関数"""
    print(f"{mode_label} PIN コード送信開始: {''.join(pin_code)}")

    # PIN 送信前に SPACE → BACKSPACE を送信してフォーカスをリセット
    if PRE_SEND_ESCAPE:
        print("  SPACE → BACKSPACE 送信中...")
        keyboard.send(Keycode.SPACE)
        keyboard.send(Keycode.BACKSPACE)
        print(f"  {PRE_SEND_DELAY} 秒待機中...")
        time.sleep(PRE_SEND_DELAY)

    for digit in pin_code:
        # 数字キーを送信
        if digit.isdigit():
            keycode = Keycode(int(digit))
            keyboard.send(keycode)
        else:
            # 数字以外の文字は対応していないことを警告
            print(f"  警告：'{digit}' は数字ではないため送信できません")
        
        # 各桁間の待機
        time.sleep(DIGIT_INTERVAL)
    
    # PIN 送信後に ENTER を送信
    if POST_SEND_ENTER:
        print("  ENTER 送信中...")
        keyboard.send(Keycode.ENTER)

    print(f"{mode_label} PIN コード送信完了")


#
# 起動メッセージ
#
print(f"=== {board_name} PIN コード送信キーボード起動 ===")
print(f"ボードタイプ：{cuskey_settings.BOARD_TYPE}")
print(f"デバッグモード：{features['debug_enabled']}")
print("-" * 50)
print("【設定された PIN コード】")
print(f"  Mode A（スイッチ ON）: {''.join(PIN_MODE_A)}")
print(f"  Mode B（スイッチ OFF）: {''.join(PIN_MODE_B)}")
print("-" * 50)
print("【操作方法】")
print("  - ボタンをシングルクリック")
print("    * Mode A: PIN_MODE_A を送信")
print("    * Mode B: PIN_MODE_B を送信")
print("-" * 50)

#
# メインループ
#
while True:
    # ボタンの現在の状態を読み取り
    current_button_state = button.value
    
    # ボタンが押された瞬間を検出（High → Low）
    if last_button_state and not current_button_state:
        # チャタリング防止のため少し待機
        time.sleep(DEBOUNCE_TIME)
        
        # 現在のモードを取得
        current_mode = mode_a.value
        
        if features["debug_enabled"]:
            print(f"[DEBUG] ボタンが押されました (mode_a.value = {current_mode})")
        else:
            print("ボタンが押されました")
        
        # モードに応じて PIN コードを送信
        if current_mode == False:  # Mode A（スイッチが GND に接続）
            send_pin(PIN_MODE_A, "[Mode A]")
        else:  # Mode B（スイッチが開いている）
            send_pin(PIN_MODE_B, "[Mode B]")
        
        # チャタリング防止のため少し待機
        time.sleep(DEBOUNCE_TIME)
    
    # 前回の状態を更新
    last_button_state = current_button_state
    
    # CPU 負荷軽減のため短時間待機
    time.sleep(LOOP_DELAY)

"""
============================================================================
【使い方】

1. CircuitPython がインストールされた Raspberry Pi Pico を準備

2. 必要なライブラリのコピー
   - Adafruit_CircuitPython_HID フォルダ内の adafruit_hid フォルダを Pico にコピー
   - cuskey_settings.py を Pico にコピー

3. このファイルを Pico にコピー
   - pin_sender.py という名前で Pico のルートディレクトリに保存
   - 自動起動させたい場合は、code.py という名前に変更

4. PIN コードの設定（プログラムの上部で変更）
   - PIN_MODE_A: Mode A で送信する PIN コード
     例：PIN_MODE_A = ["1", "2", "3", "4"]  # 1234 を送信
   
   - PIN_MODE_B: Mode B で送信する PIN コード
     例：PIN_MODE_B = ["5", "6", "7", "8"]  # 5678 を送信

5. 動作確認
   - Pico を接続すると自動的にプログラムが起動
   - シリアルモニタで動作状況を確認可能（Mu Editor、Thonny 等）

6. 操作方法
   - セルフロックスイッチで Mode A/B を切り替え
   - ボタンをシングルクリックすると、現在のモードの PIN コードを送信

7. 設定のカスタマイズ
   - DIGIT_INTERVAL: 各桁間の送信間隔（デフォルト 0.1 秒）
     遅い場合は小さく、早すぎる場合は大きく調整
   
   - DEBOUNCE_TIME: チャタリング防止の待機時間（デフォルト 0.05 秒）
   
   - LOOP_DELAY: メインループの待機時間（デフォルト 0.01 秒）

============================================================================
【セキュリティ上の注意】

⚠️ このプログラムは PIN コードを平文で保存します。
   - Pico のファイルシステムは暗号化されていません
   - 物理アクセス可能な人が PIN コードを閲覧できます
   
⚠️ 重要な PIN コード（銀行、セキュリティなど）はこの方法で管理しないでください。
   - パスワードマネージャーを使用することを推奨します

============================================================================
【更新履歴】

■ 初期バージョン
  - シングルクリックで PIN コード送信機能を実装
  - Mode A/B で 2 種類の PIN を設定可能
  - プログラム上部でわかりやすく設定可能に

============================================================================
"""