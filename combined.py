from PyQt5.QtCore import Qt
import pytesseract
import cv2
import os
import sys
from PIL import Image
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import uic
import glob
import googletrans
import re



language_path = 'C:\\Program Files\\Tesseract-OCR\\tessdata\\'
language_path_list = glob.glob(language_path + "*.traineddata")

language_names_list = []

for path in language_path_list:
    base_name = os.path.basename(path)
    base_name = os.path.splitext(base_name)[0]
    language_names_list.append(base_name)

font_list = []
font = 2

for font in range(110):
    font += 2
    font_list.append(str(font))

class PyShine_OCR_APP(QMainWindow):
    def __init__(self):
        super(PyShine_OCR_APP, self).__init__()
        uic.loadUi('newDesign.ui', self)
        self.image = None
        self.language = 'kan'
        self.font_size = '10'
        self.text = ''

        self.pushButton.clicked.connect(self.open)
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.label_2.setMouseTracking(True)
        self.label_2.installEventFilter(self)
        self.label_2.setAlignment(Qt.AlignTop)

        self.comboBox.addItems(language_names_list)
        self.comboBox.currentIndexChanged['QString'].connect(self.update_now)
        self.comboBox.setCurrentIndex(language_names_list.index(self.language))

        self.comboBox_2.addItems(font_list)
        self.comboBox_2.currentIndexChanged['QString'].connect(self.update_font_size)
        self.comboBox_2.setCurrentIndex(font_list.index(self.font_size))

        self.textEdit.setFontPointSize(int(self.font_size))
        self.setAcceptDrops(True)

        self.t_button = self.findChild(QPushButton, "pushButton_2")
        self.c_button = self.findChild(QPushButton, "pushButton_3")
        self.combo_1 = self.findChild(QComboBox, "comboBox_3")
        self.combo_2 = self.findChild(QComboBox, "comboBox_4")
        self.text_1 = self.findChild(QTextEdit, "textEdit")
        self.text_2 = self.findChild(QTextEdit, "textEdit_2")

        self.languages = googletrans.LANGUAGES
        self.language_list = list(self.languages.values())
        self.combo_1.addItems(self.language_list)
        self.combo_2.addItems(self.language_list)
        self.combo_1.setCurrentText("kannada")
        self.combo_2.setCurrentText("english")

        self.t_button.clicked.connect(self.translate)
        self.c_button.clicked.connect(self.clear)

        self.pushButton_5.clicked.connect(self.summarize_text)

    def update_now(self, value):
        self.language = value
        print('Language Selected as:', self.language)

    def update_font_size(self, value):
        self.font_size = value
        self.textEdit.setFontPointSize(int(self.font_size))
        self.textEdit.setText(str(self.text))

    def open(self):
        filename = QFileDialog.getOpenFileName(self, 'Select File')
        self.image = cv2.imread(str(filename[0]))
        frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_RGB888)
        self.label_2.setPixmap(QPixmap.fromImage(image))

    def image_to_text(self, crop_cvimage):
        gray = cv2.cvtColor(crop_cvimage, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        crop = Image.fromarray(gray)
        text = pytesseract.image_to_string(crop, lang=self.language)
        print('Text:', text)
        return text

    def eventFilter(self, source, event):
        width = 0
        height = 0
        if event.type() == QEvent.MouseButtonPress and source is self.label_2:
            self.org = self.mapFromGlobal(event.globalPos())
            self.left_top = event.pos()
            self.rubberBand.setGeometry(QRect(self.org, QSize()))
            self.rubberBand.show()
        elif event.type() == QEvent.MouseMove and source is self.label_2:
            if self.rubberBand.isVisible():
                self.rubberBand.setGeometry(QRect(self.org, self.mapFromGlobal(event.globalPos())).normalized())
        elif event.type() == QEvent.MouseButtonRelease and source is self.label_2:
            if self.rubberBand.isVisible():
                self.rubberBand.hide()
                rect = self.rubberBand.geometry()
                self.x1 = self.left_top.x()
                self.y1 = self.left_top.y()
                width = rect.width()
                height = rect.height()
                self.x2 = self.x1 + width
                self.y2 = self.y1 + height
            if width >= 50 and height >= 50 and self.image is not None:
                self.crop = self.image[self.y1:self.y2, self.x1:self.x2]
                cv2.imwrite('cropped.png', self.crop)
                new_text = self.image_to_text(self.crop)
                self.text = self.text+'\n'+new_text
                self.textEdit.setText(str(self.text))
            else:
                self.rubberBand.hide()
        else:
            return False
        return QWidget.eventFilter(self, source, event)

    def clear(self):
        self.text = ""
        self.textEdit.setText("")
        self.textEdit_2.setText("")
        self.textEdit_3.setText("")
        self.combo_1.setCurrentText("kannada")
        self.combo_2.setCurrentText("english")

    def translate(self):
        try:
            from_language = self.combo_1.currentText()
            to_language = self.combo_2.currentText()

            translator = googletrans.Translator()
            translated = translator.translate(self.text_1.toPlainText(), src=from_language, dest=to_language)
            self.text_2.setText(translated.text)
            
        except Exception as e:
            QMessageBox.about(self, "Translator Error", str(e))

  
    def summarize_text(self):
        try:
            text_input = self.textEdit_2.toPlainText().strip()

            stopwords = ["and", "the", "is", "in", "at", "which", "on", "for", "with", "as", "I", "this", "that", "it", "to", "of", "a", "an", "or", "by", "from"]

            sentences = [sentence.strip() for sentence in re.findall(r'[^\.!\?]+[\.!\?]+', text_input) or []]
            word_frequencies = {}

            for word in text_input.split():
                lower_word = word.lower()
                if lower_word not in stopwords and len(lower_word) > 1:
                    word_frequencies[lower_word] = word_frequencies.get(lower_word, 0) + 1

            sentence_scores = [sum(word_frequencies.get(word.lower(), 0) for word in sentence.split()) for sentence in sentences]

            ranked_sentences = sorted(zip(sentences, sentence_scores), key=lambda x: x[1], reverse=True)[:3]
            summary = " ".join(sentence for sentence, _ in ranked_sentences)

            self.textEdit_3.setText(summary)

        except Exception as e:
                QMessageBox.about(self, "Summarization Error", str(e))
   

app = QApplication(sys.argv)
mainWindow = PyShine_OCR_APP()
mainWindow.show()
sys.exit(app.exec_())
