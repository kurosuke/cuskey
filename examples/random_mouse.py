"""
ランダムマウス移動コントローラー（トグル版）
ボタンを押すたびに「開始」「停止」を切り替えます。

【操作方法】
  ボタンを押す → マウスのランダム移動を開始
  もう一度押す → マウスのランダム移動を停止

  Mode A（モードスイッチON）: 大きい移動範囲（±MOVE_RANGE px）
  Mode B（モードスイッチOFF）: 小さい移動範囲（±MOVE_RANGE_B px）

  ※ 動作中にモードスイッチを切り替えると移動範囲が即座に変わります
"""

import digitalio
import time
import random
import usb_hid
from adafruit_hid.mouse import Mouse

import cuskey_settings

# ===========================
# 設定可能な定数
# ===========================

# Mode A: 1回あたりのランダム移動量の最大値（ピクセル）
MOVE_RANGE = 30

# Mode B: 1回あたりのランダム移動量の最大値（ピクセル）
MOVE_RANGE_B = 10

# 移動間隔の最小・最大（秒）- この範囲でランダムに次の移動タイミングを決定
MOVE_INTERVAL_MIN = 1.0
MOVE_INTERVAL_MAX = 5.0

# ===========================
# ボード設定の取得
# ===========================
pins = cuskey_settings.get_pins()
features = cuskey_settings.get_features()
board_name = cuskey_settings.get_board_name()

# ===========================
# マウスの初期化
# ===========================
mouse = Mouse(usb_hid.devices)

# ===========================
# ピンの初期化
# ===========================

# モード切替用GNDピンの設定
if pins["mode_gnd"]:
    mode_gnd = digitalio.DigitalInOut(pins["mode_gnd"])
    mode_gnd.direction = digitalio.Direction.OUTPUT
    mode_gnd.value = False

# MODE_A ピンの設定
mode_a = digitalio.DigitalInOut(pins["mode_a"])
mode_a.direction = digitalio.Direction.INPUT
mode_a.pull = digitalio.Pull.UP

# ボタン用GNDピンの設定
if pins["button_gnd"]:
    button_gnd = digitalio.DigitalInOut(pins["button_gnd"])
    button_gnd.direction = digitalio.Direction.OUTPUT
    button_gnd.value = False

# ボタン入力ピンの設定
button = digitalio.DigitalInOut(pins["button"])
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# ===========================
# 状態変数の初期化
# ===========================
last_button_state = True
is_running = False          # マウス移動中かどうか
last_move_time = 0.0        # 最後にマウスを動かした時刻
next_move_interval = 0.0    # 次の移動までの待機時間（秒）

if features["debug_enabled"]:
    last_mode_state = None
    debug_counter = 0

# ===========================
# 起動メッセージ
# ===========================
print(f"=== {board_name} ランダムマウス移動コントローラー（トグル版）起動 ===")
print(f"ボードタイプ: {cuskey_settings.BOARD_TYPE}")
print(f"デバッグモード: {features['debug_enabled']}")
print("-" * 40)
print("【操作方法】")
print("  ボタン押下 → 開始 / 停止 を切り替え")
print(f"  Mode A（スイッチON）: 移動範囲 ±{MOVE_RANGE}px")
print(f"  Mode B（スイッチOFF）: 移動範囲 ±{MOVE_RANGE_B}px")
print(f"  移動間隔: {MOVE_INTERVAL_MIN}〜{MOVE_INTERVAL_MAX}秒（ランダム）")
print("-" * 40)
print("状態: 停止中")

# ===========================
# メインループ
# ===========================
while True:
    now = time.monotonic()

    # デバッグモード: mode_a の値を定期的に表示
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
    if last_button_state and not current_button_state:
        time.sleep(cuskey_settings.DEBOUNCE_TIME)

        # 開始 / 停止 をトグル
        is_running = not is_running

        if is_running:
            last_move_time = time.monotonic()
            next_move_interval = random.uniform(MOVE_INTERVAL_MIN, MOVE_INTERVAL_MAX)
            if features["debug_enabled"]:
                print(f"[DEBUG] 開始しました (mode_a.value = {mode_a.value}, 次の移動まで {next_move_interval:.1f}秒)")
            else:
                print("▶ 開始しました")
        else:
            if features["debug_enabled"]:
                print("[DEBUG] 停止しました")
            else:
                print("■ 停止しました")

    # 前回の状態を更新
    last_button_state = current_button_state

    # 動作中はランダム間隔でマウスを移動
    if is_running:
        if now - last_move_time >= next_move_interval:
            current_mode = mode_a.value
            if current_mode == False:  # Mode A（スイッチがGNDに接続）
                dx = random.randint(-MOVE_RANGE, MOVE_RANGE)
                dy = random.randint(-MOVE_RANGE, MOVE_RANGE)
            else:  # Mode B（スイッチが開いている）
                dx = random.randint(-MOVE_RANGE_B, MOVE_RANGE_B)
                dy = random.randint(-MOVE_RANGE_B, MOVE_RANGE_B)

            mouse.move(x=dx, y=dy)
            last_move_time = now
            next_move_interval = random.uniform(MOVE_INTERVAL_MIN, MOVE_INTERVAL_MAX)

            if features["debug_enabled"]:
                print(f"[DEBUG] マウス移動: dx={dx:+d}, dy={dy:+d} → 次の移動まで {next_move_interval:.1f}秒")
            else:
                print(f"マウス移動: dx={dx:+d}, dy={dy:+d} → 次の移動まで {next_move_interval:.1f}秒")

    # CPU負荷軽減のため短時間待機
    time.sleep(cuskey_settings.LOOP_DELAY)


"""
【使用方法】
1. cuskey_settings.py と本ファイル（randam_mouse.py）を CIRCUITPY にコピー。
2. randam_mouse.py を code.py にリネームするか、直接実行。
3. adafruit_hid モジュールが CIRCUITPY/lib/ に必要。

【動作説明】
- ボタンを押すごとに「開始」「停止」をトグル。
- 動作中は MOVE_INTERVAL 秒ごとにマウスをランダムな方向へ移動し続ける。
- Mode A（モードスイッチON）: 移動範囲が広い（±MOVE_RANGE px）。
- Mode B（モードスイッチOFF）: 移動範囲が狭い（±MOVE_RANGE_B px）。
- 動作中にモードスイッチを切り替えると移動範囲が即座に切り替わる。

【カスタマイズ】
ファイル上部の定数を変更して動作を調整できます:
  MOVE_RANGE         : Mode A 移動範囲 (±px)
  MOVE_RANGE_B       : Mode B 移動範囲 (±px)
  MOVE_INTERVAL_MIN  : 移動間隔の最小値 (秒)
  MOVE_INTERVAL_MAX  : 移動間隔の最大値 (秒)
"""
