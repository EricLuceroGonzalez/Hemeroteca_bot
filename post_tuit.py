from connect_mongo import get_mongo_collection
from connect_Twitter import connect_to_twitter
from create_tweet import create_tweet
import logging
import os
import tweepy
import sys
from datetime import datetime

log_file = os.path.join(os.path.dirname(__file__), "hemeroteca_bot.log")
# file_path = os.path.join(os.path.dirname(__file__), "data.json")
logging.basicConfig(
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)
today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
logger.info(f"***** ***** ***** {today} ***** ***** *****")


def get_one_document(collection, x_client, x_api):
    logger.info("Iniciando búsqueda de tuit...")
    intentos = 0
    max_intentos = 2

    while intentos < max_intentos:
        try:
            pipeline = [
                {"$match": {"veces_publicado": {"$lt": 3}}},
                {"$sample": {"size": 1}},
            ]
            random_item = list(collection.aggregate(pipeline))

            if not random_item:
                logger.warning(
                    "Consulta a MongoDB vacía. Revisa si quedan documentos con veces_publicado < 3."
                )
                return None

            item = random_item[0]
            logger.info(
                f"Candidato hallado: ID {item.get('id', item.get('_id'))} | Intentos: {intentos + 1}"
            )

            # Dejamos que create_tweet se encargue de la longitud y el formato
            respuesta_twitter = create_tweet(item, x_client)

            # Verificamos si la publicación fue realmente exitosa
            if respuesta_twitter is not None:
                logger.info(
                    f"✅ Tuit publicado en X con éxito. Actualizando MongoDB..."
                )
                # Actualización en db
                collection.update_one(
                    {"_id": item["_id"]},
                    {"$set": {"isPublished": True}, "$inc": {"veces_publicado": 1}},
                )
                return item
            else:
                logger.warning(
                    "❌ El tuit no se pudo publicar en X. Probando con otro..."
                )

        except Exception as e:
            logger.error(f"Error crítico en el ciclo de búsqueda: {e}")
            break

        intentos += 1

    logger.error("Se alcanzó el límite máximo de intentos sin éxito.")
    return None


if __name__ == "__main__":
    print("🚀 Arrancando prueba aislada...")

    # Solo nos conectamos a Twitter
    x_client, x_api = connect_to_twitter()

    if x_client is not None:
        try:
            print("🐦 Intentando mandar un tuit de prueba...")

            # Texto súper simple y único para burlar cualquier filtro
            import random

            numero_random = random.randint(1000, 9999)
            texto_prueba = f"Hola, esta es una prueba de conexión desde mi nueva App. Código: {numero_random}"

            print(f"🥶 El tuit: {texto_prueba}")
            x_client.create_tweet(text=texto_prueba)
            print(f"✅ ¡EXITO! El tuit se publicó: {"respuesta"}")
        except tweepy.errors.TweepyException as e:
            print(f"❌ FALLO LA PRUEBA (Error de Tweepy): {e}")
        except Exception as e:
            print(f"❌ FALLO LA PRUEBA: {e}")
    else:
        print("❌ Error: No se pudo conectar a Twitter.")
# if __name__ == "__main__":
#     try:
#         # Ahora el log se iniciará ANTES de intentar conectar
#         logger.info("--- INICIANDO PROCESO DEL BOT ---")

#         # Conectamos dentro del try para capturar errores en el log
#         collection = get_mongo_collection()
#         x_client, x_api = connect_to_twitter()

#         if collection is not None and x_client is not None:
#             get_one_document(collection, x_client, x_api)
#         else:
#             logger.error("No se pudo establecer conexión con los servicios.")

#     except Exception as e:
#         # Esto guardará cualquier error de conexión en el log
#         logger.critical(f"--- EL BOT NO PUDO ARRANCAR: {e}", exc_info=True)
#     finally:
#         logger.info("--- FIN DE LA EJECUCIÓN ---")
