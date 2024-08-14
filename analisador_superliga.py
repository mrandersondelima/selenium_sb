from analisador_resultados_3 import numero_gols
from time import sleep
from telegram_bot import TelegramBotErro
import asyncio
import sys

async def main_loop(url):
    telegram = TelegramBotErro()

    numero_gols_ = None
    anterior = None
    qt_intercalados = 0

    while numero_gols_ == None:
        numero_gols_ = numero_gols(url)

    while True:
        print('esperando próximo jogo...')
        sleep(2 * 60)
        numero_gols_ = numero_gols(url)
        if numero_gols_ == None:
            anterior = None
            qt_intercalados = 1
            try:
                await telegram.envia_mensagem(f"erro no {url.split('/')[-1]}")
            except Exception as e:
                print(e)
        else:
            if anterior == None:
                anterior = numero_gols_
                qt_intercalados += 1
            else:
                if numero_gols_ > 2 and anterior <= 2 or numero_gols_ <= 2 and anterior > 2:
                    qt_intercalados += 1
                else:
                    qt_intercalados = 1
                anterior = numero_gols_
            print(qt_intercalados)
            if qt_intercalados >= 4:
                try:
                    await telegram.envia_mensagem(f"{url.split('/')[-1]} {qt_intercalados}")
                except Exception as e:
                    print(e)                    
                

if __name__ == '__main__':
    print(sys.argv[1])
    while True:
        try:
            asyncio.run( main_loop(sys.argv[1]) )
        except Exception as e:
            print(e)