import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import datetime
import random
import re

load_dotenv()
token = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Necesario para enviar mensajes
bot = commands.Bot(command_prefix="pande ", intents=intents)

ID_CANAL_DESTINO = 1373779915098296390
ID_CANAL_CONTENIDO = 1373781362183639081

logging.basicConfig(
    level=logging.INFO,                      # Nivel mínimo de log que se mostrará
    format='%(asctime)s - %(levelname)s - %(message)s',  # Formato del mensaje
    filename='mi_log.log',                   # (opcional) archivo donde guardar logs
    filemode='a'                             # 'w' para sobrescribir, 'a' para añadir
)

@bot.event
async def on_ready():
    logging.info("Pandemonica ready")
    enviar_mensaje_diario.start()  # Inicia la tarea periódica

@tasks.loop(hours=24)
async def enviar_mensaje_diario():
    ahora = datetime.datetime.now()
    if ahora.isoweekday() == 4:
        logging.info("recomendacion por tiempo")
        canal = bot.get_channel(ID_CANAL_DESTINO)

        mensaje = "@everyone\n"
        ":rotating_light: **MOMENTO DE ROLEAR** :rotating_light:\n"
        "Las siguientes partidas requieren jugadores:\n"
        partidas = await todas_las_partidas()
        for k in range(0, len(partidas)):
            mensaje = mensaje + "partida: **" + str(extraer_nombre(partidas[k].content)) + "**\nLink: " + str(partidas[k].jump_url) + "\n"
    
        await canal.send(mensaje)

@bot.command(help="te recomiendo una partida")
async def recomenda(ctx):
    logging.info("recomendacion por comando a pedido de " + ctx.author.display_name )
    
    partida = await partida_random()
    if partida:
        await ctx.send("Mira te recomiendo: **"+ str(extraer_nombre(partida.content)) + "**\nAca tenes el link: " + str(partida.jump_url))
    else:
        await ctx.send("No encontré mensajes en este canal.")

@bot.command()
async def listar_partidas(ctx):
    logging.info("listando por comando a pedido de " + ctx.author.display_name )
    partidas = await todas_las_partidas()

    mensaje = ""
    for k in range(0, len(partidas)):
        mensaje = mensaje + "partida: **" + str(extraer_nombre(partidas[k].content)) + "**\nLink: " + str(partidas[k].jump_url) + "\n"
    
    await ctx.send(mensaje)


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
    if random.randint(0,1):
        await ctx.send("si.")
    else:
        await ctx.send("no.")



bot.run(token)