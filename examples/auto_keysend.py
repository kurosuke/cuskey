"""
自動矢印キー送信プログラム
指定した秒数間隔で左矢印/右矢印キーを自動送信
MODE Aの時：左矢印キー
MODE A以外（MODE B）の時：右矢印キー
"""

import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

# ボード設定をインポート
import cuskey_settings

# 送信間隔の設定（秒）
SEND_INTERVAL = 8  # デフォルト8秒間隔（必要に応じて変更可能）

# 自動送信の有効/無効設定
AUTO_SEND_ENABLED = False

# 長押し判定の設定
LONG_PRESS_TIME = 0.5  # 長押しと判定する時間（秒）
MANUAL_SEND_INTERVAL = 0.1  # 手動送信時のキー送信間隔（秒）

#
# ボード設定の取得
#
pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

#
# USBキーボードの初期化
#
keyboard = Keyboard(usb_hid.devices)

#
# モード切替ピンの初期化
#
# モード切替用GNDピンの設定
if pins["mode_gnd"]:
    gnd_pin = digitalio.DigitalInOut(pins["mode_gnd"])
    gnd_pin.direction = digitalio.Direction.OUTPUT
    gnd_pin.value = False  # GND（Low）に設定

# MODE_A ピンの設定
mode_a = digitalio.DigitalInOut(pins["mode_a"])
mode_a.direction = digitalio.Direction.INPUT
mode_a.pull = digitalio.Pull.UP

#
# オプション：ボタンピンの初期化（押下で自動送信の有効/無効を切り替える場合）
#
# ボタン用GNDピンの設定
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
last_send_time = time.monotonic()
last_button_state = True  # プルアップなので通常はTrue
auto_send_active = AUTO_SEND_ENABLED
send_count = 0

# 長押し検出用変数
button_press_start_time = None
is_long_press = False
last_manual_send_time = 0
manual_send_active = False

# デバッグ用変数
if features["debug_enabled"]:
    last_mode_state = None

#
# 起動メッセージ
#
print(f"=== {board_name} 自動矢印キー送信プログラム起動 ===")
print(f"ボードタイプ: {cuskey_settings.BOARD_TYPE}")
print(f"送信間隔: {SEND_INTERVAL}秒")
print(f"デバッグモード: {features['debug_enabled']}")
print("-" * 50)
print("【動作モード】")
print("  - Mode A（スイッチON）: 左矢印キー送信")
print("  - Mode B（スイッチOFF）: 右矢印キー送信")
print("【操作方法】")
print("  - ボタン短押し: 自動送信の有効/無効切り替え")
print("  - ボタン長押し: 手動でキー送信（押している間送信）")
print(f"  - 現在の状態: {'有効' if auto_send_active else '無効'}")
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
        # ボタン押下開始時刻を記録
        button_press_start_time = current_time
        is_long_press = False
        manual_send_active = False
        
        if features["debug_enabled"]:
            print(f"[DEBUG] ボタン押下開始")
    
    # ボタンが押されている間の処理
    elif not current_button_state and button_press_start_time is not None:
        # 長押し判定
        press_duration = current_time - button_press_start_time
        
        if press_duration >= LONG_PRESS_TIME and not is_long_press:
            # 長押しと判定
            is_long_press = True
            manual_send_active = True
            
            if features["debug_enabled"]:
                print(f"[DEBUG] 長押し検出 - 手動送信モード開始")
            else:
                print("長押し検出 - 手動送信モード")
        
        # 長押し中の手動送信処理
        if is_long_press and current_time - last_manual_send_time >= MANUAL_SEND_INTERVAL:
            # 現在のモードを取得
            current_mode = mode_a.value
            
            # モードに応じてキーを送信
            if current_mode == False:  # Mode A
                keyboard.send(Keycode.LEFT_ARROW)
                if features["debug_enabled"]:
                    print(f"[DEBUG][手動] 左矢印キー送信")
            else:  # Mode B
                keyboard.send(Keycode.RIGHT_ARROW)
                if features["debug_enabled"]:
                    print(f"[DEBUG][手動] 右矢印キー送信")
            
            last_manual_send_time = current_time
    
    # ボタンが離された瞬間を検出（Low → High）
    elif not last_button_state and current_button_state:
        if button_press_start_time is not None:
            press_duration = current_time - button_press_start_time
            
            # 短押しの場合は自動送信の有効/無効を切り替え
            if not is_long_press and press_duration < LONG_PRESS_TIME:
                auto_send_active = not auto_send_active
                state_text = "有効" if auto_send_active else "無効"
                
                if features["debug_enabled"]:
                    print(f"[DEBUG] 自動送信を{state_text}にしました")
                else:
                    print(f"自動送信を{state_text}にしました")
            
            # 長押し終了
            elif is_long_press:
                if features["debug_enabled"]:
                    print(f"[DEBUG] 長押し終了 - 手動送信モード終了")
                else:
                    print("手動送信モード終了")
            
            # リセット
            button_press_start_time = None
            is_long_press = False
            manual_send_active = False
            
            # チャタリング防止のため少し待機
            time.sleep(cuskey_settings.DEBOUNCE_TIME)
    
    # 前回のボタン状態を更新
    last_button_state = current_button_state
    
    # 自動送信処理（手動送信中でない場合のみ）
    if auto_send_active and not manual_send_active:
        # 指定された間隔でキー送信
        if current_time - last_send_time >= SEND_INTERVAL:
            # 現在のモードを取得
            current_mode = mode_a.value
            
            # デバッグモード: モード変更を検出
            if features["debug_enabled"] and last_mode_state != current_mode:
                mode_text = "Mode B" if current_mode else "Mode A"
                print(f"[DEBUG] モード切替検出: {mode_text} (mode_a.value = {current_mode})")
                last_mode_state = current_mode
            
            # モードに応じてキーを送信
            if current_mode == False:  # Mode A（スイッチがGNDに接続）
                # 左矢印キーを送信
                keyboard.send(Keycode.LEFT_ARROW)
                send_count += 1
                
                if features["debug_enabled"]:
                    print(f"[DEBUG][Mode A] 左矢印キー送信 (送信回数: {send_count})")
                else:
                    print(f"[Mode A] 左矢印キー送信 (送信回数: {send_count})")
            
            else:  # Mode B（スイッチが開いている）
                # 右矢印キーを送信
                keyboard.send(Keycode.RIGHT_ARROW)
                send_count += 1
                
                if features["debug_enabled"]:
                    print(f"[DEBUG][Mode B] 右矢印キー送信 (送信回数: {send_count})")
                else:
                    print(f"[Mode B] 右矢印キー送信 (送信回数: {send_count})")
            
            # 次回送信時刻を更新
            last_send_time = current_time
    
    # CPU負荷軽減のため短時間待機
    time.sleep(cuskey_settings.LOOP_DELAY)

"""
================================================================================
【使い方】

1. CircuitPythonがインストールされたRaspberry Pi Picoを準備

2. 必要なライブラリのコピー
   - Adafruit_CircuitPython_HIDフォルダ内のadafruit_hidフォルダをPicoにコピー
   - cuskey_settings.pyをPicoにコピー

3. このファイルをPicoにコピー
   - auto_keysend.pyという名前でPicoのルートディレクトリに保存
   - 自動起動させたい場合は、code.pyという名前に変更

4. 設定の調整（必要に応じて）
   - SEND_INTERVAL: キー送信間隔（秒）を変更
     例: SEND_INTERVAL = 5.0  # 5秒間隔
   
   - AUTO_SEND_ENABLED: 起動時の自動送信状態
     例: AUTO_SEND_ENABLED = False  # 起動時は無効状態
   
   - LONG_PRESS_TIME: 長押しと判定する時間（秒）
     例: LONG_PRESS_TIME = 0.5  # 0.5秒以上で長押し
   
   - MANUAL_SEND_INTERVAL: 手動送信時のキー送信間隔（秒）
     例: MANUAL_SEND_INTERVAL = 0.1  # 0.1秒間隔で連続送信

5. 動作確認
   - Picoを接続すると自動的にプログラムが起動
   - シリアルモニタで動作状況を確認可能（Mu Editor、Thonny等）

6. 操作方法
   - モード切替スイッチの状態で送信するキーが変わる
     * MODE A（スイッチON）: 左矢印キー
     * MODE B（スイッチOFF）: 右矢印キー
   
   - ボタンを短押しすると自動送信の有効/無効が切り替わる
   - ボタンを長押し（0.5秒以上）すると、押している間手動でキーを送信
   
   - プレゼンテーションソフトやメディアプレーヤーで使用可能

7. トラブルシューティング
   - キーが送信されない場合
     * アプリケーションのウィンドウにフォーカスが当たっているか確認
     * デバッグモードを有効にして動作状況を確認
   
   - 送信間隔を変更したい場合
     * SEND_INTERVALの値を変更して再起動
   
   - 長押し機能の調整
     * LONG_PRESS_TIMEで長押し判定時間を調整
     * MANUAL_SEND_INTERVALで手動送信時の速度を調整

================================================================================

【更新履歴】

■ 長押し手動送信機能の追加
  - ボタンの長押し（デフォルト0.5秒以上）で手動送信モードに切り替え
  - 長押し中は現在のモードに応じた矢印キーを連続送信
  - 短押しと長押しを区別して異なる動作を実現
  
  追加設定：
  - LONG_PRESS_TIME: 長押し判定時間の設定
  - MANUAL_SEND_INTERVAL: 手動送信時の送信間隔設定
  
  動作仕様：
  - 短押し（0.5秒未満）: 自動送信の有効/無効切り替え
  - 長押し（0.5秒以上）: 押している間、手動でキーを連続送信
  - 手動送信中は自動送信を一時停止
  - Mode Aの時は左矢印、Mode Bの時は右矢印を送信

================================================================================
"""
