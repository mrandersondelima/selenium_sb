from analisador_resultados_3 import numero_gols
from time import sleep
from telegram_bot import TelegramBotErro
import asyncio

telegram = TelegramBotErro()

numero_gols_ = None
anterior = None
qt_intercalados = 0

while numero_gols_ == None:
    numero_gols_ = numero_gols('/home/andersonmorais/results_eurocopa.sh')

async def main_loop():
    while True:
        print('esperando próximo jogo...')
        sleep(2.7 * 60)
        numero_gols_ = numero_gols('/home/andersonmorais/results_eurocopa.sh')
        if numero_gols_ == None:
            anterior = None
            qt_intercalados = 1
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
            if qt_intercalados >= 3:
                try:
                    await telegram.envia_mensagem('eurocopa')
                except Exception as e:
                    print(e)                    
                

if __name__ == '__main__':
    while True:
        try:
            asyncio.run( main_loop )
        except:
            pass


