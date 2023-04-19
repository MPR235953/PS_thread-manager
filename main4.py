import sys
import threading
import asyncio

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import utils

class Worker(QObject):
    sig_update = pyqtSignal(str, name='sig_update')
    sig_finished = pyqtSignal(int, name='sig_finished')
    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)

        self.main_thread = threading.Thread(target=self.box_env)
        self.killed_ids = {i: False for i in range(10)}

    def kill_id(self, id: int):
        if id in self.killed_ids.keys():
            self.killed_ids[id] = True

    def box_env(self):
        loop = asyncio.new_event_loop()
        tasks = [loop.create_task(self.task(i)) for i in range(10)]
        loop.run_until_complete(asyncio.wait(tasks))

    async def task(self, id):
        pointer = 0
        while True:
            if self.killed_ids[id]: break
            char = chr(ord('A') + pointer)
            if char == 'Z': break
            self.sig_update.emit(char + str(id) + '\n')
            pointer += 1
            await asyncio.sleep(utils.thread_pause)
        self.sig_finished.emit(id)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setWindowTitle(__file__.split('/')[-1])
        self.setGeometry(100, 100, 500, 300)
        self.resize(268, 598)

        self.start_button = QPushButton("Start", self)
        self.start_button.setGeometry(20, 30, 89, 25)
        self.start_button.clicked.connect(self.resume_worker)
        self.start_button.setDisabled(True)

        self.stop_button = QPushButton("Stop", self)
        self.stop_button.setGeometry(20, 60, 89, 25)
        self.stop_button.clicked.connect(self.pause_worker)
        self.stop_button.setDisabled(True)

        self.stop_button = QPushButton("Kill", self)
        self.stop_button.setGeometry(20, 90, 89, 25)
        self.stop_button.clicked.connect(self.delete_worker)

        self.quit_button = QPushButton("Quit", self)
        self.quit_button.setGeometry(20, 120, 89, 25)
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
        self.te_terminal.setGeometry(QRect(20, 160, 211, 390))
        self.te_terminal.setObjectName("te_terminal")
        self.te_terminal.setReadOnly(True)

        self.terminal_text = ""

        self.init_worker()

    def update_terminal(self, msg: str):
        ''' this method is called by worker to update terminal '''
        self.terminal_text += msg
        self.te_terminal.setText(self.terminal_text)
        self.te_terminal.verticalScrollBar().setValue(self.te_terminal.verticalScrollBar().maximum())

    def init_worker(self):
        ''' method to initialize worker object with a given id '''
        self.worker = Worker()
        self.worker.sig_update.connect(self.update_terminal)
        self.worker.sig_finished.connect(self.finish_worker)
        self.worker.main_thread.start()

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

    def delete_worker(self):
        ''' delete threads that checkboxes are checked and put info on terminal, it also disable checkboxes'''
        for checkbox in self.checkboxes:
            if checkbox.isChecked() and checkbox.isEnabled():
                w_id = int(checkbox.text())
                if w_id == 10: w_id = 0
                self.worker.kill_id(w_id)
                checkbox.setDisabled(True)
                checkbox.setChecked(False)

    def finish_worker(self, w_id: int) -> None:
        ''' this method is called when a worker was finished by user or by self'''
        if w_id == 0: w_id = 10
        self.update_terminal("Worker " + str(w_id) + " was finished" + '\n')

    def quit_app(self) -> None:
        ''' close app by button '''
        for i in range(10):
            self.worker.kill_id(i)
        QApplication.quit()

    def closeEvent(self, event) -> None:
        ''' close app by X '''
        for i in range(10):
            self.worker.kill_id(i)
        QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
