# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'calibration_window.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

import base64

from PySide6.QtCore import (QCoreApplication, QMetaObject, QSize, Qt)
from PySide6.QtGui import (QFont)
from PySide6.QtWidgets import (QApplication, QFrame, QGraphicsView, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget)


# ---------------------------------------------------------------------------
# Inline SVG icon: mouse with right button highlighted.
#
# Embedded as a base64 data URI so no external image file is needed.
# The SVG is 12 × 18 px:
#   - rounded rectangle = mouse body
#   - vertical line     = left/right button divider
#   - filled right half = highlighted right button
#   - horizontal line   = top/bottom button boundary
#   - small rect        = scroll wheel (centred, left of divider)
# ---------------------------------------------------------------------------
_MOUSE_RIGHT_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="12" height="18" viewBox="0 0 12 18">
  <!-- Left button (white) -->
  <path d="M0.5,9.5 L0.5,9 Q0.5,4.5 6,4.5 L6,10.5 L0.5,10.5 Z"
        fill="#f0f0f0" stroke="#555" stroke-width="0.8"/>
  <!-- Right button (black) -->
  <path d="M6,4.5 Q11.5,4.5 11.5,9 L11.5,10.5 L6,10.5 Z"
        fill="#333333" stroke="#555" stroke-width="0.8"/>
  <!-- Body outline -->
  <rect x="0.5" y="4.5" width="11" height="13" rx="5.5" ry="5.5"
        fill="none" stroke="#555" stroke-width="1"/>
  <!-- Left / right divider -->
  <line x1="6" y1="4.5" x2="6" y2="10.5" stroke="#555" stroke-width="0.8"/>
  <!-- Button / grip divider (horizontal) -->
  <line x1="0.5" y1="10.5" x2="11.5" y2="10.5" stroke="#555" stroke-width="0.8"/>
  <!-- Scroll wheel (left of divider) -->
  <rect x="3.2" y="6" width="2" height="3.5" rx="1"
        fill="#ccc" stroke="#888" stroke-width="0.6"/>
</svg>
"""

_MOUSE_LEFT_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" width="12" height="18" viewBox="0 0 12 18">
  <!-- Left button (black) -->
  <path d="M0.5,9.5 L0.5,9 Q0.5,4.5 6,4.5 L6,10.5 L0.5,10.5 Z"
        fill="#333333" stroke="#555" stroke-width="0.8"/>
  <!-- Right button (white) -->
  <path d="M6,4.5 Q11.5,4.5 11.5,9 L11.5,10.5 L6,10.5 Z"
        fill="#f0f0f0" stroke="#555" stroke-width="0.8"/>
  <!-- Body outline -->
  <rect x="0.5" y="4.5" width="11" height="13" rx="5.5" ry="5.5"
        fill="none" stroke="#555" stroke-width="1"/>
  <!-- Left / right divider -->
  <line x1="6" y1="4.5" x2="6" y2="10.5" stroke="#555" stroke-width="0.8"/>
  <!-- Button / grip divider (horizontal) -->
  <line x1="0.5" y1="10.5" x2="11.5" y2="10.5" stroke="#555" stroke-width="0.8"/>
  <!-- Scroll wheel (left of divider) -->
  <rect x="3.2" y="6" width="2" height="3.5" rx="1"
        fill="#ccc" stroke="#888" stroke-width="0.6"/>
</svg>
"""

# Encode once at import time; reused in retranslateUi.
_MOUSE_RIGHT_B64 = base64.b64encode(_MOUSE_RIGHT_SVG.strip()).decode("ascii")
_MOUSE_RIGHT_IMG = (
    f'<img src="data:image/svg+xml;base64,{_MOUSE_RIGHT_B64}" '
    f'width="12" height="18" style="vertical-align:middle;"/>'
)
_MOUSE_LEFT_B64 = base64.b64encode(_MOUSE_LEFT_SVG.strip()).decode("ascii")
_MOUSE_LEFT_IMG = (
    f'<img src="data:image/svg+xml;base64,{_MOUSE_LEFT_B64}" '
    f'width="12" height="18" style="vertical-align:middle;"/>'
)

from widgets.sidebar.sidebar import Sidebar
from widgets.titlebar.titlebar import Titlebar


# Shared yellow button style
_BTN_STYLE = (
    "QPushButton {\n"
    "background-color: rgb(255, 215, 0);\n"
    "font: 600 12pt \"Segoe UI\";\n"
    "border-radius: 10px;\n"
    "border: none;\n"
    "}\n"
    "QPushButton:hover {\n"
    "background-color: rgb(255, 230, 50);\n"
    "font-size: 14pt;\n"
    "}\n"
)


class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(862, 550)
        Form.setStyleSheet(u"")

        # ── Outer horizontal layout ────────────────────────────────────────
        self.horizontalLayout = QHBoxLayout(Form)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)

        # ── Sidebar ───────────────────────────────────────────────────────
        self.sidebar = Sidebar(Form)
        self.sidebar.setObjectName(u"sidebar")
        sp_expand = QSizePolicy(QSizePolicy.Policy.Expanding,
                                QSizePolicy.Policy.Expanding)
        sp_expand.setHorizontalStretch(1)
        sp_expand.setVerticalStretch(1)
        sp_expand.setHeightForWidth(self.sidebar.sizePolicy().hasHeightForWidth())
        self.sidebar.setSizePolicy(sp_expand)
        self.horizontalLayout.addWidget(self.sidebar)

        # ── Right panel ───────────────────────────────────────────────────
        self.rightpanel = QWidget(Form)
        self.rightpanel.setObjectName(u"rightpanel")
        sp_right = QSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Expanding)
        sp_right.setHeightForWidth(self.rightpanel.sizePolicy().hasHeightForWidth())
        self.rightpanel.setSizePolicy(sp_right)

        self.verticalLayout = QVBoxLayout(self.rightpanel)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)

        # Title bar
        self.titlebar = Titlebar(self.rightpanel)
        self.titlebar.setObjectName(u"titlebar")
        sp_title = QSizePolicy(QSizePolicy.Policy.Expanding,
                               QSizePolicy.Policy.Fixed)
        sp_title.setHeightForWidth(self.titlebar.sizePolicy().hasHeightForWidth())
        self.titlebar.setSizePolicy(sp_title)
        self.titlebar.setMinimumSize(QSize(0, 70))
        self.verticalLayout.addWidget(self.titlebar)

        # Main panel (image view + details column)
        self.mainpanel = QFrame(self.rightpanel)
        self.mainpanel.setObjectName(u"mainpanel")
        self.mainpanel.setSizePolicy(sp_right)
        self.mainpanel.setFrameShape(QFrame.Shape.StyledPanel)
        self.mainpanel.setFrameShadow(QFrame.Shadow.Raised)

        self.horizontalLayout_2 = QHBoxLayout(self.mainpanel)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        # Image view
        self.VTK_display = QGraphicsView(self.mainpanel)
        self.VTK_display.setObjectName(u"VTK_display")
        self.VTK_display.setEnabled(True)
        self.VTK_display.setFrameShape(QFrame.Shape.Box)
        self.horizontalLayout_2.addWidget(self.VTK_display)

        # ── Details column (buttons + controls hint) ──
        self.details = QWidget(self.mainpanel)
        self.details.setObjectName(u"details")
        self.details.setStyleSheet(u"")

        self.verticalLayout_2 = QVBoxLayout(self.details)
        self.verticalLayout_2.setSpacing(15)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)

        sp_btn = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sp_btn.setHorizontalStretch(0)
        sp_btn.setVerticalStretch(20)

        # ------------------------------------------------------------------
        # pushButton   →  Load Calibration Grid
        # ------------------------------------------------------------------
        self.pushButton = QPushButton(self.details)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setSizePolicy(sp_btn)
        self.pushButton.setMinimumSize(QSize(160, 40))
        self.pushButton.setMaximumSize(QSize(16777215, 90))
        self.pushButton.setStyleSheet(_BTN_STYLE)
        self.verticalLayout_2.addWidget(self.pushButton)

        # ------------------------------------------------------------------
        # pushButton_2  →  Overlay Square Grid
        # ------------------------------------------------------------------
        self.pushButton_2 = QPushButton(self.details)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setSizePolicy(sp_btn)
        self.pushButton_2.setMinimumSize(QSize(160, 40))
        self.pushButton_2.setMaximumSize(QSize(16777215, 90))
        self.pushButton_2.setStyleSheet(_BTN_STYLE)
        self.verticalLayout_2.addWidget(self.pushButton_2)

        # ------------------------------------------------------------------
        # pushButton_3  →  Snap to Beads
        # ------------------------------------------------------------------
        self.pushButton_3 = QPushButton(self.details)
        self.pushButton_3.setObjectName(u"pushButton_3")
        self.pushButton_3.setSizePolicy(sp_btn)
        self.pushButton_3.setMinimumSize(QSize(160, 40))
        self.pushButton_3.setMaximumSize(QSize(16777215, 90))
        self.pushButton_3.setStyleSheet(_BTN_STYLE)
        self.verticalLayout_2.addWidget(
            self.pushButton_3, 0, Qt.AlignmentFlag.AlignVCenter
        )

        # ------------------------------------------------------------------
        # pushButton_4  →  Correct Distortion
        # ------------------------------------------------------------------
        self.pushButton_4 = QPushButton(self.details)
        self.pushButton_4.setObjectName(u"pushButton_4")
        self.pushButton_4.setSizePolicy(sp_btn)
        self.pushButton_4.setMinimumSize(QSize(160, 40))
        self.pushButton_4.setMaximumSize(QSize(16777215, 90))
        self.pushButton_4.setStyleSheet(_BTN_STYLE)
        self.verticalLayout_2.addWidget(
            self.pushButton_4,
            0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # ------------------------------------------------------------------
        # pushButton_5  →  Save Correction
        # ------------------------------------------------------------------
        self.pushButton_5 = QPushButton(self.details)
        self.pushButton_5.setObjectName(u"pushButton_5")
        self.pushButton_5.setSizePolicy(sp_btn)
        self.pushButton_5.setMinimumSize(QSize(160, 40))
        self.pushButton_5.setMaximumSize(QSize(16777215, 90))
        self.pushButton_5.setStyleSheet(_BTN_STYLE)
        self.verticalLayout_2.addWidget(
            self.pushButton_5,
            0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        # ------------------------------------------------------------------
        # Divider line
        # ------------------------------------------------------------------
        self.divider = QFrame(self.details)
        self.divider.setObjectName(u"divider")
        self.divider.setFrameShape(QFrame.Shape.HLine)
        self.divider.setFrameShadow(QFrame.Shadow.Sunken)
        self.divider.setStyleSheet(u"color: #CCCCCC;")
        self.verticalLayout_2.addWidget(self.divider)

        # ------------------------------------------------------------------
        # Controls reference label
        #
        # Mirrors the interactive controls used in Calibrate_Fluoro.m:
        #   partype = 'translation'    ← left-drag near centre
        #   partype = 'in_rotation'   ← left-drag near edge  (Rz)
        #   partype = 'out_rotation'  ← right-drag            (Rx, Ry)
        #   scroll                    ← uniform scale
        # ------------------------------------------------------------------
        self.controls_label = QLabel(self.details)
        self.controls_label.setObjectName(u"controls_label")
        self.controls_label.setWordWrap(True)
        self.controls_label.setAlignment(Qt.AlignmentFlag.AlignLeft
                                         | Qt.AlignmentFlag.AlignTop)
        font = QFont("Segoe UI", 8)
        self.controls_label.setFont(font)
        self.controls_label.setStyleSheet(
            u"color: #555555; padding: 4px 0px;"
        )
        self.verticalLayout_2.addWidget(self.controls_label)

        # Push remaining space down so buttons stay at top
        self.verticalLayout_2.addStretch(1)

        self.horizontalLayout_2.addWidget(
            self.details, 0, Qt.AlignmentFlag.AlignTop
        )
        self.horizontalLayout_2.setStretch(0, 3)

        self.verticalLayout.addWidget(self.mainpanel)
        self.horizontalLayout.addWidget(self.rightpanel)
        self.horizontalLayout.setStretch(0, 1)
        self.horizontalLayout.setStretch(1, 3)

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(
            QCoreApplication.translate("Form", u"Form", None)
        )
        self.pushButton.setText(
            QCoreApplication.translate("Form", u"Load Calibration Grid", None)
        )

        self.pushButton_2.setText(
            QCoreApplication.translate("Form", u"Overlay Square Grid", None)
        )
        self.pushButton_3.setText(
            QCoreApplication.translate("Form", u"Snap to Beads", None)
        )
        self.pushButton_4.setText(
            QCoreApplication.translate("Form", u"Correct Distortion", None)
        )
        self.pushButton_5.setText(
            QCoreApplication.translate("Form", u"Save Correction", None)
        )
        self.controls_label.setText(
            QCoreApplication.translate(
                "Form",
                u"<b>Grid Controls</b><br>"
                u"<table cellspacing='4'>"
                u"<tr><td>🖱 <b>Scroll</b></td>"
                u"    <td>Scale grid (both front and back)</td></tr>"
                u"<tr><td>" + _MOUSE_LEFT_IMG + u"<b> Left-drag</b> (centre)</td>"
                u"    <td>Translate in-plane (Rz)</td></tr>"
                u"<tr><td>" + _MOUSE_LEFT_IMG + u"  ↻ <b>Left-drag</b> (edge)</td>"
                u"    <td>Rotate in-plane (Rz)</td></tr>"
                u"<tr><td>" + _MOUSE_RIGHT_IMG + u" <b> Right-drag</b></td>"
                u"    <td>Tilt in X / Y (Rx, Ry)</td></tr>"
                u"<tr><td> <b>Ctrl + S</b></td>"
                u"    <td>Save correction</td></tr>"
                u"</table>",
                None,
            )
        )
    # retranslateUi