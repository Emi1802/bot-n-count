import os
import discord
import json
from flask import Flask
from threading import Thread

# --- NUEVA PARTE: SERVIDOR WEB ---
# Esto es solo para mantener el bot despierto en Render
app = Flask('')

@app.route('/')
def home():
    # Esta página web solo dirá "Estoy vivo!"
    return "Estoy vivo!"

def run_web_server():
    # Ejecuta el servidor web en el puerto 8080
    app.run(host='0.0.0.0', port=8080)

def start_web_server_thread():
    # Inicia el servidor web en un hilo (proceso) separado
    t = Thread(target=run_web_server)
    t.start()
# --- FIN DE LA NUEVA PARTE ---


# --- Configuración del Bot ---
CANAL_ID_REPORTE = 1434272560773599302  # <--- REEMPLAZA ESTE NÚMERO
PALABRAS_A_RASTREAR = ["nigger", "nigga"] # <--- PON TUS PALABRAS AQUÍ
# --- AJUSTE IMPORTANTE ---
# Guardaremos el archivo en una subcarpeta llamada 'data'
ARCHIVO_CONTEO = "data/conteo_usuarios.json"

# --- Cargar/Guardar Conteos ---
def cargar_conteo():
    try:
        # Apuntamos a la nueva ruta del archivo
        with open(ARCHIVO_CONTEO, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def guardar_conteo(conteo):
    # --- AJUSTE IMPORTANTE ---
    # Asegurarnos de que la carpeta 'data' exista antes de guardar
    os.makedirs('data', exist_ok=True) 
    with open(ARCHIVO_CONTEO, 'w') as f:
        json.dump(conteo, f, indent=4)

# --- Lógica del Bot (Tu código de antes) ---
user_counts = cargar_conteo()
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'¡Bot conectado como {client.user}!')
    canal = client.get_channel(CANAL_ID_REPORTE)
    if canal:
        print(f'Reportando infracciones en el canal: #{canal.name}')
    else:
        print(f'¡ERROR! No se pudo encontrar el canal con ID: {CANAL_ID_REPORTE}.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    contenido_mensaje = message.content.lower()

    if contenido_mensaje.startswith('!conteo'):
        respuesta = "--- Conteo de Palabras por Usuario ---\n"
        if not user_counts:
            respuesta = "Aún no se ha registrado ninguna palabra."
        else:
            try:
                sorted_users = sorted(user_counts.items(), key=lambda item: item[1]['count'], reverse=True)
                for user_id, data in sorted_users:
                    user_name = data.get('username', f"Usuario (ID: {user_id})")
                    conteo = data.get('count', 0)
                    respuesta += f'**{user_name}**: {conteo} veces\n'
            except Exception as e:
                respuesta = f"Error al procesar conteos: {e}"
        await message.channel.send(respuesta)
        return

    palabra_encontrada = None
    for palabra in PALABRAS_A_RASTREAR:
        if palabra in contenido_mensaje:
            palabra_encontrada = palabra
            break

    if palabra_encontrada:
        user_id = str(message.author.id)
        user_name = str(message.author)
        if user_id not in user_counts:
            user_counts[user_id] = {'username': user_name, 'count': 0}
        user_counts[user_id]['username'] = user_name
        user_counts[user_id]['count'] += 1
        conteo_actual = user_counts[user_id]['count']
        guardar_conteo(user_counts)
        
        canal_reporte = client.get_channel(CANAL_ID_REPORTE)
        if canal_reporte:
            try:
                mensaje_alerta = f"El usuario **{user_name}** ha dicho la N-word. Veces totales: **{conteo_actual}**"
                await canal_reporte.send(mensaje_alerta)
                print(f"Reporte enviado: {user_name} dijo '{palabra_encontrada}'. Total: {conteo_actual}")
            except discord.Forbidden:
                print(f"ERROR: ¡No tengo permisos para enviar mensajes en el canal #{canal_reporte.name}!")
            except Exception as e:
                print(f"ERROR al enviar mensaje de reporte: {e}")
        else:
            print(f"ERROR: No se encontró el canal de reporte (ID: {CANAL_ID_REPORTE}) durante el reporte.")

# --- Ejecutar el Bot y el Servidor Web ---

# Carga el token desde las "Variables de Entorno" del servidor
TOKEN = os.environ.get("DISCORD_TOKEN") 

if not TOKEN:
    print("ERROR FATAL: No se encontró la variable de entorno 'DISCORD_TOKEN'.")
    print("Asegúrate de configurarla en el panel de Render.")
else:
    # Iniciar el servidor web ANTES de iniciar el bot
    start_web_server_thread()

    # Iniciar el bot

    client.run(TOKEN)
