from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QPixmap, QImage, QTransform

import util


class TextRenderWorker(QThread):
    notations = []
    dictionary_images = {}
    temp_dir = ''
    sgn_worker_done = Signal(list)
    sgn_process_changed = Signal(int)

    def __init__(self, notations, temp_dir, parent=None):
        super(TextRenderWorker, self).__init__(parent)
        self.notations = notations
        self.temp_dir = temp_dir

    def run(self):
        for i, n in enumerate(self.notations):
            util.text2img(n, self.temp_dir)
            pmap = QPixmap(QImage(f'{self.temp_dir}/{n}.png'))
            self.dictionary_images[n] = pmap.transformed(QTransform().rotate(90))
            self.sgn_process_changed.emit(i + 1)
        self.sgn_worker_done.emit([self.dictionary_images])
