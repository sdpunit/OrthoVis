# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'new_project_windowWzVYGL.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QSizePolicy,
    QVBoxLayout, QWidget)

from widgets.sidebar.sidebar import Sidebar
from widgets.titlebar.titlebar import Titlebar

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(699, 607)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.sidebar = Sidebar(Form)
        self.sidebar.setObjectName(u"sidebar")

        self.horizontalLayout.addWidget(self.sidebar)

        self.mainpanel = QWidget(Form)
        self.mainpanel.setObjectName(u"mainpanel")
        self.verticalLayout = QVBoxLayout(self.mainpanel)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.titlebar = Titlebar(self.mainpanel)
        self.titlebar.setObjectName(u"titlebar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sizePolicy)
        self.titlebar.setMinimumSize(QSize(0, 70))

        self.verticalLayout.addWidget(self.titlebar)

        self.frame = QFrame(self.mainpanel)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout.addWidget(self.frame)


        self.horizontalLayout.addWidget(self.mainpanel)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
    # retranslateUi

