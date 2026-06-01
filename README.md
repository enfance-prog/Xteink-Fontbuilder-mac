# Xteink-Fontbuilder-mac

> 🇯🇵 [日本語版はこちら (Japanese)](./README_ja.md)

A macOS desktop app for building custom font BIN files for **XTeink X3/X4** e-ink devices.
This is a Python/PySide6 reimplementation of the original Windows C# WinForms tool created by [@feeeeeeen](https://github.com/feeeeeeen/XTeinkToolkit_jp).

---

## Features

- Select any TTF/OTF font file via the file picker
- Configure font size (pt), line spacing (px), character spacing (px), and vertical writing mode
- Live preview before generating
- Export a `.bin` file covering the full Unicode BMP (65,536 characters)
- One-click launch from Finder (no terminal required after setup)

---

## Requirements

- macOS (Apple Silicon or Intel)
- Python 3.9 or later (system or [Homebrew](https://brew.sh))
- Internet connection for first-time setup (pip packages)

---

## Installation

```bash
# 1. Clone this repository
git clone https://github.com/enfance-prog/Xteink-Fontbuilder-mac.git
cd Xteink-Fontbuilder-mac

# 2. Make scripts executable
chmod +x setup_mac.sh run.sh Xteink-Fontbuilder-mac.command

# 3. Run setup (creates .venv and installs dependencies)
./setup_mac.sh
```

Dependencies installed automatically:
- [PySide6](https://pypi.org/project/PySide6/) — GUI framework
- [Pillow](https://pypi.org/project/Pillow/) — Font rendering and preview

---

## Usage

### Launch from Terminal

```bash
./run.sh
```

### Launch from Finder

Double-click **`Xteink-Fontbuilder-mac.command`** — no terminal needed.

> On first launch, macOS may show a security warning.  
> Go to **System Settings → Privacy & Security** and click **"Open Anyway"**.

### Workflow

1. Click **TTFを選択…** and choose a TTF or OTF file
2. Adjust **font size (pt)**, **line spacing (px)**, **character spacing (px)**, and **threshold** as needed
3. Enable **縦書きフォント** (vertical writing) if required
4. Click **プレビュー更新**, or click the preview area, to verify the output
5. Click **BINファイルを生成** and choose a save location

> **Note:** Generating the BIN covers all 65,536 Unicode BMP characters and may take a minute or two. File sizes can be large depending on font size settings.

### Output filename format

```
FontName 18.0pt.24×32.bin
```

(`×` is the multiplication sign; width and height depend on your settings.)

---

## Tested Settings (X3)

The following settings were confirmed working on **XTeink X3**.
X4 compatibility is untested — results may vary.

| Font | Size | Line Spacing | Char Spacing | Threshold |
|---|---|---|---|---|
| BIZUD Gothic Regular | 18pt | 1px | 0–1px | 96 |
| BIZUD Gothic Bold | 18pt | 1px | 0–1px | 128 |

Feel free to share your settings via [Issues](https://github.com/enfance-prog/Xteink-Fontbuilder-mac/issues) if you find a good combination!

---

## Project Structure

```
Xteink-Fontbuilder-mac/
├── main.py                         # GUI entry point (PySide6)
├── xteink_font.py                  # BIN format & TTF rendering core logic
├── setup_mac.sh                    # First-time setup (venv + pip install)
├── run.sh                          # Launch script
└── Xteink-Fontbuilder-mac.command  # Finder double-click launcher
```

---

## Settings

App preferences (last used font path, etc.) are saved via macOS `QSettings`:

- **Organization:** `XteinkFontbuilder`
- **Application:** `XteinkFontbuilderMac`

---

## Credits

Based on the original **XTeinkToolkit_jp** by [@feeeeeeen](https://github.com/feeeeeeen/XTeinkToolkit_jp), released under the MIT License.

This project is maintained as an independent macOS fork (the original author was contacted but no reply was received). The font builder was reimplemented in Python/PySide6.

---

## License

[MIT License](./LICENSE)
