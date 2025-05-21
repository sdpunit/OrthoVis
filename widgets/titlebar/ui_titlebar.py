# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'titlebarpIBfuF.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QSizePolicy, QToolButton, QWidget)

class Ui_TitleBar(object):
    def setupUi(self, TitleBar):
        if not TitleBar.objectName():
            TitleBar.setObjectName(u"TitleBar")
        TitleBar.resize(790, 91)
        self.gridLayout = QGridLayout(TitleBar)
        self.gridLayout.setObjectName(u"gridLayout")
        self.horizontalFrame = QFrame(TitleBar)
        self.horizontalFrame.setObjectName(u"horizontalFrame")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.horizontalFrame.sizePolicy().hasHeightForWidth())
        self.horizontalFrame.setSizePolicy(sizePolicy)
        self.horizontalFrame.setStyleSheet(u"background-color: rgb(111, 138, 183);")
        self.horizontalLayout = QHBoxLayout(self.horizontalFrame)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.title = QLabel(self.horizontalFrame)
        self.title.setObjectName(u"title")
        font = QFont()
        font.setFamilies([u"Dubai"])
        font.setPointSize(24)
        font.setBold(False)
        self.title.setFont(font)
        self.title.setStyleSheet(u"color: rgb(255, 255, 255);")

        self.horizontalLayout.addWidget(self.title)

        self.collapse = QToolButton(self.horizontalFrame)
        self.collapse.setObjectName(u"collapse")
        icon = QIcon()
        icon.addFile(u"assets/collapse_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.collapse.setIcon(icon)

        self.horizontalLayout.addWidget(self.collapse)

        self.expand = QToolButton(self.horizontalFrame)
        self.expand.setObjectName(u"expand")
        icon1 = QIcon()
        icon1.addFile(u"assets/expand_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.expand.setIcon(icon1)

        self.horizontalLayout.addWidget(self.expand)

        self.close = QToolButton(self.horizontalFrame)
        self.close.setObjectName(u"close")
        self.close.setStyleSheet(u"color: rgb(255, 255, 255)")
        icon2 = QIcon()
        icon2.addFile(u"assets/exit_icon.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.close.setIcon(icon2)

        self.horizontalLayout.addWidget(self.close)


        self.gridLayout.addWidget(self.horizontalFrame, 0, 0, 1, 1)


        self.retranslateUi(TitleBar)

        QMetaObject.connectSlotsByName(TitleBar)
    # setupUi

    def retranslateUi(self, TitleBar):
        TitleBar.setWindowTitle(QCoreApplication.translate("TitleBar", u"Form", None))
        self.title.setText(QCoreApplication.translate("TitleBar", u"Page Title", None))
        self.collapse.setText(QCoreApplication.translate("TitleBar", u"...", None))
        self.expand.setText(QCoreApplication.translate("TitleBar", u"...", None))
        self.close.setText(QCoreApplication.translate("TitleBar", u"...", None))
    # retranslateUi

