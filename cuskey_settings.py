"""
ボード設定ファイル
各ボードのピン設定と機能設定を定義
"""

import board

# ボードタイプを選択（"ProMiroPico" または "Piromoni_PocoMini"）
BOARD_TYPE = "PinPat4"  # 使用するボードをここで指定

# デバッグモードの有効/無効
DEBUG_MODE = True  # デバッグ出力を有効にする場合はTrue

# 長押し判定の閾値（秒）
LONG_PRESS_THRESHOLD = 1.0

# チャタリング防止の待機時間（秒）
DEBOUNCE_TIME = 0.05

# CPUサイクル待機時間（秒）
LOOP_DELAY = 0.01

# デバッグカウンターの閾値（約1秒ごとに表示）
DEBUG_COUNTER_THRESHOLD = 100

# ボード固有のピン設定
BOARD_CONFIGS = {
    "PinPat4": {
        "name": "4pin",
        "pins": {
            "button_gnd": board.GP5,    # ボタン用GNDピン
            "button": board.GP6,         # ボタン入力ピン
            "mode_gnd": board.GP7,       # モード切替用GNDピン
            "mode_a": board.GP8,         # モードAピン
            "mode_b": None,              # モードBピン（未使用）
        },
        "features": {
            "debug_enabled": True,       # デバッグ機能の有効化
            "dual_mode": False,          # デュアルモード（mode_bを使用）
        }
    },
    "PinPat23": {
        "name": "2pin_3pin ",
        "pins": {
            "button_gnd": board.GP7,    # ボタン用GNDピン
            "button": board.GP8,         # ボタン入力ピン
            "mode_gnd": board.GP11,      # モード切替用GNDピン
            "mode_a": board.GP10,        # モードAピン
            "mode_b": board.GP12,        # モードBピン（定義はあるが未使用）
        },
        "features": {
            "debug_enabled": False,      # デバッグ機能の無効化
            "dual_mode": False,          # デュアルモード（mode_bを使用）
        }
    }
}

# 選択されたボードの設定を取得
def get_board_config():
    """現在選択されているボードの設定を返す"""
    if BOARD_TYPE not in BOARD_CONFIGS:
        raise ValueError(f"不明なボードタイプ: {BOARD_TYPE}")
    return BOARD_CONFIGS[BOARD_TYPE]

# ピン設定を取得
def get_pins():
    """現在のボードのピン設定を返す"""
    return get_board_config()["pins"]

# 機能設定を取得
def get_features():
    """現在のボードの機能設定を返す"""
    config = get_board_config()["features"]
    # グローバル設定でオーバーライド可能
    if DEBUG_MODE is not None:
        config["debug_enabled"] = DEBUG_MODE
    return config

# ボード名を取得
def get_board_name():
    """現在のボード名を返す"""
    return get_board_config()["name"]