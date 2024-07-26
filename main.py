import json   
import logging
import os
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, pyqtSignal, QObject
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication, 
    QLabel,
    QMainWindow, 
    QPushButton,
    QSplitter,
    QVBoxLayout, 
    QWidget
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
import sys



'''
    This app is meant to generate notes in markdown format from a user's Audible.com audio book
    library. The user provides login credentials, enters the year that they wish to generate 
    notes for and download cover art for.

    By: jGDarkenss@github.com
    Date: July 2024
'''



class JSONStreamHandler(logging.StreamHandler):
    '''
    This class is used to write logs to a JSON file.
    '''
    def emit(self, record):
        log_entry = {
            'timestamp': self.formatter.formatTime(record),
            'level': record.levelname,
            'message': self.format(record)
        }
        json.dump(log_entry, self.stream)
        self.stream.write('\n')
        self.flush()



class Worker(QRunnable):
    '''
    This class is used to run the web driver and load the Audible page.
    '''
    class Signals(QObject):
        '''
        This class is used to emit signals from the worker thread.
        '''
        finished = pyqtSignal(str)


    def __init__(self, fn, *args, **kwargs):
        '''
        Initialize the worker thread.
        '''
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = Worker.Signals()


    def run(self):
        '''
        Run the web driver and load the Audible page.
        '''
        result = self.fn(*self.args, **self.kwargs)
        self.signals.finished.emit(result)



class MainWindow(QMainWindow):
    def __init__(self):
        '''
        Initialize the main window and set its properties and methods.
        '''
        super().__init__()


        # WINDOW SETTINGS
        self.setWindowTitle("Aldo - Audible.com Library Downloader for Obsidian")
        self.setObjectName("Main_Window")
        self.screen = QApplication.primaryScreen().geometry()
        window_width = 1500
        window_height = 800
        x = (self.screen.width() - window_width) // 2
        y = (self.screen.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)


        # CENTRAL WIDGET
        central_widget = QWidget()
        central_widget.setObjectName("Central_Widget")
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)

        
        # THREE-COLUMN LAYOUT
        three_column_splitter = QSplitter()        
        three_column_splitter.setObjectName("Three_Column_Layout")
        three_column_splitter.setHandleWidth(2)
        three_column_splitter.setChildrenCollapsible(False)
        layout.addWidget(three_column_splitter)


        # First column: navigation_bar
        self.navigation_bar = QWidget()
        self.navigation_bar.setObjectName("Navigation_Bar")
        navigation_layout = QVBoxLayout()
        navigation_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        navigation_layout.setContentsMargins(0, 0, 0, 0)
        navigation_layout.setSpacing(0)
        self.navigation_bar.setLayout(navigation_layout)
        self.navigation_bar.setAutoFillBackground(True)
        self.navigation_bar.setFixedWidth(225)
        navigation_palette = self.navigation_bar.palette()
        navigation_palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
        self.navigation_bar.setPalette(navigation_palette)
        three_column_splitter.addWidget(self.navigation_bar)


        # Home Button
        home_button = QPushButton("Home")
        home_button.setObjectName("Home_Button")
        home_button.setStyleSheet("""
            color: white; 
            font-size: 14pt; 
            border-top: 0px; 
            border-right: 1px solid black; 
            border-bottom: 1px solid black; 
            border-left: 0px solid black; 
            text-align: left; 
            padding-left: 10px; 
            padding-top: 2px;
        """)                
        home_button.setFixedHeight(45)
        home_button.setFixedWidth(225)
        home_button.clicked.connect(self.show_home_content)
        home_button.clicked.connect(lambda: self.statusBar().showMessage("Home"))        
        navigation_layout.addWidget(home_button)


        # Credentials Button
        credentials_button = QPushButton("Credentials")
        credentials_button.setObjectName("Credentials_Button")
        credentials_button.setStyleSheet("""
            color: white;
            font-size: 14pt;
            border-top: 0px;
            border-right: 1px solid black;
            border-bottom: 1px solid black;
            border-left: 0px solid black;
            text-align: left;
            padding-left: 10px;
            padding-top: 2px;
        """)
        credentials_button.setFixedHeight(45)
        credentials_button.setFixedWidth(225)
        credentials_button.clicked.connect(self.show_credentials_content)
        credentials_button.clicked.connect(
            lambda: self.statusBar().showMessage("Viewing/editing credentials."))
        navigation_layout.addWidget(credentials_button)


        # Settings Button
        settings_button = QPushButton("Settings")
        settings_button.setObjectName("Settings_Button")
        settings_button.setStyleSheet("""
            color: white; 
            font-size: 14pt; 
            border-top: 0px; 
            border-right: 1px solid black;
            border-left: 0px solid black;
            border-bottom: 1px solid black;                                      
            text-align: left; 
            padding-left: 10px; 
            padding-top: 2px;
        """)
        settings_button.setFixedHeight(45)
        settings_button.setFixedWidth(225)
        settings_button.clicked.connect(self.show_settings_content)
        settings_button.clicked.connect(
            lambda: self.statusBar().showMessage("Viewing/editing settings."))
        navigation_layout.addWidget(settings_button)


        # Second column: central_widget_content
        self.central_widget_content = QWidget()
        self.central_widget_content.setObjectName("Central_Widget_Content")
        self.central_widget_content.setStyleSheet("""
            border-top: 0px; 
            border-bottom: 0px;
            border-left: 0px;
            border-right: 1px solid black;
        """)
        central_content_layout = QVBoxLayout()
        central_content_layout.setContentsMargins(10, 10, 10, 10)
        central_content_layout.setSpacing(10)
        self.central_widget_content.setLayout(central_content_layout)
        three_column_splitter.addWidget(self.central_widget_content)


        # Third column: logging_content
        self.logging_content = QWidget()
        self.logging_content.setObjectName("Logging_Content")
        self.logging_content.setStyleSheet("""
            border-top: 0px;
            border-bottom: 1px solid black;
            border-left: 0px;
            border-right: 0px solid black;
        """)
        self.logging_layout = QVBoxLayout()
        self.logging_layout.setContentsMargins(10, 10, 10, 10)
        self.logging_layout.setSpacing(10)
        self.logging_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.logging_content.setFixedWidth(325)
        self.logging_content.setLayout(self.logging_layout)
        three_column_splitter.addWidget(self.logging_content)


        # STATUS BAR
        status_bar = self.statusBar()
        status_bar.setObjectName("Status_Bar")
        status_bar.setAutoFillBackground(True)
        status_palette = status_bar.palette()
        status_palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
        status_palette.setColor(QPalette.ColorRole.WindowText, QColor("white"))
        status_bar.setPalette(status_palette)


        # Set up Selenium Logging
        self.log_path = os.path.join('logs', 'chrome_logs.json')
        if not os.path.exists('logs'):
            os.makedirs('logs')
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                json.dump({}, f)
        self.log_file = open(self.log_path, 'a')
        json_handler = JSONStreamHandler(self.log_file)
        json_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(json_handler)
        sys.stdout = root_logger.handlers[0].stream
        sys.stderr = root_logger.handlers[0].stream

 
        # Set up Chrome Options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--silent")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument(f"--output={self.log_path}")
        chrome_options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})        


        # Set up the web view
        service = Service()
        self.driver = webdriver.Chrome(service=service, options=chrome_options)        
        self.web_view = QWebEngineView()


    def append_logs(self):
        '''
        Save the Chrome logs to a JSON file.
        '''
        browser_logs = self.driver.get_log('browser')
        for log in browser_logs:
            logging.info(json.dumps(log))

    
    def clear_logs(self):
        '''
        Clear the Chrome logs.
        '''
        self.driver.get_log('browser').clear()


    def __del__(self):
        '''
        Close the browser and quit the program.
        '''
        if hasattr(self, "driver"):
            self.driver.quit()
        if hasattr(self, "log_file"):
            self.log_path.close()


    def load_audible_page(self):
        '''
        Load the Audible page and return the page source.
        '''
        self.driver.get("https://www.audible.com")
        page_source = self.driver.page_source
        self.append_logs()
        self.clear_logs()
        return page_source
    

    def update_web_view(self, page_source):
        '''
        Update the web view with the page source.
        '''
        self.web_view.setHtml(page_source)
        

    def initialize_browser(self):
        '''
        Initialize the browser.
        '''
        self.web_view.setZoomFactor(0.5)  # Set zoom factor to 50%
        self.web_view.loadStarted.connect(
            lambda: self.statusBar().showMessage("Loading Audible..."))

        worker = Worker(self.load_audible_page)
        worker.signals.finished.connect(self.update_web_view)
        QThreadPool.globalInstance().start(worker)

        for i in reversed(range(self.central_widget_content.layout().count())):
            self.central_widget_content.layout().itemAt(i).widget().setParent(None)
        self.central_widget_content.layout().addWidget(self.web_view)    
        self.web_view.loadFinished.connect(
            lambda: self.statusBar().showMessage("Loading Audible... Done."))


    def clear_logging_content(self):
        '''
        This function clears the central content of the main window.
        '''
        for i in reversed(range(self.logging_layout.layout().count())):
            self.logging_layout.layout().itemAt(i).widget().setParent(None)

    
    def show_home_content(self):
        '''
        This function shows the home content in the logging content area of the main window.
        '''
        self.clear_logging_content()
        home_label = QLabel("Welcome to Aldo!")
        home_label.setStyleSheet("""
            font-size: 12pt;
            border-top: 0px;
            border-right: 0px;
            border-left: 0px;
            border-bottom: 0px;
        """)
        self.logging_layout.addWidget(home_label)


    def show_credentials_content(self):
        '''
        This function shows the credentials content in the logging content area of the main 
        window.
        '''
        self.clear_logging_content()
        # Add widgets for credentials content
        credentials_label = QLabel("Enter or adjust your credentials")
        credentials_label.setStyleSheet("""
            font-size: 12pt;
            border-top: 0px;
            border-right: 0px;
            border-left: 0px;
            border-bottom: 0px;
            text-align: left;
            padding-left: 5px;
        """)
        self.logging_layout.addWidget(credentials_label)


    def show_settings_content(self):
        '''
        This function shows the settings content in the logging content area of the main 
        window.
        '''
        self.clear_logging_content()
        settings_label = QLabel("Adjust your settings")
        settings_label.setStyleSheet("""
            font-size: 12pt;
            border-top: 0px;
            border-right: 0px;
            border-left: 0px;
            border-bottom: 0px;
            text-align: left;
            padding-left: 5px;
        """)

        # ADD ADDITIONAL WIDGETS AND FUNCTIONALITY HERE
        self.logging_layout.addWidget(settings_label)


    
def main():
    '''
    This function is the main entry point for the app.
    '''
    QtCore.qInstallMessageHandler(lambda *args: None)
    app = QApplication(sys.argv)
    app.setObjectName("MANGO")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    window.show_home_content()
    window.initialize_browser()
    sys.exit(app.exec())



if __name__ == "__main__":
    '''
    This is the entry point for the app.
    '''
    main()