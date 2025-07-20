import sys
import os
import io
import argparse
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QRadioButton, QButtonGroup, QTextEdit, QComboBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from main import run_flow

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', errors='replace')  

class Worker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, func, args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            result = self.func(self.args)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Run main.py with File/Directory Input')
        self.resize(600, 350)
        self.input_type = "file"  # Default to file input
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Input mode (File/Dir or URL)
        mode_layout = QHBoxLayout()
        self.file_radio = QRadioButton('文件/目录')
        self.file_radio.setChecked(True)
        self.url_radio = QRadioButton('URL')
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.file_radio)
        self.mode_group.addButton(self.url_radio)
        mode_layout.addWidget(self.file_radio)
        mode_layout.addWidget(self.url_radio)
        layout.addLayout(mode_layout)
        self.file_radio.toggled.connect(self.toggle_input_mode)

        # Input file/dir
        input_layout = QHBoxLayout()
        self.input_label = QLabel('输入文件/目录:')
        self.input_edit = QLineEdit()
        self.input_btn = QPushButton('选择...')
        self.input_btn.clicked.connect(self.select_input)
        input_layout.addWidget(self.input_label)
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.input_btn)
        layout.addLayout(input_layout)

        # URL input
        self.url_layout = QHBoxLayout()
        self.url_label = QLabel('输入URL:')
        self.url_edit = QLineEdit()
        self.url_layout.addWidget(self.url_label)
        self.url_layout.addWidget(self.url_edit)
        layout.addLayout(self.url_layout)
        self.url_label.hide()
        self.url_edit.hide()
        self.url_layout.setEnabled(False)

        # Language
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel('语言:')
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['Chinese', 'English'])
        lang_layout.addWidget(self.lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Output dir
        output_layout = QHBoxLayout()
        self.output_label = QLabel('输出目录:')
        self.output_edit = QLineEdit()
        self.output_edit.setText('output')  # Set default output folder
        self.output_btn = QPushButton('选择...')
        self.output_btn.clicked.connect(self.select_output)
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_edit)
        output_layout.addWidget(self.output_btn)
        layout.addLayout(output_layout)

        # Run button
        self.run_btn = QPushButton('运行 main.py')
        self.run_btn.clicked.connect(self.run_main)
        layout.addWidget(self.run_btn)

        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setLayout(layout)

    def toggle_input_mode(self):
        if self.file_radio.isChecked():
            self.input_label.show()
            self.input_edit.show()
            self.input_btn.show()
            self.url_label.hide()
            self.url_edit.hide()
            self.url_layout.setEnabled(False)
        else:
            self.input_label.hide()
            self.input_edit.hide()
            self.input_btn.hide()
            self.url_label.show()
            self.url_edit.show()
            self.url_layout.setEnabled(True)

    def select_input(self):
        options = QFileDialog.Options()
        # Add radio buttons to choose between file and directory
        file_or_dir = QFileDialog.getOpenFileName(self, '选择文件或目录', '', 'All Files (*)', options=options)
        
        if file_or_dir[0]:
            self.input_edit.setText(file_or_dir[0])
            # Check if it's a file or directory
            if os.path.isdir(file_or_dir[0]):
                self.input_type = "dir"
            else:
                self.input_type = "file"
        else:
            # If cancel was pressed, try directory selection
            dir_path = QFileDialog.getExistingDirectory(self, '选择目录', '', options=options)
            if dir_path:
                self.input_edit.setText(dir_path)
                self.input_type = "dir"

    def select_output(self):
        options = QFileDialog.Options()
        dir_path = QFileDialog.getExistingDirectory(self, '选择输出目录', 'output', options=options)
        if dir_path:
            self.output_edit.setText(dir_path)

    def run_main(self):
        language = self.lang_combo.currentText()
        output_dir = self.output_edit.text().strip()
        if self.file_radio.isChecked():
            input_path = self.input_edit.text().strip()
            if not input_path or not output_dir:
                self.output_area.append('请填写输入文件/目录和输出目录!')
                return
        else:
            url = self.url_edit.text().strip()
            if not url or not output_dir:
                self.output_area.append('请填写URL和输出目录!')
                return

        # Determine if input is file or directory
        if self.file_radio.isChecked():
            input_path = self.input_edit.text().strip()
            is_dir = os.path.isdir(input_path)
            file_arg = None if is_dir else input_path
            dir_arg = input_path if is_dir else None
        else:
            file_arg = None
            dir_arg = None

        args = argparse.Namespace(
            file=file_arg,
            url=self.url_edit.text().strip() if self.url_radio.isChecked() else None,
            dir=dir_arg,
            repo=None, 
            name=None, 
            token=None, 
            github=None,
            use_relative_paths=False,
            max_size=100000,
            include=None,
            exclude=None,
            language=self.lang_combo.currentText(),
            output=output_dir,
            model_name='gemini-1.5-flash',
            template_path='prompts/tutorial_template.md',
            temperature=0.7,
            max_tokens=4096,
            stop=None,
            top_p=1.0,
            top_k=32,
            retries=3,
            timeout=120,
            use_proxy=False,
            proxy_address=None,
            debug=True
        )

        input_type = "URL" if self.url_radio.isChecked() else ("Directory" if dir_arg else "File")
        input_path = args.url or args.dir or args.file
        self.output_area.append(f'Starting tutorial generation for: {input_path} ({input_type})')
        self.output_area.append('...Please wait...\n')

        self.worker = Worker(run_flow, args)
        self.worker.finished.connect(self.on_run_finished)
        self.worker.error.connect(self.on_run_error)
        self.worker.start()

    def on_run_finished(self, result):
        self.output_area.append("\n--- Tutorial Generation Finished ---")
        if 'error' in result:
            self.output_area.append(f"An error occurred: {result['error']}")
        else:
            self.output_area.append(f"Tutorial saved to: {result.get('tutorial_path', 'N/A')}")
        self.run_btn.setEnabled(True)

    def on_run_error(self, error_message):
        self.output_area.append(f"\n--- An unexpected error occurred ---")
        self.output_area.append(error_message)
        self.run_btn.setEnabled(True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
