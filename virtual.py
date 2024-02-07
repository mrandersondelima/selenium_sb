from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from dutching import calcula_dutching
import time
import pause
import json
from datetime import datetime, timedelta, date
from credenciais import usuario, senha, bwin_id
from telegram_bot import TelegramBot, TelegramBotErro
from random import randrange, randint
import os
from utils import *
import sys
from itertools import combinations, permutations
from exceptions import ErroDeNavegacao, ErroCotaForaIntervalo, ErroSelecaoDeMercado
import psycopg2
from dateutil import parser
import re
import csv
from subprocess import Popen, PIPE
from itertools import cycle
from analisador_resultados_3 import empatou
import threading

hora_jogo_atual = None

# & C:/Python39/python.exe c:/Users/anderson.morais/Documents/dev/sportingbet3/app.py 2 5 4 50 1 20 1 2
class ChromeAuto():
    def __init__(self, numero_apostas=243, numero_jogos_por_aposta=5, apenas_acompanhar=False):
        self.numero_jogos_por_aposta = numero_jogos_por_aposta
        self.saldo = 0
        self.saldo_inicial = 0
        self.valor_aposta = self.saldo_inicial / 10
        self.meta = self.saldo_inicial + self.valor_aposta
        self.saldo_antes_aposta = 0.0
        self.aposta_fechada = False
        self.telegram_bot = TelegramBot()
        self.telegram_bot_erro = TelegramBotErro()                     
        self.apenas_acompanhar = apenas_acompanhar        
        self.jogos_aleatorios = dict()
        self.numero_apostas = numero_apostas
        #self.gera_jogos_aleatorios()
        self.primeiro_alerta_depois_do_jogo = True
        self.numero_erros_global = 0
        self.tempo_pausa = None
        self.primeiro_alerta_sem_jogos_elegiveis = True
        self.numero_apostas_feitas = 0
        self.jogos_inseridos = []
        self.varios_jogos = True
        self.saldo_inicio_dia = 0.0
        self.aposta_fechada = False
        #self.meta_ganho = 0.0
        self.hora_ultima_aposta = ''
        self.ganhou = False
        self.estilo_jogo = None
        self.qt_apostas_feitas = None
        self.odds = []
        self.odds_clicadas = []
        self.perdas_acumuladas = 0
        self.proximo_jogo = None
        self.numero_reds = 0
        self.meta_fixa = True
        # dicionario do tipo { 'nome': nome_time, 'jogos_sem_empate': jogos_sem_empate }
        self.times_jogos_sem_empate = {}
        self.time_de_interesse = None
        self.times_de_interesse = []
        self.qt_jogos_sem_empate = 7
        self.proximo_jogo_time_casa = None
        self.time_casa = None
        self.proximo_jogo_time_fora = None
        self.time_fora = None
        self.jogos_computados = 0
        self.n_empates = 0
        self.proporcao_empates = 0.0

        self.jogos = [
            '00:20',
            '01:17',
            '02:02',
            '02:44',
            '03:29',
            '04:14',
            '05:11',
            '05:56',
            '06:41',
            '07:38',
            '08:23',
            '09:08',
            '10:05',
            '10:50',
            '11:35',
            '12:32',
            '13:17',
            '14:02',
            '14:59',
            '15:44',
            '16:29',
            '17:26',
            '18:11',
            '18:56',
            '19:53',
            '20:38',
            '21:08',
            '21:53',
            '22:50',
            '23:35'
        ]
        return

    def acessa(self, site):         
        carregou_site = False
        self.chrome = None
        while not carregou_site:
            try:
                self.driver_path = 'chromedriver.exe'
                self.options = Options()
                self.options.add_argument('--ignore-certificate-errors')
                self.options.add_argument('--ignore-ssl-errors')
                self.chrome = webdriver.Chrome(options=self.options, service=ChromeService(ChromeDriverManager().install()))                
                # definimos quanto um script vai esperar pela resposta
                self.chrome.get(site)
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()
                carregou_site = True
            except Exception as e:
                print(e)
                if self.chrome:
                    self.chrome.quit()
                sleep(5)

    def sair(self):
        self.chrome.quit()

    def faz_login(self):
        print('faz login')

        #return input()
        # preciso verificar se já está logado
        sleep(2)        

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        url_acesso = 'https://sports.sportingbet.com/pt-br/sports'

        tentativas = 0
        fez_login_com_sucesso = False
        while not fez_login_com_sucesso:
            try:
                try:
                    jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                    if jogos_abertos['summary']['liveBetsCount']:
                        print('logou com sucesso')
                        return
                except Exception as e:
                    print('não está logado')

                vezes_fechar_banner = 0        

                while vezes_fechar_banner < 5:
                    try:
                        self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
                    except Exception as e:
                        print('Erro ao tentar fechar banner')
                        print(e)
                        self.numero_erros_global += 1
                    vezes_fechar_banner += 1
                    sleep(1)

                # self.chrome.switch_to.default_content()
                if url_acesso == 'https://sports.sportingbet.com/pt-br/sports':
                    try: 
                        botao_login = WebDriverWait(self.chrome, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='https://www.sportingbet.com/pt-br/labelhost/login']" )  )) 
                        botao_login.click()
                    except Exception as e:
                        # se não encontrar botão de login é porque já está logado
                        print('não encontrou o botão de login')
                        print(e)
                        return


                input_login = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'userId' )  )) 
                input_login.clear()
                input_login.send_keys(usuario)         

                print('achou campo login')
                
                input_password = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.NAME, 'password' )  )) 
                input_password.clear()
                input_password.send_keys(senha)

                print('achou campo senha')

                remember_me = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'rememberMe' )  ))
                remember_me.click()

                print('clicou no remember me')

                sleep(1)

                botao_login = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="login w-100 btn btn-primary"]' )  )) 
                sleep(1)

                print('achou botaão de login')
                
                botao_login.click()

                print('clicou no login')              

                tentativas_de_ler_api = 0
                while True:
                    if tentativas_de_ler_api >= 5:
                        raise Exception
                    try:
                        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        if not jogos_abertos['summary']['hasError']:
                            print('logou com sucesso')     
                            break                   
                    except Exception as e:
                        sleep(2)
                        tentativas_de_ler_api += 1
                        print(e)
                  

                # aqui vou tentar buscar algo da API pra ver se logou de verdade
                # jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                # if jogos_abertos['summary']['liveBetsCount']:
                #     print('logou com sucesso')

                try:
                    cookies = WebDriverWait(self.chrome, 10).until(
                        EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler' ) )) 
                    cookies.click() 
                except Exception as e:
                    print('erro ao clicar no botão dos cookies')
                    print(e)

                fez_login_com_sucesso = True

                try:
                    self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-close-i.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
                except Exception as e:
                    print('Erro ao tentar fechar banner')

            except Exception as e:
                print('erro aleatório')
                tentativas += 1
                if url_acesso == 'https://sports.sportingbet.com/pt-br/sports':
                    url_acesso = 'https://sports.sportingbet.com/pt-br/labelhost/login'
                else:
                    url_acesso = 'https://sports.sportingbet.com/pt-br/sports'
                self.chrome.get(url_acesso)
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()
                print(e)
                if tentativas == 5:
                    self.telegram_bot.envia_mensagem('SISTEMA TRAVADO NO LOGIN')

    def quantidade_apostas_feitas(self):
        jogos_feitos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=20&typeFilter=2"); return await d.json();')
        jogos_perdidos = 0
        for jogo_feito in jogos_feitos['betslips']:
            if jogo_feito['state'] == 'Lost':
                jogos_perdidos += 1
            elif jogo_feito['state'] == 'Won':
                break
        return jogos_perdidos
      
    def le_saldo(self):        
        leu_saldo = False
        contador_de_trava = 0
        while not leu_saldo:
            try:
                saldo_request = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/api/balance?forceFresh=1"); return await d.json();')
                self.saldo = float(saldo_request['balance']['accountBalance'])
                leu_saldo = True
            except Exception as e:
                sleep(5)
                print(e)
                contador_de_trava += 1
                if contador_de_trava % 10 == 0:
                    self.testa_sessao()
                    self.telegram_bot_erro.envia_mensagem('SISTEMA POSSIVELMENTE TRAVADO AO LER SALDO.')
                    self.chrome.refresh()
                print('Não foi possível ler saldo. Tentando de novo...')

    def insere_valor(self, id_jogo):
        try:
            print('entrou no insere valor')

            if self.valor_aposta < 1:
                self.valor_aposta = 1

    
            try:
                input_valor = WebDriverWait(self.chrome, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
                input_valor.clear()
                input_valor.send_keys(f'{self.valor_aposta:.2f}')
            except Exception as e:
                raise Exception('erro ao inserir valor no campo')
                        
            sleep(0.2)

            try:
                botao_aposta = WebDriverWait(self.chrome, 20).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                botao_aposta.click()     
            except:
                raise Exception('erro ao clicar no botão')
                    
            sleep(0.2)
            
            try:
                botao_fechar = WebDriverWait(self.chrome, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                botao_fechar.click() 

            except:
                # se ele não clicou no botão de fechar é porque a aposta não foi feita
                # então vai clicar no botão de fazer aposta de novo
                print('erro ao clicar no botão de fechar')
                raise Exception('erro ao clicar no botão de fechar')
                
                # verificamos se há apostas em aberto
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            
            print('jogos_abertos ', jogos_abertos['summary']['openBetsCount'])
            if jogos_abertos['summary']['openBetsCount'] >= 1:
                self.qt_apostas_feitas += 1


                perda_acumulada = None
                with open('perda_acumulada.txt', 'r') as f:
                    perda_acumulada = float( f.read() )
                    print('perda_acumulada ', perda_acumulada)
                    perda_acumulada += self.valor_aposta
                with open('perda_acumulada.txt', 'w') as f:
                    f.write(f'{perda_acumulada:.2f}')
     
                self.le_saldo()

                self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")

                if not self.varios_jogos:                    
                    # try:
                    #     conn = self.get_bd_connection()
                    #     cur = conn.cursor()

                    #     cur.execute("select valor from meta_ganho")
                    #     rows = cur.fetchall()
                    #     self.meta_ganho = rows[0][0]
                    #     conn.commit()
                    #     conn.close()
                    # except Exception as e:
                    #     print('erro ao conectar ao banco')
                    #     print(e)
                    mensagem = f'APOSTA {self.qt_apostas_feitas} REALIZADA.'

                    if self.qt_apostas_feitas == 1:
                        self.saldo_antes_aposta = self.saldo
                        print('saldo antes da aposta ', self.saldo_antes_aposta)

                    print(mensagem)
                    self.telegram_bot.envia_mensagem(mensagem)
                else:                                        
                    self.telegram_bot.envia_mensagem(f'APOSTA REALIZADA.')
                self.primeiro_alerta_depois_do_jogo = True
                self.primeiro_alerta_sem_jogos_elegiveis = True

                if id_jogo:
                    self.jogos_inseridos.append(f"{id_jogo['id']}{id_jogo['tempo']}")
                self.numero_apostas_feitas = 0
                return True
            else:
                print('sem apostas abertas')
                # deu algum erro maluco, limpamos a aposta e esperamos o próximo laço
                self.testa_sessao()
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
                return False

        except Exception as e:
            self.testa_sessao()
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')
            print(e)
            return False

        return
    
    def testa_sessao(self):
        print('testando sessão...')
        try:
            self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-close-i.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
        except Exception as e:
            print('Erro ao tentar fechar banner')
        try:
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if not jogos_abertos['summary']['hasError']:
                print('sessão ativa')
        except:
            print('sessão expirada. tentando login novamente.')
            self.chrome.quit()
            self.acessa('https://sports.sportingbet.com/pt-br/sports')        
            self.faz_login()

    def define_hora_jogo(self, hora_jogo_atual):
        hora = int(hora_jogo_atual.split(':')[0])
        minuto = int(hora_jogo_atual.split(':')[1])
        now = datetime.today()  
        hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
        hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=3)
        hora_jogo_atual =  hora_jogo_atual_datetime.strftime("%H:%M")
        return hora_jogo_atual

    def clica_horario_jogo(self, horario_jogo):

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        try:
            self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
        except:
            print('Erro ao tentar fechar banner')

        try:
            self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
        except Exception as e:
            print('Erro ao tentar fechar banner')

        try:
            horario = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, horario_jogo)))
            horario.click()
            sleep(2)
            horario.click()
            sleep(2)
            print('clicou no jogo')
            return True
        except Exception as e:
            print(e) 
            return False
            # se não encontrar o jogo para o horário então a gente aborta logo a brincadeira
            ''' aqui a gente verifica se o item atual tem sibling, 
            se tiver é porque o horário não existe, então passamos pro próximo horário '''            
             
    def analisa_odds(self):

        # caso haja algum jogo no cupom a gente vai tentar limpar
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
        except Exception as e:
            print('Não conseguiu limpar os jogos...')
            print(e)

        try:
            odd_zero_gol = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = '0']/following-sibling::div")))
            print('odd ', odd_zero_gol.get_property('innerText'))

            odd_zero_gol = float( odd_zero_gol.get_property('innerText') )

            clique_zero_gol = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '0']/ancestor::ms-event-pick")))
            clique_zero_gol.click()

            odd_acima_1_meio = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Acima de 1.5']/following-sibling::div")))
            print('odd ', odd_acima_1_meio.get_property('innerText'))

            odd_acima_1_meio = float( odd_acima_1_meio.get_property('innerText') )

            clique_odd_acima_1_meio = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Acima de 1.5']/ancestor::ms-event-pick")))
            clique_odd_acima_1_meio.click()

            with open('gastos.txt', 'r') as f:
                gastos = float( f.read() )

            print('gastos', gastos)

            array_valores = calcula_dutching( [ odd_zero_gol, odd_acima_1_meio ], 2.5 + gastos )
            total_gasto = sum(array_valores)

            print('total_gasto', total_gasto)

            if total_gasto > 150:
                array_valores = calcula_dutching( [ odd_zero_gol, odd_acima_1_meio ], 2.5 )
                total_gasto = sum(array_valores)
                gastos = 0

            with open('gastos.txt', 'w') as f:
                f.write( f"{(gastos+total_gasto):.2f}" )

            input_1 = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[2]/div/div/div/div/ms-widget-column/ms-widget-slot/ms-bet-column/bs-betslip/div/bs-betslip-edit-state/div[1]/div/div[1]/bs-digital-single-bet/bs-digital-pick-list/bs-digital-single-bet-pick[1]/bs-digital-single-bet-pick-info-column/div/div[4]/bs-digital-single-bet-pick-stake/ms-stake/div/ms-stake-input/div/input')))
            input_1.clear()

            sleep(0.2)

            input_1.send_keys( f"{array_valores[0]:.2f}")            
            
            input_2 = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[2]/div/div/div/div/ms-widget-column/ms-widget-slot/ms-bet-column/bs-betslip/div/bs-betslip-edit-state/div[1]/div/div[1]/bs-digital-single-bet/bs-digital-pick-list/bs-digital-single-bet-pick[2]/bs-digital-single-bet-pick-info-column/div/div[4]/bs-digital-single-bet-pick-stake/ms-stake/div/ms-stake-input/div/input')))
            input_2.clear()

            input_2.send_keys(f"{array_valores[1]:.2f}")            

            self.aposta_fechada = False


            sleep(0.2)

            try:
                botao_aposta = WebDriverWait(self.chrome, 20).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                botao_aposta.click()     
            except:
                self.tempo_pausa = 30
                raise Exception('erro ao clicar no botão')
                    
            sleep(0.2)
            
            try:
                botao_fechar = WebDriverWait(self.chrome, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                botao_fechar.click() 

            except:
                # se ele não clicou no botão de fechar é porque a aposta não foi feita
                # então vai clicar no botão de fazer aposta de novo
                print('erro ao clicar no botão de fechar')
                raise Exception('erro ao clicar no botão de fechar')
            
            self.telegram_bot.envia_mensagem('APOSTA REALIZADA.')

        except:
            self.aposta_fechada = True
            print('erro ao selecionar os mercados')

    def analisa_odds_2(self, padrao_jogo):

        # caso haja algum jogo no cupom a gente vai tentar limpar
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
        except Exception as e:
            print('Não conseguiu limpar os jogos...')
            print(e)

        placares = [ '0-0', '0-1', '0-2', '0-3', '0-4', '1-0', '1-1', '1-2', '1-3', '2-0', '2-1', '2-2', '3-0', '3-1', '4-0']
        self.odds = []
        valores_odds_clicadas = []
        self.odds_clicadas = []

        try:
            for placar in placares:
                odd_temp = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[normalize-space(text()) = '{placar}']/following-sibling::div")))
                print(f'odd {placar}', odd_temp.get_property('innerText'))

                odd_temp = float( odd_temp.get_property('innerText') )
                self.odds.append({ 'placar': placar, 'odd': float( odd_temp ) })
        except Exception as e:
            self.aposta_fechada = True
            print(e)

        self.odds = sorted( self.odds, key=lambda el: ( el['odd'] ) )
        print('odds ', self.odds)

        cliques_feitos = 0
        for odd in self.odds:
            if odd['placar'] != padrao_jogo:
                try:
                    clique = WebDriverWait(self.chrome, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{odd['placar']}']/ancestor::ms-event-pick")))
                    clique.click()
                    cliques_feitos += 1
                    valores_odds_clicadas.append( odd['odd'])
                    self.odds_clicadas.append( odd['placar'])
                except Exception as e:
                    print('erro ao clicar em um mercado')
                    print(e)
                    self.aposta_fechada = True
                    return
            if cliques_feitos == 4:
                break


        
        print('valores odds clicadas', valores_odds_clicadas)

        gastos = None

        with open('gastos.txt', 'r') as f:
            gastos = float( f.read() )

        valores_aposta = calcula_dutching( valores_odds_clicadas, 5 + gastos )

        print('valores aposta ', valores_aposta)
        print('odds clicadas ', self.odds_clicadas)
        

        for input_field in range(1, 5):
            try:
                input_1 = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, f'/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[2]/div/div/div/div/ms-widget-column/ms-widget-slot/ms-bet-column/bs-betslip/div/bs-betslip-edit-state/div[1]/div/div[1]/bs-digital-single-bet/bs-digital-pick-list/bs-digital-single-bet-pick[{input_field}]/bs-digital-single-bet-pick-info-column/div/div[4]/bs-digital-single-bet-pick-stake/ms-stake/div/ms-stake-input/div/input')))
                input_1.clear()
                input_1.send_keys(f"{valores_aposta[input_field-1]:.2f}")   
            except:
                self.aposta_fechada = True
                return


        with open('gastos.txt', 'r') as f:
            gastos = float( f.read() ) + sum(valores_aposta)

        print('gastos ', gastos)

        with open('gastos.txt', 'w') as f:
            f.write( f"{gastos:.2f}" )       

        self.aposta_fechada = False

        sleep(0.2)

        try:
            botao_aposta = WebDriverWait(self.chrome, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
            botao_aposta.click()     
        except:
            self.tempo_pausa = 30
            raise Exception('erro ao clicar no botão')
                
        sleep(0.2)
        
        try:
            botao_fechar = WebDriverWait(self.chrome, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
            botao_fechar.click() 

        except:
            # se ele não clicou no botão de fechar é porque a aposta não foi feita
            # então vai clicar no botão de fazer aposta de novo
            print('erro ao clicar no botão de fechar')
            raise Exception('erro ao clicar no botão de fechar')
        
        self.telegram_bot.envia_mensagem('APOSTA REALIZADA.')

    def espera_resultado_jogo(self, horario_jogo):

        try:
            horario = horario_jogo
            print('HORÁRIO',  horario )
            print('Esperando resultado da partida...')
            self.telegram_bot.envia_mensagem(f'esperando resultado aposta {horario}')
            hora = int(horario.split(':')[0])
            minuto = int(horario.split(':')[1])
            now = datetime.today()  
            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
            pause.until( hora_do_jogo + timedelta(minutes=1, seconds=10)  )
            '''saldo = self.chrome.find_element(By.XPATH, '/html/body/vn-app/vn-dynamic-layout-single-slot[2]/vn-header/header/nav/vn-header-section[2]/vn-h-avatar-balance/vn-h-balance/div[2]')
            saldo.click()'''
            
            try:               
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            except:
                self.testa_sessao()

            while jogos_abertos['summary']['openBetsCount'] >= 1:
                print('ainda não apurou resultado')
                sleep(5)
                try:
                    jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                except:
                    self.testa_sessao()


            self.atualiza_horario_jogos()
            self.proximo_jogo = self.horario_proximo_jogo()
            # se chegar aqui é porque não há mais jogos em aberto
            # try:
            #     jogos_encerrados = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=2"); return await d.json();')
            #     for jogo_encerrado in jogos_encerrados['betslips']:
            #         if jogo_encerrado['state'] == 'Won':
            #             self.ganhou = True
            #             self.telegram_bot_erro.envia_mensagem('GANHOU')
            #             with open('gastos.txt', 'w') as f:
            #                 f.write( "0.0" )
            #             break
            # except:
            #     self.testa_sessao()

            try:
                jogos_encerrados = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                jogo_encerrado = jogos_encerrados['betslips'][0]
                if jogo_encerrado['state'] == 'Won':

                    self.n_empates += 1
                    self.escreve_em_arquivo('n_empates.txt', f'{self.n_empates}', 'w')

                    # quanto menor for essa proporção maior a chance de sair empate
                    self.proporcao_empates = self.n_empates / self.jogos_computados
                    self.escreve_em_arquivo('proporcao_empates.txt', f'{self.proporcao_empates:.2f}', 'w') 

                    self.escreve_em_arquivo('historico_empates.txt', f"{self.proporcao_empates:.2f};true{os.linesep}" , 'a')

                    self.numero_reds = 0
                    self.time_de_interesse = None
                    self.ganhou = True
                    with open('time_de_interesse.txt', 'w') as f:
                        f.write('None')

                    self.le_saldo()

                    print('saldo depois do resultado ', self.saldo )

                    while self.saldo < self.saldo_antes_aposta:
                        print('saldo desatualizado')
                        self.le_saldo()
                        sleep(5)

                    meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')

                    meta_ganho = self.saldo * 0.1 if not self.meta_fixa else meta_ganho

                    self.telegram_bot.envia_mensagem(f'ganhou\nmeta de ganho: {meta_ganho:.2f}\npróximo jogo: {self.proximo_jogo}')
                    with open('perda_acumulada.txt', 'w') as f:
                        f.write('0.0')

                    if not self.meta_fixa:
                        with open('meta_ganho.txt', 'w') as f:
                            f.write(f'{meta_ganho:.2f}')

                    self.qt_apostas_feitas = 0
                else:
                    self.telegram_bot.envia_mensagem(f'perdeu\npróximo jogo: {self.proximo_jogo}')
            except Exception as e:
                print(e)

            self.le_saldo()

            print(f'SALDO ATUAL: {self.saldo}')
        except Exception as e:
            print(e)
            print('Algo saiu errada no espera_resultado')

    def espera_resultado_jogo_sem_aposta(self, horario_jogo):

        try:
            horario = horario_jogo
            print('HORÁRIO',  horario )
            print('Esperando resultado da partida...')
            #self.telegram_bot.envia_mensagem(f'esperando resultado aposta {horario}\nnumero reds: {self.numero_reds}')
            hora = int(horario.split(':')[0])
            minuto = int(horario.split(':')[1])
            now = datetime.today()  
            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
            pause.until( hora_do_jogo + timedelta(minutes=1, seconds=10)  )
            self.jogos_computados += 1
            self.escreve_em_arquivo( 'jogos_computados.txt', f'{self.jogos_computados}', 'w' )
            self.atualiza_horario_jogos()
        except:
            print('algo saiu errado no espera resultado sem aposta')


    def espera_ate_hora_do_jogo(self, horario_jogo):
        try:
            horario = horario_jogo
            print(f'esperando até hora do jogo {horario}')
            hora = int(horario.split(':')[0])
            minuto = int(horario.split(':')[1])
            now = datetime.today()  

            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
           
            pause.until( hora_do_jogo - timedelta(minutes=3) )        

        except Exception as e:
            print(e)
            print('Algo saiu errada no espera_um_minuto_antes_jogo')

    def espera_tres_minutos_antes_jogo(self, horario_jogo):

        try:
            horario = horario_jogo
            print(f'esperando três minutos antes da aposta {horario}')
            hora = int(horario.split(':')[0])
            minuto = int(horario.split(':')[1])
            now = datetime.today()  

            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
           
            pause.until( hora_do_jogo - timedelta(minutes=3)  )        

        except Exception as e:
            print(e)
            print('Algo saiu errada no espera_um_minuto_antes_jogo')


    def espera_resultado_jogo_2(self, horario_jogo):
        if not self.aposta_fechada:
            try:
                horario = WebDriverWait(self.chrome, 60).until(
                    EC.presence_of_element_located((By.XPATH, horario_jogo)))
                print('HORÁRIO',  horario.get_property('innerText') )
                print('Esperando resultado da partida...')
                hora = int(horario.get_property('innerText').split(':')[0])
                minuto = int(horario.get_property('innerText').split(':')[1])
                now = datetime.today()  
                hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
                pause.until( hora_do_jogo + timedelta(minutes=1)  )
                '''saldo = self.chrome.find_element(By.XPATH, '/html/body/vn-app/vn-dynamic-layout-single-slot[2]/vn-header/header/nav/vn-header-section[2]/vn-h-avatar-balance/vn-h-balance/div[2]')
                saldo.click()'''


                
                try:               
                    jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=4&typeFilter=1"); return await d.json();')

                    while jogos_abertos['summary']['openBetsCount'] >= 1:
                        print('ainda não apurou resultado')
                        sleep(3)
                        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=4&typeFilter=1"); return await d.json();')
                except Exception as e:
                    print(e)
                    self.testa_sessao()

                checou_jogos = False
                self.ganhou = False
                # se chegar aqui é porque não há mais jogos em aberto

                self.le_saldo()
               
                while not checou_jogos:
                    try:
                        jogos_encerrados = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=4&typeFilter=2"); return await d.json();')
                        for jogo_encerrado in jogos_encerrados['betslips']:
                            if jogo_encerrado['state'] == 'Won':
                                self.ganhou = True
                                self.telegram_bot_erro.envia_mensagem(f'GANHOU: {self.saldo}')
                                self.perdas_acumuladas = 0
                                with open('gastos.txt', 'w') as f:
                                    f.write( "0.0" )
                        checou_jogos = True
                    except Exception as e:
                        print(e)
                        checou_jogos = False

                if not self.ganhou:
                    self.perdas_acumuladas += 1
                    perda_acumulada = 0.0
                    with open('gastos.txt', 'r') as f:
                        perda_acumulada = float( f.read() )
                    self.telegram_bot.envia_mensagem(f'perdeu {self.perdas_acumuladas} vez(es)\nperda acumulada: {perda_acumulada}')
                
                print(f'SALDO ATUAL: {self.saldo}')
            except Exception as e:
                print(e)
                print('Algo saiu errada no espera_resultado')
       
    def existem_mercados_dois_jogos_seguintes(self, horario_jogo):
        if not self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']"):
            return False
        try:
            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = '0']/following-sibling::div")))      

            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Acima de 1.5']/following-sibling::div")))
        except:
            return False

        horario_jogo = self.define_hora_jogo(horario_jogo)

        if not self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']"):
            return False
        try:
            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = '0']/following-sibling::div")))      

            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Acima de 1.5']/following-sibling::div")))
        except:
            return False

        return True
    
    def resultado_diferente_1_gol_jogo_unico(self, esporte, horario_jogo):
        self.testa_sessao()

        url = None
        if esporte == 1:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204'
        else:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/champions-cup-100199'        

        self.chrome.get(url)
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()

        if not self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']"):
            return
        self.analisa_odds()

    def resultado_diferente_1_gol_virtual(self, esporte, horario_jogo ):
        print(esporte)

        self.testa_sessao()

        url = None
        if esporte == 1:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204'
        else:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/champions-cup-100199'        

        self.chrome.get(url)
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()

        if not self.existem_mercados_dois_jogos_seguintes( horario_jogo ):
            print('não existem mercados após o 1 x 1')
            return

        # horario_jogo = '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-tab-bar/ms-scroll-adapter/div/div/ul/li[1]/a/span'
                        

        # primeiro_horario = self.chrome.find_element(By.XPATH, horario_jogo )
        # hora_jogo_atual = primeiro_horario.get_property('innerText')

        # print(hora_jogo_atual)

        self.ganhou = False
        while not self.ganhou:
            self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")
            self.analisa_odds()
            self.espera_resultado_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")

            # se aposta tiver fechada devemos sair do laço
            if self.aposta_fechada:
                break

            horario_jogo = self.define_hora_jogo(horario_jogo)

            if horario_jogo == '20:59':
                horario_jogo = '21:05'

            if horario_jogo == '20:58':
                horario_jogo = '21:01'
    
    def resultado_diferente(self, esporte, horario_jogo, padrao_jogo ):
        print(esporte)

        #self.testa_sessao()

        url = None
        if esporte == 1:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204'
        else:
            url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/champions-cup-100199'        

        self.chrome.get(url)
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()

        # horario_jogo = '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-tab-bar/ms-scroll-adapter/div/div/ul/li[1]/a/span'
                        

        # primeiro_horario = self.chrome.find_element(By.XPATH, horario_jogo )
        # hora_jogo_atual = primeiro_horario.get_property('innerText')

        # print(hora_jogo_atual)


        if not self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']"):
            return
        self.analisa_odds_2(padrao_jogo)
        self.espera_resultado_jogo_2(f"//*[normalize-space(text()) = '{horario_jogo}']" )

    def main_loop_2(self):

        ultimo_id_lido_1 = None
        horario_ultima_checagem = datetime.now()

        while True:

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO.')
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

                        #print( horario_jogo )

                        soma_gols_1 = sum( [ int(x) for x in saida_1[2].split()] )      
                        

                        if ultimo_id_lido_1 == None:
                            ultimo_id_lido_1 = result_id_1 - 1

                        # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
                        # se o sistema pular um result_id, vamos zerar a contagem de soma_gols_1
                        if ultimo_id_lido_1 + 1 == result_id_1:
                            ultimo_id_lido_1 = result_id_1     

                            print('RESULT ID: ', result_id_1)
                            print('SOMA GOLS COPA: ', soma_gols_1)    

                            # se lemos sem ruído, então vamos definir o horário do próximo jogo aqui...
                            #horario_jogo = time.strftime( "%H:%M", time.localtime() + timedelta(minutes=2) )
                            now = datetime.today()  
                            hora_do_jogo = datetime( now.year, now.month, now.day, now.hour, now.minute, 0)
                            hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=2)
                            horario_jogo =  hora_jogo_atual_datetime.strftime("%H:%M")
                            
                            padrao_jogo = saida_1[2].replace(' ', '-')

                            self.resultado_diferente( 1, horario_jogo, padrao_jogo )
                        else:
                            ultimo_id_lido_1 = None
            
            except Exception as e:
                print('ERRO ', e)            

            sleep(1)

    def seleciona_zebra(self):
        try: 
            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, f"//*[normalize-space(text()) = 'Resultado da partida']") )) 

            odd_casa = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-option-group-list/div[1]/ms-option-panel[1]/ms-regular-group/ms-regular-option-group/div/ms-option[1]/ms-event-pick/div/div[2]') )) 
                                                           

            odd_casa = float( odd_casa.get_property('innerText') )
            
            odd_fora = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-option-group-list/div[1]/ms-option-panel[1]/ms-regular-group/ms-regular-option-group/div/ms-option[3]/ms-event-pick/div/div[2]') )) 

            odd_fora = float( odd_fora.get_property('innerText') )

            if odd_casa >= 3.0:
                odd_casa_clique = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-option-group-list/div[1]/ms-option-panel[1]/ms-regular-group/ms-regular-option-group/div/ms-option[1]/ms-event-pick') )) 
                odd_casa_clique.click()
                sleep(1)
                
            elif odd_fora >= 3.0:
                odd_fora_clique = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar[1]/div/div/div/div/ms-main-column/div/ms-virtual-list/ms-virtual-fixture/div/ms-option-group-list/div[1]/ms-option-panel[1]/ms-regular-group/ms-regular-option-group/div/ms-option[3]/ms-event-pick') )) 
                odd_fora_clique.click()
                sleep(1)
            else:
                return 0

            return 1
        except Exception as e:
            return 0
            print(e)

    def multipla_zebra(self):
        print('multipla zebra')
        horario_jogo_copa = input('hora jogo copa')
        horario_jogo_champions = input('hora jogo champions')
        hora_jogo_atual = None
        self.qt_apostas_feitas = 0
        self.varios_jogos = False

        while True:
            numero_apostas = 0
            aba = 1
            while numero_apostas <= 2:

                url = None
                if aba == 1:
                    url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204'
                    hora_jogo_atual = horario_jogo_copa
                    horario_jogo_copa = self.define_hora_jogo(hora_jogo_atual)
                else:
                    url = 'https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/champions-cup-100199'  
                    hora_jogo_atual = horario_jogo_champions
                    horario_jogo_champions = self.define_hora_jogo(hora_jogo_atual)

                self.chrome.get(url)
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()

                if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{hora_jogo_atual}']"):
                    numero_apostas += self.seleciona_zebra()

                if numero_apostas == 2:
                    self.valor_aposta = 1

                    # caso haja algum jogo no cupom a gente vai tentar limpar
                    try:
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    except Exception as e:
                        print('Não conseguiu limpar os jogos...')
                        print(e)

                    if self.insere_valor(None):
                        self.espera_resultado_jogo(hora_jogo_atual)
                        numero_apostas = 0


                if horario_jogo_copa == '20:56':
                    horario_jogo_copa = '21:05'

                if horario_jogo_champions == '20:58':
                    horario_jogo_champions = '21:01'

                aba = 1 if aba == 2 else 2

    def main_loop(self):

        #self.resultado_diferente_1_gol_virtual( 1 )

        um_gol_seguido_1 = 0
        um_gol_seguido_2 = 0
        ultimo_id_lido_1 = None
        ultimo_id_lido_2 = None
        com_ruido_1 = False
        com_ruido_2 = False
        horario_ultima_checagem = datetime.now()

        # estilo jogo = 1 usa martingale, estilo jogo = 2 vai fazer uma aposta depois que sair o primeiro jogo com apenas um gol
        self.estilo_jogo = 1

        while True:

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO.')
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

                        # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
                        # se o sistema pular um result_id, vamos zerar a contagem de soma_gols_1
                        if ultimo_id_lido_1 + 1 == result_id_1:
                            ultimo_id_lido_1 = result_id_1     

                            print('RESULT ID: ', result_id_1)
                            print('SOMA GOLS COPA: ', soma_gols_1)    
                            

                            if soma_gols_1 == 1:
                                um_gol_seguido_1 += 1
                               
                                if um_gol_seguido_1 >= 4:
                                    self.resultado_diferente_1_gol_virtual( 1, horario_jogo )  
                                    ultimo_id_lido_1 = None
                                    ultimo_id_lido_2 = None
                                    um_gol_seguido_1 = 0
                                    um_gol_seguido_2 = 0
                            else:
                                um_gol_seguido_1 = 0

                            print('1 A 1 SEGUIDOS ', um_gol_seguido_1)
                        else:
                            ultimo_id_lido_1 = None
                            um_gol_seguido_1 = 0
            
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

                        # só vai levar em conta se os ids forem distintos e a última leitura for sem ruídos
                        if ultimo_id_lido_2 +1 == result_id_2:
                            ultimo_id_lido_2 = result_id_2         

                            print('RESULT ID: ', result_id_2)
                            print('SOMA GOLS CHAMPIONS: ', soma_gols_2)                             

                            if soma_gols_2 == 1:
                                um_gol_seguido_2 += 1                           
                                
                                if um_gol_seguido_2 >= 4:
                                    self.resultado_diferente_1_gol_virtual( 2, horario_jogo )  
                                    ultimo_id_lido_1 = None
                                    ultimo_id_lido_2 = None
                                    um_gol_seguido_1 = 0
                                    um_gol_seguido_2 = 0                                
                            else:
                                um_gol_seguido_2 = 0
                            print('1 A 1 SEGUIDOS ', um_gol_seguido_2)
                        else:
                            ultimo_id_lido_2 = None
                            um_gol_seguido_2 = 0
            
            except Exception as e:
                print('ERRO ', e)

            if com_ruido_2 or com_ruido_1:
                print('resultado com ruído')
                sleep(1)
            else:
                sleep(10)

    def aposta_empate(self):
         # caso haja algum jogo no cupom a gente vai tentar limpar
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
        except Exception as e:
            print('Não conseguiu limpar os jogos...')
            print(e)

        try:
            WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Resultado da partida']")))

            odd_empate = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'X']/following-sibling::div")))
            print('odd empate', odd_empate.get_property('innerText'))

            clique_empate = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'X']/ancestor::ms-event-pick")))
            clique_empate.click()
            
            perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')   

            sleep(1)

            self.valor_aposta = self.le_de_arquivo('meta_ganho.txt', 'float')

            cota = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
            cota = float( cota.get_property('innerText') )

            self.valor_aposta = ( ( self.valor_aposta + perda_acumulada ) / ( cota - 1 ) ) + 0.01

            self.insere_valor(None)

        except:
            self.aposta_fechada = True
            print('erro ao selecionar os mercados')

    def jogo_ja_passou(self, horario_jogo):

        horario = horario_jogo        
        hora = int(horario.split(':')[0])
        minuto = int(horario.split(':')[1])
        now = datetime.today()  
        hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
        if hora_do_jogo < now:
            return True
        return False

    def quantidade_apostas_feitas(self):
        jogos_feitos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=20&typeFilter=2"); return await d.json();')
        jogos_perdidos = 0
        for jogo_feito in jogos_feitos['betslips']:
            if jogo_feito['state'] == 'Lost':
                jogos_perdidos += 1
            elif jogo_feito['state'] == 'Won':
                break
        return jogos_perdidos
    
    def retorna_proximo_jogo(self, jogo_atual):
        tamanho_array = len( self.jogos )
        for i in range( tamanho_array ):
            if self.jogos[i] == jogo_atual and i < tamanho_array - 1:
                return self.jogos[i+1]
        return None
    
    def jogos_ira_depois_7_reds(self):

        self.varios_jogos = False
        self.qt_apostas_feitas = self.quantidade_apostas_feitas()
        self.proximo_jogo = None
        self.numero_reds = 0
        self.meta_fixa = True

        with open('meta_ganho.txt', 'r') as f:
            self.valor_aposta = float( f.read())
        with open('perda_acumulada.txt', 'r') as f:
            self.valor_aposta += float( f.read() )
        with open('numero_reds.txt', 'r') as f:
            self.numero_reds = int( f.read() )

        for jogo in self.jogos:
            # hora_atual = datetime.now().hour
            
            # if jogo == '00:20' and hora_atual == 23:
            #     sleep( 40 * 60)

            if self.jogo_ja_passou(jogo):     
                print(f'jogo {jogo} já passou')    
                continue
            erro_fora_normal = True
            while erro_fora_normal:
                print(f'jogo atual {jogo}')
                self.proximo_jogo = self.retorna_proximo_jogo(jogo)
                try:
                    # vamos esperar até o momento do jogo
                    if self.numero_reds < 7:
                        self.espera_ate_hora_do_jogo(jogo)

                        self.chrome.get('https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204')
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()

                        sleep(5)

                        mensagem_telegram = ''
                        # vamos tentar clicar no jogo, se acontecer erro então zeramos o numero_reds
                        if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{jogo}']"):
                            self.espera_resultado_jogo_sem_aposta(jogo)
                            jogo_empatado = empatou()
                            if jogo_empatado == None:
                                mensagem_telegram += 'jogo com erro'
                                print('jogo com erro')
                                self.numero_reds = 0
                            elif jogo_empatado == True:
                                mensagem_telegram += 'jogo empatado'
                                print('jogo empatado')
                                self.numero_reds = 0
                            elif jogo_empatado == False:
                                mensagem_telegram += 'jogo não saiu empatado'
                                print('jogo não saiu empatado')
                                self.numero_reds += 1
                            mensagem_telegram += f'\nnumero reds: {self.numero_reds}\nproximo jogo: {self.proximo_jogo}'
                            self.telegram_bot.envia_mensagem(mensagem_telegram)
                        else:
                            self.telegram_bot.envia_mensagem('erro ao clicar no horário. zerando numero_reds')
                            self.numero_reds = 0

                        with open('numero_reds.txt', 'w') as f:
                            f.write(f'{self.numero_reds}')
                    else:
                        self.espera_tres_minutos_antes_jogo(jogo)

                        self.chrome.get('https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204')
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()

                        sleep(5)

                        if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{jogo}']"):
                            self.aposta_empate()
                            self.espera_resultado_jogo(jogo)
                        else:
                            self.numero_reds = 0
                            with open('numero_reds.txt', 'w') as f:
                                f.write(f'{self.numero_reds}')

                    print(f'NÚMERO DE REDS: {self.numero_reds}')

                    with open('numero_reds.txt', 'w') as f:
                        f.write(f'{self.numero_reds}')

                    erro_fora_normal = False

                except Exception as e:                   
                    print(f'erro no laço principal no jogo {jogo}')
                    print(e)
        
        print('fim dos jogos do dia... encerrando programa')

    def jogos_ira(self):       

        self.varios_jogos = False
        self.qt_apostas_feitas = self.quantidade_apostas_feitas()
        self.proximo_jogo = None

        with open('meta_ganho.txt', 'r') as f:
            self.valor_aposta = float( f.read())
        with open('perda_acumulada.txt', 'r') as f:
            self.valor_aposta += float( f.read() )

        for jogo in self.jogos:
            # hora_atual = datetime.now().hour
            
            # if jogo == '00:20' and hora_atual == 23:
            #     sleep( 40 * 60)

            if self.jogo_ja_passou(jogo):     
                print(f'jogo {jogo} já passou')    
                continue
            erro_fora_normal = True
            while erro_fora_normal:
                print(f'jogo atual {jogo}')
                self.proximo_jogo = self.retorna_proximo_jogo(jogo)
                try:
                    self.espera_tres_minutos_antes_jogo(jogo)

                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204')
                    self.chrome.maximize_window()
                    self.chrome.fullscreen_window()

                    sleep(5)

                    if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{jogo}']"):
                        self.aposta_empate()
                        self.espera_resultado_jogo(jogo)

                    erro_fora_normal = False

                except Exception as e:                    
                    print(f'erro no laço principal no jogo {jogo}')
                    print(e)
        
        print('fim dos jogos do dia... encerrando programa')

    def get_bd_connection(self):
        try:
            conn = psycopg2.connect(database = 'sportingbet', 
                                user = 'postgres', 
                                host= 'localhost',
                                password = 'postgres',
                                port = '5432')
            return conn
        except:
            print('Erro ao abrir conexão')

    def le_de_arquivo(self, nome_arquivo, tipo):
        with open(nome_arquivo, 'r') as f:
            if tipo == 'int':
                return int( f.read() )
            elif tipo == 'float':
                return float( f.read() )
            
    def escreve_em_arquivo(self, nome_arquivo, valor, tipo_escrita):
        with open(nome_arquivo, tipo_escrita) as f:
            f.write(valor)

    def depois_7_jogos_sem_empate(self ):
        print('depois_7_jogos_sem_empate')

        self.varios_jogos = False
        self.qt_apostas_feitas = self.quantidade_apostas_feitas()
        self.meta_fixa = False
        self.ganhou = False
        self.qt_jogos_sem_empate = 0
        self.numero_reds = self.le_de_arquivo('numero_reds.txt', 'int')
        self.jogos_computados = self.le_de_arquivo('jogos_computados.txt', 'int')
        self.n_empates = self.le_de_arquivo('n_empates.txt', 'int')
        self.proporcao_empates = self.le_de_arquivo('proporcao_empates.txt', 'float')

        self.times_de_interesse = self.read_array_from_disk('times_de_interesse.json')

        # with open('time_de_interesse.txt', 'r') as f:
        #     time_interesse = f.read()
        #     if time_interesse == 'None':
        #         self.time_de_interesse = None
        #     else:
        #         self.time_de_interesse = time_interesse
        
        self.valor_aposta = self.le_de_arquivo('meta_ganho.txt', 'float')
        if not self.meta_fixa:
            self.valor_aposta += self.le_de_arquivo('perda_acumulada.txt', 'float')

        while True:

            try:
                #vamos pegar o próximo horário de jogo depois do jogo de agora
                conn = self.get_bd_connection()
                cur = conn.cursor()
                hora_atual = time.strftime("%H:%M", time.localtime())
                cur.execute(f"select * from jogos_copa_mundo where horario > '{hora_atual}' order by horario asc limit 1")
                proximo_horario = cur.fetchone()

                #self.espera_ate_hora_do_jogo(proximo_horario[0])

                #self.time_casa = proximo_horario[1]
                #self.time_fora = proximo_horario[2]

                # print(f'jogo atual {proximo_horario}')
                # self.proximo_jogo_time_casa = self.retorna_proximo_horario_por_time( self.time_casa, proximo_horario[0] )
                # self.proximo_jogo_time_fora = self.retorna_proximo_horario_por_time( self.time_fora, proximo_horario[0] )
                # print('proximo horario time casa', self.proximo_jogo_time_casa )
                # print('proximo horario time fora', self.proximo_jogo_time_fora )

                #agora vamos pegar o número de reds dos dois times
                # cur.execute(f"select * from empates_copa_mundo where time = '{self.time_casa}'")
                # qt_empates_casa = cur.fetchone()   
                # print('qt_empate_casa ', qt_empates_casa)             
                # if qt_empates_casa == None:
                #     cur.execute(f"insert into empates_copa_mundo values ('{self.time_casa}', 0, '{self.proximo_jogo_time_casa}')")
                #     qt_empates_casa = 0
                #     conn.commit()
                # else:
                #     # se o horário for diferente do horário do último jogo é porque pulamos algum horário
                #     # então vamos zerar o qt_empates
                #     print('qt_empates_casa[2] ', qt_empates_casa[2])
                #     print('proximo_horario[0] ', proximo_horario[0])
                #     if qt_empates_casa[2] != proximo_horario[0]:
                #         print('o horário não corresponde ao previsto. zerando número de jogos sem empate.')
                #         cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_casa}'")
                #         qt_empates_casa = 0
                #         self.numero_reds = 0
                #         with open('numero_reds.txt', 'w') as f:
                #             f.write(f'{self.numero_reds}')
                #         conn.commit()
                #     else:
                #         qt_empates_casa = qt_empates_casa[1]

                # cur.execute(f"select * from empates_copa_mundo where time = '{self.time_fora}'")
                # qt_empates_fora = cur.fetchone()
                # print('qt_empate_fora ', qt_empates_fora)
                # if qt_empates_fora == None:
                #     cur.execute(f"insert into empates_copa_mundo values ('{self.time_fora}', 0, '{self.proximo_jogo_time_fora}')")
                #     qt_empates_fora = 0
                #     conn.commit()
                # else:
                #     # se o horário for diferente do horário do último jogo é porque pulamos algum horário
                #     # então vamos zerar o qt_empates
                #     print('qt_empates_fora[2] ', qt_empates_fora[2])
                #     print('proximo_horario[0] ', proximo_horario[0])
                #     if qt_empates_fora[2] != proximo_horario[0]:
                #         print('o horário não corresponde ao previsto. zerando número de jogos sem empate.')
                #         cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_fora}'")
                #         self.numero_reds = 0
                #         with open('numero_reds.txt', 'w') as f:
                #             f.write(f'{self.numero_reds}')
                #         qt_empates_fora = 0
                #         conn.commit()
                #     else:
                #         qt_empates_fora = qt_empates_fora[1]

                #     if qt_empates_casa >= self.qt_jogos_sem_empate and self.time_casa not in self.times_de_interesse:                        
                #         self.times_de_interesse.append(self.time_casa)
                #         self.save_array_on_disk(self.times_de_interesse)
                #     if qt_empates_fora >= self.qt_jogos_sem_empate and self.time_fora not in self.times_de_interesse:
                #         self.times_de_interesse.append(self.time_fora)
                #         self.save_array_on_disk(self.times_de_interesse)                    
                        
                try:
                    hora_jogo = proximo_horario[0]
                    # vamos esperar até o momento do jogo
                    if self.numero_reds < 14:
                        
                        self.espera_ate_hora_do_jogo(hora_jogo)
                        
                        self.chrome.get('https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204')
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()

                        sleep(5)

                        mensagem_telegram = ''
                        # vamos tentar clicar no jogo, se acontecer erro então zeramos o numero_reds
                        if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{hora_jogo}']"):
                            self.espera_resultado_jogo_sem_aposta(hora_jogo)
                            jogo_empatado = empatou('jogos_copa_mundo')
                            if jogo_empatado == None:
                                mensagem_telegram += 'jogo com erro'
                                print('jogo com erro')
                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_casa}'")
                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_fora}'")
                                self.numero_reds = 0
                                # conn.commit()
                            elif jogo_empatado == True:
                                mensagem_telegram += 'jogo empatado'
                                print('jogo empatado')
                                self.n_empates += 1
                                self.escreve_em_arquivo('n_empates.txt', f'{self.n_empates}', 'w')

                                # quanto menor for essa proporção maior a chance de sair empate
                                self.proporcao_empates = self.n_empates / self.jogos_computados
                                self.escreve_em_arquivo('proporcao_empates.txt', f'{self.proporcao_empates:.2f}', 'w') 

                                self.escreve_em_arquivo('historico_empates.txt', f"{self.proporcao_empates:.2f};true{os.linesep}" , 'a')

                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_casa}'")
                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_fora}'")
                                self.numero_reds = 0
                                # conn.commit()
                            elif jogo_empatado == False:
                                mensagem_telegram += 'jogo não saiu empatado'
                                self.numero_reds += 1
                                print('jogo não saiu empatado')

                                self.proporcao_empates = self.n_empates / self.jogos_computados
                                self.escreve_em_arquivo('proporcao_empates.txt', f'{self.proporcao_empates:.2f}', 'w') 
                                # cur.execute(f"update empates_copa_mundo set qt_empates = qt_empates + 1 where time = '{self.time_casa}'")
                                # cur.execute(f"update empates_copa_mundo set qt_empates = qt_empates + 1 where time = '{self.time_fora}'")
                                # conn.commit()

                            #mensagem_telegram += f'\nnumero reds: {self.numero_reds}\nproximo jogo: {self.proximo_jogo}'
                            #self.telegram_bot.envia_mensagem(mensagem_telegram)
                        else:
                            self.telegram_bot.envia_mensagem('erro ao clicar no horário. zerando numero_reds')
                            # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_casa}'")
                            # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_fora}'")
                            # conn.commit()
                            self.numero_reds = 0
                        
                        self.escreve_em_arquivo('numero_reds.txt', f'{self.numero_reds}', 'w')

                        # aqui no final temos que atualizar o valor do próximo jogo

                    else:
                        #self.espera_tres_minutos_antes_jogo(hora_jogo)

                        self.testa_sessao()
                        
                        self.chrome.get('https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/copa-do-mundo-100204')
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()

                        sleep(5)

                        if self.clica_horario_jogo(f"//*[normalize-space(text()) = '{hora_jogo}']"):
                            self.aposta_empate()
                            self.espera_resultado_jogo(hora_jogo)
                            # se aqui for None é porque deu green
                            if self.ganhou:
                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_casa}'")
                                # cur.execute(f"update empates_copa_mundo set qt_empates = 0 where time = '{self.time_fora}'")
                                self.numero_reds = 0
                                # try:
                                #     self.times_de_interesse.remove(self.time_casa)
                                # except Exception as e:
                                #     print(e)

                                # try:
                                #     self.times_de_interesse.remove(self.time_fora)
                                # except Exception as e:
                                #     print(e)

                                # self.save_array_on_disk(self.times_de_interesse)
                                # conn.commit()   
                                self.ganhou = False
                            else:
                                self.numero_reds += 1
                                # cur.execute(f"update empates_copa_mundo set qt_empates = qt_empates + 1 where time = '{self.time_casa}'")
                                # cur.execute(f"update empates_copa_mundo set qt_empates = qt_empates + 1 where time = '{self.time_fora}'")
                                
                                # conn.commit()
                            
                    print(f'NÚMERO DE REDS: {self.numero_reds}')

                    if self.proporcao_empates <= 0.25:
                        try:
                            self.telegram_bot.envia_mensagem(self.proporcao_empates)
                        except Exception as e:
                            print(e)

                    self.escreve_em_arquivo('numero_reds.txt', f'{self.numero_reds}', 'w')

                    # conn.close()

                except Exception as e:                   
                    print(f'erro no laço principal no jogo {hora_jogo}')
                    # cur.execute(f"update empates_copa_mundo set proximo_jogo = '{self.proximo_jogo_time_casa}', qt_empates = 0 where time = '{self.time_casa}'")
                    # cur.execute(f"update empates_copa_mundo set proximo_jogo = '{self.proximo_jogo_time_fora}', qt_empates = 0 where time = '{self.time_fora}'")
                    # conn.commit()
                    self.numero_reds = 0
                    self.escreve_em_arquivo('numero_reds.txt', f'{self.numero_reds}', 'w')

                    # conn.close()
                    print(e)

                conn.close()
            except Exception as e:
                conn.close()
                print(e)

    def atualiza_horario_jogos(self):
        try:
            conn = self.get_bd_connection()
            cur = conn.cursor()
            cur.execute(f"update empates_copa_mundo set proximo_jogo = '{self.proximo_jogo_time_casa}' where time = '{self.time_casa}'")
            cur.execute(f"update empates_copa_mundo set proximo_jogo = '{self.proximo_jogo_time_fora}' where time = '{self.time_fora}'")
            conn.commit()
        except Exception as e:
            print(e)

    def save_array_on_disk(self, array):        
        with open("times_de_interesse.json", "w") as fp:
            json.dump(array, fp)

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list   
        
    def horario_proximo_jogo(self):
        try:
            conn = self.get_bd_connection()
            cur = conn.cursor()
            cur.execute(f"select * from empates_copa_mundo where qt_empates >= {self.qt_jogos_sem_empate} order by proximo_jogo asc limit 1")
            proximo_horario = cur.fetchall()
            conn.commit()
            conn.close()

            if len(proximo_horario) == 0:
                return 'sem jogo'
            else:
                return proximo_horario[0][2]
            
        except:
            print('erro ao trazer horário do próximo jogo')

    def retorna_proximo_horario_por_time(self, time, hora_atual):
        try:
            conn = self.get_bd_connection()
            cur = conn.cursor()         
            
            cur.execute(f"select * from jogos_copa_mundo where horario > '{hora_atual}' and ( time_casa = '{time}' or time_fora = '{time}' ) order by horario asc limit 1")
            proximo_horario = cur.fetchone()

            if proximo_horario == None:
                cur.execute(f"select * from jogos_copa_mundo where time_casa = '{time}' or time_fora = '{time}' order by horario asc limit 1")
                proximo_horario = cur.fetchone()

            return proximo_horario[0]
        except Exception as e:
            print(e)


if __name__ == '__main__':

    #numero_jogos_por_aposta = int(input())

    #apenas_analisa = int(input())   

    chrome = ChromeAuto(numero_apostas=200, numero_jogos_por_aposta=10)
    chrome.acessa('https://sports.sportingbet.com/pt-br/sports')        
    #chrome.clica_sign_in()

    chrome.faz_login()  
    #chrome.jogos_ira()
    #chrome.jogos_ira_depois_7_reds()

    chrome.depois_7_jogos_sem_empate()

    #chrome.busca_odds_acima_meio_gol_sem_login('Mais de 0,5', 1.9, 2.9 )
    #chrome.busca_odds_acima_meio_gol('Mais de 0,5', 1.75, 2.9, 1, False, False, 100.0)
    # parâmetros: mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria

    #chrome.multipla_zebra()

    #chrome.main_loop_2()

    #chrome.busca_odds_fim_jogo_sem_gol('Mais de 0,5', 3.5, 4, 1, True, False, 100.0)