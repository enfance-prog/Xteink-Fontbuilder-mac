# Xteink-Fontbuilder-mac

> 🇺🇸 [English version](./README.md)

**XTeink X3/X4** 向けカスタムフォント BIN ファイルを Mac 上で作成するデスクトップアプリです。
[@feeeeeeen](https://github.com/feeeeeeen/XTeinkToolkit_jp) さんが公開されている Windows 版 C# WinForms ツールを、Python/PySide6 で macOS 向けに再実装したものです。

---

## 機能

- ファイル選択ダイアログから任意の TTF/OTF フォントを指定
- フォントサイズ (pt)・行間 (px)・字間 (px)・縦書き・閾値を設定
- 生成前にプレビューで確認
- Unicode BMP 全文字（65,536 文字）を収録した `.bin` ファイルを出力
- Finder からダブルクリックで起動（セットアップ後はターミナル不要）

---

## 動作環境

- macOS（Apple Silicon・Intel どちらも対応）
- Python 3.9 以上（システム付属または [Homebrew](https://brew.sh) 等でインストール済みのもの）
- 初回セットアップ時のみインターネット接続が必要（pip によるパッケージ取得）

---

## インストール

```bash
# 1. リポジトリをクローン
git clone https://github.com/enfance-prog/Xteink-Fontbuilder-mac.git
cd Xteink-Fontbuilder-mac

# 2. スクリプトに実行権限を付与
chmod +x setup_mac.sh run.sh Xteink-Fontbuilder-mac.command

# 3. セットアップ実行（.venv 作成・依存パッケージのインストール）
./setup_mac.sh
```

自動インストールされる依存パッケージ：
- [PySide6](https://pypi.org/project/PySide6/) — GUI フレームワーク
- [Pillow](https://pypi.org/project/Pillow/) — フォントレンダリング・プレビュー画像

---

## 使い方

### ターミナルから起動

```bash
./run.sh
```

### Finder から起動

**`Xteink-Fontbuilder-mac.command`** をダブルクリックするだけです（ターミナル不要）。

> 初回起動時に macOS のセキュリティ警告が出る場合があります。  
> **システム設定 → プライバシーとセキュリティ** から **「このまま開く」** をクリックしてください。

### 操作の流れ

1. **「TTFを選択…」** から TTF または OTF ファイルを指定する
2. **フォントサイズ (pt)・行間 (px)・字間 (px)・閾値** を好みに合わせて調整する
3. 必要に応じて **「縦書きフォント」** にチェックを入れる
4. **「プレビュー更新」** を押すか、プレビュー領域をクリックして表示を確認する
5. **「BINファイルを生成」** をクリックし、保存先を指定する

> **注意：** Unicode BMP 全 65,536 文字を処理するため、生成には数分かかる場合があります。フォントサイズによってはファイルサイズも大きくなります。

### 出力ファイル名の形式

```
フォント名 18.0pt.24×32.bin
```

（`×` は乗算記号です。幅・高さは設定により変わります。）

---

## 動作確認済みの設定例（X3）

以下の設定は **XTeink X3** で動作確認済みです。
X4 では未確認のため、設定値が変わる可能性があります。

| フォント | サイズ | 行間 | 字間 | 閾値 |
|---|---|---|---|---|
| BIZUDゴシック Regular | 18pt | 1px | 0〜1px | 96 |
| BIZUDゴシック Bold | 18pt | 1px | 0〜1px | 128 |

他のデバイスや設定で試した方は、ぜひ [Issues](https://github.com/enfance-prog/Xteink-Fontbuilder-mac/issues) で共有してください！

---

## ファイル構成

```
Xteink-Fontbuilder-mac/
├── main.py                         # GUI エントリポイント（PySide6）
├── xteink_font.py                  # BIN フォーマット・TTF レンダリングのコアロジック
├── setup_mac.sh                    # 初回セットアップ（venv 作成・依存インストール）
├── run.sh                          # 起動スクリプト
└── Xteink-Fontbuilder-mac.command  # Finder ダブルクリック起動用
```

---

## 設定の保存先

アプリの設定（前回使用したフォントのパスなど）は macOS の `QSettings` に保存されます。

- **Organization:** `XteinkFontbuilder`
- **Application:** `XteinkFontbuilderMac`

---

## クレジット

[@feeeeeeen](https://github.com/feeeeeeen/XTeinkToolkit_jp) さんによる **XTeinkToolkit_jp**（MIT ライセンス）をベースにしています。

本プロジェクトは、返信を待ちましたが連絡が取れなかったため、独立した macOS フォークとして管理しています。フォントビルダー機能を Python/PySide6 で再実装したものです。

---

## ライセンス

[MIT License](./LICENSE)
