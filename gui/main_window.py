import sys

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QApplication, QVBoxLayout, QHBoxLayout, QLabel, \
    QLineEdit, QPushButton, QWidget, QSpacerItem, QSizePolicy, QCheckBox, QFrame, QProgressBar
from PySide6.QtCore import Slot, Signal, QThread, QRunnable, QThreadPool
from pathlib import Path

from gui.tool import get_all_image
from resources import resources
from image_utils.api import main as process_image
from types import SimpleNamespace
import pandas as pd
import time


class MainWindow(QMainWindow):
    # 按钮样式
    button_style_process = """
    QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #4CAF50, stop: 1 #81C784);
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #45A047, stop: 1 #66BB6A);
            }
            """
    button_cancel_style = """
    QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #F44336, stop: 1 #E57373);
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
            }
            """
    processing = False
    status_signal = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("底栖动物识别")
        self.setWindowIcon(QPixmap(":/resources/icon/icon.svg"))

        self.worker = QThread()
        self.data = {'filename': [], 'area': [], 'index': [], 'path': [], 'x_min': [], 'y_min': [], 'x_max': [],
                     'y_max': []}
        self.destination_path = None
        self.start_time = None

        central_widget = QWidget()

        # 创建程序主Layout
        main_layout = QVBoxLayout()
        source_fold_layout = QHBoxLayout()
        destination_fold_layout = QHBoxLayout()
        save_options_layout = QHBoxLayout()
        process_layout = QHBoxLayout()
        status_layout = QHBoxLayout()
        speed_layout = QHBoxLayout()
        left_time_layout = QHBoxLayout()
        begin_layout = QHBoxLayout()

        # 设置设置源目录
        source_label = QLabel("图片目录")
        source_label.setFixedSize(50, 20)
        # source_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.source_line_edit = QLineEdit()
        self.source_button = QPushButton("选择文件夹")
        source_fold_layout.addWidget(source_label, 1)
        source_fold_layout.addWidget(self.get_space_line(0, 20, ), 0)
        source_fold_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        source_fold_layout.addWidget(self.source_line_edit, 2)
        source_fold_layout.addWidget(self.source_button, 1)
        source_fold_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 设置保存文件夹
        destination_label = QLabel("保存目录")
        destination_label.setFixedSize(50, 20)
        self.destination_line_edit = QLineEdit()
        self.destination_button = QPushButton("选择文件夹")
        destination_fold_layout.addWidget(destination_label, 1)
        destination_fold_layout.addWidget(self.get_space_line(0, 20, ), 0)
        destination_fold_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        destination_fold_layout.addWidget(self.destination_line_edit, 2)
        destination_fold_layout.addWidget(self.destination_button, 1)
        destination_fold_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 设置保存选项
        save_options_label = QLabel("保存选项")
        save_options_label.setFixedSize(50, 20)
        self.option_cut = QCheckBox("裁剪")
        self.option_cut.setChecked(True)
        self.option_foreground = QCheckBox("前景")
        self.option_foreground.setChecked(False)
        save_options_layout.addWidget(save_options_label, 1)
        save_options_layout.addWidget(self.get_space_line(0, 20, ), 0)
        save_options_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        save_options_layout.addWidget(self.option_cut, 1)
        save_options_layout.addWidget(self.option_foreground, 1)
        save_options_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 日志
        stat_label = QLabel("详细信息")
        stat_label.setFixedSize(50, 20)
        self.stat_text = QLabel("---")
        status_layout.addWidget(stat_label, 1)
        status_layout.addWidget(self.get_space_line(0, 20, ), 0)
        status_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        status_layout.addWidget(self.stat_text, 2)

        # 处理速度
        speed_label = QLabel("处理速度")
        speed_label.setFixedSize(50, 20)
        self.speed_text = QLabel("---")
        speed_layout.addWidget(speed_label, 1)
        speed_layout.addWidget(self.get_space_line(0, 20, ), 0)
        speed_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        speed_layout.addWidget(self.speed_text, 2)

        # 进度条
        process_label = QLabel("进度")
        process_label.setFixedSize(50, 20)
        self.process_bar = QProgressBar()
        process_layout.addWidget(process_label, 1)
        process_layout.addWidget(self.get_space_line(0, 20, ), 0)
        process_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        process_layout.addWidget(self.process_bar, 2)

        # 剩余时间
        left_time_label = QLabel("剩余时间")
        left_time_label.setFixedSize(50, 20)
        self.left_time_text = QLabel("---")
        left_time_layout.addWidget(left_time_label, 1)
        left_time_layout.addWidget(self.get_space_line(0, 20, ), 0)
        left_time_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        left_time_layout.addWidget(self.left_time_text, 2)

        # 开始按钮
        self.begin_button = QPushButton("开始")
        self.begin_button.setStyleSheet(self.button_style_process)
        begin_layout.addWidget(self.begin_button, 1)

        # 添加子Layout
        main_layout.addLayout(source_fold_layout)
        main_layout.addLayout(destination_fold_layout)
        main_layout.addLayout(save_options_layout)
        # 添加分割线
        main_layout.addWidget(self.get_space_line(1, h=5))
        main_layout.addLayout(status_layout)
        main_layout.addLayout(speed_layout)
        main_layout.addLayout(process_layout)
        main_layout.addLayout(left_time_layout)
        main_layout.addWidget(self.get_space_line(1, h=5))
        main_layout.addLayout(begin_layout)

        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.resize(400, 300)

        self.bind_event()

    def get_space_line(self, direction: int, h: int = None, w: int = None):
        """
        获取分割线
        :param direction: 分割线方向, 0表示纵向，1表示横向
        :param h: 分割线高度
        :param w: 分割线宽度
        :return: 分割线
        """
        assert direction in [0, 1], "direction must be 0 or 1"
        line = QFrame()
        if direction == 0:
            line.setFrameShape(QFrame.VLine)
        else:
            line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        if h is not None:
            line.setFixedHeight(h)
        if w is not None:
            line.setFixedWidth(w)
        return line

    # 绑定事件
    def bind_event(self):
        self.source_button.clicked.connect(
            lambda: self.source_line_edit.setText(QFileDialog.getExistingDirectory(self, "选择文件夹")))
        self.destination_button.clicked.connect(
            lambda: self.destination_line_edit.setText(QFileDialog.getExistingDirectory(self, "选择文件夹")))
        self.status_signal.connect(self.set_status)
        self.begin_button.clicked.connect(self.begin)

    @Slot()
    def begin(self):
        # 样式修改
        if not self.processing:
            self.status_signal.emit(False)
        else:
            self.status_signal.emit(True)

        # 检验参数
        source_path = self.source_line_edit.text()
        self.destination_path = self.destination_line_edit.text()
        if not self.verify_params(source_path, self.destination_path):
            self.status_signal.emit(True)
            return

        # 获取保存选项
        cut_image = self.option_cut.isChecked()
        foreground = self.option_foreground.isChecked()

        # 获取图片目录下的所有图片
        images = get_all_image(source_path)
        if not images:
            QMessageBox.warning(self, "警告", "图片目录下没有图片")
            self.status_signal.emit(True)
            return

        # 设置进度条
        self.process_bar.setMaximum(len(images))
        self.process_bar.setValue(0)

        # 初始化变量
        self.data = {'filename': [], 'area': [], 'index': [], 'path': [], 'x_min': [], 'y_min': [], 'x_max': [],
                     'y_max': []}

        # 开始处理
        try:
            self.start_time = time.time()
            self.worker = WorkerThread(images, self.destination_path, source_path, cut_image=cut_image,
                                       foreground=foreground,
                                       piex_threshold=3000)
            self.worker.result_signal.connect(self.process_result)
            self.worker.finished.connect(self.finnish_work)
            self.worker.start()

        except Exception as e:
            QMessageBox.warning(self, "警告", str(e))
            self.status_signal.emit(True)
            return

    @Slot(SimpleNamespace)
    def process_result(self, result: SimpleNamespace):
        current = time.time()
        speed = (current - self.start_time) / result.count
        self.process_bar.setValue(self.process_bar.value() + 1)
        self.stat_text.setText(f"处理完成: {result.filename}")
        self.speed_text.setText(f"处理速度: {speed:.2f} s/item")
        self.left_time_text.setText(
            f"剩余时间: {speed * (self.process_bar.maximum() - self.process_bar.value()):.2f} s")
        number_cls = result.cls
        if number_cls == 0:
            self.data['filename'].append(result.filename)
            self.data['area'].append(0)
            self.data['index'].append(1)
            self.data['path'].append(result.image_path)
            self.data['x_min'].append('')
            self.data['y_min'].append('')
            self.data['x_max'].append('')
            self.data['y_max'].append('')
        else:
            for item in range(number_cls):
                self.data['filename'].append(result.filename)
                self.data['area'].append(result.area[item])
                self.data['index'].append(item + 1)
                self.data['path'].append(result.image_path)
                self.data['x_min'].append(result.boxes[item][0])
                self.data['y_min'].append(result.boxes[item][1])
                self.data['x_max'].append(result.boxes[item][2])
                self.data['y_max'].append(result.boxes[item][3])

    @Slot()
    def finnish_work(self):
        self.status_signal.emit(True)
        df = pd.DataFrame(self.data)
        self.stat_text.setText(f"处理完成, 共处理{self.process_bar.maximum()}张图片")
        self.left_time_text.setText(f"---")
        df.to_excel(str(Path(self.destination_path) / 'result.xlsx'), index=False)
        QMessageBox.information(self, "提示", "处理完成")

    def set_status(self, status: bool):
        """
        禁用组件
        """
        self.source_button.setEnabled(status)
        self.destination_button.setEnabled(status)
        self.option_cut.setEnabled(status)
        self.option_foreground.setEnabled(status)
        self.source_line_edit.setEnabled(status)
        self.destination_line_edit.setEnabled(status)
        if status:
            self.begin_button.setText("开始")
            self.begin_button.setStyleSheet(self.button_style_process)
            self.processing = False
        else:
            self.begin_button.setText("停止")
            self.begin_button.setStyleSheet(self.button_cancel_style)
            self.processing = True

    def verify_params(self, source_path: str, destination_path: str) -> bool:
        """
        参数路径
        :param source_path: 图片路径
        :param destination_path: 图片保存路径
        """
        if not source_path:
            QMessageBox.warning(self, "警告", "请选择图片目录")
            return False
        if not destination_path:
            QMessageBox.warning(self, "警告", "请选择保存目录")
            return False
        if source_path == destination_path:
            QMessageBox.warning(self, "警告", "图片目录和保存目录不能相同")
            return False
        if not Path(source_path).exists():
            QMessageBox.warning(self, "警告", "图片目录不存在")
            return False
        if not Path(destination_path).exists():
            QMessageBox.warning(self, "警告", "保存目录不存在")
            return False
        if Path(source_path).is_file():
            QMessageBox.warning(self, "警告", "图片目录不能是文件")
            return False
        if Path(destination_path).is_file():
            QMessageBox.warning(self, "警告", "保存目录不能是文件")
            return False
        return True


class WorkerThread(QThread):
    result_signal = Signal(SimpleNamespace)

    def __init__(self, images: list | tuple, save_path: str, source_dir: str, cut_image: bool = False,
                 foreground: bool = False,
                 piex_threshold: int = 3000):
        super().__init__()
        self.images = images
        self.save_path = save_path
        self.source_dir = source_dir
        self.cut_image = cut_image
        self.foreground = foreground
        self.piex_threshold = piex_threshold

    def run(self) -> None:
        try:
            # start = time.time()
            count = 0
            for item in self.images:
                result = process_image(item, save_path=self.save_path, source_dir=self.source_dir,
                                       cut_image=self.cut_image, foreground=self.foreground,
                                       piex_threshold=self.piex_threshold)
                count += 1
                # end = time.time()
                # result.speed = (end - start) / count
                result.count = count
                self.result_signal.emit(result)
        except Exception as e:
            print(e)
            return


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
