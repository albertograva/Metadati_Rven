
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog

class MetadatiDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Parametri Metadati")
        self.setMinimumWidth(420)

        layout = QVBoxLayout()

        self.input_folder = QLineEdit()
        self.input_ente = QLineEdit()
        self.input_email = QLineEdit()

        layout.addWidget(QLabel("Cartella root"))
        layout.addWidget(self.input_folder)

        layout.addWidget(QLabel("Ente / Responsabile"))
        layout.addWidget(self.input_ente)

        layout.addWidget(QLabel("Email"))
        layout.addWidget(self.input_email)

        self.chk_ods = QCheckBox("Usa ODS personalizzato")
        self.input_ods = QLineEdit()
        self.input_ods.setEnabled(False)

        self.btn_ods = QPushButton("Sfoglia ODS")
        self.btn_ods.setEnabled(False)

        layout.addWidget(self.chk_ods)
        layout.addWidget(self.input_ods)
        layout.addWidget(self.btn_ods)

        self.chk_ods.stateChanged.connect(self.toggle_ods)
        self.btn_ods.clicked.connect(self.seleziona_ods)

        self.btn_run = QPushButton("Genera")
        layout.addWidget(self.btn_run)
        self.btn_run.clicked.connect(self.accept)

        self.setLayout(layout)

    def toggle_ods(self):
        attivo = self.chk_ods.isChecked()
        self.input_ods.setEnabled(attivo)
        self.btn_ods.setEnabled(attivo)

    def seleziona_ods(self):
        file, _ = QFileDialog.getOpenFileName(self, "Seleziona ODS", "", "ODS (*.ods)")
        if file:
            self.input_ods.setText(file)
