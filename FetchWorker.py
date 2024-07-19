import re

from PySide6.QtCore import QObject, QThread, Slot, QByteArray, Signal, QEventLoop
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from lxml import etree


class FetchWorker(QThread):
    notations = []
    dictionary_images = {}
    counter = 0
    network_manager = QNetworkAccessManager()
    event_loop = QEventLoop()
    sgn_worker_done = Signal(list)
    sgn_process_changed = Signal(int)

    def __init__(self, notations, parent=None):
        super(FetchWorker, self).__init__(parent)
        self.notations = notations
        self.network_manager.finished.connect(self.on_request_finished)

    def run(self):
        for i, notation in enumerate(self.notations):
            request = QNetworkRequest(
                f'http://anakv.com/msc.php?input={notation}&font=1&wpc=5&fontsize=25&cspace=10&fcolor=Black&bcolor=White')
            request.setRawHeader(b'X-Request-Number', QByteArray.number(i))
            request.setRawHeader(b'X-Request-Notation', QByteArray(notation))
            self.network_manager.get(request)
        self.event_loop.exec_()

    @Slot()
    def on_request_finished(self, reply: QNetworkReply):
        content = reply.readAll()
        content_type = reply.header(QNetworkRequest.KnownHeaders.ContentTypeHeader)
        print(reply.error())

        if content == b'':
            pass
        elif content_type is None or 'html' in content_type:
            html = etree.HTML(content.toStdString())
            js_tag = html.xpath('/html/body/script')[0]
            uri = js_tag.text.split('window.location=')[1]
            url = 'http://anakv.com' + re.sub('"\s*\+\s*"', '', uri).strip(';').strip('"')
            print(f'redirect url: {url}')
            request = QNetworkRequest(url)
            self.network_manager.get(request)
        else:
            pmap = QPixmap()
            pmap.loadFromData(content)
            notation = reply.request().url().url().split('?')[1].split('&')[0].split('=')[1]
            self.dictionary_images[notation] = pmap
            self.counter += 1
            self.sgn_process_changed.emit(self.counter)

        if self.counter == len(self.notations):
            self.sgn_worker_done.emit([self.dictionary_images])
            self.event_loop.quit()
