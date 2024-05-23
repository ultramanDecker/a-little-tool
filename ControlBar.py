import random

from PySide6.QtCore import Slot, Signal
from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QHBoxLayout, QCheckBox, QSpinBox, QVBoxLayout

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
        self.index_label = QLabel(f'进度: 0/0')
        self.rate_label = QLabel(f'正确率: 0/0')
        self.index_label.setMaximumSize(100, 100)
        self.confirm_button = QPushButton('重命名')
        self.rate_spin = QSpinBox()
        self.rate_spin.setMaximum(100)
        self.rate_spin.setMinimum(0)
        self.rate_spin.setSuffix('%')
        self.random_button = QPushButton('随机设置')

        self.random_button.clicked.connect(self.on_random_button_clicked)
        self.prev_button.clicked.connect(self.on_prev_button_clicked)
        self.next_button.clicked.connect(self.on_next_button_clicked)
        self.sgn_index_changed.connect(self.on_index_change)
        self.check_box.clicked.connect(self.on_check_box_clicked)
        self.check_box.stateChanged.connect(self.on_check_box_clicked)
        self.confirm_button.clicked.connect(self.on_confirm_button_clicked)

        self.control_layout = QHBoxLayout()
        self.status_layout = QHBoxLayout()

        self.control_layout.addWidget(self.prev_button)
        self.control_layout.addWidget(self.next_button)
        self.control_layout.addWidget(self.check_box)
        self.control_layout.addWidget(self.rate_spin)
        self.control_layout.addWidget(self.random_button)
        self.control_layout.addWidget(self.confirm_button)
        self.status_layout.addWidget(self.index_label)
        self.status_layout.addWidget(self.rate_label)

        self.layout = QVBoxLayout(self)

        self.layout.addLayout(self.control_layout)
        self.layout.addLayout(self.status_layout)

    def disable(self):
        self.prev_button.setDisabled(True)
        self.next_button.setDisabled(True)
        self.check_box.setDisabled(True)
        self.confirm_button.setDisabled(True)
        self.random_button.setDisabled(True)

    def enable(self):
        self.prev_button.setDisabled(False)
        self.next_button.setDisabled(False)
        self.check_box.setDisabled(False)
        self.confirm_button.setDisabled(False)
        self.random_button.setDisabled(False)

    def set_max_count(self, max_count):
        self.max_count = max_count
        self.check_list = [False] * max_count
        self.rate_label.setText(f'准确率: {self.check_list.count(True)}/{self.max_count}')
        self.index_label.setText(f'进度: {self.index + 1}/{self.max_count}')
        self.sgn_index_changed.emit(self.index)

    @Slot()
    def on_random_button_clicked(self):
        rate = self.rate_spin.value() / 100
        self.check_list = random.choices([True, False], weights=[rate, 1 - rate], k=self.max_count)
        self.rate_label.setText(f'准确率: {self.check_list.count(True)}/{self.max_count}')

    @Slot()
    def on_index_change(self, index):
        self.index_label.setText(f'进度: {self.index + 1}/{self.max_count}')
        self.check_box.setChecked(self.check_list[index])

    @Slot()
    def on_check_box_clicked(self):
        self.check_list[self.index] = self.check_box.isChecked()
        self.rate_label.setText(f'准确率: {self.check_list.count(True)}/{self.max_count}')
        # self.sgn_index_changed.emit(self.index)

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
