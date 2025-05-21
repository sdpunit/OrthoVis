# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sidebar.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(247, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setStyleSheet(u"background-color: #1D3461")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(70, 20, 171, 51))
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        font = QFont()
        font.setPointSize(40)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet(u"background-color: #1D3461;\n"
"color: white;")
        self.project_setup = QPushButton(Form)
        self.project_setup.setObjectName(u"project_setup")
        self.project_setup.setGeometry(QRect(0, 90, 251, 85))
        font1 = QFont()
        font1.setPointSize(19)
        font1.setBold(True)
        font1.setKerning(True)
        self.project_setup.setFont(font1)
        self.project_setup.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.segmentation = QPushButton(Form)
        self.segmentation.setObjectName(u"segmentation")
        self.segmentation.setGeometry(QRect(0, 170, 251, 85))
        font2 = QFont()
        font2.setPointSize(19)
        font2.setBold(True)
        self.segmentation.setFont(font2)
        self.segmentation.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.calibration = QPushButton(Form)
        self.calibration.setObjectName(u"calibration")
        self.calibration.setGeometry(QRect(0, 250, 251, 85))
        self.calibration.setFont(font2)
        self.calibration.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.define_axis = QPushButton(Form)
        self.define_axis.setObjectName(u"define_axis")
        self.define_axis.setGeometry(QRect(0, 330, 251, 85))
        self.define_axis.setFont(font2)
        self.define_axis.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.registration = QPushButton(Form)
        self.registration.setObjectName(u"registration")
        self.registration.setGeometry(QRect(0, 410, 251, 85))
        self.registration.setFont(font2)
        self.registration.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.visualisaiton = QPushButton(Form)
        self.visualisaiton.setObjectName(u"visualisaiton")
        self.visualisaiton.setGeometry(QRect(0, 490, 251, 85))
        self.visualisaiton.setFont(font2)
        self.visualisaiton.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: left;")
        self.background = QFrame(Form)
        self.background.setObjectName(u"background")
        self.background.setGeometry(QRect(0, 0, 251, 601))
        self.background.setFrameShape(QFrame.Shape.StyledPanel)
        self.background.setFrameShadow(QFrame.Shadow.Raised)
        self.background.raise_()
        self.label.raise_()
        self.project_setup.raise_()
        self.segmentation.raise_()
        self.calibration.raise_()
        self.define_axis.raise_()
        self.registration.raise_()
        self.visualisaiton.raise_()

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"OrthoVis", None))
        self.project_setup.setText(QCoreApplication.translate("Form", u"Project Setup", None))
        self.segmentation.setText(QCoreApplication.translate("Form", u"Segmentation", None))
        self.calibration.setText(QCoreApplication.translate("Form", u"Calibration", None))
        self.define_axis.setText(QCoreApplication.translate("Form", u"Define Axis", None))
        self.registration.setText(QCoreApplication.translate("Form", u"Registration", None))
        self.visualisaiton.setText(QCoreApplication.translate("Form", u"Visualisation", None))
    # retranslateUi

