# Raspberry Pi Pico メディアキーボード - 統合版

## 概要

このプロジェクトは、Raspberry Pi Picoを使用したUSBメディアキーボードの実装です。
PIN配置は、設定ファイルで簡単に切り替えることができます。

## 機能

- **Play/Pause コントロール**: メディア再生の制御
- **マウスホイール操作**: スクロール制御
- **巻き戻し機能**: 左矢印キーによる巻き戻し
- **モード切替**: スイッチによる動作モードの切り替え
- **長押し検出**: 1.5秒の長押しで異なる動作を実行

## ファイル構成

```
/
├── code.py          # メインプログラム（統合版）
├── settings.py      # ボード設定ファイル
└── examples/       # sample code
```

## 対応ボード

### 1. Pattern Pin配置 4PIN

**ピン接続:**
- GP5: ボタン用GND
- GP6: ボタン入力（プルアップ）
- GP7: モード切替用GND
- GP8: モードA入力（プルアップ）

### 2. Pattern Pin配置 2PIN + 3PIN

**ピン接続:**
- GP7: ボタン用GND
- GP8: ボタン入力（プルアップ）
- GP11: モード切替用GND
- GP10: モードA入力（プルアップ）
- GP12: モードB入力（未使用、将来の拡張用）

## セットアップ手順

### 1. 必要なライブラリのインストール

CircuitPython用のHIDライブラリが必要です。以下のファイルを`lib/`フォルダにコピーしてください：

ex on mac /Volumes/CIRCUITPY/
```
lib/
├── adafruit_hid/
│   ├── __init__.py
│   ├── keyboard.py
│   ├── keycode.py
│   ├── consumer_control.py
│   ├── consumer_control_code.py
│   └── mouse.py
```

### 2. ボードの選択

`cuskey_settings.py`ファイルを開き、使用するボードを指定します：

```python
# ボードタイプを選択（"PinPat4" または "PinPat23"）
BOARD_TYPE = "PinPat4"  # <- ここを変更
```

### 3. デバッグモードの設定

必要に応じてデバッグモードの有効/無効を切り替えます：

```python
# デバッグモードの有効/無効
DEBUG_MODE = True  # デバッグ出力を有効にする場合はTrue
```

### 4. ファイルの転送

1. Raspberry Pi PicoをUSBケーブルでPCに接続
2. `code.py`と`cuskey_settings.py`をPicoのルートディレクトリにコピー
3. 必要なライブラリを`lib/`フォルダにコピー
4. Picoが自動的に再起動し、プログラムが実行されます

## 使用方法

### 動作モード

#### Mode A（スイッチをGNDに接続）
- **通常押下**: Play/Pause
- **長押し（1.5秒）**: 巻き戻し（左矢印キー×2）

#### Mode B（スイッチ開放）
- **通常押下**: マウスホイール下
- **長押し（1.5秒）**: Play/Pause

### 回路図

```
[ボタン回路]
Button Pin ──┬── Button ──── Button GND Pin
             └── Pull-up抵抗（内部）

[モード切替回路]
Mode A Pin ──┬── Switch ──── Mode GND Pin
             └── Pull-up抵抗（内部）
```

## カスタマイズ

### 設定パラメータの変更

`settings.py`で以下のパラメータを調整できます：

- `LONG_PRESS_THRESHOLD`: 長押し判定時間（デフォルト: 1.0秒）
- `DEBOUNCE_TIME`: チャタリング防止時間（デフォルト: 0.05秒）
- `LOOP_DELAY`: メインループの待機時間（デフォルト: 0.01秒）
- `DEBUG_COUNTER_THRESHOLD`: デバッグ表示の頻度（デフォルト: 100サイクル）

### 新しいボードの追加

`cuskey_settings.py`の`BOARD_CONFIGS`辞書に新しいボード設定を追加できます：

```python
BOARD_CONFIGS = {
    "PinPatX": {
        "name": "Your Board Name",
        "pins": {
            "button_gnd": board.GPxx,
            "button": board.GPxx,
            "mode_gnd": board.GPxx,
            "mode_a": board.GPxx,
            "mode_b": None,
        },
        "features": {
            "debug_enabled": True,
            "dual_mode": False,
        }
    }
}
```

## トラブルシューティング

### よくある問題と解決方法

1. **ボタンが反応しない**
   - ピン接続を確認
   - プルアップ抵抗が有効になっているか確認
   - GNDピンが正しく設定されているか確認

2. **モード切替が機能しない**
   - スイッチの接続を確認
   - `settings.py`でピン番号が正しく設定されているか確認

3. **デバッグ出力が表示されない**
   - `DEBUG_MODE`が`True`に設定されているか確認
   - シリアルモニターが正しく接続されているか確認

4. **巻き戻しが効かない**
   - 対象アプリケーションにフォーカスが当たっているか確認
   - Windowsの場合、メディアプレーヤーが左矢印キーに対応しているか確認

## 技術仕様

- **プログラミング言語**: CircuitPython
- **対応OS**: Windows, macOS, Linux
- **USB仕様**: USB HID (Human Interface Device)
- **消費電力**: 約50mA（動作時）

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

バグ報告や機能提案は、GitHubのIssuesにてお願いします。

## 更新履歴

- **v1.0.0** (2025-08-24): 初回リリース


## 参考資料

- [CircuitPython HID Library](https://github.com/adafruit/Adafruit_CircuitPython_HID)
- [Raspberry Pi Pico Documentation](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html)
- [USB HID Usage Tables](https://www.usb.org/hid)
