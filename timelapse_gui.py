import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QMessageBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtWidgets import QGroupBox, QPushButton, QSlider
from PyQt5.QtWidgets import QLabel, QFileDialog, QSizePolicy
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QImage
from PyQt5.QtCore import Qt
from timelapse_processing import ImageList, Image, loadImage, toRGB

'''
QApplication: manages application object.
QWidget: base class of all user interface objects. Receives events from the window system.
QMainWindow: main application window - framework to build the apps' user interface.
QDesktopWidget: provides access to user screen information.
'''

class DropButton(QPushButton):
    def __init__(self, title, parent):
        super().__init__(title, parent)
        self.setVisible(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: rgba(85, 153, 255, 10%);"
                           "border-style: dashed;"
                           "border-width: 1px;"
                           "border-color: gray;"
                           "color: gray;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(200, 100)
    
    def dragEnterEvent(self, e):
        m = e.mimeData()
        if m.hasUrls():
            e.accept()
        else:
            e.ignore()
    
    def dropEvent(self, e):
        m = e.mimeData()
        if m.hasUrls():
            e.accept()
            self.parent().parent().statusBar().showMessage('Processing...')
            #[self.parent().parent().origImages.append(u.toLocalFile()) for u in m.urls()]
            [self.parent().parent().origImages.append(Image(loadImage(u.toLocalFile()))) for u in m.urls()]
            self.setVisible(False)

            newImages = ImageList(self.parent().parent().origImages[:])
            newImages.computeStats()
            newImages.fixExposure()
            self.parent().parent().processedImages = newImages
            self.parent().parent().statusBar().showMessage('Ready')
            
            self.parent().parent().updateViewer(0)
            self.parent().parent().sld.setRange(0, len(self.parent().parent().origImages) - 1)
            self.parent().parent().sld.setValue(0)
        else:
            e.ignore()


class TimelapseApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Timelapse Exposure Fix'
        self.icon = 'camera_icon.png'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.origImages = ImageList()
        self.processedImages = ImageList()
        self.initUI()

    def initUI(self):
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        reloadAct = QAction('New Session', self)
        reloadAct.setShortcut('Ctrl+R')
        reloadAct.triggered.connect(self.reloadSession)
        fileMenu.addAction(reloadAct)
        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(self.close)
        fileMenu.addAction(exitAct)
        helpMenu = mainMenu.addMenu('Help')
        aboutAct = QAction('Drag n Drop', self)
        aboutAct.triggered.connect(self.helpWindow)
        helpMenu.addAction(aboutAct)
        
        self.createGridLayout()

        self.statusBar()
        self.statusBar().setStyleSheet("background-color: white;")
        self.statusBar().showMessage('Ready')

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon(self.icon))
        self.center()
        self.show()
    
    def createGridLayout(self):
        self.centralWidget = QWidget(self)
        self.centralWidget.setStyleSheet("background-color: white;")
        self.setCentralWidget(self.centralWidget)

        self.sld = QSlider(Qt.Horizontal, self)

        grid = QGridLayout()
        grid.setSpacing(25)
        grid.setContentsMargins(25, 25, 25, 25)
        self.centralWidget.setLayout(grid)

        self.dragndrop = DropButton('Drop images here', self)
        grid.addWidget(self.dragndrop, 0, 0, 1, 4)
        #grid.setRowStretch(0,2)

        groupBox = QGroupBox('Time-lapse viewer')
        self.img1 = QLabel(self.centralWidget)
        self.img1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img1.setMinimumSize(100, 100)

        self.img2 = QLabel(self.centralWidget)
        self.img2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img2.setMinimumSize(100, 100)

        imgviewer = QHBoxLayout()
        imgviewer.addWidget(self.img1)
        imgviewer.addWidget(self.img2)
        groupBox.setLayout(imgviewer)

        grid.addWidget(groupBox, 2, 1)

        grid.addWidget(self.sld, 3, 1)
        self.sld.setValue(0)
        self.sld.setRange(0,0)
        self.sld.valueChanged.connect(self.updateViewerIndex)
    
    def updateViewerIndex(self):
        self.updateViewer(self.sld.value())

    def updateViewer(self, imageNumber):
        if len(self.origImages) > 0:
            rgb = toRGB(self.origImages[imageNumber].img)
            qimage = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            pixmap1 = QPixmap(qimage)
            pixmap1 = pixmap1.scaledToWidth(self.width*0.45)
            self.img1.setPixmap(pixmap1)
            
        if len(self.processedImages) > 0:
            rgb = toRGB(self.processedImages[imageNumber].img)
            qimage = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            pixmap2 = QPixmap(qimage)
            pixmap2 = pixmap2.scaledToWidth(self.width*0.45)
            self.img2.setPixmap(pixmap2)
    
    def reloadSession(self):
        mboxtitle = 'Warning'
        mboxmsg = 'Are you sure you want to start a new session?\nAll unsaved changes will be lost.'
        reply = QMessageBox.question(self, mboxtitle, mboxmsg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.origImages[:]
            del self.processedImages[:]
            self.img1.clear()
            self.img2.clear()
            self.sld.setValue(0)
            self.sld.setRange(0,0)
            self.dragndrop.setVisible(True)
    
    def helpWindow(self):
        mboxtitle = 'Help'
        mboxmsg = ('If your time-lapse is not displaying in the proper order, or there seems to be a jump '
        'cut to previous frames, make sure the last item clicked when the images were dragged was '
        'the first image of your sequence. The order of selection is preserved during drag and drop.')
                   
        reply = QMessageBox.question(self, mboxtitle, mboxmsg,
            QMessageBox.Ok, QMessageBox.Ok)

    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def closeEvent(self, event):
        mboxtitle = 'Message'
        mboxmsg = 'Are you sure you want to quit?'
        reply = QMessageBox.question(self, mboxtitle, mboxmsg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = TimelapseApp()
    sys.exit(app.exec_())