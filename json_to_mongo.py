import json
import os
from connect_mongo import get_mongo_collection

collection = get_mongo_collection()
file = os.path.join(os.path.dirname(__file__), "data_mongo.json")

import re


def limpiar_texto(texto):
    """
    Elimina las etiquetas de citación o fuentes de un texto y ajusta los espacios.
    """
    if not texto:
        return texto

    # Patrón para atrapar [cite: 1, 2] o
    patron = r"\[(?:cite|source):[^\]]+\]"

    # Sustituir la etiqueta por nada y quitar espacios a los extremos
    texto_limpio = re.sub(patron, "", texto).strip()

    # Reemplazar los dobles espacios accidentales (que quedan al borrar la etiqueta) por un solo espacio
    texto_limpio = re.sub(r"\s+", " ", texto_limpio)

    return texto_limpio


import json
import re
import os

file = os.path.join(os.path.dirname(__file__), "data_mongo.json")


def limpiar_json_local():
    """
    Lee el archivo JSON local, limpia el campo 'text' eliminando
    las etiquetas o, y sobrescribe el archivo.
    """
    # 1. Leer los datos actuales del JSON
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"No se encontró el archivo: {file}")
        return

    # Patrón para atrapar o
    patron = r"\[(?:cite|source):[^\]]+\]"
    cambios = 0

    # 2. Modificar el texto si es una lista de diccionarios
    if isinstance(data, list):
        for item in data:
            texto_original = item.get("text", "")

            if texto_original:
                # Quitar etiqueta y espacios en blanco extra
                texto_limpio = re.sub(patron, "", texto_original).strip()
                texto_limpio = re.sub(
                    r"\s+", " ", texto_limpio
                )  # Reemplaza dobles espacios accidentales

                # Solo actualizamos si realmente hubo un cambio
                if texto_original != texto_limpio:
                    item["text"] = texto_limpio
                    cambios += 1
    else:
        print("El archivo JSON no tiene el formato de lista esperado.")
        return

    # 3. Sobrescribir el archivo original si se hicieron cambios
    if cambios > 0:
        with open(file, "w", encoding="utf-8") as f:
            # indent=4 lo guarda bonito y legible, ensure_ascii=False respeta los acentos
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(
            f"¡Listo! Se limpiaron y actualizaron {cambios} tuits en el archivo JSON."
        )
    else:
        print("El archivo ya estaba limpio. No se hicieron cambios.")


def insert_json_to_mongo():
    """Insert JSON data into MongoDB collection.
    This function reads a JSON file and inserts its contents into a MongoDB collection.
    If the data is a list of documents, it checks for duplicates based on the "texto" field
    before inserting each document. If the data is not a list, it prints an error message.
    """
    # Load JSON file
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If data is a list of documents:
    if isinstance(data, list):
        # Optionally, avoid duplicates (e.g., by "text")
        for item in data:
            texto_original = item.get("text")
            item["text"] = limpiar_texto(texto_original)
            if not collection.find_one({"text": item.get("text")}):
                collection.insert_one(item)
                print(f"Inserted: {item.get('texto')}")
            else:
                print(f"Already exists: {item.get('text')}")
    else:
        print("JSON file does not contain a list of documents.")


def update_text_by_id():
    """To take the json and compare with "texto" in mongo,
    and update if there is a difference
    """
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated = 0
    for item in data:
        doc_id = item.get("id")
        new_text = item.get("text")
        if doc_id is not None and new_text is not None:
            mongo_doc = collection.find_one({"id": doc_id})
            if mongo_doc and mongo_doc.get("text") != new_text:
                result = collection.update_one(
                    {"id": doc_id}, {"$set": {"text": new_text}}
                )
                if result.modified_count:
                    print(f"Updated id {doc_id}")
                    updated += 1
    print(f"Total updated: {updated}")


# update_text_by_id()
# limpiar_json_local()
# insert_json_to_mongo()
