"""
PPT(Push To Talk)  キーボード

MODE Aの時：
    シングルクリックでEnterキー送信
    ボタン長押しでマイクON。離すとOFF。PPTキー送信は、F12
    ダブルクリックでESCキー送信

MODE A以外（MODE B）の時：
    シングルクリックでページダウンキー送信
    ボタン長押しでその期間はマウスのホイールダウン状態維持
    ダブルクリックでページアップキー送信
"""

import digitalio
import time
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

# ボード設定をインポート
import cuskey_settings

# マルチクリック検出の設定
DOUBLE_CLICK_TIME = 0.3  # マルチクリック判定時間（秒）
MIN_PRESS_TIME = 0.05  # 最小押下時間（チャタリング防止）
LONG_PRESS_TIME = 0.3  # 長押し判定時間（秒）
WHEEL_SCROLL_INTERVAL = 0.05  # マウスホイールスクロール間隔（秒）

# PTTキーの設定（最大3つまで同時押し可能）
# 例: [Keycode.CONTROL, Keycode.TAB, Keycode.ONE]          # Ctrl+Tab+1
#     [Keycode.CONTROL, Keycode.SHIFT, Keycode.F12]        # Ctrl+Shift+F12
#     [Keycode.OPTION, Keycode.CONTROL, Keycode.ONE]       # Option+Ctrl+1
PTT_KEYS = [Keycode.CONTROL, Keycode.TAB, Keycode.ONE] 

#
# ボード設定の取得
#
pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

#
# USBキーボードとマウスの初期化
#
keyboard = Keyboard(usb_hid.devices)
mouse = Mouse(usb_hid.devices)

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
# ボタンピンの初期化
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
last_button_state = True  # プルアップなので通常はTrue
button_press_start_time = None
ptt_key_pressed = False  # PTTキーが現在押されているか（MODE A用）
is_long_press = False  # 長押し状態か
wheel_scrolling = False  # マウスホイールスクロール中か（MODE B用）
last_wheel_scroll_time = 0  # 最後のホイールスクロール時刻

# マルチクリック検出用変数
last_click_time = 0
click_count = 0
pending_single_click = False  # MODE B用：シングルクリック待機中
last_mode = None  # 最後に記録したモード

#
# 起動メッセージ
#
print(f"=== {board_name} PTTキーボード起動 ===")
print(f"ボードタイプ: {cuskey_settings.BOARD_TYPE}")
print(f"デバッグモード: {features['debug_enabled']}")
print("-" * 50)
print("【動作モード】")
print("  Mode A（スイッチON）:")
print("    - シングルクリック: Enter")
ptt_key_names = " + ".join([str(key) for key in PTT_KEYS])
print(f"    - ボタン長押し: {ptt_key_names}（PTT）")
print("    - ダブルクリック: ESC")
print("  Mode B（スイッチOFF）:")
print("    - シングルクリック: PAGE DOWN")
print("    - ボタン長押し: マウスホイールダウン")
print("    - ダブルクリック: PAGE UP")
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
        wheel_scrolling = False
        
        # 現在のモードを取得
        current_mode = mode_a.value
        
        # MODE Aでは長押し判定待ち、MODE Bは既存フロー
        if current_mode == False:  # Mode A
            if features["debug_enabled"]:
                print(f"[DEBUG][Mode A] ボタン押下開始")
        else:
            if features["debug_enabled"]:
                print(f"[DEBUG][Mode B] ボタン押下開始")
    
    # ボタンが押されている間の処理
    elif not current_button_state and button_press_start_time is not None:
        current_mode = mode_a.value
        press_duration = current_time - button_press_start_time
        
        # MODE Aで長押し判定（0.3秒以上）
        if current_mode == False and not is_long_press and press_duration >= LONG_PRESS_TIME:
            is_long_press = True
            # 設定された全てのPTTキーを押下
            for key in PTT_KEYS:
                keyboard.press(key)
            ptt_key_pressed = True
            ptt_key_names = " + ".join([str(key) for key in PTT_KEYS])
            if features["debug_enabled"]:
                print(f"[DEBUG][Mode A] 長押し検出 → {ptt_key_names}キー押下")
            else:
                print(f"[Mode A] PTT ON ({ptt_key_names})")
        
        # MODE Bで長押し判定（0.3秒以上）
        elif current_mode == True and not is_long_press and press_duration >= LONG_PRESS_TIME:
            is_long_press = True
            wheel_scrolling = True
            if features["debug_enabled"]:
                print(f"[DEBUG][Mode B] 長押し検出 - ホイールスクロール開始")
            else:
                print("[Mode B] ホイールスクロール開始")
        
        # MODE Bで長押し中はマウスホイールを動かす
        if current_mode == True and wheel_scrolling:
            if current_time - last_wheel_scroll_time >= WHEEL_SCROLL_INTERVAL:
                mouse.move(wheel=-1)  # ホイールダウン
                last_wheel_scroll_time = current_time
                if features["debug_enabled"]:
                    print(f"[DEBUG][Mode B] ホイールダウン")
    
    # ボタンが離された瞬間を検出（Low → High）
    elif not last_button_state and current_button_state:
        if button_press_start_time is not None:
            press_duration = current_time - button_press_start_time
            current_mode = mode_a.value
            
            # MODE Aの場合: PTTキーをリリース
            if current_mode == False:
                if ptt_key_pressed:
                    # 設定された全てのPTTキーをリリース（逆順で）
                    for key in reversed(PTT_KEYS):
                        keyboard.release(key)
                    ptt_key_names = " + ".join([str(key) for key in PTT_KEYS])
                    if features["debug_enabled"]:
                        print(f"[DEBUG][Mode A] {ptt_key_names}キーリリース (押下時間: {press_duration:.3f}秒)")
                    else:
                        print("[Mode A] PTT OFF")
                    ptt_key_pressed = False
                
                # MODE Aのマルチクリック検出（長押し以外）
                if press_duration >= MIN_PRESS_TIME and press_duration < LONG_PRESS_TIME:
                    if current_time - last_click_time <= DOUBLE_CLICK_TIME and last_mode == False:
                        click_count += 1
                        
                        # ダブルクリック検出
                        if click_count >= 2:
                            keyboard.send(Keycode.ESCAPE)
                            if features["debug_enabled"]:
                                print(f"[DEBUG][Mode A] ダブルクリック → ESC送信")
                            else:
                                print("[Mode A] ダブルクリック → ESC")
                            click_count = 0
                            last_click_time = 0
                            last_mode = None
                            pending_single_click = False
                        else:
                            last_click_time = current_time
                            last_mode = False
                            pending_single_click = True
                    else:
                        click_count = 1
                        last_click_time = current_time
                        last_mode = False
                        pending_single_click = True
            
            # MODE Bの場合
            else:
                # 長押しだった場合はホイールスクロール終了
                if is_long_press and wheel_scrolling:
                    wheel_scrolling = False
                    if features["debug_enabled"]:
                        print(f"[DEBUG][Mode B] ホイールスクロール終了 (押下時間: {press_duration:.3f}秒)")
                    else:
                        print("[Mode B] ホイールスクロール終了")
                
                # 短い押下の場合はクリックとしてカウント
                elif press_duration >= MIN_PRESS_TIME and press_duration < LONG_PRESS_TIME:
                    if current_time - last_click_time <= DOUBLE_CLICK_TIME and last_mode == True:
                        click_count += 1
                        
                        # ダブルクリック検出
                        if click_count >= 2:
                            keyboard.send(Keycode.PAGE_UP)
                            if features["debug_enabled"]:
                                print(f"[DEBUG][Mode B] ダブルクリック → PAGE UP送信")
                            else:
                                print("[Mode B] ダブルクリック → PAGE UP")
                            click_count = 0
                            last_click_time = 0
                            pending_single_click = False
                            last_mode = None
                        else:
                            last_click_time = current_time
                            pending_single_click = True
                            last_mode = True
                    else:
                        # 新しいクリックシーケンス開始（シングルクリック候補）
                        click_count = 1
                        last_click_time = current_time
                        pending_single_click = True
                        last_mode = True
            
            # リセット
            button_press_start_time = None
            is_long_press = False
            
            # チャタリング防止のため少し待機
            time.sleep(cuskey_settings.DEBOUNCE_TIME)
    
    # 前回のボタン状態を更新
    last_button_state = current_button_state
    
    # マルチクリックのタイムアウト処理
    if click_count > 0 and (current_time - last_click_time > DOUBLE_CLICK_TIME):
        if click_count == 1 and pending_single_click:
            # シングルクリック確定
            if last_mode == False:  # MODE A
                keyboard.send(Keycode.ENTER)
                if features["debug_enabled"]:
                    print(f"[DEBUG][Mode A] シングルクリック → Enter送信")
                else:
                    print("[Mode A] シングルクリック → Enter")
            elif last_mode == True:  # MODE B
                keyboard.send(Keycode.PAGE_DOWN)
                if features["debug_enabled"]:
                    print(f"[DEBUG][Mode B] シングルクリック → PAGE DOWN送信")
                else:
                    print("[Mode B] シングルクリック → PAGE DOWN")
        
        # リセット
        pending_single_click = False
        click_count = 0
        last_click_time = 0
        last_mode = None
    
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
   - ppt_key.pyという名前でPicoのルートディレクトリに保存
   - 自動起動させたい場合は、code.pyという名前に変更

4. 設定の調整（必要に応じて）
    - PTT_KEYS: PTTで使用するキー（最大3つまで）
      例: PTT_KEYS = [Keycode.F12]  # F12のみ
          PTT_KEYS = [Keycode.CONTROL, Keycode.SHIFT, Keycode.F12]  # Ctrl+Shift+F12
          PTT_KEYS = [Keycode.ALT, Keycode.F12]  # Alt+F12
    
    - DOUBLE_CLICK_TIME: マルチクリック判定時間（秒）
      例: DOUBLE_CLICK_TIME = 0.3  # 0.3秒以内の複数クリック
    
    - MIN_PRESS_TIME: 最小押下時間（チャタリング防止）
      例: MIN_PRESS_TIME = 0.05  # 0.05秒以上の押下をカウント
    
    - LONG_PRESS_TIME: 長押し判定時間（秒）
      例: LONG_PRESS_TIME = 0.3  # 0.3秒以上で長押し
    
    - WHEEL_SCROLL_INTERVAL: マウスホイールスクロール間隔（秒）
      例: WHEEL_SCROLL_INTERVAL = 0.05  # 0.05秒間隔でスクロール

5. 動作確認
   - Picoを接続すると自動的にプログラムが起動
   - シリアルモニタで動作状況を確認可能（Mu Editor、Thonny等）

6. 操作方法
    MODE A（スイッチON）: Whisper Flow
      * ボタン長押し: PTT_KEYSで設定したキー（PTT - マイクON/OFF）
      * ダブルクリック: Enterキー（チャット送信）
      * トリプルクリック: ESCキー（キャンセル）
      * Discord、Zoom、Teamsなどで使用可能
      * 最大3つのキーを同時押しできます（例: Ctrl+Shift+F12）
   
   MODE B（スイッチOFF）: ページスクロール用
     * シングルクリック: PAGE DOWNキー（次ページ）
     * ボタン長押し: マウスホイールダウン（連続スクロール）
     * ダブルクリック: PAGE UPキー（前ページ）
     * トリプルクリック: HOMEキー（先頭へ）
     * PDFビューアー、ブラウザなどで使用可能

7. トラブルシューティング
   - キーが送信されない場合
     * アプリケーションのウィンドウにフォーカスが当たっているか確認
     * デバッグモードを有効にして動作状況を確認
   
   - マルチクリックが反応しない場合
     * DOUBLE_CLICK_TIMEの値を大きくして再起動
   
   - 長押し判定が早すぎる/遅すぎる場合
     * LONG_PRESS_TIMEの値を調整
   
   - ホイールスクロールの速度を変更したい場合
     * WHEEL_SCROLL_INTERVALの値を調整（小さいほど速い）
   
   - 誤検出が多い場合
     * MIN_PRESS_TIMEの値を大きくしてチャタリング対策を強化

================================================================================

【機能詳細】

■ MODE A: AIチャット用PTT機能
  - ボタン長押しでPTT_KEYSで設定したキーをPress/Release
  - Whisper Flowアプリ(https://wisprflow.ai/)のPTT（Push To Talk）機能に対応
  - マイクのON/OFFをボタンで直感的に操作
  - ダブルクリックでEnter（チャット送信）
  - トリプルクリックでESC（ダイアログキャンセル）
  - 最大3つのキーを同時押し可能（例: Ctrl+Tab+1）
  
  動作仕様：
  - ボタン押下と同時にPTTキー押下開始（遅延なし）
  - ボタンリリースで即座にPTTキーリリース
  - Discord、Zoom、Teamsで設定したキーをPTTキーに設定して使用
  - 修飾キー（Ctrl、Shift、Alt）との組み合わせも可能

■ MODE B: ページスクロール機能
  - シングルクリック: PAGE DOWNキー送信
  - ボタン長押し（0.3秒以上）: マウスホイールダウン連続送信
  - ダブルクリック: PAGE UPキー送信
  - トリプルクリック: HOMEキー送信
  
  動作仕様：
  - 0.3秒未満の押下: シングルクリックとして扱う
  - 0.3秒以上の押下: 長押しとしてホイールスクロール開始
  - 長押し中は0.05秒間隔でホイールダウンイベント送信
  - PDFビューアー、Webブラウザなどで快適なスクロール操作

■ モード切替機能
  - ハードウェアスイッチでMODE A/Bを切替
  - MODE A: Whisper Flow用（PTT、Enter、ESC）
  - MODE B: スクロール用（PAGE DOWN/UP、ホイール、HOME）
  - リアルタイムでモード変更が反映されます

================================================================================
"""
