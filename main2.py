import sys
import threading
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import utils

class Worker(QObject):
    sig_update = pyqtSignal(str, name='sig_update')
    sig_finished = pyqtSignal(int, name='sig_finished')
    def __init__(self, id, parent=None):
        super(Worker, self).__init__(parent)

        self.id = id % 10
        self.pointer = 0
        self.paused = True
        self.quit = False
        self.finished = False

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
                time.sleep(utils.thread_pause)
            else: self.lock.acquire()
        self.finished = True
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

        self.checkboxes = []
        x, y = 0, 0
        for i in range(10):
            if i == 5: x = 40; y = 0;
            self.checkboxes.append(QCheckBox(self))
            self.checkboxes[-1].setCheckable(True)
            self.checkboxes[-1].setText(str(i + 1))
            self.checkboxes[-1].setGeometry(QRect(130 + x, 30 + y, 40, 20))
            y += 20

        self.te_terminal = QTextEdit(self)
        self.te_terminal.setGeometry(QRect(20, 130, 211, 421))
        self.te_terminal.setObjectName("te_terminal")
        self.te_terminal.setReadOnly(True)

        self.terminal_text = ""

        self.workers = []
        for i in range(10):
            self.init_worker(id=i+1)

    def update_terminal(self, msg: str):
        ''' method to updating terminal '''
        self.terminal_text += msg
        self.te_terminal.setText(self.terminal_text)
        self.te_terminal.verticalScrollBar().setValue(self.te_terminal.verticalScrollBar().maximum())

    def init_worker(self, id):
        ''' method to initialize worker object with a given id '''
        worker = Worker(id)
        worker.sig_update.connect(self.update_terminal)
        worker.sig_finished.connect(self.finish_worker)
        worker.start()
        self.workers.append(worker)
        self.update_terminal("Worker " + str(id) + " waiting" + '\n')

    def pause_worker(self) -> None:
        ''' resume threads that checkboxes are checked and put info on terminal '''
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                w_id = int(checkbox.text())
                if self.workers[w_id - 1].finished:
                    self.update_terminal("Worker " + str(w_id) + " was already finished" + '\n')
                    continue
                if self.workers[w_id - 1].paused:
                    self.update_terminal("Worker " + str(w_id) + " already paused" + '\n')
                else:
                    self.workers[w_id - 1].pause()
                    self.update_terminal("Worker " + str(w_id) + " paused" + '\n')

    def resume_worker(self) -> None:
        ''' resume threads that checkboxes are checked and put info on terminal '''
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                w_id = int(checkbox.text())
                if self.workers[w_id - 1].finished:
                    self.update_terminal("Worker " + str(w_id) + " was already finished" + '\n')
                    continue
                if not self.workers[w_id - 1].paused:
                    self.update_terminal("Worker " + str(w_id) + " already running" + '\n')
                else:
                    self.workers[w_id - 1].resume()
                    self.update_terminal("Worker " + str(w_id) + " resumed" + '\n')

    def finish_worker(self, w_id: int) -> None:
        if w_id == 0: w_id = 10
        self.update_terminal("Worker " + str(w_id) + " was finished" + '\n')

    def quit_app(self) -> None:
        ''' close app by button '''
        for worker in self.workers:
            worker.finish()
        QApplication.quit()

    def closeEvent(self, event) -> None:
        ''' close app by X '''
        for worker in self.workers:
            worker.finish()
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
