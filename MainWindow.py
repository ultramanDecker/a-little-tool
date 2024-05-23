import os
import re
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QUrl, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PySide6.QtWidgets import QWidget, QFileDialog, QDialog, QDialogButtonBox
from lxml import etree

import util
from ControlBar import ControlBar
from ImageComparePanel import ImageComparePanel
from util import get_phonetic_info


class MainWidget(QWidget):
    page_number = 0
    workplace_path = ''
    recognition_text_file = ''
    page_image_file = ''
    word_images_directory = ''

    def __init__(self):
        super().__init__()

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_request_finished)
        self.notations = []
        self.file_button = QtWidgets.QPushButton('选择路径')
        self.file_button.clicked.connect(self.on_file_button_clicked)
        self.layout = QtWidgets.QVBoxLayout(self)

        self.images = []
        self.dictionary_images = []
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.file_button)
        center_layout = QtWidgets.QHBoxLayout()
        bottom_layout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(header_layout)
        self.control_bar = ControlBar()
        self.compare_panel = ImageComparePanel()
        center_layout.addWidget(self.compare_panel)
        bottom_layout.addWidget(self.control_bar)

        self.control_bar.sgn_index_changed.connect(self.on_index_changed)
        self.control_bar.sgn_confirmed.connect(self.on_confirmed)
        self.control_bar.disable()
        self.layout.addLayout(center_layout)
        self.layout.addLayout(bottom_layout)
        self.layout.setStretch(0, 2)
        self.layout.setStretch(1, 8)
        self.layout.setStretch(2, 2)

    def fetch_image(self, notation):
        self.control_bar.disable()
        notation = util.notation_transcribe(notation)
        print(notation)
        url = QUrl(
            f'http://anakv.com/msc.php?input={notation}&font=1&wpc=5&fontsize=25&cspace=10&fcolor=Black&bcolor=White')
        request = QNetworkRequest(url)
        self.network_manager.get(request)

    @Slot()
    def on_index_changed(self, index):
        self.fetch_image(self.notations[index]['notation'])
        self.compare_panel.set_left(QPixmap(self.images[index]['image']), self.images[index]['filename'])

    @Slot()
    def on_request_finished(self, reply):
        content = reply.readAll()
        content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader)
        if content_type is None or 'html' in content_type:
            html = etree.HTML(content.toStdString())
            js_tag = html.xpath('/html/body/script')[0]
            uri = js_tag.text.split('window.location=')[1]
            url = 'http://anakv.com' + re.sub('"\s*\+\s*"', '', uri).strip(';').strip('"')
            request = QNetworkRequest(url)
            self.network_manager.get(request)
        else:
            pmap = QPixmap()
            pmap.loadFromData(content)
            notation = reply.request().url().url().split('?')[1].split('&')[0].split('=')[1]
            self.compare_panel.set_right(pmap, notation)
            self.control_bar.enable()

    @Slot()
    def on_confirmed(self, check_list):
        util.rename(check_list, self.page_number, self.page_image_file, self.word_images_directory, self.notations)
        self.show_dialog('完成')
        sys.exit(0)

    def is_directory_valid(self, path: str):
        if not path.isascii():
            return False, f'{path},  路径不要包含非ascii(中文)字符', []
        page_number = path.split('/')[-1]
        if not page_number.isdigit():
            return False, f'请选择一个代表页号的纯数字目录', []
        file_to_find = [[f'Image_{page_number}.jpg'],
                        [f'Image_{page_number}'],
                        [f'Image_{page_number}_clustered.txt', f'Image_{page_number}.txt']]
        required_files = util.get_required_files(path, file_to_find)
        if len(required_files) < len(file_to_find):
            msg = '缺少下列必要文件或目录之一\n'
            for i in file_to_find:
                msg += '或'.join(i) + '\n'
            return False, msg, []
        files_index = [f.split('.')[0] for f in os.listdir(f'{path}/Image_{page_number}')]
        for index in files_index:
            if not index.isdigit():
                return False, f'{path}/Image_{page_number} 下包含了不是纯数字.png的图片',[]
        return True, '', required_files

    def show_dialog(self, error_msg):
        dlg = QDialog()
        dlg.setWindowTitle('')
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(error_msg)
        button = QtWidgets.QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
        )
        button.accepted.connect(dlg.accept)
        layout.addWidget(label)
        layout.addWidget(button)
        dlg.setLayout(layout)
        dlg.exec()

    @Slot()
    def on_file_button_clicked(self):
        selected_path = QFileDialog.getExistingDirectory(self)
        if selected_path == '':
            return
        is_valid, error_msg, required_files = self.is_directory_valid(selected_path)
        if not is_valid:
            self.show_dialog(error_msg)
            return
        self.file_button.setDisabled(True)
        self.workplace_path = selected_path
        self.page_number = selected_path.split('/')[-1]
        self.page_image_file = required_files[0]
        self.word_images_directory = required_files[1]
        self.recognition_text_file = required_files[2]
        self.notations = get_phonetic_info(self.recognition_text_file)
        files = os.listdir(f'{self.workplace_path}/Image_{self.page_number}')
        files.sort(key=lambda x: int(x.split('.')[0]))
        for f in files:
            if f.endswith('.png'):
                self.images.append(
                    {'filename': f, 'image': QImage(f'{self.workplace_path}/Image_{self.page_number}/{f}')})
        self.compare_panel.set_left(QPixmap(self.images[0]['image']), self.images[0]['filename'])
        self.control_bar.set_max_count(len(self.images))
        self.control_bar.enable()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWidget()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
