import sys
import os
import imghdr
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QMessageBox
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QGridLayout
from PyQt5.QtWidgets import QGroupBox, QPushButton, QSlider
from PyQt5.QtWidgets import QLabel, QFileDialog, QSizePolicy, QSpacerItem
from PyQt5.QtGui import QIcon, QDrag, QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal
from timelapse_processing import ImageList, Image, loadImage, toRGB

"""
QApplication: manages application object.
QWidget: base class of all user interface objects. Receives events from the window system.
QMainWindow: main application window - framework to build the apps' user interface.
QDesktopWidget: provides access to user screen information.
"""

class DropButton(QPushButton):
    """
    Drag n Drop area widget
    """
    itemDropped = pyqtSignal(list)

    def __init__(self, title, width, height, parent):
        super().__init__(title, parent)
        self.setVisible(True)
        self.setAcceptDrops(True)
        self.setStyleSheet("background-color: rgba(85, 153, 255, 10%);"
                           "border-style: dashed;"
                           "border-width: 1px;"
                           "border-color: gray;"
                           "color: gray;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(width, height)
    
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
            links = []
            [links.append(u.toLocalFile()) for u in m.urls()]
            self.itemDropped.emit(links)
            self.setVisible(False)
        else:
            e.ignore()


class TimelapseApp(QMainWindow):
    """
    Timelapse exposure fix application window
    """
    def __init__(self):
        super().__init__()
        self.title = 'Timelapse Exposure Fix'
        self.icon = 'camera_icon.png'
        self.left = 100
        self.top = 100
        self.width = 640
        self.height = 480
        self.minSize = 100
        self.imgScale = 0.45
        self.origImages = ImageList()
        self.processedImages = ImageList()
        self.imageFormat = ''
        self.initUI()

    def initUI(self):
        # Menu bar
        mainMenu = self.menuBar()
        self.fileMenu = mainMenu.addMenu('File')
        reloadAct = QAction('New Session', self)
        reloadAct.setShortcut('Ctrl+R')
        reloadAct.triggered.connect(self.reloadSession)
        reloadAct.setStatusTip('Reload a new session for timelapse processing')
        self.fileMenu.addAction(reloadAct)
        saveAct = QAction('Save Images', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.triggered.connect(self.saveImages)
        saveAct.setStatusTip('Save processed images')
        self.fileMenu.addAction(saveAct)
        saveAct.setDisabled(True)
        exitAct = QAction('Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(self.close)
        exitAct.setStatusTip('Exit timelapse processing tool')
        self.fileMenu.addAction(exitAct)
        helpMenu = mainMenu.addMenu('Help')
        aboutAct = QAction('Drag n Drop', self)
        aboutAct.triggered.connect(self.helpWindow)
        aboutAct.setStatusTip('Drag n Drop information')
        helpMenu.addAction(aboutAct)

        # Grid layout
        self.createGridLayout()
        self.dragndrop.itemDropped.connect(self.pictureDropped)

        # Status bar
        self.statusBar()
        self.statusBar().setStyleSheet("background-color: white;")

        # Window settings
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon(self.icon))
        self.center()
        self.show()
    
    def createGridLayout(self):
        self.centralWidget = QWidget(self)
        self.centralWidget.setStyleSheet("background-color: white;")
        self.centralWidget.setStatusTip('Ready')
        self.setCentralWidget(self.centralWidget)

        self.sld = QSlider(Qt.Horizontal, self)

        mainLayout = QHBoxLayout()
        vLayout = QVBoxLayout()
        grid = QGridLayout()
        grid.setSpacing(25)
        grid.setContentsMargins(25, 25, 25, 25)

        self.dragndrop = DropButton('Drop images here', self.width - self.minSize, self.minSize, self)
        grid.addWidget(self.dragndrop, 0, 0, 1, 4)

        self.viewerGroupBox = QGroupBox('Time-lapse viewer')
        self.img1 = QLabel(self.centralWidget)
        self.img1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img1.setMinimumSize(self.minSize, self.minSize)

        self.img2 = QLabel(self.centralWidget)
        self.img2.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.img2.setMinimumSize(self.minSize, self.minSize)

        imgviewer = QHBoxLayout()
        leftSpacer = QSpacerItem(self.minSize/10, self.minSize, QSizePolicy.Expanding, QSizePolicy.Minimum)
        imgviewer.addSpacerItem(leftSpacer)
        imgviewer.addWidget(self.img1)
        imgviewer.addWidget(self.img2)
        rightSpacer = QSpacerItem(self.minSize/10, self.minSize, QSizePolicy.Expanding, QSizePolicy.Minimum)
        imgviewer.addSpacerItem(rightSpacer)
        self.viewerGroupBox.setLayout(imgviewer)
        self.viewerGroupBox.setVisible(False)

        grid.addWidget(self.viewerGroupBox, 2, 1)

        grid.addWidget(self.sld, 3, 1)
        self.sld.setValue(0)
        self.sld.setRange(0,0)
        self.sld.valueChanged.connect(self.updateViewerIndex)
        self.sld.setVisible(False)

        # Encapsulate grid layout in VBox and HBox
        vLayout.addLayout(grid)
        verticalSpacer = QSpacerItem(self.minSize, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vLayout.addItem(verticalSpacer)
        hLeftSpacer = QSpacerItem(self.minSize/10, self.minSize, QSizePolicy.Expanding, QSizePolicy.Minimum)
        mainLayout.addItem(hLeftSpacer)
        mainLayout.addLayout(vLayout)
        hRightSpacer = QSpacerItem(self.minSize/10, self.minSize, QSizePolicy.Expanding, QSizePolicy.Minimum)
        mainLayout.addItem(hRightSpacer)
        self.centralWidget.setLayout(mainLayout)
    
    def updateViewerIndex(self):
        self.updateViewer(self.sld.value())

    def updateViewer(self, imageNumber):
        if len(self.origImages) > 0:
            rgb = toRGB(self.origImages[imageNumber].img)
            qimage = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            pixmap1 = QPixmap(qimage)
            pixmap1 = pixmap1.scaledToWidth(self.width * self.imgScale)
            self.img1.setPixmap(pixmap1)
            
        if len(self.processedImages) > 0:
            rgb = toRGB(self.processedImages[imageNumber].img)
            qimage = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            pixmap2 = QPixmap(qimage)
            pixmap2 = pixmap2.scaledToWidth(self.width * self.imgScale)
            self.img2.setPixmap(pixmap2)
    
    def pictureDropped(self, links):
        self.statusBar().showMessage('Processing...')
        self.imageFormat = imghdr.what(links[0])
        [self.origImages.append(Image(loadImage(link))) for link in links]
        newImages = ImageList(self.origImages[:])
        newImages.computeStats()
        newImages.fixExposure()
        self.processedImages = newImages

        self.fileMenu.actions()[1].setDisabled(False)

        self.updateViewer(0)
        self.sld.setRange(0, len(self.origImages) - 1)
        self.sld.setValue(0)
        self.statusBar().showMessage('Ready')

        self.viewerGroupBox.setVisible(True)
        self.sld.setVisible(True)
    
    def saveImages(self):
        self.statusBar().showMessage('Saving Images...')
        newDir = '/processed-images'
        destDir = QFileDialog.getExistingDirectory(self, "Select Directory") + newDir
        if not os.path.exists(destDir):
            os.makedirs(destDir)
        for i,obj in enumerate(self.processedImages):
            rgb = toRGB(obj.img)
            qimage = QImage(rgb, rgb.shape[1], rgb.shape[0], QImage.Format_RGB888)
            qimage.save(destDir + '/processed_image' + str(i+1).zfill(4) + '.' + self.imageFormat)
        self.statusBar().showMessage('Ready')
    
    def reloadSession(self):
        mboxtitle = 'Warning'
        mboxmsg = 'Are you sure you want to start a new session?\nAll unsaved changes will be lost.'
        reply = QMessageBox.warning(self, mboxtitle, mboxmsg,
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.origImages[:]
            del self.processedImages[:]
            self.img1.clear()
            self.img2.clear()
            self.sld.setValue(0)
            self.sld.setRange(0,0)
            self.dragndrop.setVisible(True)
            self.viewerGroupBox.setVisible(False)
            self.sld.setVisible(False)
    
    def helpWindow(self):
        mboxtitle = 'Help'
        mboxmsg = ('If your time-lapse is not displaying in the proper order, or there seems to be a jump '
        'cut to previous frames, make sure the last item clicked when the images were dragged was '
        'the first image of your sequence. The order of selection is preserved during drag and drop.')
                   
        reply = QMessageBox.information(self, mboxtitle, mboxmsg,
                                        QMessageBox.Ok, QMessageBox.Ok)

    def center(self):
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

    def closeEvent(self, event):
        mboxtitle = 'Message'
        mboxmsg = 'Are you sure you want to quit?'
        reply = QMessageBox.warning(self, mboxtitle, mboxmsg,
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = TimelapseApp()
    sys.exit(app.exec_())