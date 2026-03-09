import os
import json
import requests
import logging
import random
import sys
import time
from datetime import datetime
from babel.dates import format_date

# USAMOS TU MÓDULO DE CONEXIÓN QUE YA TIENE AMBOS MOTORES
from connect_Twitter import connect_to_twitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def post_hemeroteca_hybrid():
    json_path = os.path.join(os.path.dirname(__file__), "data.json")

    with open(json_path, "r", encoding="utf-8") as f:
        tweets = json.load(f)

    # Selección aleatoria estilo Chuchu
    candidatos = [t for t in tweets if t.get("veces_publicado", 0) < 3]
    if not candidatos:
        logger.warning("No hay candidatos.")
        return

    item = random.choice(candidatos)
    idx = tweets.index(item)

    # Obtenemos Client (v2) y API (v1.1) de tu propio módulo
    x_client, x_api = connect_to_twitter()

    try:
        # 1. Preparar Imagen
        img_url = item["image"]
        if not img_url.startswith("http"):
            img_url = os.getenv("CLOUDINARY_BASE_URL") + img_url

        temp_img = "temp_hemeroteca.jpg"
        res = requests.get(img_url, timeout=15)
        with open(temp_img, "wb") as f:
            f.write(res.content)

        # 2. SUBIR MEDIA (v1.1 - Único endpoint v1.1 permitido)
        logger.info(f"Subiendo imagen para item {item.get('id')}...")
        media = x_api.media_upload(filename=temp_img)
        media_id = media.media_id

        # 3. PUBLICAR TEXTO (v2 - Obligatorio para tu nivel de acceso)
        texto = f"📰 {item['text']}\n\n📚 Fuente: {item['source']}"

        max_retries = 5  # Aumentamos intentos ante la inestabilidad de X
        for intento in range(max_retries):
            try:
                logger.info(f"Publicando tuit (v2) - Intento {intento + 1}...")
                x_client.create_tweet(text=texto, media_ids=[media_id])

                # ÉXITO: Actualizar base de datos
                item["veces_publicado"] = item.get("veces_publicado", 0) + 1
                item["isPublished"] = True
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(tweets, f, indent=4, ensure_ascii=False)

                logger.info("✅ Publicación exitosa tras los reintentos.")
                break

            except Exception as e:
                # Si es el error 503 (Servidor ocupado), esperamos mucho más tiempo
                if "503" in str(e) and intento < max_retries - 1:
                    wait = (intento + 1) * 60  # Esperamos 1 min, luego 2 mins...
                    logger.warning(
                        f"⚠️ X sigue saturado (503). Esperando {wait}s para reintentar..."
                    )
                    time.sleep(wait)
                else:
                    raise e

        if os.path.exists(temp_img):
            os.remove(temp_img)

    except Exception as e:
        logger.error(f"💥 Error final en el bot: {e}")


if __name__ == "__main__":
    post_hemeroteca_hybrid()
