# examples/ プログラム一覧

`cuskey_settings.py` で管理するハードウェア設定を共通で利用する CircuitPython サンプル集です。
すべてのスクリプトはボタン 1 個＋モードスイッチ 1 個の構成を前提としています。

---

## 1. [`auto_keysend.py`](auto_keysend.py)

**自動矢印キー送信**

> ボタンを短押しすることで自動送信の ON/OFF をトグルし、設定した秒数間隔で矢印キーを自動送信します。
> 長押し中は手動で連続送信が可能で、プレゼンのスライド送りや定期的なキー入力の自動化に使用します。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 自動送信 | 左矢印キーを `SEND_INTERVAL` 秒ごとに送信 | 右矢印キーを `SEND_INTERVAL` 秒ごとに送信 |
| 短押し | 自動送信を有効／無効トグル | 同左 |
| 長押し | 押している間、左矢印を連続送信 | 押している間、右矢印を連続送信 |

主要定数: `SEND_INTERVAL`（秒）、`LONG_PRESS_TIME`、`MANUAL_SEND_INTERVAL`

---

## 2. [`meeting_controller.py`](meeting_controller.py)

**リモート会議用コントローラー**

> Zoom・Teams・Google Meet などのオンライン会議でよく使う「マイクミュート切り替え」と「音量調整」を
> ボタン 1 個で操作できます。短押しでミュートトグル、長押しでモードに応じた音量変更を行います。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 短押し | マイクミュート切り替え（`MIC_MUTE`） | 同左 |
| 長押し | 音量アップを連続送信 | 音量ダウンを連続送信 |

主要定数: `LONG_PRESS_TIME`（0.3秒）、`VOLUME_INTERVAL`（0.1秒）

---

## 3. [`pin_sender.py`](pin_sender.py)

**PINコード自動入力キーボード**

> ボタンを押すだけで、あらかじめ設定した数字列（PINコード）を自動でタイプします。
> Mode A / B に 2 種類の PIN を登録でき、ロック解除画面への入力補助などに使用します。
> ⚠️ PIN は平文保存のため、銀行等の重要情報への使用は非推奨です。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 短押し | `PIN_MODE_A` の数字列を送信 | `PIN_MODE_B` の数字列を送信 |

主要定数: `PIN_MODE_A`、`PIN_MODE_B`、`DIGIT_INTERVAL`、`PRE_SEND_ESCAPE`、`POST_SEND_ENTER`

---

## 4. [`ptt_key.py`](ptt_key.py)

**Push-To-Talk（PTT）キーボード**

> Whisper Flow・Discord・Zoom などの PTT（押している間だけマイク ON）操作と、
> PDF ビューアやブラウザのページスクロールをモードで切り替えて使うコントローラーです。
> ダブルクリック検出により、1 つのボタンで 3 種類のアクションを割り当てられます。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 短押し（タイムアウト後確定） | Enter キー送信 | Page Down 送信 |
| 長押し | `PTT_KEYS` のキーを押し続ける（離すとリリース） | マウスホイールダウンを連続送信 |
| ダブルクリック | ESC キー送信 | Page Up 送信 |

主要定数: `PTT_KEYS`（最大 3 キー同時押し）、`DOUBLE_CLICK_TIME`、`LONG_PRESS_TIME`、`WHEEL_SCROLL_INTERVAL`

---

## 5. [`random_mouse.py`](random_mouse.py)

**ランダムマウス移動コントローラー**

> ボタンを押すたびにマウスのランダム移動を開始／停止します。
> スクリーンセーバーや画面ロックの防止、PCのアイドル状態を回避するために使用します。
> Mode でランダム移動の幅を大小切り替えられます。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 短押し | ランダム移動を開始（±30px） | ランダム移動を開始（±10px） |
| もう一度短押し | 停止 | 停止 |
| 動作中のモード切替 | 移動範囲が即座に変わる | 同左 |

主要定数: `MOVE_RANGE`（30px）、`MOVE_RANGE_B`（10px）、`MOVE_INTERVAL_MIN` / `MOVE_INTERVAL_MAX`

---

## 6. [`youtube_controller.py`](youtube_controller.py)

**メディアプレイヤーコントローラー**

> YouTube などの動画プレイヤーを手元のボタンで操作するためのコントローラーです。
> 短押しで再生・一時停止、長押しで巻き戻し／ページスクロールを操作できます。
> Keyboard・ConsumerControl・Mouse をすべて組み合わせたリファレンス実装です。

| 操作 | Mode A | Mode B |
|------|--------|--------|
| 短押し | `PLAY_PAUSE` 送信 | マウスホイール下（スクロール） |
| 長押し | 左矢印キー×2（5秒巻き戻し） | `PLAY_PAUSE` 送信 |

主要定数: `LONG_PRESS_THRESHOLD`（[`cuskey_settings.py`](../cuskey_settings.py) で管理）

---

## HID 機能の使用一覧

| スクリプト | Keyboard | ConsumerControl | Mouse |
|-----------|:--------:|:---------------:|:-----:|
| `auto_keysend.py` | ✅ | — | — |
| `meeting_controller.py` | — | ✅ | — |
| `pin_sender.py` | ✅ | — | — |
| `ptt_key.py` | ✅ | — | ✅ |
| `random_mouse.py` | — | — | ✅ |
| `youtube_controller.py` | ✅ | ✅ | ✅ |
