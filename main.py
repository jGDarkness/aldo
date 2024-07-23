import json   
from PyQt6.QtCore import Qt, QUrl
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
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import sys



'''
    This app is meant to generate notes in markdown format from a user's Audible.com audio book
    library. The user provides login credentials, enters the year that they wish to generate 
    notes for and download cover art for.

    By: jGDarkenss@github.com
    Date: July 2024
'''



class MainWindow(QMainWindow):
    def __init__(self):
        '''
        Initialize the main window and set its properties and methods.
        '''
        super().__init__()


        # WINDOW SETTINGS
        self.setWindowTitle("Aldo - Audible.com Library Downloader for Obsidian")
        self.setObjectName("Main_Window")
        screen = QApplication.primaryScreen().geometry()
        window_width = 1500
        window_height = 800
        x = (screen.width() - window_width) // 2
        y = (screen.height() - window_height) // 2
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
        three_column_splitter.setStretchFactor(0, 10)
        three_column_splitter.setStretchFactor(1, 60)
        three_column_splitter.setStretchFactor(2, 30)
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


        # LOAD DEFAULT VIEW
        self.show_home_content()
        self.initialize_browser()

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
            font-size: 14pt;
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
            font-size: 14pt;
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
            font-size: 14pt;
            border-top: 0px;
            border-right: 0px;
            border-left: 0px;
            border-bottom: 0px;
            text-align: left;
            padding-left: 5px;
        """)

        # ADD ADDITIONAL WIDGETS AND FUNCTIONALITY HERE

        self.logging_layout.addWidget(settings_label)


    def initialize_browser(self):
        chrome_options = Options()
        service = Service() 
        chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl("https://www.audible.com"))
        self.web_view.setZoomFactor(0.60)
        for i in reversed(range(self.central_widget_content.layout().count())):
            self.central_widget_content.layout().itemAt(i).widget().setParent(None)
        self.central_widget_content.layout().addWidget(self.web_view)



def main():
    '''
    This function is the main entry point for the app.
    '''

    # APP SETTINGS
    app = QApplication(sys.argv)
    app.setObjectName("MANGO")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()