from PySide6.QtGui import QPixmap, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QSizePolicy


class ImageComparePanel(QWidget):
    def __init__(self):
        super().__init__()
        # self.setStyleSheet('border: 1px solid red;')
        self.right_layout = QVBoxLayout()
        self.left_layout = QVBoxLayout()

        self.left_image = QLabel()
        # self.left_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.left_tips = QLabel()
        self.left_layout.addWidget(self.left_image)
        self.left_layout.addWidget(self.left_tips)
        self.left_layout.setStretch(0, 10)
        self.left_layout.setStretch(1, 1)

        self.right_image = QLabel()
        # self.right_image.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.right_tips = QLabel()
        self.right_layout.addWidget(self.right_image)
        self.right_layout.addWidget(self.right_tips)
        self.right_layout.setStretch(0, 10)
        self.right_layout.setStretch(1, 1)

        self.layout = QHBoxLayout(self)

        self.layout.addLayout(self.left_layout)
        self.layout.addLayout(self.right_layout)

    def set_left(self, image: QPixmap, tips: str = ''):
        self.left_image.setScaledContents(True)
        image.scaled(self.left_image.size(), Qt.AspectRatioMode.KeepAspectRatio)

        self.left_image.setPixmap(image)
        # self.left_image.setGeometry(0, 0, image.height()*2, image.width()*2)
        self.left_tips.setText(tips)

    def set_right(self, image: QPixmap, tips: str = ''):
        self.right_image.setScaledContents(True)
        self.right_image.setPixmap(image)
        self.right_tips.setText(tips)
