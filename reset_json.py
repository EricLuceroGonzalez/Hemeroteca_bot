# reset_json.py
import json
import os


def reset_database():
    json_path = os.path.join(os.path.dirname(__file__), "data.json")

    if not os.path.exists(json_path):
        print("❌ No se encontró el archivo data.json")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    for tweet in tweets:
        # Resetear el estado de publicación
        tweet["isPublished"] = False
        # Agregar el contador si no existe, o resetearlo a 0
        tweet["veces_publicado"] = 0

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tweets, f, indent=4, ensure_ascii=False)

    print(f"✅ Se han reseteado {len(tweets)} entradas. ¡Listo para volver a empezar!")


if __name__ == "__main__":
    reset_database()
