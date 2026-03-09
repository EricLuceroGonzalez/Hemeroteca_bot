import tweepy
import os
import json
import requests
import logging
import random
import sys
from datetime import datetime
from dotenv import load_dotenv
from babel.dates import format_date

# --- CONFIGURACIÓN DE LOGS ---
log_path = os.path.join(os.path.dirname(__file__), "hemeroteca_bot.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),  # Ver en terminal (útil para GitHub Actions)
    ],
)
logger = logging.getLogger(__name__)

load_dotenv()


# --- UTILIDADES ---
def get_credential(name):
    val = os.getenv(name)
    if not val:
        raise ValueError(f"Falta la variable de entorno: {name}")
    return val


EMOJIS = {
    "opener": ["📰", "📜", "🎞️", "🗞️", "🔍", "📸", "🏛️"],
    "items": ["✨", "🔹", "🎯", "🔖", "📌"],
    "publicado": ["📅", "🗓️", "🕰️"],
    "fuente": ["📚", "🏷️", "🗃️", "🌴"],
}


def generar_texto_tweet(tweet_data):
    """Construye el cuerpo del mensaje con emojis aleatorios."""
    try:
        pub_date = datetime.strptime(tweet_data["published"], "%Y-%m-%d")
        f_date = format_date(pub_date, "d 'de' MMMM 'de' yyyy", locale="es")
    except:
        f_date = "fecha desconocida"

    opener = random.choice(EMOJIS["opener"])
    item_m = random.choice(EMOJIS["items"])
    fuente_m = random.choice(EMOJIS["fuente"])
    reloj = random.choice(EMOJIS["publicado"])

    texto = (
        f"{opener} {tweet_data.get('text', 'Archivo de hemeroteca.')}\n\n"
        f"{reloj} Publicado el {f_date}\n"
        f"{fuente_m} Fuente: {tweet_data.get('source', 'Biblioteca Nacional')}"
    )

    # Hashtags aleatorios
    tags = ["#PanamáAntiguo", "#Historia", "#Hemeroteca", "#Archivo"]
    if random.random() > 0.5:
        texto += f"\n\n{random.choice(tags)}"

    return texto


# --- LÓGICA PRINCIPAL ---
def post_from_hemeroteca():
    json_path = os.path.join(os.path.dirname(__file__), "data.json")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            tweets = json.load(f)
    except Exception as e:
        logger.error(f"Error cargando JSON: {e}")
        return

    now = datetime.now()
    tweet_a_publicar = None

    # BUSCAR CANDIDATO:
    # 1. Que su fecha programada ya haya pasado o sea hoy
    # 2. Que tenga el menor número de publicaciones posibles
    # 3. Ordenados por fecha para no saltarnos el orden cronológico

    candidatos = [
        t for t in tweets if datetime.strptime(t["date"], "%Y-%m-%dT%H:%M:%S") <= now
    ]

    # Ordenamos por veces_publicado (asc) y luego por fecha (asc)
    candidatos.sort(key=lambda x: (x.get("veces_publicado", 0), x["date"]))

    if not candidatos:
        logger.info("💤 No hay contenido programado para hoy o fechas anteriores.")
        return

    tweet_a_publicar = candidatos[0]
    idx_en_lista = tweets.index(tweet_a_publicar)

    try:
        # 1. Conexiones
        logger.info(f"Intentando publicar item ID: {tweet_a_publicar.get('id', 'N/A')}")

        # Twitter V1.1 (para media) y V2 (para tweet)
        auth = tweepy.OAuthHandler(
            get_credential("X_API_KEY"), get_credential("X_API_KEY_SECRET")
        )
        auth.set_access_token(
            get_credential("X_ACCESS_TOKEN"), get_credential("X_ACCESS_TOKEN_SECRET")
        )
        api_v1 = tweepy.API(auth)

        client_v2 = tweepy.Client(
            bearer_token=get_credential("X_BEARER_TOKEN"),
            consumer_key=get_credential("X_API_KEY"),
            consumer_secret=get_credential("X_API_KEY_SECRET"),
            access_token=get_credential("X_ACCESS_TOKEN"),
            access_token_secret=get_credential("X_ACCESS_TOKEN_SECRET"),
        )

        # 2. Manejo de Imagen
        img_url = tweet_a_publicar["image"]
        # Si la URL no es completa, le pegamos la base de Cloudinary
        if not img_url.startswith("http"):
            img_url = os.getenv("CLOUDINARY_BASE_URL") + img_url

        temp_img = os.path.join(os.path.dirname(__file__), "temp_item.jpg")
        res = requests.get(img_url, timeout=15)
        res.raise_for_status()

        with open(temp_img, "wb") as f:
            f.write(res.content)

        # 3. Subida y Publicación
        media = api_v1.media_upload(temp_img)
        texto_final = generar_texto_tweet(tweet_a_publicar)

        client_v2.create_tweet(text=texto_final, media_ids=[media.media_id])

        # 4. Actualizar Datos
        tweets[idx_en_lista]["isPublished"] = True
        tweets[idx_en_lista]["veces_publicado"] = (
            tweets[idx_en_lista].get("veces_publicado", 0) + 1
        )

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(tweets, f, indent=4, ensure_ascii=False)

        logger.info(
            f"✅ ÉXITO: Publicado intento #{tweets[idx_en_lista]['veces_publicado']}"
        )

        if os.path.exists(temp_img):
            os.remove(temp_img)

    except Exception as e:
        logger.error(f"💥 Fallo crítico: {e}", exc_info=True)


if __name__ == "__main__":
    logger.info("--- INICIANDO PROCESO HEMEROTECA ---")
    post_from_hemeroteca()
    logger.info("--- PROCESO FINALIZADO ---")
