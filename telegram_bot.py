from datetime import datetime
from credenciais import token, chat_id, token_id_erro, chat_id_grupo
import telegram

class TelegramBot:

    bot = None

    def __init__(self):
        self.bot = telegram.Bot(token)

    async def envia_mensagem(self, mensagem):
        try:
            if chat_id_grupo != '':
                await self.bot.send_message(text=mensagem, chat_id=chat_id_grupo, read_timeout=2, write_timeout=2, connect_timeout=2, pool_timeout=2)
            await self.bot.send_message(text=mensagem, chat_id=chat_id, read_timeout=2, write_timeout=2, connect_timeout=2, pool_timeout=2)
        except:
            raise Exception('erro ao enviar mensagem')

if __name__ == '__main__':
    telegram_bot = TelegramBot()
    telegram_bot.envia_mensagem( datetime.now() )

class TelegramBotErro:

    bot = None

    def __init__(self):
        self.bot = telegram.Bot(token_id_erro)

    async def envia_mensagem(self, mensagem):        
        try:
            if chat_id_grupo != '':                
                await self.bot.send_message(text=mensagem, chat_id=chat_id_grupo, read_timeout=2, write_timeout=2, connect_timeout=2, pool_timeout=2)
            await self.bot.send_message(text=mensagem, chat_id=chat_id, read_timeout=2, write_timeout=2, connect_timeout=2, pool_timeout=2)
        except:
            raise Exception('erro ao enviar mensagem')