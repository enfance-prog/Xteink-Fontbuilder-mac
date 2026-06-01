"""
XTEinkFontBinary - XTeink X3/X4のBINフォーマットをPythonで実装
C#ソース（XTEinkFontBinary.cs / Utility.cs）から完全移植

BINフォーマット仕様（ソース解析結果）:
  - 0x10000文字（Unicode全域）分のビットマップを格納
  - 各文字: ceil(width/8) * height バイト
  - ピクセルはMSBファースト（0x80が左端）
  - ファイルサイズ = ceil(width/8) * height * 65536
"""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import struct


TOTAL_CHARS = 0x10000  # Unicode BMP全域


class XTEinkFontBinary:
    """XTeinkのBINフォントファイルを生成・操作するクラス"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.width_byte = math.ceil(width / 8)
        self.char_byte = self.width_byte * height
        # 全文字分ゼロ初期化
        self.data = bytearray(self.char_byte * TOTAL_CHARS)

    # ---- ビット操作 ----
    _BIT_MASK = [0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01]

    def _pixel_offset(self, char_code: int, x: int, y: int) -> tuple[int, int]:
        base = char_code * self.char_byte
        base += y * self.width_byte
        base += x // 8
        return base, x % 8

    def get_pixel(self, char_code: int, x: int, y: int) -> bool:
        idx, bit = self._pixel_offset(char_code, x, y)
        return bool(self.data[idx] & self._BIT_MASK[bit])

    def set_pixel(self, char_code: int, x: int, y: int, value: bool):
        idx, bit = self._pixel_offset(char_code, x, y)
        if value:
            self.data[idx] |= self._BIT_MASK[bit]
        else:
            self.data[idx] &= ~self._BIT_MASK[bit] & 0xFF

    # ---- PIL Image からグリフを読み込む ----
    def load_from_image(self, char_code: int, img: Image.Image,
                        sx: int = 0, sy: int = 0, threshold: int = 128):
        """PIL Imageからグリフデータを読み込む（Greenチャンネルで輝度判定）"""
        rgb = img.convert("RGB")
        for y in range(self.height):
            for x in range(self.width):
                r, g, b = rgb.getpixel((sx + x, sy + y))
                # C#版: Green > threshold でON（白=文字）
                self.set_pixel(char_code, x, y, g > threshold)

    # ---- ファイルI/O ----
    def save(self, path: str | Path):
        Path(path).write_bytes(self.data)

    def load(self, path: str | Path):
        raw = Path(path).read_bytes()
        length = min(len(raw), len(self.data))
        self.data[:length] = raw[:length]

    def get_suggested_filename(self, font_name: str) -> str:
        return f"{font_name} {self.width}×{self.height}.bin"


class XTEinkFontRenderer:
    """TTFフォントをXTEinkFontBinaryにレンダリングするクラス"""

    def __init__(self):
        self.font: ImageFont.FreeTypeFont | None = None
        self.font_path: str = ""
        self.font_size_pt: float = 18.0
        self.is_vertical: bool = False
        self.threshold: int = 128
        self.line_spacing_px: int = 0
        self.char_spacing_px: int = 0

    def load_font(self, ttf_path: str, size_pt: float):
        """TTFファイルを読み込む。size_ptはポイント単位（96dpi基準でpxに変換）"""
        self.font_path = ttf_path
        self.font_size_pt = size_pt
        # 96dpi: px = pt * 96 / 72
        size_px = int(round(size_pt * 96 / 72))
        self.font = ImageFont.truetype(ttf_path, size_px)

    def calculate_render_size(self) -> tuple[int, int]:
        """フォントサイズからグリフのピクセルサイズを計算"""
        if self.font is None:
            raise RuntimeError("フォントが読み込まれていません")
        # テスト文字で測定
        test_img = Image.new("RGB", (256, 256), (0, 0, 0))
        draw = ImageDraw.Draw(test_img)
        bbox = draw.textbbox((0, 0), "坐", font=self.font)
        w = bbox[2] - bbox[0] + self.char_spacing_px
        h = bbox[3] - bbox[1] + self.line_spacing_px
        w = max(w, 5)
        h = max(h, 5)
        return w, h

    def render_char(self, char_code: int, font_binary: XTEinkFontBinary):
        """1文字をレンダリングしてfont_binaryに書き込む"""
        if self.font is None:
            raise RuntimeError("フォントが読み込まれていません")
        w, h = font_binary.width, font_binary.height
        # 黒背景に白文字でレンダリング（C#版と同じ）
        img = Image.new("RGB", (w, h), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        char = chr(char_code)

        if self.is_vertical:
            # 縦書き: 90度回転して描画
            tmp = Image.new("RGB", (h, w), (0, 0, 0))
            tmp_draw = ImageDraw.Draw(tmp)
            offset_y = self.line_spacing_px // 2 if self.line_spacing_px > 0 else 0
            offset_x = self.char_spacing_px // 2 if char_code > 255 and self.char_spacing_px != 0 else 0
            tmp_draw.text((offset_x, offset_y), char, font=self.font, fill=(255, 255, 255))
            rotated = tmp.rotate(90, expand=False)
            img.paste(rotated.crop((0, 0, w, h)), (0, 0))
        else:
            offset_y = self.line_spacing_px // 2 if self.line_spacing_px > 0 else 0
            offset_x = self.char_spacing_px // 2 if char_code > 255 and self.char_spacing_px != 0 else 0
            draw.text((offset_x, offset_y), char, font=self.font, fill=(255, 255, 255))

        font_binary.load_from_image(char_code, img, threshold=self.threshold)

    def render_all(self, font_binary: XTEinkFontBinary,
                   progress_callback=None, target_chars: list[int] | None = None):
        """全Unicode BMP（または指定文字リスト）をレンダリング"""
        chars = target_chars if target_chars is not None else range(TOTAL_CHARS)
        total = len(list(chars)) if hasattr(chars, '__len__') else TOTAL_CHARS
        for i, code in enumerate(chars):
            try:
                self.render_char(code, font_binary)
            except Exception:
                pass  # レンダリング不可文字はスキップ
            if progress_callback and i % 256 == 0:
                progress_callback(i, total)
