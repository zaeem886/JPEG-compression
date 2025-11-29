# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_MainWindowUI(object):
    def setupUi(self, MainWindowUI):
        if not MainWindowUI.objectName():
            MainWindowUI.setObjectName(u"MainWindowUI")
        MainWindowUI.resize(700, 500)
        self.verticalLayout = QVBoxLayout(MainWindowUI)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setObjectName(u"buttonLayout")
        self.btn_load = QPushButton(MainWindowUI)
        self.btn_load.setObjectName(u"btn_load")

        self.buttonLayout.addWidget(self.btn_load)

        self.btn_compress = QPushButton(MainWindowUI)
        self.btn_compress.setObjectName(u"btn_compress")

        self.buttonLayout.addWidget(self.btn_compress)


        self.verticalLayout.addLayout(self.buttonLayout)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setObjectName(u"imageLayout")
        self.lbl_original = QLabel(MainWindowUI)
        self.lbl_original.setObjectName(u"lbl_original")
        self.lbl_original.setMinimumSize(QSize(300, 300))
        self.lbl_original.setFrameShape(QFrame.Box)
        self.lbl_original.setAlignment(Qt.AlignCenter)

        self.imageLayout.addWidget(self.lbl_original)

        self.lbl_result = QLabel(MainWindowUI)
        self.lbl_result.setObjectName(u"lbl_result")
        self.lbl_result.setMinimumSize(QSize(300, 300))
        self.lbl_result.setFrameShape(QFrame.Box)
        self.lbl_result.setAlignment(Qt.AlignCenter)

        self.imageLayout.addWidget(self.lbl_result)


        self.verticalLayout.addLayout(self.imageLayout)

        self.downloadLayout = QHBoxLayout()
        self.downloadLayout.setObjectName(u"downloadLayout")
        self.btn_download_compressed = QPushButton(MainWindowUI)
        self.btn_download_compressed.setObjectName(u"btn_download_compressed")

        self.downloadLayout.addWidget(self.btn_download_compressed)

        self.btn_download_decompressed = QPushButton(MainWindowUI)
        self.btn_download_decompressed.setObjectName(u"btn_download_decompressed")

        self.downloadLayout.addWidget(self.btn_download_decompressed)


        self.verticalLayout.addLayout(self.downloadLayout)


        self.retranslateUi(MainWindowUI)

        QMetaObject.connectSlotsByName(MainWindowUI)
    # setupUi

    def retranslateUi(self, MainWindowUI):
        MainWindowUI.setWindowTitle(QCoreApplication.translate("MainWindowUI", u"JPEG Compression Demo", None))
        self.btn_load.setText(QCoreApplication.translate("MainWindowUI", u"Load Image", None))
        self.btn_compress.setText(QCoreApplication.translate("MainWindowUI", u"Compress & Decompress", None))
        self.lbl_original.setText(QCoreApplication.translate("MainWindowUI", u"Original Image", None))
        self.lbl_result.setText(QCoreApplication.translate("MainWindowUI", u"Decompressed Image", None))
        self.btn_download_compressed.setText(QCoreApplication.translate("MainWindowUI", u"Download Compressed", None))
        self.btn_download_decompressed.setText(QCoreApplication.translate("MainWindowUI", u"Download Decompressed", None))
    # retranslateUi

