from PySide6.QtCore import QThread


class TestThread(QThread):
    def __init__(self,parent=None):
        super().__init__(parent)

    def run(self):
        return
