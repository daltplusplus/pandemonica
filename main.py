import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import random
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

argentina_tz = pytz.timezone("America/Argentina/Buenos_Aires")

load_dotenv()
token = os.getenv('TOKEN')
log_dir = os.getenv('LOG_DIR')

intents = discord.Intents.default()
intents.message_content = True  # Necesario para enviar mensajes
bot = commands.Bot(command_prefix="pande ", intents=intents)
scheduler = AsyncIOScheduler()

ID_CANAL_DESTINO = 1373779915098296390
ID_CANAL_CONTENIDO = 1373781362183639081
ID_CANAL_TEST = 842495175766573057


logging.basicConfig(
    level=logging.INFO,                      # Nivel mínimo de log que se mostrará
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del mensaje
    filename=log_dir,                   # (opcional) archivo donde guardar logs
    filemode='w'                             # 'w' para sobrescribir, 'a' para añadir
)

@bot.event
async def on_ready():
    logging.info("Pandemonica ready")
    scheduler.start()

    scheduler.add_job(
        aviso_antiguedad,
        CronTrigger(day=1, hour=19, minute=30, timezone=argentina_tz),
        name="Aviso de partidas viejas"
    )
    scheduler.add_job(
        enviar_recordatorio_programado,
        CronTrigger(day_of_week="fri", hour=16, minute=40, timezone=argentina_tz),
        name="Recomendacion de partidas"
    )
    aviso_poco_trafico.start()

@tasks.loop(minutes=10)
async def aviso_poco_trafico():
    canal = bot.get_channel(ID_CANAL_DESTINO)
    ahora = datetime.now(timezone.utc)
    mensaje = await ultimo_mensaje(canal)
    
    dif = ahora.replace(tzinfo=None) - mensaje.created_at.replace(tzinfo=None)
    logging.info("checkendo tiempo ultimo mensaje")
    if dif.total_seconds() > 13 * 3600:
        logging.info("tiempo ultimo mensaje " + str(mensaje.created_at))
        logging.info("aviso poco trafico")
        poemas = leer_poemas("poemas.txt")
        await canal.send(random.choice(poemas))



async def enviar_recordatorio_programado():
    logging.info("recomendacion por tiempo")
    canal = bot.get_channel(ID_CANAL_DESTINO)

    mensaje = "@everyone\n" 
    mensaje += ":rotating_light: **ANUNCIOS DE PARTIDAS** :rotating_light:\n"
    mensaje += "**aprovecho esta oportunidad para recordarles que las siguientes partidas requieren jugadores:**\n"
    partidas = await todas_las_partidas()
    for k in range(0, len(partidas)):
        mensaje += "partida: **" + str(extraer_nombre(partidas[k].content)) + "**\nLink: " + str(partidas[k].jump_url) + "\n"

    await canal.send(mensaje)

async def aviso_antiguedad():
    logging.info("aviso antiguedad")
    ahora = datetime.datetime.now()
    atleastone = False
    canal = bot.get_channel(ID_CANAL_DESTINO)
    partidas = await todas_las_partidas()

    mensaje = "Los siguiente anuncios tienen mas de un mes de antiguedad :book:\n"
    for k in range(0, len(partidas)):
        dif = ahora.replace(tzinfo=None) - partidas[k].created_at.replace(tzinfo=None)
        if dif.days > 31:
            atleastone = True
            mensaje += "**" + str(extraer_nombre(partidas[k].content)) + "** de @" + str(partidas[k].author) + "\n"

    mensaje += "revisarlos por favor :coffee:"
    if atleastone:
        await canal.send(mensaje)

@bot.command(help="te recomiendo una partida")
async def recomenda(ctx):
    logging.info("recomendacion por comando a pedido de " + ctx.author.display_name )
    
    partida = await partida_random()
    if partida:
        await ctx.reply("Mira te recomiendo: **"+ str(extraer_nombre(partida.content)) + "**\nAca tenes el link: " + str(partida.jump_url))
    else:
        await ctx.reply("No encontré mensajes en este canal.")

@bot.command(help="listo todas las partidas existentes")
async def listar_partidas(ctx):
    logging.info("listando por comando a pedido de " + ctx.author.display_name )
    partidas = await todas_las_partidas()

    mensaje = ""
    for k in range(0, len(partidas)):
        mensaje = mensaje + "partida: **" + str(extraer_nombre(partidas[k].content)) + "**\nLink: " + str(partidas[k].jump_url) + "\n"
    
    await ctx.reply(mensaje)


async def todas_las_partidas():
    canal = bot.get_channel(ID_CANAL_CONTENIDO)
    mensajes = [mensaje async for mensaje in canal.history(limit=None)]
    filtrados = []
    for k in range(0, len(mensajes)):
        string = ""
        string = mensajes[k].content
        string = string.casefold()
        if string.count("partida:") or string.count("partida]:"):
            filtrados.append(mensajes[k])

    return filtrados

async def partida_random():
    filtrados = await todas_las_partidas()

    rn = random.randint(0, len(filtrados)-1)
    return filtrados[rn]

def extraer_nombre(texto):
    patron = r'(?:partida:?]?\:*\**)\s*(.*)'
    lineas = texto.split('\n')
    resultados = []

    for linea in lineas:
        match = re.search(patron, linea, re.IGNORECASE)
        if match:
            resultados.append(match.group(1).strip())

    return resultados[0]

@bot.command()
async def siono(ctx):
    logging.info("si o no a pedido de " + ctx.author.display_name )
    if random.randint(0,1):
        await ctx.reply("si.")
    else:
        await ctx.reply("no.")


async def ultimo_mensaje(canal):
    mensajes = [mensaje async for mensaje in canal.history(limit=1)]
    return mensajes[0]

def leer_poemas(nombre_archivo):
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    poemas = contenido.strip().split('\n\n')
    return poemas


bot.run(token)
