import os
import re
import shutil
import sys

from PySide6 import QtWidgets
from PySide6.QtCore import QUrl, Slot, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PySide6.QtWidgets import QWidget, QFileDialog, QDialog, QDialogButtonBox, QProgressBar
from lxml import etree

import util
from ControlBar import ControlBar
from ImageComparePanel import ImageComparePanel
from ImageWorker import ImageWorker
from MatchWorker import MatchWorker


class MainWidget(QWidget):
    page_number = 0
    workplace_path = ''
    recognition_text_file = ''
    page_image_file = ''
    word_images_directory = ''
    position_dict = {}
    counter = 0
    match_worker = None
    image_worker = None

    sgn_data_arrived = Signal()

    def __init__(self):
        super().__init__()

        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_request_finished)
        self.notations = {}
        self.file_button = QtWidgets.QPushButton('选择路径')
        # self.file_button.setStyle(QStyleFactory.create('Fusion'))
        self.file_button.clicked.connect(self.on_file_button_clicked)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.process_bar = QProgressBar()
        self.process_bar.setRange(0, 0)
        # self.process_bar.setStyle(QStyleFactory.create('Fusion'))
        # self.process_bar.setValue(50)

        self.sgn_data_arrived.connect(self.on_data_arrived)

        self.images = {}
        self.dictionary_images = {}
        self.indexes = []
        self.temp_dir = ''
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(self.process_bar)
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
    def on_data_arrived(self):
        self.control_bar.sgn_refresh.emit()

    @Slot()
    def on_index_changed(self, index):
        notation = self.notations[index]
        if index in self.images.keys():
            tips = f'{self.images[index]["filename"]}  列:{self.images[index]["position"][0]} 行: {self.images[index]["position"][1]}'
            self.compare_panel.set_left(QPixmap(self.images[index]['image']), tips)
        else:
            self.compare_panel.set_right(QPixmap(), '加载中...')
        if notation in self.dictionary_images.keys():
            self.compare_panel.set_right(self.dictionary_images[notation], notation)
        else:
            self.compare_panel.set_right(QPixmap(), '加载中...')

    @Slot()
    def on_request_finished(self, reply):
        content = reply.readAll()
        content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader)
        if content == b'':
            pass
        elif content_type is None or 'html' in content_type:
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
            self.dictionary_images[notation] = pmap
            self.counter += 1
            self.sgn_data_arrived.emit()
            self.control_bar.enable()

    @Slot()
    def on_confirmed(self, check_list):
        util.rename(check_list[0], self.page_number, self.word_images_directory, self.notations, self.images)
        shutil.rmtree(self.temp_dir)
        self.show_dialog('完成')
        sys.exit(0)

    def is_directory_valid(self, path: str):
        if not path.isascii():
            return False, f'{path},  路径不要包含非ascii(中文)字符', []
        page_number = path.split('/')[-1]
        if not page_number.isdigit():
            return False, f'请选择一个代表页号的纯数字目录', []
        files_to_find = [[f'Image_{page_number}.jpg'],
                         [f'Image_{page_number}'],
                         [f'Image_{page_number}_clustered.txt', f'Image_{page_number}.txt']]
        required_files = util.get_required_items(path, files_to_find)
        if len(required_files) < len(files_to_find):
            msg = '缺少下列必要文件或目录之一\n'
            for f in files_to_find:
                msg += '或'.join(f) + '\n'
            return False, msg, []
        files_index = [f.split('.')[0] for f in os.listdir(f'{path}/Image_{page_number}')]
        for index in files_index:
            if not index.isdigit():
                return False, f'{path}/Image_{page_number} 下包含了不是纯数字.png的图片', []
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
    def on_image_worker_done(self, result):
        print('image worker done')
        self.dictionary_images = result[0]
        self.control_bar.enable_confirm_button()
        self.control_bar.sgn_refresh.emit()

    @Slot()
    def on_match_worker_done(self, result):
        print('match done')
        for r in result:
            self.images[r[2]]['position'] = (r[0], r[1])
        self.images = dict(sorted(self.images.items(), key=lambda item: item[1]['position']))
        indexes = list(self.images.keys())
        notations = util.read_romanizations(self.recognition_text_file)
        corrected_notations = {}

        for i,k in enumerate(self.images.keys()):
            corrected_notations[k] = util.notation_transcribe(notations[i])

        self.notations = corrected_notations
        self.control_bar.set_indexes(indexes)
        self.control_bar.sgn_refresh.emit()

    @Slot()
    def on_process_changed(self, index):
        self.process_bar.setValue(index)

    @Slot()
    def on_file_button_clicked(self):
        selected_path = QFileDialog.getExistingDirectory(self)
        if selected_path == '':
            return
        is_valid, error_msg, required_items = self.is_directory_valid(selected_path)
        if not is_valid:
            self.show_dialog(error_msg)
            return
        self.file_button.setDisabled(True)
        self.workplace_path = selected_path
        self.page_number = selected_path.split('/')[-1]
        self.page_image_file = required_items[0]
        self.word_images_directory = required_items[1]
        self.recognition_text_file = required_items[2]
        notations = util.read_romanizations(self.recognition_text_file)
        self.images = util.read_word_images(self.word_images_directory)
        self.process_bar.setRange(0, len(self.images))
        self.process_bar.setValue(0)
        # tmp = util.get_position_list(self.page_image_file, self.word_images_directory)
        # for t in tmp:
        #     self.images[t[2]]['position'] = (t[0], t[1])
        # self.images = dict(sorted(self.images.items(), key=lambda item: item[1]['position']))
        os.makedirs(f'{self.workplace_path}/temp', exist_ok=True)
        self.temp_dir = f'{self.workplace_path}/temp'
        # self.temp_dir = os.path.join(self.workplace_path, 'temp')

        self.notations = notations
        self.match_worker = MatchWorker(self.page_image_file, self.word_images_directory)
        self.match_worker.sgn_match_done.connect(self.on_match_worker_done)
        self.match_worker.start()
        self.image_worker = ImageWorker(notations, self.temp_dir)
        self.image_worker.sgn_worker_done.connect(self.on_image_worker_done)
        self.image_worker.sgn_process_changed.connect(self.on_process_changed)
        self.image_worker.start()
        indexes = list(self.images.keys())
        self.control_bar.set_indexes(indexes)
        self.control_bar.enable()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWidget()
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
