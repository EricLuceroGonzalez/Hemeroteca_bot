import random
import logging

logger = logging.getLogger(__name__)


def create_tweet(tweet_data, twitter_client):
    """
    Crea un tuit de solo texto usando los datos históricos extraídos de MongoDB.

    :param tweet_data: Un diccionario con los datos del JSON (text, source, published).
    :param twitter_client: El cliente autenticado de Tweepy (API v2).
    :return: La respuesta de la API de X o None si falla.
    """

    # Lista de emojis adaptados a temática de hemeroteca y periódicos
    EMOJIS = {
        "opener": ["🗞️", "🕰️", "📜", "🔍", "🇵🇦", "👀", "📌"],
        "fuente": ["📰", "🏛️", "📂", "📅", "📚", "🔖"],
    }

    emoji_opener = random.choice(EMOJIS["opener"])
    emoji_fuente = random.choice(EMOJIS["fuente"])

    # Extraer los datos del diccionario (tu nuevo formato JSON)
    texto_tuit = tweet_data.get("text", "")
    fuente = tweet_data.get("source", "Hemeroteca")
    fecha = tweet_data.get("published", "")

    # Construir el tuit (30% de probabilidad de usar emojis)
    if random.random() < 0.3:
        tweet_text = f"{emoji_opener} {texto_tuit}\n\n{emoji_fuente} {fuente} ({fecha})"
    else:
        tweet_text = f"{texto_tuit}\n\nFuente: {fuente} ({fecha})"

    # Medida de seguridad: evitar pasarse de los 280 caracteres
    if len(tweet_text) > 280:
        # Calculamos cuánto sobra y le restamos 3 por los puntos suspensivos
        corte = 280 - len(f"\n\nFuente: {fuente} ({fecha})") - 3
        texto_tuit = texto_tuit[:corte].strip() + "..."
        tweet_text = f"{texto_tuit}\n\nFuente: {fuente} ({fecha})"

    logging.info(f"Intentando publicar tuit:\n{tweet_text}")

    try:
        # Publicar usando la API v2 de Tweepy
        twitter_client.create_tweet(text=tweet_text)
        logging.info("¡Tuit publicado con éxito!")
        print("¡Tuit publicado con éxito!")
        # return response
    except Exception as e:
        print("¡Tuit no publicado!")
        logging.error(f"Error al publicar el tuit: {e}")
        return None
