import sys
import threading
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class MyThread(threading.Thread):
    def __init__(self, id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id % 10
        self.pointer = 0
        self.__flag = threading.Event()  # The flag used to pause the thread
        self.__flag.clear() # Set to True
        self.__running = threading.Event()  # Used to stop the thread identification
        self.__running.set()  # Set running to True

    def run(self):
        while self.__running.is_set():
            self.__flag.wait()
            char = chr(ord('A') + self.pointer)
            if char == 'Z': break
            print(char + str(self.id))
            self.pointer += 1
            time.sleep(0.5)

    def pause(self):
        self.__flag.clear()
        time.sleep(3)
        self.resume()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()  # Resume the thread from the suspended state, if it is already suspended
        self.__running.clear()  # Set to False

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)

    def __init__(self, id, parent=None):
        super(Worker, self).__init__(parent)
        self.id = id % 10
        self.pointer = 0
        self.paused = True
        self.lock = threading.Lock()
        self.lock.acquire()

    def run(self):
        while True:
            if not self.paused:
                char = chr(ord('A') + self.pointer)
                if char == 'Z': break
                self.progress.emit(char + str(self.id))
                self.pointer += 1
                QThread.msleep(500)
            else: self.lock.acquire()
        self.finished.emit()

    def pause(self):
        self.paused = True

    def start(self):
        self.paused = False
        self.lock.release()

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("PyQt5 Threads")
        self.setGeometry(100, 100, 500, 300)
        self.resize(268, 598)

        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(20, 30, 89, 25)
        self.start_button.clicked.connect(self.start_thread)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(20, 60, 89, 25)
        self.stop_button.clicked.connect(self.pause_thread)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.setGeometry(20, 90, 89, 25)
        self.quit_button.clicked.connect(self.quit_app)

        self.lb_thread_no = QLabel("thread number", self)
        self.lb_thread_no.setGeometry(QRect(130, 10, 131, 17))
        self.lb_thread_no.setObjectName("lb_thread_no")

        self.te_thread_no = QTextEdit(self)
        self.te_thread_no.setGeometry(QRect(130, 40, 104, 70))
        self.te_thread_no.setObjectName("te_thread_no")

        self.te_terminal = QTextEdit(self)
        self.te_terminal.setGeometry(QRect(20, 130, 211, 421))
        self.te_terminal.setObjectName("te_terminal")

        self.workers = []
        self.threads = []

        self.min_id = 1
        self.max_id = 10

        for i in range(0, 10):
            self.init_thread(i+1)

        self.terminal_text = ""

    def init_thread(self, id):
        self.workers.append(Worker(id))
        self.threads.append(QThread())
        self.workers[-1].moveToThread(self.threads[-1])
        self.workers[-1].progress.connect(self.update_progress)
        self.workers[-1].finished.connect(self.threads[-1].quit)
        self.workers[-1].finished.connect(self.workers[-1].deleteLater)
        self.threads[-1].finished.connect(self.threads[-1].deleteLater)
        self.threads[-1].started.connect(self.workers[-1].run)
        self.threads[-1].start()

    def start_thread(self):
        id = int(self.te_thread_no.toPlainText())
        if id >= self.min_id and id <= self.max_id and self.workers[id-1] is not None:
            self.workers[id-1].start()

    def update_progress(self, i):
        self.terminal_text += str(i) + '\n'
        self.te_terminal.setText(self.terminal_text)

    def pause_thread(self):
        id = int(self.te_thread_no.toPlainText())
        if id >= self.min_id and id <= self.max_id and self.workers[id-1] is not None:
            self.workers[id - 1].pause()

    def stop_thread(self):
        id = int(self.te_thread_no.toPlainText())
        if id >= self.min_id and id <= self.max_id and self.workers[id-1] is not None:
            self.workers[id - 1].stop()

    def quit_app(self):
        for id in range(0, 10):
            if self.threads[id] is not None:
                self.threads[id].quit()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
