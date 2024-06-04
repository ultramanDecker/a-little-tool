from PySide6.QtCore import QThread, Signal

import util


class MatchWorker(QThread):
    sgn_match_done = Signal(list)
    page_image_file = ''
    word_images_directory = ''

    def __init__(self, page_image_file, word_images_directory, parent=None):
        super(MatchWorker, self).__init__(parent)
        self.page_image_file = page_image_file
        self.word_images_directory = word_images_directory

    def run(self):
        position_list = util.get_position_list(self.page_image_file, self.word_images_directory)
        self.sgn_match_done.emit(position_list)
