# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'startup_windowRcIVfA.ui'
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
    QLabel, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_HomePage(object):
    def setupUi(self, HomePage):
        if not HomePage.objectName():
            HomePage.setObjectName(u"HomePage")
        HomePage.resize(1175, 740)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(HomePage.sizePolicy().hasHeightForWidth())
        HomePage.setSizePolicy(sizePolicy)
        HomePage.setBaseSize(QSize(0, 0))
        font = QFont()
        font.setFamilies([u"Century Gothic"])
        font.setPointSize(16)
        font.setBold(True)
        HomePage.setFont(font)
        self.gridLayout_2 = QGridLayout(HomePage)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.mainLayout = QHBoxLayout()
        self.mainLayout.setObjectName(u"mainLayout")
        self.leftLayout = QGridLayout()
        self.leftLayout.setObjectName(u"leftLayout")
        self.leftFrame = QFrame(HomePage)
        self.leftFrame.setObjectName(u"leftFrame")
        sizePolicy.setHeightForWidth(self.leftFrame.sizePolicy().hasHeightForWidth())
        self.leftFrame.setSizePolicy(sizePolicy)
        font1 = QFont()
        font1.setFamilies([u"Segoe UI"])
        font1.setPointSize(16)
        font1.setBold(False)
        self.leftFrame.setFont(font1)
        self.leftFrame.setStyleSheet(u"background-color: rgb(29, 52, 97);")
        self.leftFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.leftFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_4 = QGridLayout(self.leftFrame)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.lblOrthoVis = QLabel(self.leftFrame)
        self.lblOrthoVis.setObjectName(u"lblOrthoVis")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(1)
        sizePolicy1.setHeightForWidth(self.lblOrthoVis.sizePolicy().hasHeightForWidth())
        self.lblOrthoVis.setSizePolicy(sizePolicy1)
        font2 = QFont()
        font2.setFamilies([u"Segoe UI"])
        font2.setPointSize(56)
        font2.setBold(True)
        font2.setItalic(False)
        self.lblOrthoVis.setFont(font2)
        self.lblOrthoVis.setStyleSheet(u"color: rgb(255, 255, 255);\n"
"font: 700 56pt \"Segoe UI\";")
        self.lblOrthoVis.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.gridLayout_4.addWidget(self.lblOrthoVis, 0, 1, 1, 1)

        self.label = QLabel(self.leftFrame)
        self.label.setObjectName(u"label")
        font3 = QFont()
        self.label.setFont(font3)
        self.label.setPixmap(QPixmap(u"assets/orthovis_logo.png"))

        self.gridLayout_4.addWidget(self.label, 0, 0, 1, 1)


        self.leftLayout.addWidget(self.leftFrame, 0, 0, 1, 1)


        self.mainLayout.addLayout(self.leftLayout)

        self.rightLayout = QVBoxLayout()
        self.rightLayout.setObjectName(u"rightLayout")
        self.rightFrame = QFrame(HomePage)
        self.rightFrame.setObjectName(u"rightFrame")
        sizePolicy.setHeightForWidth(self.rightFrame.sizePolicy().hasHeightForWidth())
        self.rightFrame.setSizePolicy(sizePolicy)
        self.rightFrame.setFont(font1)
        self.rightFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.rightFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.gridLayout_3 = QGridLayout(self.rightFrame)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.lblWelcome = QLabel(self.rightFrame)
        self.lblWelcome.setObjectName(u"lblWelcome")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.lblWelcome.sizePolicy().hasHeightForWidth())
        self.lblWelcome.setSizePolicy(sizePolicy2)
        font4 = QFont()
        font4.setFamilies([u"Segoe UI"])
        font4.setPointSize(14)
        font4.setWeight(QFont.DemiBold)
        font4.setItalic(False)
        self.lblWelcome.setFont(font4)
        self.lblWelcome.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.gridLayout_3.addWidget(self.lblWelcome, 1, 0, 1, 1)

        self.lblIntro = QLabel(self.rightFrame)
        self.lblIntro.setObjectName(u"lblIntro")
        sizePolicy2.setHeightForWidth(self.lblIntro.sizePolicy().hasHeightForWidth())
        self.lblIntro.setSizePolicy(sizePolicy2)
        font5 = QFont()
        font5.setFamilies([u"Segoe UI"])
        font5.setPointSize(12)
        font5.setBold(False)
        font5.setItalic(False)
        self.lblIntro.setFont(font5)
        self.lblIntro.setStyleSheet(u"font: 12pt \"Segoe UI\";")
        self.lblIntro.setWordWrap(True)

        self.gridLayout_3.addWidget(self.lblIntro, 2, 0, 1, 1)

        self.selectionLayout = QVBoxLayout()
        self.selectionLayout.setObjectName(u"selectionLayout")
        self.titles = QHBoxLayout()
        self.titles.setObjectName(u"titles")
        self.newPfoject = QLabel(self.rightFrame)
        self.newPfoject.setObjectName(u"newPfoject")
        self.newPfoject.setFont(font4)
        self.newPfoject.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.titles.addWidget(self.newPfoject)

        self.openProject = QLabel(self.rightFrame)
        self.openProject.setObjectName(u"openProject")
        self.openProject.setFont(font4)
        self.openProject.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.titles.addWidget(self.openProject)


        self.selectionLayout.addLayout(self.titles)

        self.texts = QHBoxLayout()
        self.texts.setObjectName(u"texts")
        self.newProjectText = QLabel(self.rightFrame)
        self.newProjectText.setObjectName(u"newProjectText")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.newProjectText.sizePolicy().hasHeightForWidth())
        self.newProjectText.setSizePolicy(sizePolicy3)
        self.newProjectText.setFont(font5)
        self.newProjectText.setStyleSheet(u"font: 12pt \"Segoe UI\";")
        self.newProjectText.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.newProjectText.setWordWrap(True)

        self.texts.addWidget(self.newProjectText)

        self.createProjectText = QLabel(self.rightFrame)
        self.createProjectText.setObjectName(u"createProjectText")
        sizePolicy3.setHeightForWidth(self.createProjectText.sizePolicy().hasHeightForWidth())
        self.createProjectText.setSizePolicy(sizePolicy3)
        self.createProjectText.setFont(font5)
        self.createProjectText.setStyleSheet(u"font: 12pt \"Segoe UI\";")
        self.createProjectText.setAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.createProjectText.setWordWrap(True)

        self.texts.addWidget(self.createProjectText)


        self.selectionLayout.addLayout(self.texts)

        self.buttonsLayout = QHBoxLayout()
        self.buttonsLayout.setObjectName(u"buttonsLayout")
        self.newProjectFrame = QFrame(self.rightFrame)
        self.newProjectFrame.setObjectName(u"newProjectFrame")
        sizePolicy.setHeightForWidth(self.newProjectFrame.sizePolicy().hasHeightForWidth())
        self.newProjectFrame.setSizePolicy(sizePolicy)
        self.newProjectFrame.setMinimumSize(QSize(0, 30))
        self.newProjectFrame.setFont(font1)
        self.newProjectFrame.setStyleSheet(u"background: transparent;\n"
"border: transparent;")
        self.newProjectFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.newProjectFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.pushButton = QPushButton(self.newProjectFrame)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setGeometry(QRect(0, 0, 120, 30))
        font6 = QFont()
        font6.setFamilies([u"Segoe UI"])
        font6.setPointSize(12)
        font6.setWeight(QFont.DemiBold)
        font6.setItalic(False)
        self.pushButton.setFont(font6)
        self.pushButton.setStyleSheet(u"background-color: rgb(255, 215, 0);\n"
"border-radius: 10px;\n"
"border: none;\n"
"font: 600 12pt \"Segoe UI\";\n"
"")

        self.buttonsLayout.addWidget(self.newProjectFrame)

        self.openProjectFrame = QFrame(self.rightFrame)
        self.openProjectFrame.setObjectName(u"openProjectFrame")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.openProjectFrame.sizePolicy().hasHeightForWidth())
        self.openProjectFrame.setSizePolicy(sizePolicy4)
        self.openProjectFrame.setMinimumSize(QSize(0, 30))
        self.openProjectFrame.setFont(font1)
        self.openProjectFrame.setStyleSheet(u"background: transparent;\n"
"border: transparent")
        self.openProjectFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.openProjectFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.pushButton_2 = QPushButton(self.openProjectFrame)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setGeometry(QRect(0, 0, 130, 30))
        self.pushButton_2.setFont(font6)
        self.pushButton_2.setStyleSheet(u"background-color: rgb(255, 215, 0);\n"
"border-radius: 10px;\n"
"border: none;\n"
"font: 600 12pt \"Segoe UI\";\n"
"")

        self.buttonsLayout.addWidget(self.openProjectFrame)


        self.selectionLayout.addLayout(self.buttonsLayout)

        self.selectionLayout.setStretch(0, 1)
        self.selectionLayout.setStretch(1, 2)
        self.selectionLayout.setStretch(2, 1)

        self.gridLayout_3.addLayout(self.selectionLayout, 3, 0, 1, 1)

        self.recentsFrame = QFrame(self.rightFrame)
        self.recentsFrame.setObjectName(u"recentsFrame")
        self.recentsFrame.setFont(font1)
        self.recentsFrame.setFrameShape(QFrame.Shape.StyledPanel)
        self.recentsFrame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_3 = QVBoxLayout(self.recentsFrame)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.recentsLabel = QLabel(self.recentsFrame)
        self.recentsLabel.setObjectName(u"recentsLabel")
        sizePolicy2.setHeightForWidth(self.recentsLabel.sizePolicy().hasHeightForWidth())
        self.recentsLabel.setSizePolicy(sizePolicy2)
        self.recentsLabel.setFont(font4)
        self.recentsLabel.setStyleSheet(u"font: 600 14pt \"Segoe UI\";")

        self.verticalLayout_3.addWidget(self.recentsLabel)

        self.headers = QFrame(self.recentsFrame)
        self.headers.setObjectName(u"headers")
        sizePolicy2.setHeightForWidth(self.headers.sizePolicy().hasHeightForWidth())
        self.headers.setSizePolicy(sizePolicy2)
        self.headers.setFont(font1)
        self.headers.setStyleSheet(u"background-color: rgb(147, 154, 171);")
        self.headers.setFrameShape(QFrame.Shape.StyledPanel)
        self.headers.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.headers)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.fileNameLabel = QLabel(self.headers)
        self.fileNameLabel.setObjectName(u"fileNameLabel")
        sizePolicy2.setHeightForWidth(self.fileNameLabel.sizePolicy().hasHeightForWidth())
        self.fileNameLabel.setSizePolicy(sizePolicy2)
        self.fileNameLabel.setFont(font5)
        self.fileNameLabel.setStyleSheet(u"color: rgba(0,0,0,128);\n"
"font: 12pt \"Segoe UI\";")

        self.horizontalLayout.addWidget(self.fileNameLabel)

        self.lastAccessLabel = QLabel(self.headers)
        self.lastAccessLabel.setObjectName(u"lastAccessLabel")
        sizePolicy2.setHeightForWidth(self.lastAccessLabel.sizePolicy().hasHeightForWidth())
        self.lastAccessLabel.setSizePolicy(sizePolicy2)
        self.lastAccessLabel.setFont(font5)
        self.lastAccessLabel.setStyleSheet(u"color: rgba(0,0,0,128);\n"
"font: 12pt \"Segoe UI\";")

        self.horizontalLayout.addWidget(self.lastAccessLabel)


        self.verticalLayout_3.addWidget(self.headers)

        self.project1Frame = QFrame(self.recentsFrame)
        self.project1Frame.setObjectName(u"project1Frame")
        self.project1Frame.setFont(font1)
        self.project1Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.project1Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.project1Frame)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.fileName1 = QLabel(self.project1Frame)
        self.fileName1.setObjectName(u"fileName1")
        self.fileName1.setFont(font6)
        self.fileName1.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: 600 12pt \"Segoe UI\";")

        self.horizontalLayout_3.addWidget(self.fileName1)

        self.lastAccess1 = QLabel(self.project1Frame)
        self.lastAccess1.setObjectName(u"lastAccess1")
        font7 = QFont()
        font7.setFamilies([u"Segoe UI"])
        font7.setPointSize(11)
        font7.setBold(False)
        font7.setItalic(True)
        self.lastAccess1.setFont(font7)
        self.lastAccess1.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: italic 11pt \"Segoe UI\";")

        self.horizontalLayout_3.addWidget(self.lastAccess1)


        self.verticalLayout_3.addWidget(self.project1Frame)

        self.project2Frame = QFrame(self.recentsFrame)
        self.project2Frame.setObjectName(u"project2Frame")
        self.project2Frame.setFont(font1)
        self.project2Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.project2Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.project2Frame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.fileName2 = QLabel(self.project2Frame)
        self.fileName2.setObjectName(u"fileName2")
        self.fileName2.setFont(font6)
        self.fileName2.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: 600 12pt \"Segoe UI\";")

        self.horizontalLayout_4.addWidget(self.fileName2)

        self.lastAccess2 = QLabel(self.project2Frame)
        self.lastAccess2.setObjectName(u"lastAccess2")
        self.lastAccess2.setFont(font7)
        self.lastAccess2.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: italic 11pt \"Segoe UI\";")

        self.horizontalLayout_4.addWidget(self.lastAccess2)


        self.verticalLayout_3.addWidget(self.project2Frame)

        self.project3Frame = QFrame(self.recentsFrame)
        self.project3Frame.setObjectName(u"project3Frame")
        self.project3Frame.setFont(font1)
        self.project3Frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.project3Frame.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_5 = QHBoxLayout(self.project3Frame)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.fileName3 = QLabel(self.project3Frame)
        self.fileName3.setObjectName(u"fileName3")
        self.fileName3.setFont(font6)
        self.fileName3.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: 600 12pt \"Segoe UI\";")

        self.horizontalLayout_5.addWidget(self.fileName3)

        self.lastAccess3 = QLabel(self.project3Frame)
        self.lastAccess3.setObjectName(u"lastAccess3")
        self.lastAccess3.setFont(font7)
        self.lastAccess3.setStyleSheet(u"font: 12pt \"Segoe UI\";\n"
"font: italic 11pt \"Segoe UI\";")

        self.horizontalLayout_5.addWidget(self.lastAccess3)


        self.verticalLayout_3.addWidget(self.project3Frame)


        self.gridLayout_3.addWidget(self.recentsFrame, 4, 0, 1, 1)

        self.gridLayout_3.setRowStretch(0, 1)
        self.gridLayout_3.setRowStretch(1, 1)
        self.gridLayout_3.setRowStretch(2, 1)
        self.gridLayout_3.setRowStretch(3, 2)
        self.gridLayout_3.setRowStretch(4, 2)

        self.rightLayout.addWidget(self.rightFrame)


        self.mainLayout.addLayout(self.rightLayout)

        self.mainLayout.setStretch(0, 4)
        self.mainLayout.setStretch(1, 7)

        self.gridLayout.addLayout(self.mainLayout, 0, 0, 1, 1)


        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)


        self.retranslateUi(HomePage)

        QMetaObject.connectSlotsByName(HomePage)
    # setupUi

    def retranslateUi(self, HomePage):
        HomePage.setWindowTitle(QCoreApplication.translate("HomePage", u"MainWindow", None))
        self.lblOrthoVis.setText(QCoreApplication.translate("HomePage", u"OrthoVis", None))
        self.label.setText("")
        self.lblWelcome.setText(QCoreApplication.translate("HomePage", u"Welcome to OrthoVis 2.0!", None))
        self.lblIntro.setText(QCoreApplication.translate("HomePage", u"OrthoVis 2.0 provides fast and accurate 3D joint movement analysis by registering CT and fluoroscopy images, streamlining orthopedic research and clinical assessment.", None))
        self.newPfoject.setText(QCoreApplication.translate("HomePage", u"New Project", None))
        self.openProject.setText(QCoreApplication.translate("HomePage", u"Open Project", None))
        self.newProjectText.setText(QCoreApplication.translate("HomePage", u"Create a new OrthoVis project. You will need valid CT scan and Fluroscopy files for OrthoVis to produce an accurate 3D reconstruction.", None))
        self.createProjectText.setText(QCoreApplication.translate("HomePage", u"Already got a project? Open an OrthoVis project from file system.", None))
        self.pushButton.setText(QCoreApplication.translate("HomePage", u"New Project", None))
        self.pushButton_2.setText(QCoreApplication.translate("HomePage", u"Open Project", None))
        self.recentsLabel.setText(QCoreApplication.translate("HomePage", u"Recents", None))
        self.fileNameLabel.setText(QCoreApplication.translate("HomePage", u"File name", None))
        self.lastAccessLabel.setText(QCoreApplication.translate("HomePage", u"Last opened by you", None))
        self.fileName1.setText(QCoreApplication.translate("HomePage", u"Neil\u2019s Kneeling Project", None))
        self.lastAccess1.setText(QCoreApplication.translate("HomePage", u"1 April 2025", None))
        self.fileName2.setText(QCoreApplication.translate("HomePage", u"Ben\u2019s Bending Knee Project", None))
        self.lastAccess2.setText(QCoreApplication.translate("HomePage", u"1 April 2024", None))
        self.fileName3.setText(QCoreApplication.translate("HomePage", u"Hanna\u2019s Hyper Knee Project", None))
        self.lastAccess3.setText(QCoreApplication.translate("HomePage", u"1 April 2023", None))
    # retranslateUi

