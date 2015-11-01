from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter
from PyQt5.QtWidgets import QDial


class Gauge(QDial):
    """Custom QDial with current value shown in middle."""

    def paintEvent(self, event):
        painter = QPainter(self)
        font = painter.font()
        font.setPointSize(self.width() / 6.0)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter | Qt.AlignVCenter, str(self.value()))
        QDial.paintEvent(self, event)
