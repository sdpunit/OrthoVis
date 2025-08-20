# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'registration_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGraphicsView,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QTextEdit, QVBoxLayout, QWidget)

from widgets.sidebar.sidebar import Sidebar
from widgets.titlebar.titlebar import Titlebar

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(862, 550)
        Form.setStyleSheet(u"")
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

        self.rightpanel = QWidget(Form)
        self.rightpanel.setObjectName(u"rightpanel")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.rightpanel.sizePolicy().hasHeightForWidth())
        self.rightpanel.setSizePolicy(sizePolicy1)
        self.verticalLayout = QVBoxLayout(self.rightpanel)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.titlebar = Titlebar(self.rightpanel)
        self.titlebar.setObjectName(u"titlebar")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sizePolicy2)
        self.titlebar.setMinimumSize(QSize(0, 70))

        self.verticalLayout.addWidget(self.titlebar)

        self.mainpanel = QFrame(self.rightpanel)
        self.mainpanel.setObjectName(u"mainpanel")
        sizePolicy1.setHeightForWidth(self.mainpanel.sizePolicy().hasHeightForWidth())
        self.mainpanel.setSizePolicy(sizePolicy1)
        self.mainpanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.mainpanel.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_2 = QHBoxLayout(self.mainpanel)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.VTK_display = QGraphicsView(self.mainpanel)
        self.VTK_display.setObjectName(u"VTK_display")

        self.horizontalLayout_2.addWidget(self.VTK_display)

        self.details = QWidget(self.mainpanel)
        self.details.setObjectName(u"details")
        self.details.setStyleSheet(u"")
        self.verticalLayout_2 = QVBoxLayout(self.details)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.pushButton = QPushButton(self.details)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setMinimumSize(QSize(0, 40))
        self.pushButton.setStyleSheet(u"background-color: rgb(255, 215, 0);\n"
"border-radius: 10px;\n"
"border: none;\n"
"font: 600 12pt \"Segoe UI\";\n"
"")

        self.verticalLayout_2.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.details)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setMinimumSize(QSize(0, 40))
        self.pushButton_2.setStyleSheet(u"background-color: rgb(255, 215, 0);\n"
"border-radius: 10px;\n"
"border: none;\n"
"font: 600 12pt \"Segoe UI\";\n"
"")

        self.verticalLayout_2.addWidget(self.pushButton_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(-1, -1, -1, 0)
        self.pos_xLabel = QLabel(self.details)
        self.pos_xLabel.setObjectName(u"pos_xLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.pos_xLabel)

        self.pos_x = QLineEdit(self.details)
        self.pos_x.setObjectName(u"pos_x")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.pos_x)

        self.pos_yLabel = QLabel(self.details)
        self.pos_yLabel.setObjectName(u"pos_yLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.pos_yLabel)

        self.pos_y = QLineEdit(self.details)
        self.pos_y.setObjectName(u"pos_y")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.pos_y)

        self.pos_zLabel = QLabel(self.details)
        self.pos_zLabel.setObjectName(u"pos_zLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.pos_zLabel)

        self.pos_z = QLineEdit(self.details)
        self.pos_z.setObjectName(u"pos_z")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.pos_z)

        self.rotation_xLabel = QLabel(self.details)
        self.rotation_xLabel.setObjectName(u"rotation_xLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.rotation_xLabel)

        self.rotation_x = QLineEdit(self.details)
        self.rotation_x.setObjectName(u"rotation_x")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.rotation_x)

        self.rotation_yLabel = QLabel(self.details)
        self.rotation_yLabel.setObjectName(u"rotation_yLabel")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.rotation_yLabel)

        self.rotation_y = QLineEdit(self.details)
        self.rotation_y.setObjectName(u"rotation_y")

        self.formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.rotation_y)

        self.rotation_zLabel = QLabel(self.details)
        self.rotation_zLabel.setObjectName(u"rotation_zLabel")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.rotation_zLabel)

        self.rotation_z = QLineEdit(self.details)
        self.rotation_z.setObjectName(u"rotation_z")

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.rotation_z)


        self.verticalLayout_2.addLayout(self.formLayout)

        self.textEdit = QTextEdit(self.details)
        self.textEdit.setObjectName(u"textEdit")

        self.verticalLayout_2.addWidget(self.textEdit)


        self.horizontalLayout_2.addWidget(self.details)

        self.horizontalLayout_2.setStretch(0, 3)
        self.horizontalLayout_2.setStretch(1, 1)

        self.verticalLayout.addWidget(self.mainpanel)


        self.horizontalLayout.addWidget(self.rightpanel)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Load Bone Mask", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Register Current Bone", None))
        self.pos_xLabel.setText(QCoreApplication.translate("Form", u"pos_x", None))
        self.pos_x.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.pos_yLabel.setText(QCoreApplication.translate("Form", u"pos_y", None))
        self.pos_y.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.pos_zLabel.setText(QCoreApplication.translate("Form", u"pos_z", None))
        self.pos_z.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.rotation_xLabel.setText(QCoreApplication.translate("Form", u"rotation_x", None))
        self.rotation_x.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.rotation_yLabel.setText(QCoreApplication.translate("Form", u"rotation_y", None))
        self.rotation_y.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.rotation_zLabel.setText(QCoreApplication.translate("Form", u"rotation_z", None))
        self.rotation_z.setText(QCoreApplication.translate("Form", u"[link to object]", None))
        self.textEdit.setHtml(QCoreApplication.translate("Form", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'.AppleSystemUIFont'; font-size:13pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Starting with the Femur, load each bone mask onto the fluoroscopy frame. Align the bone mask with the correlating bone in the frame by manipulating themask with 6 DoF. Following the Femur, the Tibia and Fibula will need to be registered.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><"
                        "br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Use mouse interactions for translations and [inset interaction type] for rotations. You may also manually change the parameters of the mask using the above input fields.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">Upon confirming registration of the current bone, our high powered AI model will register the current bone mask to the rest of the fluoroscopy frames.</p></body></html>", None))
    # retranslateUi

