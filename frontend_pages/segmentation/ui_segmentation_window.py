# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'segmentation_windowVAwnAR.ui'
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
from PySide6.QtWidgets import (QApplication, QFormLayout, QFrame, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QTextBrowser, QVBoxLayout, QWidget)

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
        self.verticalLayout_2 = QVBoxLayout(self.details)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.info = QFormLayout()
        self.info.setObjectName(u"info")
        self.info.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.info.setContentsMargins(9, 9, 6, 6)
        self.group_lbl = QLabel(self.details)
        self.group_lbl.setObjectName(u"group_lbl")
        self.group_lbl.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.info.setWidget(0, QFormLayout.ItemRole.LabelRole, self.group_lbl)

        self.patient_lbl = QLabel(self.details)
        self.patient_lbl.setObjectName(u"patient_lbl")
        self.patient_lbl.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.info.setWidget(1, QFormLayout.ItemRole.LabelRole, self.patient_lbl)

        self.label = QLabel(self.details)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"font: 12pt \"Segoe UI\";")

        self.info.setWidget(0, QFormLayout.ItemRole.FieldRole, self.label)

        self.label_2 = QLabel(self.details)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setStyleSheet(u"font: 12pt \"Segoe UI\";")

        self.info.setWidget(1, QFormLayout.ItemRole.FieldRole, self.label_2)


        self.verticalLayout_2.addLayout(self.info)

        self.progress_wdg = QWidget(self.details)
        self.progress_wdg.setObjectName(u"progress_wdg")
        self.verticalLayout_3 = QVBoxLayout(self.progress_wdg)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.textBrowser = QTextBrowser(self.progress_wdg)
        self.textBrowser.setObjectName(u"textBrowser")
        font = QFont()
        font.setPointSize(10)
        self.textBrowser.setFont(font)

        self.verticalLayout_3.addWidget(self.textBrowser)


        self.verticalLayout_2.addWidget(self.progress_wdg)

        self.button_wdg = QWidget(self.details)
        self.button_wdg.setObjectName(u"button_wdg")
        self.horizontalLayout_3 = QHBoxLayout(self.button_wdg)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.segment_btn = QPushButton(self.button_wdg)
        self.segment_btn.setObjectName(u"segment_btn")
        self.segment_btn.setMinimumSize(QSize(0, 40))
        self.segment_btn.setStyleSheet(u"background-color: rgb(255, 215, 0);\n"
"border-radius: 10px;\n"
"border: none;\n"
"font: 600 12pt \"Segoe UI\";\n"
"")

        self.horizontalLayout_3.addWidget(self.segment_btn)


        self.verticalLayout_2.addWidget(self.button_wdg)

        self.verticalLayout_2.setStretch(0, 1)
        self.verticalLayout_2.setStretch(1, 5)

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
        self.patient_lbl.setText(QCoreApplication.translate("Form", u"Project:", None))
        self.label.setText("")
        self.label_2.setText("")

        # Apply improved styling with subtle shadow-like border
        self.textBrowser.setStyleSheet("""
            QTextBrowser { 
                border: none; 
                background-color: transparent; 

                border-radius: 6px;
                padding: 8px;
            }
        """)

        # Complete replacement for the textBrowser.setHtml() call with improved table-like layout:
        self.textBrowser.setHtml(QCoreApplication.translate("Form", 
        u"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">
        <html><head><meta name="qrichtext" content="1" /><meta charset="utf-8" /><style type="text/css">
        p, li { white-space: pre-wrap; }
        hr { height: 1px; border-width: 0; }
        li.unchecked::marker { content: "\\2610"; }
        li.checked::marker { content: "\\2612"; }
        .shortcut-title { 
            font-weight: bold; 
            font-size: 12pt; 
            color: #000000; 
            margin-bottom: 15px; 
            text-align: center;
        }
        .shortcut-section { 
            font-weight: bold; 
            font-size: 11pt; 
            color: #000000; 
            margin-top: 15px; 
            margin-bottom: 8px; 
            text-decoration: underline;
        }
        .shortcut-table {
            width: 100%;
            border-collapse: collapse;
            table-layout: fixed;
        }
        .shortcut-table td {
            padding: 2px 0px;
            vertical-align: top;
        }
        .shortcut-action { 
            font-weight: bold; 
            color: #000000; 
            width: 60%;
            text-align: left;
        }
        .shortcut-control { 
            color: #666666; 
            width: 40%;
            text-align: left;
            padding-left: 5px;
        }
        </style></head><body style="font-family:'Segoe UI'; font-size:10pt; font-weight:400; font-style:normal;">

        <p class="shortcut-title">SHORTCUTS</p>

        <p class="shortcut-section">Browse Mode</p>
        <table class="shortcut-table">
            <tr>
                <td class="shortcut-action">View Slices</td>
                <td class="shortcut-control">Scroll</td>
            </tr>
            <tr>
                <td class="shortcut-action">Zoom</td>
                <td class="shortcut-control">Ctrl + Scroll</td>
            </tr>
            <tr>
                <td class="shortcut-action">Pan</td>
                <td class="shortcut-control">Ctrl + Shift + Drag</td>
            </tr>
        </table>

        <p class="shortcut-section">Edit Mode</p>
        <table class="shortcut-table">
            <tr>
                <td class="shortcut-action">Paint</td>
                <td class="shortcut-control">Drag</td>
            </tr>
            <tr>
                <td class="shortcut-action">Erase</td>
                <td class="shortcut-control">Ctrl + Drag</td>
            </tr>
            <tr>
                <td class="shortcut-action">Pan</td>
                <td class="shortcut-control">Ctrl + Shift + Drag</td>
            </tr>
            <tr>
                <td class="shortcut-action">Brush Size</td>
                <td class="shortcut-control">+/-</td>
            </tr>
            <tr>
                <td class="shortcut-action">Save Edits</td>
                <td class="shortcut-control">S</td>
            </tr>
        </table>

        </body></html>""", None))
        self.segment_btn.setText(QCoreApplication.translate("Form", u"Segment CT", None))