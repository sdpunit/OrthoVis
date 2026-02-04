# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'calibration_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
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
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

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
        self.VTK_display.setEnabled(True)
        self.VTK_display.setFrameShape(QFrame.Shape.Box)

        self.horizontalLayout_2.addWidget(self.VTK_display)

        self.details = QWidget(self.mainpanel)
        self.details.setObjectName(u"details")
        self.details.setStyleSheet(u"")
        self.verticalLayout_2 = QVBoxLayout(self.details)
        self.verticalLayout_2.setSpacing(10)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        
        # Button style
        button_style = u"""QPushButton {
background-color: rgb(255, 215, 0);
font: 600 11pt "Segoe UI";
border-radius: 10px;}

QPushButton:hover {
background-color: rgb(255, 230, 50);
font-size: 12pt;
}
"""
        
        self.pushButton = QPushButton(self.details)
        self.pushButton.setObjectName(u"pushButton")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(20)
        sizePolicy3.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy3)
        self.pushButton.setMinimumSize(QSize(160, 40))
        self.pushButton.setMaximumSize(QSize(16777215, 90))
        self.pushButton.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.details)
        self.pushButton_2.setObjectName(u"pushButton_2")
        sizePolicy3.setHeightForWidth(self.pushButton_2.sizePolicy().hasHeightForWidth())
        self.pushButton_2.setSizePolicy(sizePolicy3)
        self.pushButton_2.setMinimumSize(QSize(160, 40))
        self.pushButton_2.setMaximumSize(QSize(16777215, 90))
        self.pushButton_2.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton_2.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton_2)

        self.pushButton_3 = QPushButton(self.details)
        self.pushButton_3.setObjectName(u"pushButton_3")
        sizePolicy3.setHeightForWidth(self.pushButton_3.sizePolicy().hasHeightForWidth())
        self.pushButton_3.setSizePolicy(sizePolicy3)
        self.pushButton_3.setMinimumSize(QSize(160, 40))
        self.pushButton_3.setMaximumSize(QSize(16777215, 90))
        self.pushButton_3.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton_3.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton_3)

        self.pushButton_4 = QPushButton(self.details)
        self.pushButton_4.setObjectName(u"pushButton_4")
        sizePolicy3.setHeightForWidth(self.pushButton_4.sizePolicy().hasHeightForWidth())
        self.pushButton_4.setSizePolicy(sizePolicy3)
        self.pushButton_4.setMinimumSize(QSize(160, 40))
        self.pushButton_4.setMaximumSize(QSize(16777215, 90))
        self.pushButton_4.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton_4.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton_4)

        self.pushButton_5 = QPushButton(self.details)
        self.pushButton_5.setObjectName(u"pushButton_5")
        sizePolicy3.setHeightForWidth(self.pushButton_5.sizePolicy().hasHeightForWidth())
        self.pushButton_5.setSizePolicy(sizePolicy3)
        self.pushButton_5.setMinimumSize(QSize(160, 40))
        self.pushButton_5.setMaximumSize(QSize(16777215, 90))
        self.pushButton_5.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton_5.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton_5)

        self.pushButton_6 = QPushButton(self.details)
        self.pushButton_6.setObjectName(u"pushButton_6")
        sizePolicy3.setHeightForWidth(self.pushButton_6.sizePolicy().hasHeightForWidth())
        self.pushButton_6.setSizePolicy(sizePolicy3)
        self.pushButton_6.setMinimumSize(QSize(160, 40))
        self.pushButton_6.setMaximumSize(QSize(16777215, 90))
        self.pushButton_6.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.pushButton_6.setStyleSheet(button_style)

        self.verticalLayout_2.addWidget(self.pushButton_6)

        # Spacer between buttons and help text
        self.verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.verticalLayout_2.addItem(self.verticalSpacer)

        # Controls label
        self.controls_label = QLabel(self.details)
        self.controls_label.setObjectName(u"controls_label")
        self.controls_label.setStyleSheet(u"""
            QLabel {
                font: 10pt "Segoe UI";
                color: #333333;
                padding: 5px;
            }
        """)
        self.controls_label.setWordWrap(True)
        self.controls_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.verticalLayout_2.addWidget(self.controls_label)

        # Spacer at bottom to push everything up
        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.horizontalLayout_2.addWidget(self.details, 0, Qt.AlignmentFlag.AlignTop)

        self.horizontalLayout_2.setStretch(0, 3)

        self.verticalLayout.addWidget(self.mainpanel)

        self.horizontalLayout.addWidget(self.rightpanel)

        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"Load Calibration Grid", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"Invert Grid", None))
        self.pushButton_3.setText(QCoreApplication.translate("Form", u"Overlay Square Grid", None))
        self.pushButton_4.setText(QCoreApplication.translate("Form", u"Snap to Beads", None))
        self.pushButton_5.setText(QCoreApplication.translate("Form", u"Correct Distortion", None))
        self.pushButton_6.setText(QCoreApplication.translate("Form", u"Save Calibration", None))
        
        # Controls and workflow help text
        self.controls_label.setText(QCoreApplication.translate("Form", u"""<b>Controls</b><br>
• Scroll: Scale grid<br>
• Left-drag center: Move<br>
• Left-drag edge: Rotate<br>
• Right-drag: Tilt (shifts blue)<br>
• Ctrl+S: Save<br><br>
<b>Workflow</b><br>
1. Load image, overlay grid<br>
2. Scale to match RED beads<br>
3. Right-drag to align BLUE<br>
4. Snap → Correct → Save""", None))
    # retranslateUi