from datetime import datetime, timedelta
from subprocess import PIPE, Popen
from time import sleep
from telegram_bot import TelegramBot
from credenciais import shell_path

sequencia_jogos_mesmo_n_gols_1 = 0
sequencia_jogos_mesmo_n_gols_2 = 0
ultimo_resultado_1 = None
ultimo_resultado_2 = None
ultimo_resultado_exato_1 = None
ultimo_resultado_exato_2 = None
ultimo_id_lido_1 = None
ultimo_id_lido_2 = None
com_ruido_1 = False
com_ruido_2 = False
horario_ultima_checagem = datetime.now()
telegram = TelegramBot()

def empatou():
    print('entrou no método que lê resultado')
    tentativas_leitura = 0
    url = f'{shell_path}'
    
    while True:

        try:
            p_1 = Popen(['wsl', url], stdout=PIPE, stdin=PIPE)
            stdout_1, stderr_1 = p_1.communicate()
            if stderr_1:
                print('erro')
            saida_1 = stdout_1.decode().split('\n')
            if len(saida_1) > 2:
                result_id_1 = saida_1[1][1:]
                leu_correto = True

                if '_' not in saida_1[2]:

                    print(saida_1[2])

                    gols = [ int(x) for x in saida_1[2].split() ] 

                    if gols[0] == gols[1]:
                        return [gols[0], gols[1]]
                    else:
                        return False
                   
                else:
                    tentativas_leitura += 1
                    print(saida_1[2])
            else:
                tentativas_leitura += 1

            if tentativas_leitura >= 60:
                return None
        
            sleep(0.5)
        except Exception as e:
            tentativas_leitura += 1
            if tentativas_leitura >= 60:
                return None
            sleep(0.5)
            print('ERRO ', e)

# estilo jogo = 1 usa martingale, estilo jogo = 2 vai fazer uma aposta depois que sair o primeiro jogo com apenas um gol
def main_program():
    while True:

        diferenca_tempo = datetime.now() - horario_ultima_checagem
        if diferenca_tempo.total_seconds() >= 3600:
            try:
                telegram.envia_mensagem(f'SISTEMA RODANDO.')
                print('SISTEMA RODANDO')
            except Exception as e:
                print(e)
                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
            horario_ultima_checagem = datetime.now()

        try:
            p_1 = Popen(['wsl', '/home/andersonmorais/monkeybet/novo_results.sh'], stdout=PIPE, stdin=PIPE)
            stdout_1, stderr_1 = p_1.communicate()
            if stderr_1:
                print('erro')
            saida_1 = stdout_1.decode().split('\n')
            if len(saida_1) > 2:
                result_id_1 = saida_1[1][1:]
                #contém ruidos
                com_ruido_1 = True
                if '_' not in saida_1[2] and '_' not in result_id_1:
                    com_ruido_1 = False


                    result_id_1 = int(result_id_1)
                    # o que vou fazer aqui é o seguinte

                    # se lemos sem ruído, então vamos definir o horário do próximo jogo aqui...
                    #horario_jogo = time.strftime( "%H:%M", time.localtime() + timedelta(minutes=2) )
                    now = datetime.today()  
                    hora_do_jogo = datetime( now.year, now.month, now.day, now.hour, now.minute, 0)
                    hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=2)
                    horario_jogo =  hora_jogo_atual_datetime.strftime("%H:%M")

                    #print( horario_jogo )

                    soma_gols_1 = sum( [ int(x) for x in saida_1[2].split()] )      

                    

                    if ultimo_id_lido_1 == None:
                        ultimo_id_lido_1 = result_id_1 - 1
                        sequencia_jogos_mesmo_n_gols_1 = 1
                        ultimo_resultado_1 = None
                        ultimo_resultado_exato_1 = None

                    # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
                    # se o sistema pular um result_id, vamos zerar a contagem de soma_gols_1
                    if ultimo_id_lido_1 + 1 == result_id_1:
                        ultimo_id_lido_1 = result_id_1     

                        print('RESULT ID: ', result_id_1)
                        print('SOMA GOLS COPA: ', soma_gols_1)    

                        if ultimo_resultado_exato_1 == None:
                            ultimo_resultado_exato_1 = saida_1[2]
                        else:
                            if ultimo_resultado_exato_1 == saida_1[2]:
                                telegram.envia_mensagem(f'resultados em sequência de {saida_1[2]} copa')
                        
                        ultimo_resultado_exato_1 = saida_1[2]

                        if ultimo_resultado_1 == None:
                            ultimo_resultado_1 = soma_gols_1
                        else:
                            if ultimo_resultado_1 == soma_gols_1:
                                sequencia_jogos_mesmo_n_gols_1 += 1
                                if sequencia_jogos_mesmo_n_gols_1 >= 3:
                                    telegram.envia_mensagem(f'{sequencia_jogos_mesmo_n_gols_1} seguidos saindo {soma_gols_1} gols copa')
                            else:
                                sequencia_jogos_mesmo_n_gols_1 = 1
                        
                        ultimo_resultado_1 = soma_gols_1

                        # if soma_gols_1 == 1:
                        #     sequencia_jogos_mesmo_n_gols_1 += 1
                            
                        #     if sequencia_jogos_mesmo_n_gols_1 >= 4:
                        #         telegram.envia_mensagem(f'{sequencia_jogos_mesmo_n_gols_1} com 1 gol em seguida')
                        # else:
                        #     sequencia_jogos_mesmo_n_gols_1 = 0

                        print(f'{soma_gols_1} SEGUIDOS ', sequencia_jogos_mesmo_n_gols_1)
                    else:
                        ultimo_id_lido_1 = None
                        sequencia_jogos_mesmo_n_gols_1 = 1
        
        except Exception as e:
            print('ERRO ', e)

        try:
            p_2 = Popen(['wsl', '/home/andersonmorais/monkeybet2/novo_results.sh'], stdout=PIPE, stdin=PIPE)
            stdout_2, stderr_2 = p_2.communicate()
            if stderr_2:
                print('erro')                
            saida_2 = stdout_2.decode().split('\n')
            if len(saida_2) > 2:
                result_id_2 = saida_2[1][1:]
                #contém ruidos
                com_ruido_2 = True
                if '_' not in saida_2[2] and '_' not in result_id_2:
                    com_ruido_2 = False

                    result_id_2 = int(result_id_2)
                    # se lemos sem ruído, então vamos definir o horário do próximo jogo aqui...
                    #horario_jogo = time.strftime( "%H:%M", time.localtime() + timedelta(minutes=2) )
                    now = datetime.today()  
                    hora_do_jogo = datetime( now.year, now.month, now.day, now.hour, now.minute, 0)
                    hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=2)
                    horario_jogo =  hora_jogo_atual_datetime.strftime("%H:%M")

                    #print( horario_jogo )

                    soma_gols_2 = sum( [ int(x) for x in saida_2[2].split()] )     

                
                    if ultimo_id_lido_2 == None:
                        ultimo_id_lido_2 = result_id_2 - 1  
                        sequencia_jogos_mesmo_n_gols_2 = 1
                        ultimo_resultado_2 = None
                        ultimo_resultado_exato_2 = None

                    # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
                    if ultimo_id_lido_2 +1 == result_id_2:
                        ultimo_id_lido_2 = result_id_2         

                        print('RESULT ID: ', result_id_2)
                        print('SOMA GOLS CHAMPIONS: ', soma_gols_2)          

                        if ultimo_resultado_exato_2 == None:
                            ultimo_resultado_exato_2 = saida_2[2]
                        else:
                            if ultimo_resultado_exato_2 == saida_2[2]:
                                telegram.envia_mensagem(f'resultados em sequência de {saida_2[2]} champions')

                        ultimo_resultado_exato_2 = saida_2[2]

                        if ultimo_resultado_2 == None:
                            ultimo_resultado_2 = soma_gols_2
                        else:
                            if ultimo_resultado_2 == soma_gols_2:
                                sequencia_jogos_mesmo_n_gols_2 += 1
                                if sequencia_jogos_mesmo_n_gols_2 >= 3:
                                    telegram.envia_mensagem(f'{sequencia_jogos_mesmo_n_gols_2} seguidos saindo {soma_gols_2} gols champions')                   
                            else:                            
                                sequencia_jogos_mesmo_n_gols_2 = 1

                        ultimo_resultado_2 = soma_gols_2

                        # if soma_gols_2 == 1:
                        #     sequencia_jogos_mesmo_n_gols_2 += 1                           
                            
                        #     if sequencia_jogos_mesmo_n_gols_2 >= 4:
                        #        telegram.envia_mensagem(f'{sequencia_jogos_mesmo_n_gols_2} com 1 gol em seguida')                              
                        # else:
                        #     sequencia_jogos_mesmo_n_gols_2 = 0
                        print(f'{soma_gols_2} SEGUIDOS ', sequencia_jogos_mesmo_n_gols_2)
                    else:
                        ultimo_id_lido_2 = None
                        sequencia_jogos_mesmo_n_gols_2 = 1
        
        except Exception as e:
            print('ERRO ', e)

        if com_ruido_2 or com_ruido_1:
            print('resultado com ruído')
            sleep(1)
        else:
            sleep(10)

if __name__ == '__main__':
    main_program()