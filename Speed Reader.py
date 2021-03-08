import sys
import sqlite3
import clipboard
import time
import random
from PyQt5 import uic  # Импортируем uic
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QFileDialog, QMessageBox
from time import sleep

username = ''
password = ''


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('Login.ui', self)  # Загружаем дизайн
        self.btn_login.clicked.connect(self.login)
        self.btn_create_acc.clicked.connect(self.register)
        global username
        global password
        self.user = []
        self.Menu = MenuWindow()

    def get_db_user(self):
        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        result = cur.execute("""SELECT * FROM User
            WHERE login = ?
            AND password = ?""", (username, password)).fetchall()
        con.close()
        return result

    def add_new_user(self):
        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        cur.execute("""INSERT INTO User (Login,Password) VALUES (?,?)""", (username, password))
        cur.execute("""INSERT INTO Stats (wm_rating, score) VALUES (0,0)""")
        con.commit()
        con.close()

    def login(self):
        self.label_alert.setText('')
        global username
        global password
        username = self.line_login.text()
        password = self.line_password.text()
        self.user = self.get_db_user()
        if not self.user:
            self.label_alert.setText("Пользователь не найден")
        else:
            self.close()
            uic.loadUi('Menu.ui', self)
            self.Menu.show()

    def register(self):
        self.label_alert.setText('')
        global username
        global password
        try:
            username = self.line_login.text()
            password = self.line_password.text()
            self.user = self.get_db_user()
            # проверяем наличие заригистрированного пользователя с такими данными
            if self.user:
                self.label_alert.setText("данный пользователь уже зарегестрирован")
            else:
                self.add_new_user()
                self.close()
                uic.loadUi('Menu.ui', self)
                self.Menu = MenuWindow()
                self.Menu.show()
        except Exception:
            self.label_alert.setText("Неверное имя пользователя или пароль")


class MenuWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('Menu.ui', self)  # Загружаем дизайн
        global username
        self.opt = 0
        self.SpeedLineWin = SpeedLineWindow()
        self.RunningLineWin = RunningLineWindow()
        self.TestWin = TestWindow()

        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        rating = cur.execute("""SELECT * FROM Stats 
                            WHERE id=(
                                SELECT id FROM User
                                    WHERE Login = ?)""", (username,)).fetchall()
        con.close()
        print(username)
        self.label_username.setText(username)
        # self.label_wm_rating.setText(rating[0])
        # self.label_score.setText(rating[1])
        self.btn_SpeedLine.clicked.connect(self.open_SpeedLine)
        self.btn_Ex.clicked.connect(self.open_Ex)
        self.btn_Test.clicked.connect(self.open_Test)
        self.btn_Exit.clicked.connect(self.open_Exit)

    def open_SpeedLine(self):
        self.close()
        self.SpeedLineWin.show()

    def open_Ex(self):
        self.close()
        self.RunningLineWin.open()

    def open_Test(self):
        self.close()
        self.TestWin.show()

    def open_Exit(self):
        self.close()


class TestWindow(QDialog):
    def __init__(self):
        super().__init__()

        global username
        global password
        self.text = ""
        uic.loadUi('Speed_Test.ui', self)  # Загружаем дизайн
        self.stop_reading = True
        self.seconds = 0
        self.btn_OpenFile.clicked.connect(lambda: self.open_file())
        self.btn_CopyClip.clicked.connect(lambda: self.copy_clipboard())
        self.btn_Start.clicked.connect(lambda: self.start_test())
        self.btn_Stop.clicked.connect(lambda: self.stop())
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.show_time())
        timer.start(100)

    def open_file(self):
        # открытие файла с текстом
        fname = QFileDialog.getOpenFileName(self, 'Выбрать файл с текстом', '')[0]
        text_file = open(fname, mode="r")
        self.text = text_file.read()
        self.textEdit_MainText.setText(self.text)
        text_file.close()

    def copy_clipboard(self):
        # копирование текста из буфера обмена
        clip = clipboard.paste()
        self.textEdit_MainText.setText(clip)

    def show_time(self):
        if not self.stop_reading:
            self.seconds += 1
            self.lcdTime.display(int(self.seconds / 10))

    def start_test(self):
        self.stop_reading = False
        self.seconds = 0

    def stop(self):
        self.stop_reading = True
        global username
        WordArr = self.text.split()

        self.wmRating = (len(WordArr) / (self.seconds / 10)) * 60

        # запись в бд
        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        # находим старый результат по имени пользователя
        rating = cur.execute("""SELECT wm_rating FROM Stats 
                    WHERE id=(
                        SELECT id FROM User
                            WHERE Login = ?)""", (username,)).fetchall()
        # записываем новый результат
        if self.wmRating != rating:
            cur.execute("""UPDATE Stats
                                SET wm_rating = ?
                                    WHERE id = (
                                    SELECT id FROM User
                                    WHERE login = ?)""", (self.wmRating, username))
        con.commit()
        con.close()
        # выводим результат пользователю

        buttonReply = QMessageBox.question(self, 'Результат',
                                           "Ваш результат составил {} слов/мин".format(self.wmRating),
                                           QMessageBox.Yes)
        self.Menu = MenuWindow()
        if buttonReply == QMessageBox.Yes:
            self.close()
            self.Menu.show()
        self.close()
        self.Menu.show()


class SpeedLineWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('Speed_Line.ui', self)  # Загружаем дизайн
        #####################################################################
        self.stop_reading = True
        self.seconds = 0
        self.text = ""
        self.WordArr = []
        self.btn_OpenFile.clicked.connect(lambda: self.open_file())
        self.btn_CopyClip.clicked.connect(lambda: self.copy_clipboard())
        self.btn_Start.clicked.connect(lambda: self.start_reading())
        timer = QTimer(self)
        timer.timeout.connect(lambda: self.show_word())
        timer.start(100)
        if self.seconds == len(self.WordArr):
            self.end_reading()

    def open_file(self):
        # открытие файла с текстом
        fname = QFileDialog.getOpenFileName(self, 'Выбрать файл с текстом', '')[0]
        text_file = open(fname, mode="r")
        self.text = text_file.read()
        self.textEdit_MainText.setText(self.text)
        text_file.close()

    def copy_clipboard(self):
        # копирование текста из буфера обмена
        clip = clipboard.paste()
        self.textEdit_MainText.setText(clip)

    def show_word(self):
        if not self.stop_reading and self.seconds < len(self.WordArr) - 1:
            self.seconds += 1
            self.line_SpeedLine.setText(self.WordArr[self.seconds])

    def end_reading(self):
        self.stop_reading = True
        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        rating = cur.execute("""SELECT wm_rating FROM Stats 
                            WHERE id=(
                                SELECT id FROM User
                                    WHERE Login = ?)""", (username,)).fetchall()
        con.close()
        # wmRating = int(rating[0])
        # self.slider_speed.setTickPosition(wmRating)

        self.close()
        # self.Menu = MenuWindow()
        # self.Menu.show()

    def start_reading(self):
        self.WordArr = self.text.split()
        self.stop_reading = False
        self.seconds = 0

        # wmRating = int(rating[0])
        # self.slider_speed.setTickPosition(wmRating)
        # while i < len(WordArr):
        #     timing = time.time()
        #     ping = self.slider_speed.value()
        #     print(ping)
        #     if time.time() - timing > ping/10:
        #         timing = time.time()
        #         self.line_SpeedLine.setText(WordArr[i])
        #         i += 1


class RunningLineWindow(QDialog):
    def __init__(self):
        super().__init__()
        global username
        global password
        uic.loadUi('Running_Words.ui', self)  # Загружаем дизайн
        # установка скорости для пользователя
        con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
        cur = con.cursor()
        rating = cur.execute("""SELECT wm_rating FROM Stats 
                    WHERE id=(
                        SELECT id FROM User
                            WHERE Login = ?)""", (username,)).fetchall()
        con.close()
        self.points = 0
        self.user_speed = rating
        self.text_arr = []
        self.random_word = ""
        self.btn_Start.clicked.connect(lambda: self.run())
        self.btn_ok.clicked.connect(lambda: self.check())
        self.btn_openFile.clicked.connect(lambda: self.open_file())

    def open_file(self):
        # открытие файла с текстом
        fname = QFileDialog.getOpenFileName(self, 'Выбрать файл с текстом', '')[0]
        text_file = open(fname, mode="r")
        self.text = text_file.read()
        self.text_arr = self.text.split()
        text_file.close()

    def run(self):
        i = 0
        line = 0
        timing = time.time()
        self.random_word = ""
        # отображение случайных слов в полях по порядку
        while i < random.randint(10, 30):
            if time.time() - timing > 10:  #################self.user_speed[0]:
                timing = time.time()
                if line == 1:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line1.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line1.setText("")
                elif line == 2:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line2.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line2.setText("")
                elif line == 3:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line3.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line3.setText("")
                elif line == 4:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line4.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line4.setText("")
                elif line == 5:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line5.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line5.setText("")
                elif line == 6:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line6.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line6.setText("")
                elif line == 7:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line7.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line7.setText("")
                elif line == 8:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line8.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line8.setText("")
                elif line == 9:
                    self.random_word = self.text_arr[random.randint(0, len(self.text_arr) - 1)]
                    self.line9.setText(self.random_word)
                    timing2 = time.time()
                    if time.time() - timing2 > 10:  # self.user_speed:
                        self.line9.setText("")
                line += 1
                i += 1

    def check(self):

        answer = self.line_Answer.text()
        if self.points < 10:
            # пока пользователь не набрал 10 правильных ответов упражнение продолжается
            if self.random_word == answer:
                self.label_alert.setText("Верно")
                self.points += 1
                self.run()
            else:
                self.label_alert.setText("Не верно")
                self.run()
        else:
            # запись результатов
            con = sqlite3.connect('../../Documents/Programms/Проект Ершов Степан/Speed Reader/Users.db')
            cur = con.cursor()
            # находим старый результат по имени пользователя
            rating = cur.execute("""SELECT Score FROM Stats 
                            WHERE id=(
                                SELECT id FROM User
                                    WHERE Login = ?)""", (username,)).fetchall()
            # записываем новый результат
            if self.points != rating[0]:
                cur.execute("""INSERT INTO Stats (score) VALUES (?)
                WHERE id=(
                    SELECT id FROM User
                        WHERE login = ?)""", (self.points, username))
            con.commit()
            con.close()
            self.close()
            self.Menu.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    log = LoginWindow()
    log.show()
    sys.exit(app.exec_())

# первый вариант таймера (не рабочий)

# self.timer = QTimer(self)
# self.time.start()
# self.timing = time.time()
# t = 0
# while not self.stop_reading:
#     if time.time() - self.timing > 1:
#         timing = time.time()
#         t += 1
#         self.lcdTime.display(t)

# def timer(self):
#     while not self.stop_reading:
#         if not self.stop_reading:
#             self.seconds += 1
#             self.lcdTime.display(self.seconds)
#             sleep(1)
#         else:
#             return self.seconds
#     return self.seconds
