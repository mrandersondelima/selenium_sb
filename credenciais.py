import os
from dotenv import load_dotenv

load_dotenv()

usuario = os.getenv('USUARIO')
senha = os.getenv('SENHA')
token = os.getenv('BOT_TOKEN')
chat_id = os.getenv('CHAT_ID')
token_id_erro = os.getenv('BOT_TOKEN_ERRO')
bwin_id = os.getenv('BWIN_ID')
chat_id_grupo = os.getenv('CHAT_ID_GRUPO')
shell_path = os.getenv('SHELL_PATH')