"""
統合版 Raspberry Pi Pico メディアキーボード
ProMiroPico と Piromoni_PocoMini の両方に対応
設定はcuskey_settings.pyで管理
"""

import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse

# ボード設定をインポート
import cuskey_settings

#
# ボード設定の取得
#
pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

#
# USBキーボード、コンシューマーコントロール、マウスの初期化
#
keyboard = Keyboard(usb_hid.devices)
consumer_control = ConsumerControl(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

#
# Play/Stop ボタンキー初期化
#
# ボタン用GNDピンの設定
if pins["button_gnd"]:
    gnd_pin = digitalio.DigitalInOut(pins["button_gnd"])
    gnd_pin.direction = digitalio.Direction.OUTPUT
    gnd_pin.value = False  # GND（Low）に設定

# ボタン入力ピンの設定
button = digitalio.DigitalInOut(pins["button"])
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

#
# モード切替ピンの初期化
#
# モード切替用GNDピンの設定
if pins["mode_gnd"]:
    gnd_pin2 = digitalio.DigitalInOut(pins["mode_gnd"])
    gnd_pin2.direction = digitalio.Direction.OUTPUT
    gnd_pin2.value = False  # GND（Low）に設定

# MODE_A ピンの設定
mode_a = digitalio.DigitalInOut(pins["mode_a"])
mode_a.direction = digitalio.Direction.INPUT
mode_a.pull = digitalio.Pull.UP

# MODE_B ピンの設定（使用する場合）
mode_b = None
if features["dual_mode"] and pins["mode_b"]:
    mode_b = digitalio.DigitalInOut(pins["mode_b"])
    mode_b.direction = digitalio.Direction.INPUT
    mode_b.pull = digitalio.Pull.UP

#
# 状態管理変数の初期化
#
last_button_state = True  # プルアップなので通常はTrue
button_pressed = False
button_press_time = 0  # ボタンが押された時刻を記録

# デバッグ用変数（デバッグモードが有効な場合のみ使用）
if features["debug_enabled"]:
    last_mode_state = None
    debug_counter = 0

#
# 起動メッセージ
#
print(f"=== {board_name} メディアキーボード起動 ===")
print(f"ボードタイプ: {cuskey_settings.BOARD_TYPE}")
print(f"デバッグモード: {features['debug_enabled']}")
print("-" * 40)
print("【操作方法】")
print("通常押下:")
print("  - Mode A: PLAY_PAUSE")
print("  - Mode B: マウスホイール下")
print(f"長押し({cuskey_settings.LONG_PRESS_THRESHOLD}秒):")
print("  - Mode A: 巻き戻し(左矢印×2)")
print("  - Mode B: PLAY_PAUSE")
print("-" * 40)

#
# メインループ
#
while True:
    # デバッグモード: mode_aの値を定期的に表示
    if features["debug_enabled"]:
        debug_counter += 1
        if debug_counter >= cuskey_settings.DEBUG_COUNTER_THRESHOLD:
            current_mode = mode_a.value
            if last_mode_state != current_mode:
                print(f"[DEBUG] モード切替検出: mode_a.value = {current_mode} (False=Mode A, True=Mode B)")
                last_mode_state = current_mode
            debug_counter = 0
    
    # ボタンの現在の状態を読み取り
    current_button_state = button.value
    
    # ボタンが押された瞬間を検出（High → Low）
    if last_button_state and not current_button_state and not button_pressed:
        button_pressed = True
        button_press_time = time.monotonic()  # 押された時刻を記録
        if features["debug_enabled"]:
            print("[DEBUG] ボタンが押されました")
        else:
            print("ボタンが押されました")
        
        # チャタリング防止のため少し待機
        time.sleep(cuskey_settings.DEBOUNCE_TIME)
    
    # ボタンが離された瞬間を検出（Low → High）
    elif not last_button_state and current_button_state and button_pressed:
        button_pressed = False
        # 押されていた時間を計算
        press_duration = time.monotonic() - button_press_time
        
        if features["debug_enabled"]:
            print(f"[DEBUG] ボタンが離されました（押下時間: {press_duration:.2f}秒）")
        else:
            print(f"ボタンが離されました（押下時間: {press_duration:.2f}秒）")
        
        # 現在のモードを取得
        current_mode = mode_a.value
        
        if press_duration >= cuskey_settings.LONG_PRESS_THRESHOLD:
            # 長押しの処理
            if features["debug_enabled"]:
                print(f"[DEBUG] 長押しを検出しました (mode_a.value = {current_mode})")
            else:
                print("長押しを検出しました")
            
            if current_mode == False:  # Mode A（スイッチがGNDに接続）
                # MEMO: Windowにフォーカスが当たっていないと効かない
                # 巻き戻し：左矢印キーを2回送信
                keyboard.send(Keycode.LEFT_ARROW)
                time.sleep(0.05)  # キー送信間の遅延
                keyboard.send(Keycode.LEFT_ARROW)
                
                mode_label = "[Mode A]" if features["debug_enabled"] else ""
                print(f"{mode_label} 巻き戻し：左矢印キー×2を送信")
            else:  # Mode B（スイッチが開いている）
                # PLAY_PAUSEコマンドを送信
                consumer_control.send(ConsumerControlCode.PLAY_PAUSE)
                
                mode_label = "[Mode B]" if features["debug_enabled"] else ""
                print(f"{mode_label} PLAY_PAUSEコマンドを送信")
        else:
            # 通常の押下の処理
            if features["debug_enabled"]:
                print(f"[DEBUG] 通常の押下を検出しました (mode_a.value = {current_mode})")
            else:
                print("通常の押下を検出しました")
            
            if current_mode == False:  # Mode A（スイッチがGNDに接続）
                # PLAY_PAUSEコマンドを送信
                consumer_control.send(ConsumerControlCode.PLAY_PAUSE)
                
                mode_label = "[Mode A]" if features["debug_enabled"] else ""
                print(f"{mode_label} PLAY_PAUSEコマンドを送信")
            else:  # Mode B（スイッチが開いている）
                # マウスホイール下方向を送信
                mouse.move(wheel=-1)  # 負の値で下方向
                
                mode_label = "[Mode B]" if features["debug_enabled"] else ""
                print(f"{mode_label} マウスホイール下方向を送信")
        
        time.sleep(cuskey_settings.DEBOUNCE_TIME)  # チャタリング防止
    
    # 前回の状態を更新
    last_button_state = current_button_state
    
    # CPU負荷軽減のため短時間待機
    time.sleep(cuskey_settings.LOOP_DELAY)
