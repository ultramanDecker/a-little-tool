from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QCheckBox

import util


class ControlBar(QWidget):
    index = 0
    max_count = 0
    sgn_index_changed = Signal(int)
    sgn_confirmed = Signal(list)
    check_list = []

    def __init__(self):
        super().__init__()
        self.prev_button = QPushButton('前一个')
        self.next_button = QPushButton('后一个')
        self.check_box = QCheckBox('是否正确')
        self.index_label = QLabel(f'0/0')
        self.index_label.setMaximumSize(100, 100)
        self.confirm_button = QPushButton('完成')

        self.prev_button.clicked.connect(self.on_prev_button_clicked)
        self.next_button.clicked.connect(self.on_next_button_clicked)
        self.sgn_index_changed.connect(self.on_index_change)
        self.check_box.clicked.connect(self.on_check_box_clicked)
        self.confirm_button.clicked.connect(self.on_confirm_button_clicked)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.prev_button)
        self.layout.addWidget(self.next_button)
        self.layout.addWidget(self.check_box)
        self.layout.addWidget(self.index_label)
        self.layout.addWidget(self.confirm_button)

    def disable(self):
        self.prev_button.setDisabled(True)
        self.next_button.setDisabled(True)
        self.check_box.setDisabled(True)
        self.confirm_button.setDisabled(True)

    def enable(self):
        self.prev_button.setDisabled(False)
        self.next_button.setDisabled(False)
        self.check_box.setDisabled(False)
        self.confirm_button.setDisabled(False)

    def set_max_count(self, max_count):
        self.max_count = max_count
        self.check_list = [False] * max_count
        self.sgn_index_changed.emit(self.index)

    @Slot()
    def on_index_change(self, index):
        self.index_label.setText(f'{self.index + 1}/{self.max_count}')
        self.check_box.setChecked(self.check_list[index])

    @Slot()
    def on_check_box_clicked(self):
        self.check_list[self.index] = self.check_box.isChecked()

    @Slot()
    def on_prev_button_clicked(self):
        if self.index <= 0:
            return
        else:
            self.index -= 1
            self.sgn_index_changed.emit(self.index)

    @Slot()
    def on_next_button_clicked(self):
        if self.index >= self.max_count - 1:
            return

        else:
            self.index += 1
            self.sgn_index_changed.emit(self.index)

    @Slot()
    def on_confirm_button_clicked(self):
        self.disable()
        self.sgn_confirmed.emit(self.check_list)
