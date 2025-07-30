# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'project_setup_windowuwvBFy.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListView, QPushButton, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget)

from widgets.sidebar.sidebar import Sidebar
from widgets.titlebar.titlebar import Titlebar

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(623, 564)
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.sidebar = Sidebar(Form)
        self.sidebar.setObjectName(u"sidebar")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.sidebar.sizePolicy().hasHeightForWidth())
        self.sidebar.setSizePolicy(sizePolicy)

        self.horizontalLayout.addWidget(self.sidebar)

        self.mainpanel = QWidget(Form)
        self.mainpanel.setObjectName(u"mainpanel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.mainpanel.sizePolicy().hasHeightForWidth())
        self.mainpanel.setSizePolicy(sizePolicy1)
        self.verticalLayout = QVBoxLayout(self.mainpanel)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.titlebar = Titlebar(self.mainpanel)
        self.titlebar.setObjectName(u"titlebar")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sizePolicy2)
        self.titlebar.setMinimumSize(QSize(0, 70))

        self.verticalLayout.addWidget(self.titlebar)

        self.dataPanel = QFrame(self.mainpanel)
        self.dataPanel.setObjectName(u"dataPanel")
        sizePolicy1.setHeightForWidth(self.dataPanel.sizePolicy().hasHeightForWidth())
        self.dataPanel.setSizePolicy(sizePolicy1)
        self.dataPanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.dataPanel.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.dataPanel)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.details = QHBoxLayout()
        self.details.setObjectName(u"details")
        self.inputLayout = QVBoxLayout()
        self.inputLayout.setSpacing(0)
        self.inputLayout.setObjectName(u"inputLayout")
        self.projectNameLayout = QVBoxLayout()
        self.projectNameLayout.setObjectName(u"projectNameLayout")
        self.projectNameLayout.setContentsMargins(9, 9, 9, 9)
        self.projectNameLabel = QLabel(self.dataPanel)
        self.projectNameLabel.setObjectName(u"projectNameLabel")
        sizePolicy2.setHeightForWidth(self.projectNameLabel.sizePolicy().hasHeightForWidth())
        self.projectNameLabel.setSizePolicy(sizePolicy2)
        font = QFont()
        font.setFamilies([u"Segoe UI"])
        font.setPointSize(16)
        font.setWeight(QFont.DemiBold)
        font.setItalic(False)
        self.projectNameLabel.setFont(font)
        self.projectNameLabel.setStyleSheet(u"font: 600 16pt \"Segoe UI\";")
        self.projectNameLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.projectNameLayout.addWidget(self.projectNameLabel)

        self.projectNameInput = QLineEdit(self.dataPanel)
        self.projectNameInput.setObjectName(u"projectNameInput")
        sizePolicy2.setHeightForWidth(self.projectNameInput.sizePolicy().hasHeightForWidth())
        self.projectNameInput.setSizePolicy(sizePolicy2)
        self.projectNameInput.setMaximumSize(QSize(16777215, 50))

        self.projectNameLayout.addWidget(self.projectNameInput)


        self.inputLayout.addLayout(self.projectNameLayout)

        self.projectDesLayout = QVBoxLayout()
        self.projectDesLayout.setObjectName(u"projectDesLayout")
        self.projectDesLayout.setContentsMargins(9, 9, 9, 9)
        self.projectDesLabel = QLabel(self.dataPanel)
        self.projectDesLabel.setObjectName(u"projectDesLabel")
        sizePolicy2.setHeightForWidth(self.projectDesLabel.sizePolicy().hasHeightForWidth())
        self.projectDesLabel.setSizePolicy(sizePolicy2)
        self.projectDesLabel.setFont(font)
        self.projectDesLabel.setStyleSheet(u"font: 600 16pt \"Segoe UI\";")
        self.projectDesLabel.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)

        self.projectDesLayout.addWidget(self.projectDesLabel)

        self.projectDesInput = QTextEdit(self.dataPanel)
        self.projectDesInput.setObjectName(u"projectDesInput")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.projectDesInput.sizePolicy().hasHeightForWidth())
        self.projectDesInput.setSizePolicy(sizePolicy3)
        self.projectDesInput.setMaximumSize(QSize(16777215, 200))
        self.projectDesInput.setTabStopDistance(80.000000000000000)

        self.projectDesLayout.addWidget(self.projectDesInput)


        self.inputLayout.addLayout(self.projectDesLayout)


        self.details.addLayout(self.inputLayout)

        self.importListLayout = QVBoxLayout()
        self.importListLayout.setObjectName(u"importListLayout")
        self.importListLayout.setContentsMargins(9, 9, 9, 9)
        self.importListLabel = QLabel(self.dataPanel)
        self.importListLabel.setObjectName(u"importListLabel")
        sizePolicy2.setHeightForWidth(self.importListLabel.sizePolicy().hasHeightForWidth())
        self.importListLabel.setSizePolicy(sizePolicy2)
        self.importListLabel.setFont(font)
        self.importListLabel.setStyleSheet(u"font: 600 16pt \"Segoe UI\";")

        self.importListLayout.addWidget(self.importListLabel)

        self.importListView = QListView(self.dataPanel)
        self.importListView.setObjectName(u"importListView")
        self.importListView.setMaximumSize(QSize(16777215, 280))

        self.importListLayout.addWidget(self.importListView)


        self.details.addLayout(self.importListLayout)

        self.details.setStretch(0, 1)
        self.details.setStretch(1, 1)

        self.verticalLayout_2.addLayout(self.details)

        self.buttons = QVBoxLayout()
        self.buttons.setObjectName(u"buttons")
        self.buttons.setContentsMargins(9, 9, 9, 9)
        self.importsLayout = QHBoxLayout()
        self.importsLayout.setSpacing(20)
        self.importsLayout.setObjectName(u"importsLayout")
        self.importFluoro = QPushButton(self.dataPanel)
        self.importFluoro.setObjectName(u"importFluoro")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.importFluoro.sizePolicy().hasHeightForWidth())
        self.importFluoro.setSizePolicy(sizePolicy4)
        self.importFluoro.setMinimumSize(QSize(180, 40))
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(12)
        font1.setWeight(QFont.DemiBold)
        font1.setItalic(False)
        self.importFluoro.setFont(font1)
        self.importFluoro.setStyleSheet(u"QPushButton {\n"
"background-color: rgb(255, 215, 0);\n"
"font: 600 12pt \"Segoe UI\";\n"
"border-radius: 10px;}\n"
"\n"
"QPushButton:hover {\n"
"background-color: rgb(255, 230, 50);\n"
"font-size: 14pt;\n"
"}\n"
"")

        self.importsLayout.addWidget(self.importFluoro)

        self.save = QPushButton(self.dataPanel)
        self.save.setObjectName(u"save")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(1)
        sizePolicy5.setVerticalStretch(1)
        sizePolicy5.setHeightForWidth(self.save.sizePolicy().hasHeightForWidth())
        self.save.setSizePolicy(sizePolicy5)
        self.save.setMinimumSize(QSize(60, 40))
        self.save.setStyleSheet(u"QPushButton {\n"
"background-color: rgb(255, 215, 0);\n"
"font: 600 12pt \"Segoe UI\";\n"
"border-radius: 10px;}\n"
"\n"
"QPushButton:hover {\n"
"background-color: rgb(255, 230, 50);\n"
"font-size: 14pt;\n"
"}\n"
"")

        self.importsLayout.addWidget(self.save)

        self.importsLayout.setStretch(0, 1)

        self.buttons.addLayout(self.importsLayout)


        self.verticalLayout_2.addLayout(self.buttons)

        self.verticalLayout_2.setStretch(0, 5)
        self.verticalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.dataPanel)


        self.horizontalLayout.addWidget(self.mainpanel)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.projectNameLabel.setText(QCoreApplication.translate("Form", u"Project Name", None))
        self.projectDesLabel.setText(QCoreApplication.translate("Form", u"Project Description", None))
        self.importListLabel.setText(QCoreApplication.translate("Form", u"Successful Imports", None))
        self.importFluoro.setText(QCoreApplication.translate("Form", u"Import Data", None))
        self.save.setText(QCoreApplication.translate("Form", u"Save", None))
    # retranslateUi

