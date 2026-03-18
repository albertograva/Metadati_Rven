
import os
import xml.etree.ElementTree as ET
import zipfile
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QMessageBox
from qgis.core import QgsVectorLayer
from .dialog import MetadatiDialog

NS = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco"
}

class Metadati_RVen:

    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("Metadati RVen", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        dlg = MetadatiDialog()
        dlg.input_folder.setText(QFileDialog.getExistingDirectory(None, "Seleziona cartella"))

        if not dlg.exec_():
            return

        cartella = dlg.input_folder.text()
        ente = dlg.input_ente.text()
        email = dlg.input_email.text()

        plugin_dir = os.path.dirname(__file__)

        if dlg.chk_ods.isChecked() and dlg.input_ods.text():
            ods_path = dlg.input_ods.text()
        else:
            ods_path = os.path.join(plugin_dir, "data", "elenco_layer.ods")

        template_xml = os.path.join(plugin_dir, "template.xml")

        records = self.leggi_ods(ods_path)

        confini_path = None
        for rec in records:
            nome = rec.get("file","")
            if "confini" in nome.lower():
                confini_path = self.trova_file_esatto(cartella, nome)
                break

        bbox_confini = None
        if confini_path:
            layer = QgsVectorLayer(confini_path, "confini", "ogr")
            if layer.isValid():
                ext = layer.extent()
                bbox_confini = (ext.xMinimum(), ext.yMinimum(), ext.xMaximum(), ext.yMaximum())

        generati = 0
        mancanti = []

        for rec in records:
            nome = rec.get("file","")
            if not nome:
                continue

            path = self.trova_file_esatto(cartella, nome)

            if not path:
                print(f"NON TROVATO: {nome}")
                mancanti.append(nome)
                continue

            if os.path.isdir(path):
                output = os.path.join(os.path.dirname(path), os.path.splitext(nome)[0] + ".xml")
                tipo = "folder"
            else:
                output = os.path.splitext(path)[0] + ".xml"
                tipo = "vector" if nome.lower().endswith(".shp") else "pdf"

            print(f"Trovato: {path}")
            print(f"Output: {output}")

            self.genera_xml(template_xml, output, rec, path, tipo, bbox_confini, ente, email)
            generati += 1

        msg = f"Generati: {generati}\nNon trovati: {len(mancanti)}"
        QMessageBox.information(None, "Fine", msg)

    def trova_file_esatto(self, root, nome):
        nome = nome.lower()
        for r, d, files in os.walk(root):
            for f in files:
                if f.lower() == nome:
                    return os.path.join(r, f)
            for dir in d:
                if dir.lower() == nome:
                    return os.path.join(r, dir)
        return None

    def genera_xml(self, template, output, rec, path, tipo, bbox_confini, ente, email):

        tree = ET.parse(template)
        root = tree.getroot()

        root.find(".//gmd:title//gco:CharacterString", NS).text = rec.get("titolo","")
        root.find(".//gmd:abstract//gco:CharacterString", NS).text = rec.get("abstract","")

        root.find(".//gmd:organisationName//gco:CharacterString", NS).text = ente
        root.find(".//gmd:electronicMailAddress//gco:CharacterString", NS).text = email

        if tipo == "vector":
            layer = QgsVectorLayer(path, "layer", "ogr")
            ext = layer.extent()
            xmin, ymin, xmax, ymax = ext.xMinimum(), ext.yMinimum(), ext.xMaximum(), ext.yMaximum()
        elif bbox_confini:
            xmin, ymin, xmax, ymax = bbox_confini
        else:
            xmin, ymin, xmax, ymax = 0,0,0,0

        root.find(".//gmd:westBoundLongitude//gco:Decimal", NS).text = str(xmin)
        root.find(".//gmd:eastBoundLongitude//gco:Decimal", NS).text = str(xmax)
        root.find(".//gmd:southBoundLatitude//gco:Decimal", NS).text = str(ymin)
        root.find(".//gmd:northBoundLatitude//gco:Decimal", NS).text = str(ymax)

        tree.write(output, encoding="utf-8", xml_declaration=True)

    def leggi_ods(self, path):
        with zipfile.ZipFile(path) as z:
            xml_content = z.read("content.xml")

        root = ET.fromstring(xml_content)

        ns = {'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
              'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'}

        rows = root.findall(".//table:table-row", ns)

        data = []
        headers = []

        for i, row in enumerate(rows):
            cells = row.findall("table:table-cell", ns)
            values = []
            for cell in cells:
                texts = cell.findall(".//text:p", ns)
                text = "".join([t.text or "" for t in texts])
                values.append(text)

            if i == 0:
                headers = values
            else:
                data.append(dict(zip(headers, values)))

        return data
