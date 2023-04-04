import sys
import threading
import time
from typing import Any

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Worker(QObject):
    sig_update = pyqtSignal(str, name='sig_update')
    sig_finished = pyqtSignal(int, name='sig_finished')
    def __init__(self, id, parent=None):
        super(Worker, self).__init__(parent)

        self.id = id % 10
        self.pointer = 0
        self.paused = True
        self.quit = False

        self.thread = threading.Thread(target=self.task)
        self.lock = threading.Lock()

    def task(self):
        while True:
            if self.quit: break
            if not self.paused:
                char = chr(ord('A') + self.pointer)
                if char == 'Z': break
                self.sig_update.emit(char + str(self.id) + '\n')
                self.pointer += 1
                time.sleep(0.5)
            else: self.lock.acquire()
        self.sig_finished.emit(self.id)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.lock.release()

    def start(self):
        self.thread.start()

    def finish(self):
        self.quit = True
        self.lock.release()


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle("PyQt5 Threads")
        self.setGeometry(100, 100, 500, 300)
        self.resize(268, 598)

        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(20, 30, 89, 25)
        self.start_button.clicked.connect(self.resume_worker)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(20, 60, 89, 25)
        self.stop_button.clicked.connect(self.pause_worker)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.setGeometry(20, 90, 89, 25)
        self.quit_button.clicked.connect(self.quit_app)

        self.lb_thread_no = QLabel("thread number", self)
        self.lb_thread_no.setGeometry(QRect(130, 10, 131, 17))
        self.lb_thread_no.setObjectName("lb_thread_no")

        self.sb_thread_no = QSpinBox(self)
        self.sb_thread_no.setGeometry(QRect(130, 40, 104, 70))
        self.sb_thread_no.setObjectName("sb_thread_no")
        self.sb_thread_no.setMinimum(1)
        self.sb_thread_no.setMaximum(10)

        self.te_terminal = QTextEdit(self)
        self.te_terminal.setGeometry(QRect(20, 130, 211, 421))
        self.te_terminal.setObjectName("te_terminal")
        self.te_terminal.setReadOnly(True)

        self.terminal_text = ""

        self.workers = []
        for i in range(10):
            self.init_worker(id=i+1)

    def update_terminal(self, msg: str):
        self.terminal_text += msg
        self.te_terminal.setText(self.terminal_text)
        self.te_terminal.verticalScrollBar().setValue(self.te_terminal.verticalScrollBar().maximum())

    def init_worker(self, id):
        worker = Worker(id)
        worker.sig_update.connect(self.update_terminal)
        worker.sig_finished.connect(self.clear_worker)
        worker.start()
        self.workers.append(worker)
        self.update_terminal("Worker " + str(id) + " initialized" + '\n')

    def find_worker(self, raw_id) -> Worker | None:
        try:
            w_id = int(raw_id)
            for worker in self.workers:
                if worker.id == w_id:
                    return worker
        except:
            return None

    def pause_worker(self):
        raw_id = self.sb_thread_no.value()
        worker = self.find_worker(raw_id)
        if worker:
            worker.pause()
            self.update_terminal("Worker " + str(raw_id) + " paused" + '\n')

    def resume_worker(self):
        raw_id = self.sb_thread_no.value()
        worker = self.find_worker(raw_id)
        if worker:
            worker.resume()
            self.update_terminal("Worker " + str(raw_id) + " resumed" + '\n')
        else:
            self.init_worker(int(raw_id))

    def clear_worker(self, i):
        worker = self.find_worker(i)
        worker.finish()
        index = self.workers.index(worker)
        del self.workers[index]
        self.update_terminal("Worker " + str(i) + " finished" + '\n')

    def quit_app(self):
        for worker in self.workers:
            worker.finish()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
