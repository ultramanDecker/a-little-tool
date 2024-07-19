from PySide6.QtCore import Signal
from PySide6.QtWidgets import QProgressBar


class ProcessBar(QProgressBar):
    sgn_finished = Signal()

    def __init__(self, parent=None):
        super(ProcessBar, self).__init__(parent)
        self.valueChanged.connect(self.sgn_finished)

    def increase(self):
        self.setValue(self.value() + 1)

    def on_index_changed(self, index):
        if self.value() == self.maximum():
            self.sgn_finished.emit()
