from PySide6.QtCore import QObject, Signal

## The bridge that connects the stdout to GUI for displaying progress
class StdoutEmitter(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text.strip():
            self.text_written.emit(text)

    def flush(self):
        pass
