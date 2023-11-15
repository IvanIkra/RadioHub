import sys
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QListView, QLineEdit, QPushButton, QVBoxLayout, QDialogButtonBox, \
    QLabel, QVBoxLayout
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QListView
from PyQt5.QtCore import Qt
import vlc
import urllib.request
import sqlite3
import os


class Dialog(QDialog):
    def __init__(self, parent=None):
        super(Dialog, self).__init__(parent)

        self.setWindowTitle("Радиостанции")
        self.setGeometry(100, 100, 324, 493)

        self.listView = QListView()
        self.lineEdit = QLineEdit()
        self.lineEdit.setText('Введите радиостанцию в формате: Имя % url')
        self.pushButton = QPushButton("➕")

        layout = QVBoxLayout()
        layout.addWidget(self.listView)
        layout.addWidget(self.lineEdit)
        layout.addWidget(self.pushButton)

        self.setLayout(layout)

        self.pushButton.clicked.connect(self.add_radio_station)

    def add_radio_station(self):
        try:
            station = self.lineEdit.text()
            url = station.split(' % ', 2)[1]
            station = station.split(' % ', 2)[0]
            try:
                if urllib.request.urlopen(url).getcode() == 200:
                    self.parent().cursor.execute("INSERT INTO stations VALUES (?, ?)", (station, url))
                    self.parent().conn.commit()
                    item = QStandardItem(station)
                    self.parent().list_model.appendRow(item)
                    self.lineEdit.clear()
                    self.parent().load_stations()
                    self.lineEdit.setText('Введите радиостанцию в формате: Имя % url')
                else:
                    self.lineEdit.setText('Ошибка ссылки')
            except Exception:
                self.lineEdit.setText('Ошибка ссылки')
        except IndexError:
            self.lineEdit.setText('Неверный формат')


class ShareWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(ShareWindow, self).__init__(parent)
        uic.loadUi('Share.ui', self)


class DialogWindow(QtWidgets.QDialog):
    def __init__(self, conn, parent=None):
        super(DialogWindow, self).__init__(parent)
        self.parent = parent
        self.conn = conn
        self.setWindowTitle("RadioHub")
        self.setFixedSize(500, 150)
        self.name_label = QLabel("RadioHub")
        self.version_label = QLabel("Версия: 1.6")
        self.developer_label = QLabel("Разработчик: Технический гений")
        self.delete_button = QPushButton(
            "Удалить все данные (также закрывает приложение, после удаления откройте заново)")
        self.delete_button.clicked.connect(self.delete_data)

        layout = QVBoxLayout()
        layout.addWidget(self.name_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.version_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.developer_label, alignment=Qt.AlignCenter)
        layout.addWidget(self.delete_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def delete_data(self):
        if os.path.exists("radio_stations.db"):
            self.conn.close()
            os.remove("radio_stations.db")
        sys.exit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('MainWindow.ui', self)
        self.pushButton_5.clicked.connect(self.open_second_window)
        self.share_window = ShareWindow()
        self.dialog = Dialog(self)
        self.verticalSlider.valueChanged.connect(self.set_volume)
        self.pushButton_3.clicked.connect(self.play)
        self.pushButton.clicked.connect(self.next)
        self.pushButton_2.clicked.connect(self.prev)
        self.pushButton_4.clicked.connect(self.share)
        self.label_3.setPixmap(QPixmap('logo.png'))
        self.pushButton_6.clicked.connect(self.open_settings)
        self.stan = 0
        self.flag = False
        self.conn = sqlite3.connect('radio_stations.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS stations(
                name TEXT,
                url TEXT
            )
        ''')
        self.conn.commit()
        self.load_stations()
        self.sett = DialogWindow(self.conn)

    def load_stations(self):
        self.cursor.execute("SELECT name FROM stations")
        self.names = [name[0] for name in self.cursor.fetchall()]
        self.cursor.execute("SELECT url FROM stations")
        self.urls = [url[0] for url in self.cursor.fetchall()]
        self.list_model = QStandardItemModel()
        self.dialog.listView.setModel(self.list_model)
        self.cursor.execute("SELECT name FROM stations")
        for station in self.cursor.fetchall():
            item = QStandardItem(station[0])
            self.list_model.appendRow(item)

    def set_volume(self):
        volume = self.verticalSlider.value()
        if self.flag:
            self.player.audio_set_volume(volume)

    def open_second_window(self):
        self.dialog.show()
        self.load_stations()
        self.dialog.lineEdit.setText('Введите радиостанцию в формате: Имя % url')

    def open_settings(self):
        self.sett.show()

    def play(self):
        if self.flag:
            self.player.stop()
            self.flag = False
            self.pushButton_3.setText("▶")
            self.label_2.setText('  Приложение запущено')
        else:
            try:
                url = self.urls[self.stan]
                self.player = vlc.MediaPlayer(url)
                self.label_2.setText(f'  Сейчас играет: {self.names[self.stan]}')
                self.player.play()
                self.player.audio_set_volume(self.verticalSlider.value())
                self.flag = True
                self.pushButton_3.setText("⏸")
            except IndexError:
                self.label_2.setText('  Нет радиостанций')

    def next(self):
        if self.stan == len(self.urls) - 1:
            self.stan = 0
        else:
            self.stan += 1
        if self.flag:
            self.player.stop()
            url = self.urls[self.stan]
            self.player = vlc.MediaPlayer(url)
            self.player.play()
            self.label_2.setText(f'  Сейчас играет: {self.names[self.stan]}')

    def prev(self):
        if self.stan == 0:
            self.stan = len(self.urls) - 1
        else:
            self.stan -= 1
        if self.flag:
            self.player.stop()
            url = self.urls[self.stan]
            self.player = vlc.MediaPlayer(url)
            self.player.play()
            self.label_2.setText(f'  Сейчас играет: {self.names[self.stan]}')

    def share(self):
        self.share_window.show()
        try:
            self.share_window.lineEdit.setText(f'{self.names[self.stan]} % {self.urls[self.stan]}')
        except Exception:
            self.share_window.lineEdit.setText('Нет радиостанций')


app = QtWidgets.QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
