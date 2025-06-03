#先安装包pip install PyQt5 PyQtWebEngine
#cd C:\Users\19122\Desktop\软件工程\实验\代码\Live2D\backend
#uvicorn main:app --reload
#cd C:\Users\19122\Desktop\软件工程\实验\代码\Live2D\frontend
#npm run serve
import sys
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

class MainWindow(QMainWindow):
    def __init__(self, id):
        super().__init__()
        self.setWindowTitle("实时内容")
        self.setGeometry(100, 100, 800, 800)
        self.chat = id
        self.m = 0

        # 创建主布局
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # 只保留网页视图
        self.web_view = QWebEngineView()
        self.web_view.load(QUrl("http://localhost:9003"))
        
        main_layout.addWidget(self.web_view)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow(1)
    window.show()
    sys.exit(app.exec_())