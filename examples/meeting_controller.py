"""
リモート会議用コントローラー
シングルクリック：マイクミュート切り替え
長押し：音量アップ/ダウン（モードで切り替え）
Zoom、Teams、Google Meet などで使用可能
"""

import digitalio
import time
import usb_hid
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# =============================================================================
# ===================== ここから設定エリア =====================
# =============================================================================

# 長押し判定時間（秒）
LONG_PRESS_TIME = 0.3

# 音量変更の間隔（秒）- 長押し中の連続送信間隔
VOLUME_INTERVAL = 0.1

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
# ConsumerControl の初期化（メディアキー用）
#
consumer_control = ConsumerControl(usb_hid.devices)

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
button_press_start_time = None
is_long_press = False
volume_adjusting = False
last_volume_send_time = 0


def toggle_mute():
    """マイクミュートを切り替え"""
    consumer_control.send(ConsumerControlCode.MIC_MUTE)
    print("🎤 マイクミュート切り替え")


def adjust_volume(direction):
    """音量を調整（direction: 'up' または 'down'）"""
    if direction == 'up':
        consumer_control.send(ConsumerControlCode.VOLUME_UP)
        if features["debug_enabled"]:
            print("🔊 音量アップ")
    else:
        consumer_control.send(ConsumerControlCode.VOLUME_DOWN)
        if features["debug_enabled"]:
            print("🔉 音量ダウン")


#
# 起動メッセージ
#
print(f"=== {board_name} リモート会議用コントローラー起動 ===")
print(f"ボードタイプ：{cuskey_settings.BOARD_TYPE}")
print(f"デバッグモード：{features['debug_enabled']}")
print("-" * 50)
print("【操作方法】")
print("  シングルクリック：< 1 秒）: マイクミュート切り替え 🎤")
print("  長押し（>= 1 秒）:")
print(f"    * Mode A（スイッチ ON）: 音量アップ 🔊")
print(f"    * Mode B（スイッチ OFF）: 音量ダウン 🔉")
print("-" * 50)
print("【対応アプリ】")
print("  - Zoom")
print("  - Microsoft Teams")
print("  - Google Meet")
print("  - Discord")
print("  - Skype など")
print("-" * 50)

#
# メインループ
#
while True:
    current_time = time.monotonic()
    
    # ボタンの現在の状態を読み取り
    current_button_state = button.value
    
    # ボタンが押された瞬間を検出（High → Low）
    if last_button_state and not current_button_state:
        button_press_start_time = current_time
        is_long_press = False
        volume_adjusting = False
        last_volume_send_time = 0
        
        if features["debug_enabled"]:
            print("[DEBUG] ボタンが押されました")
        
        # チャタリング防止のため少し待機
        time.sleep(DEBOUNCE_TIME)
    
    # ボタンが押されている間の処理
    elif not current_button_state and button_press_start_time is not None:
        press_duration = current_time - button_press_start_time
        
        # 長押し判定（設定時間以上）
        if press_duration >= LONG_PRESS_TIME and not is_long_press:
            is_long_press = True
            volume_adjusting = True
            
            # 現在のモードを取得
            current_mode = mode_a.value
            
            if features["debug_enabled"]:
                if current_mode == False:
                    print("[DEBUG] Mode A: 音量アップ開始")
                else:
                    print("[DEBUG] Mode B: 音量ダウン開始")
            
            # 最初の音量変更を送信
            current_mode = mode_a.value
            if current_mode == False:  # Mode A: 音量アップ
                adjust_volume('up')
            else:  # Mode B: 音量ダウン
                adjust_volume('down')
        
        # 長押し中は連続で音量変更
        if volume_adjusting and (current_time - last_volume_send_time >= VOLUME_INTERVAL):
            current_mode = mode_a.value
            if current_mode == False:  # Mode A: 音量アップ
                adjust_volume('up')
            else:  # Mode B: 音量ダウン
                adjust_volume('down')
            
            last_volume_send_time = current_time
    
    # ボタンが離された瞬間を検出（Low → High）
    elif not last_button_state and current_button_state:
        if button_press_start_time is not None:
            press_duration = current_time - button_press_start_time
            
            # 長押しでなかった場合はマイクミュート切り替え
            if not is_long_press:
                toggle_mute()
            
            if features["debug_enabled"]:
                print(f"[DEBUG] ボタンが離されました（押下時間：{press_duration:.2f}秒）")
            
            # リセット
            button_press_start_time = None
            volume_adjusting = False
            
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
   - meeting_controller.py という名前で Pico のルートディレクトリに保存
   - 自動起動させたい場合は、code.py という名前に変更

4. 設定のカスタマイズ（プログラムの上部で変更）
   - LONG_PRESS_TIME: 長押し判定時間（デフォルト 0.3 秒）
     シングルクリックと長押しの境界を調整
   
   - VOLUME_INTERVAL: 音量変更の間隔（デフォルト 0.1 秒）
     小さいほど速く、大きいほどゆっくり変化
   
   - DEBOUNCE_TIME: チャタリング防止の待機時間（デフォルト 0.05 秒）

5. 動作確認
   - Pico を接続すると自動的にプログラムが起動
   - シリアルモニタで動作状況を確認可能（Mu Editor、Thonny 等）

6. 操作方法
   - セルフロックスイッチで Mode A/B を切り替え
     * Mode A（スイッチ ON）: 長押しで音量アップ
     * Mode B（スイッチ OFF）: 長押しで音量ダウン
   
   - ボタン操作:
     * シングルクリック（0.3 秒未満）: マイクミュート切り替え 🎤
     * 長押し（0.3 秒以上）: 音量変更（Mode A=UP, Mode B=DOWN）

7. 対応アプリ
   - Zoom
   - Microsoft Teams
   - Google Meet
   - Discord
   - Skype
   - その他、ConsumerControl をサポートするアプリケーション

============================================================================
【機能詳細】

■ マイクミュート切り替え（シングルクリック）
  - ConsumerControlCode.MIC_MUTE を送信
  - Zoom、Teams、Google Meet などでマイクオン/オフを切り替え
  - アプリケーションに依存しない標準的な操作

■ 音量調整（長押し）
  - Mode A: 音量アップ（ConsumerControlCode.VOLUME_UP）
  - Mode B: 音量ダウン（ConsumerControlCode.VOLUME_DOWN）
  - 押している間、設定間隔で連続送信
  - 離すと即座に停止

============================================================================
【トラブルシューティング】

■ マイクミュートが反応しない場合
  - アプリケーションのウィンドウにフォーカスが当たっているか確認
  - アプリが ConsumerControl をサポートしているか確認
  
■ 音量変更が遅い/速すぎる場合
  - VOLUME_INTERVAL の値を調整（小さいほど速い）
  
■ 誤検出が多い場合
  - LONG_PRESS_TIME の値を大きくしてシングルクリックと長押しの境界を明確に

============================================================================
【更新履歴】

■ 初期バージョン
  - シングルクリックでマイクミュート切り替え機能を実装
  - 長押しで音量アップ/ダウン（モード切り替え）を実装
  - Zoom、Teams、Google Meet などのリモート会議アプリに対応

============================================================================
"""