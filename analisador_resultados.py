import os
from time import sleep
from telegram_bot import TelegramBot
#from app import AnalisadorResultados
from datetime import datetime
from subprocess import Popen, PIPE
import subprocess
import psycopg2

def get_bd_connection():
        try:
            conn = psycopg2.connect(database = 'sportingbet', 
                                user = 'postgres', 
                                host= 'localhost',
                                password = 'postgres',
                                port = '5432')
            return conn
        except:
            print('Erro ao abrir conexão')

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'



ultima_lista = ''

# a cada 20 jogos o sistema vai emitir um alerta avisando que ainda está rodando
contador_jogos = 0

ultimo_id_lido = None
sem_ruido = True
um_gol_seguido = 0
telegram = TelegramBot()
n_jogos_antes_padrao_2_3_2 = 0
n_jogos_antes_padrao_2_2_2 = 0
n_jogos_antes_padrao_3_2_2 = 0
n_jogos_antes_padrao_2_2_3 = 0
n_jogos_antes_padrao_2_2 = 0

array_jogos = []

while True:
    p = Popen(['wsl', '/home/andersonmorais/monkeybet/novo_results.sh'], stdout=PIPE, stdin=PIPE)
    stdout, stderr = p.communicate()
    saida = stdout.decode().split('\n')
    if len(saida) > 2:
        result_id = saida[1][1:]
        #contém ruidos
        if '_' in saida[2] or '_' in result_id:
            sem_ruido = False
            continue
        else:
            sem_ruido = True

        soma_gols = sum( [ int(x) for x in saida[2].split()] )
    # print(saida)

        # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
        if ultimo_id_lido != result_id and sem_ruido:
            ultimo_id_lido = result_id

            print( f'RESULTID: {result_id}\nSOMA DOS GOLS: {soma_gols}')

            array_jogos.insert(0, soma_gols)

            if len(array_jogos) >= 2:
                gols_jogo_1 = array_jogos[1]
                gols_jogo_2 = array_jogos[0]
                if gols_jogo_1 == 2 and gols_jogo_2 == 2:
                    #telegram.envia_mensagem(f'{n_jogos_antes_padrao_2_2} ANTES DE PADRÃO 2 2 COPA')
                    n_jogos_antes_padrao_2_2 = 0

            if len(array_jogos) >= 3:
                gols_jogo_1 = array_jogos[2]
                gols_jogo_2 = array_jogos[1]
                gols_jogo_3 = array_jogos[0]
                if gols_jogo_1 == 2 and gols_jogo_2 == 3 and gols_jogo_3 == 2:
                    #telegram.envia_mensagem(f'{n_jogos_antes_padrao_2_3_2} ANTES DE PADRÃO 2 3 2 COPA')
                    n_jogos_antes_padrao_2_3_2 = 0
                # elif gols_jogo_1 == 2 and gols_jogo_2 == 2 and gols_jogo_3 == 2:
                #     telegram.envia_mensagem(f'{n_jogos_antes_padrao_2_2_2} ANTES DE PADRÃO 2 2 2 COPA')
                #     n_jogos_antes_padrao_2_2_2 = 0
                # if gols_jogo_1 == 3 and gols_jogo_2 == 2 and gols_jogo_3 == 2:
                #     telegram.envia_mensagem(f'{n_jogos_antes_padrao_3_2_2} ANTES DE PADRÃO 3 2 2 COPA')
                #     n_jogos_antes_padrao_3_2_2 = 0
                # elif gols_jogo_1 == 2 and gols_jogo_2 == 2 and gols_jogo_3 == 3:
                #     telegram.envia_mensagem(f'{n_jogos_antes_padrao_2_3_2} ANTES DE PADRÃO 2 2 3 COPA')
                #     n_jogos_antes_padrao_2_2_3 = 0
                else:
                    n_jogos_antes_padrao_2_3_2 += 1
                    n_jogos_antes_padrao_2_2_2 += 1
                    n_jogos_antes_padrao_3_2_2 += 1
                    n_jogos_antes_padrao_2_2_3 += 1
                    n_jogos_antes_padrao_2_2 += 1

                conn = get_bd_connection()             
                cur_1 = conn.cursor()
                cur_2 = conn.cursor()

                padrao = f'{gols_jogo_1} {gols_jogo_2} {gols_jogo_3}'
                padrao_2 = f'{gols_jogo_1} {gols_jogo_2}'
                cur_1.execute(f"select * from padrao_tres_jogos where padrao = '{padrao}'")
                cur_2.execute(f"select * from padrao_dois_jogos where padrao = '{padrao_2}'")
                rows_1 = cur_1.fetchall()
                rows_2 = cur_2.fetchall()
                if len(rows_1) == 0:
                    cur_1.execute(f"insert into padrao_tres_jogos values ('{padrao}', 1)")                    
                else:
                    total = rows_1[0][1]
                    cur_1.execute(f"update padrao_tres_jogos set qt = {total + 1} where padrao = '{padrao}'")                    

                if len(rows_2) == 0:
                    cur_2.execute(f"insert into padrao_dois_jogos values ('{padrao}', 1)")                    
                else:
                    total = rows_2[0][1]
                    cur_2.execute(f"update padrao_dois_jogos set qt = {total + 1} where padrao = '{padrao}'")
                    
                conn.commit()
                conn.close()


            if soma_gols == 1:
                um_gol_seguido += 1
                if um_gol_seguido >= 4:
                    telegram.envia_mensagem(f'{um_gol_seguido} COM APENAS 1 GOL EM SEGUIDA. COPA DO MUNDO.')    
            else:
                um_gol_seguido = 0
            
    
    sleep(10)

    




