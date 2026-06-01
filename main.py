"""
Xteink-Fontbuilder-mac
C# WinForms版をPython + PySide6で完全再実装
フォント選択 → サイズ調整 → BIN生成 → プレビュー
"""
from __future__ import annotations
import sys
import os
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFileDialog, QProgressBar, QGroupBox, QSlider, QMessageBox,
    QSizePolicy, QFrame
)
from PySide6.QtCore import Qt, Signal, QObject, QThread, QSettings
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont, QFontDatabase

from xteink_font import XTEinkFontBinary, XTEinkFontRenderer, TOTAL_CHARS
from PIL import Image, ImageDraw


# ---- プレビュー生成 ----
PREVIEW_TEXT = (
    "あいうえおかきくけこさしすせそたちつてと\n"
    "なにぬねのはひふへほまみむめもやゆよ\n"
    "らりるれろわをんアイウエオカキクケコ\n"
    "漢字テスト：吾輩は猫である。名前はまだない。\n"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\n"
    "0123456789 !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
)


def render_preview_image(font_binary: XTEinkFontBinary,
                          renderer: XTEinkFontRenderer,
                          screen_w: int = 480, screen_h: int = 800) -> QPixmap:
    """プレビュー画像を生成してQPixmapで返す"""
    img = Image.new("RGB", (screen_w, screen_h), (253, 250, 247))
    draw = ImageDraw.Draw(img)
    fw, fh = font_binary.width, font_binary.height
    padding = 4
    cols = (screen_w - padding * 2) // fw
    rows = (screen_h - padding * 2) // fh

    col, row = 0, 0
    for line in PREVIEW_TEXT.split("\n"):
        for ch in line:
            if row >= rows:
                break
            code = ord(ch)
            # グリフをBINから取り出してimgに貼る
            glyph = Image.new("RGB", (fw, fh), (0, 0, 0))
            gdraw = ImageDraw.Draw(glyph)
            for y in range(fh):
                for x in range(fw):
                    if font_binary.get_pixel(code, x, y):
                        glyph.putpixel((x, y), (0, 0, 0))
                    else:
                        glyph.putpixel((x, y), (253, 250, 247))
            px = padding + col * fw
            py = padding + row * fh
            img.paste(glyph, (px, py))
            col += 1
            if col >= cols:
                col = 0
                row += 1
        if row >= rows:
            break
        row += 1
        col = 0

    # PIL → QPixmap
    data = img.tobytes("raw", "RGB")
    qimg = QImage(data, img.width, img.height, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg)


# ---- ワーカースレッド ----
class GenerateWorker(QObject):
    progress = Signal(int, int)   # (current, total)
    finished = Signal(str)         # 保存パス
    error = Signal(str)

    def __init__(self, renderer: XTEinkFontRenderer, output_path: str):
        super().__init__()
        self.renderer = renderer
        self.output_path = output_path

    def run(self):
        try:
            w, h = self.renderer.calculate_render_size()
            fb = XTEinkFontBinary(w, h)

            def on_progress(cur, total):
                self.progress.emit(cur, total)

            self.renderer.render_all(fb, progress_callback=on_progress)
            fb.save(self.output_path)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


# ---- メインウィンドウ ----
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xteink-Fontbuilder-mac")
        self.setMinimumWidth(620)
        self.renderer = XTEinkFontRenderer()
        self.ttf_path: str = ""
        self.preview_fb: XTEinkFontBinary | None = None
        self._worker_thread: QThread | None = None
        self._settings = QSettings("XteinkFontbuilder", "XteinkFontbuilderMac")
        self._build_ui()
        self._restore_settings()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ---- フォント選択 ----
        font_group = QGroupBox("フォント設定")
        fg_layout = QVBoxLayout(font_group)

        row1 = QHBoxLayout()
        self.lbl_font = QLabel("（フォント未選択）")
        self.lbl_font.setWordWrap(True)
        self.lbl_font.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btn_font = QPushButton("TTFを選択…")
        btn_font.setFixedWidth(120)
        btn_font.clicked.connect(self._select_font)
        row1.addWidget(self.lbl_font)
        row1.addWidget(btn_font)
        fg_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("フォントサイズ (pt):"))
        self.spin_size = QDoubleSpinBox()
        self.spin_size.setRange(6.0, 72.0)
        self.spin_size.setSingleStep(0.5)
        self.spin_size.setValue(18.0)
        self.spin_size.valueChanged.connect(self._on_settings_changed)
        row2.addWidget(self.spin_size)

        row2.addSpacing(20)
        row2.addWidget(QLabel("行間 (px):"))
        self.spin_line = QSpinBox()
        self.spin_line.setRange(-20, 40)
        self.spin_line.setValue(0)
        self.spin_line.valueChanged.connect(self._on_settings_changed)
        row2.addWidget(self.spin_line)

        row2.addSpacing(20)
        row2.addWidget(QLabel("字間 (px):"))
        self.spin_char = QSpinBox()
        self.spin_char.setRange(-20, 40)
        self.spin_char.setValue(0)
        self.spin_char.valueChanged.connect(self._on_settings_changed)
        row2.addWidget(self.spin_char)
        row2.addStretch()
        fg_layout.addLayout(row2)

        row3 = QHBoxLayout()
        self.chk_vertical = QCheckBox("縦書きフォント")
        self.chk_vertical.stateChanged.connect(self._on_settings_changed)
        row3.addWidget(self.chk_vertical)

        row3.addSpacing(20)
        row3.addWidget(QLabel("閾値 (threshold):"))
        self.spin_threshold = QSpinBox()
        self.spin_threshold.setRange(1, 254)
        self.spin_threshold.setValue(128)
        self.spin_threshold.valueChanged.connect(self._on_settings_changed)
        row3.addWidget(self.spin_threshold)
        row3.addStretch()
        fg_layout.addLayout(row3)

        root.addWidget(font_group)

        # ---- 生成サイズ表示 ----
        self.lbl_render_size = QLabel("レンダリングサイズ: 未計算")
        self.lbl_render_size.setStyleSheet("color: #666;")
        root.addWidget(self.lbl_render_size)

        # ---- プレビュー ----
        prev_group = QGroupBox("プレビュー（クリックで更新）")
        prev_layout = QVBoxLayout(prev_group)
        self.lbl_preview = QLabel()
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setFixedHeight(280)
        self.lbl_preview.setStyleSheet("background:#fdfaf7; border:1px solid #ccc;")
        self.lbl_preview.mousePressEvent = lambda _: self._update_preview()
        prev_layout.addWidget(self.lbl_preview)
        btn_preview = QPushButton("プレビュー更新")
        btn_preview.clicked.connect(self._update_preview)
        prev_layout.addWidget(btn_preview)
        root.addWidget(prev_group)

        # ---- 生成ボタン ----
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        btn_row = QHBoxLayout()
        self.btn_generate = QPushButton("BINファイルを生成")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.setStyleSheet(
            "QPushButton { background:#2a6ebb; color:white; font-weight:bold; border-radius:6px; }"
            "QPushButton:disabled { background:#aaa; }"
        )
        self.btn_generate.clicked.connect(self._generate)
        btn_row.addWidget(self.btn_generate)
        root.addLayout(btn_row)

        # ---- プログレスバー ----
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, TOTAL_CHARS)
        root.addWidget(self.progress_bar)

        self.lbl_status = QLabel("")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.lbl_status)

    # ---- イベント ----
    def _select_font(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "TTFフォントを選択", "", "フォントファイル (*.ttf *.otf)"
        )
        if not path:
            return
        self.ttf_path = path
        name = Path(path).name
        self.lbl_font.setText(name)
        self._on_settings_changed()

    def _on_settings_changed(self):
        if not self.ttf_path:
            return
        try:
            self.renderer.load_font(self.ttf_path, self.spin_size.value())
            self.renderer.line_spacing_px = self.spin_line.value()
            self.renderer.char_spacing_px = self.spin_char.value()
            self.renderer.is_vertical = self.chk_vertical.isChecked()
            self.renderer.threshold = self.spin_threshold.value()
            w, h = self.renderer.calculate_render_size()
            self.lbl_render_size.setText(
                f"レンダリングサイズ: {w}×{h} px  "
                f"（ファイルサイズ目安: {((-(-w//8))*h*65536)//1024//1024:.1f} MB）"
            )
        except Exception as e:
            self.lbl_render_size.setText(f"エラー: {e}")

    def _update_preview(self):
        if not self.ttf_path:
            QMessageBox.information(self, "情報", "先にTTFフォントを選択してください。")
            return
        try:
            self._apply_renderer_settings()
            w, h = self.renderer.calculate_render_size()
            fb = XTEinkFontBinary(w, h)
            # プレビューに必要な文字だけレンダリング（高速化）
            chars_needed = set()
            for line in PREVIEW_TEXT.split("\n"):
                for ch in line:
                    chars_needed.add(ord(ch))
            self.renderer.render_all(fb, target_chars=list(chars_needed))
            self.preview_fb = fb
            pix = render_preview_image(fb, self.renderer)
            scaled = pix.scaled(
                self.lbl_preview.width(), self.lbl_preview.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.lbl_preview.setPixmap(scaled)
        except Exception as e:
            self.lbl_status.setText(f"プレビューエラー: {e}")

    def _apply_renderer_settings(self):
        self.renderer.load_font(self.ttf_path, self.spin_size.value())
        self.renderer.line_spacing_px = self.spin_line.value()
        self.renderer.char_spacing_px = self.spin_char.value()
        self.renderer.is_vertical = self.chk_vertical.isChecked()
        self.renderer.threshold = self.spin_threshold.value()

    def _generate(self):
        if not self.ttf_path:
            QMessageBox.warning(self, "エラー", "TTFフォントを選択してください。")
            return
        try:
            self._apply_renderer_settings()
            w, h = self.renderer.calculate_render_size()
        except Exception as e:
            QMessageBox.warning(self, "エラー", str(e))
            return

        font_name = Path(self.ttf_path).stem
        suggested = f"{font_name} {self.spin_size.value():.1f}pt.{w}×{h}.bin"
        out_path, _ = QFileDialog.getSaveFileName(
            self, "BINファイルの保存先", suggested, "BINファイル (*.bin)"
        )
        if not out_path:
            return

        # スレッドで生成
        self.btn_generate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("生成中…（Unicode全文字をレンダリングしています）")

        self._worker_thread = QThread()
        self._worker = GenerateWorker(self.renderer, out_path)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker_thread.start()

    def _on_progress(self, cur: int, total: int):
        self.progress_bar.setValue(cur)
        pct = int(cur / total * 100)
        self.lbl_status.setText(f"生成中… {pct}%")

    def _on_finished(self, path: str):
        self._worker_thread.quit()
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"✅ 生成完了: {Path(path).name}")
        QMessageBox.information(self, "完了", f"BINファイルを保存しました。\n{path}")
        self._save_settings()

    def _on_error(self, msg: str):
        self._worker_thread.quit()
        self.btn_generate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"❌ エラー: {msg}")
        QMessageBox.critical(self, "エラー", msg)

    def _save_settings(self):
        self._settings.setValue("ttf_path", self.ttf_path)
        self._settings.setValue("font_size", self.spin_size.value())
        self._settings.setValue("line_spacing", self.spin_line.value())
        self._settings.setValue("char_spacing", self.spin_char.value())
        self._settings.setValue("vertical", self.chk_vertical.isChecked())
        self._settings.setValue("threshold", self.spin_threshold.value())

    def _restore_settings(self):
        path = self._settings.value("ttf_path", "")
        if path and Path(path).exists():
            self.ttf_path = path
            self.lbl_font.setText(Path(path).name)
        self.spin_size.setValue(float(self._settings.value("font_size", 18.0)))
        self.spin_line.setValue(int(self._settings.value("line_spacing", 0)))
        self.spin_char.setValue(int(self._settings.value("char_spacing", 0)))
        self.chk_vertical.setChecked(self._settings.value("vertical", False) == "true")
        self.spin_threshold.setValue(int(self._settings.value("threshold", 128)))
        if self.ttf_path:
            self._on_settings_changed()

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Xteink-Fontbuilder-mac")
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
