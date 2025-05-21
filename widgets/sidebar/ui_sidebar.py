# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'sidebarBIGugz.ui'
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
    QPushButton, QSizePolicy, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(300, 599)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QSize(300, 0))
        Form.setStyleSheet(u"background-color: #1D3461")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.background = QFrame(Form)
        self.background.setObjectName(u"background")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.background.sizePolicy().hasHeightForWidth())
        self.background.setSizePolicy(sizePolicy1)
        self.background.setFrameShape(QFrame.Shape.StyledPanel)
        self.background.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.background)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.orthovis = QFrame(self.background)
        self.orthovis.setObjectName(u"orthovis")
        sizePolicy1.setHeightForWidth(self.orthovis.sizePolicy().hasHeightForWidth())
        self.orthovis.setSizePolicy(sizePolicy1)
        self.orthovis.setMinimumSize(QSize(0, 70))
        self.orthovis.setFrameShape(QFrame.Shape.StyledPanel)
        self.orthovis.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.orthovis)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 9, 0)
        self.logo = QLabel(self.orthovis)
        self.logo.setObjectName(u"logo")
        sizePolicy1.setHeightForWidth(self.logo.sizePolicy().hasHeightForWidth())
        self.logo.setSizePolicy(sizePolicy1)
        self.logo.setPixmap(QPixmap(u"assets/logo_small.png"))
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.horizontalLayout.addWidget(self.logo)

        self.label = QLabel(self.orthovis)
        self.label.setObjectName(u"label")
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        font = QFont()
        font.setPointSize(30)
        font.setBold(True)
        self.label.setFont(font)
        self.label.setStyleSheet(u"background-color: #1D3461;\n"
"color: white;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.verticalLayout_2.addWidget(self.orthovis)

        self.project_setup = QPushButton(self.background)
        self.project_setup.setObjectName(u"project_setup")
        sizePolicy1.setHeightForWidth(self.project_setup.sizePolicy().hasHeightForWidth())
        self.project_setup.setSizePolicy(sizePolicy1)
        font1 = QFont()
        font1.setPointSize(19)
        font1.setBold(True)
        font1.setKerning(True)
        self.project_setup.setFont(font1)
        self.project_setup.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.project_setup)

        self.segmentation = QPushButton(self.background)
        self.segmentation.setObjectName(u"segmentation")
        sizePolicy1.setHeightForWidth(self.segmentation.sizePolicy().hasHeightForWidth())
        self.segmentation.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setPointSize(19)
        font2.setBold(True)
        self.segmentation.setFont(font2)
        self.segmentation.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.segmentation)

        self.calibration = QPushButton(self.background)
        self.calibration.setObjectName(u"calibration")
        sizePolicy1.setHeightForWidth(self.calibration.sizePolicy().hasHeightForWidth())
        self.calibration.setSizePolicy(sizePolicy1)
        self.calibration.setFont(font2)
        self.calibration.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.calibration)

        self.define_axis = QPushButton(self.background)
        self.define_axis.setObjectName(u"define_axis")
        sizePolicy1.setHeightForWidth(self.define_axis.sizePolicy().hasHeightForWidth())
        self.define_axis.setSizePolicy(sizePolicy1)
        self.define_axis.setFont(font2)
        self.define_axis.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.define_axis)

        self.registration = QPushButton(self.background)
        self.registration.setObjectName(u"registration")
        sizePolicy1.setHeightForWidth(self.registration.sizePolicy().hasHeightForWidth())
        self.registration.setSizePolicy(sizePolicy1)
        self.registration.setFont(font2)
        self.registration.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.registration)

        self.visualisaiton = QPushButton(self.background)
        self.visualisaiton.setObjectName(u"visualisaiton")
        sizePolicy1.setHeightForWidth(self.visualisaiton.sizePolicy().hasHeightForWidth())
        self.visualisaiton.setSizePolicy(sizePolicy1)
        self.visualisaiton.setFont(font2)
        self.visualisaiton.setStyleSheet(u"color: white;\n"
"background-color: #1D3461;\n"
"border: none;\n"
"padding: 10px 25px;      \n"
"text-align: center;")

        self.verticalLayout_2.addWidget(self.visualisaiton)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 1)
        self.verticalLayout_2.setStretch(2, 1)
        self.verticalLayout_2.setStretch(3, 1)
        self.verticalLayout_2.setStretch(4, 1)
        self.verticalLayout_2.setStretch(5, 1)
        self.verticalLayout_2.setStretch(6, 1)

        self.verticalLayout.addWidget(self.background)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.logo.setText("")
        self.label.setText(QCoreApplication.translate("Form", u"OrthoVis", None))
        self.project_setup.setText(QCoreApplication.translate("Form", u"Project Setup", None))
        self.segmentation.setText(QCoreApplication.translate("Form", u"Segmentation", None))
        self.calibration.setText(QCoreApplication.translate("Form", u"Calibration", None))
        self.define_axis.setText(QCoreApplication.translate("Form", u"Define Axis", None))
        self.registration.setText(QCoreApplication.translate("Form", u"Registration", None))
        self.visualisaiton.setText(QCoreApplication.translate("Form", u"Visualisation", None))
    # retranslateUi

