import streamlit as st
from lxml import etree
import copy
import tempfile
import os
from io import BytesIO
import zipfile

def regrouper_par_lots(liste, taille):
    return [liste[i:i+taille] for i in range(0, len(liste), taille)]

def fusionner_batch(batch_fichiers):
    base_tree = etree.parse(batch_fichiers[0])
    base_root = base_tree.getroot()
    export_attrs = dict(base_root.attrib)

    nouvelle_racine = etree.Element("STEP-ProductInformation", **export_attrs)
    bloc_products = etree.SubElement(nouvelle_racine, "Products")

    for fichier in batch_fichiers:
        tree = etree.parse(fichier)
        racine = tree.getroot()
        for products_tag in racine.findall(".//Products"):
            for produit in products_tag.findall("Product"):
                bloc_products.append(copy.deepcopy(produit))

    buffer = BytesIO()
    etree.ElementTree(nouvelle_racine).write(
        buffer,
        pretty_print=True,
        encoding="ISO-8859-15",
        xml_declaration=True
    )
    buffer.seek(0)
    return buffer

# Streamlit UI
st.set_page_config(page_title="Fusion STEPXML UGAP", layout="wide")
st.title("🔗 Fusionneur STEPXML (par lots de 6 fichiers)")

uploaded_files = st.file_uploader(
    "📤 Fichiers XML", 
    type="xml", 
    accept_multiple_files=True
)

if uploaded_files:
    fichiers_temp = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for file in uploaded_files:
            temp_path = os.path.join(tmpdir, file.name)
            with open(temp_path, "wb") as f:
                f.write(file.read())
            fichiers_temp.append(temp_path)

        fichiers_temp.sort()
        lots = regrouper_par_lots(fichiers_temp, 6)

        fichiers_fusionnes = []

        st.subheader("📁 Fichiers fusionnés disponibles :")
        for i, batch in enumerate(lots, start=1):
            buffer = fusionner_batch(batch)
            nom_fichier = f"fusion_batch_{i:03d}.xml"
            fichiers_fusionnes.append((nom_fichier, buffer.getvalue()))

            st.download_button(
                label=f"📥 Télécharger {nom_fichier}",
                data=buffer,
                file_name=nom_fichier,
                mime="application/xml"
            )

        if fichiers_fusionnes:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                for nom_fichier, contenu in fichiers_fusionnes:
                    zipf.writestr(nom_fichier, contenu)
            zip_buffer.seek(0)

            st.subheader("📦 Tout télécharger")
            st.download_button(
                label="📥 Télécharger tous les fichiers fusionnés (.zip)",
                data=zip_buffer,
                file_name="fusion_stepxml.zip",
                mime="application/zip"
            )
