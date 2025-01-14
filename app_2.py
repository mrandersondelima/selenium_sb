from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import psycopg2
from dutching import calcula_dutching
import time
import json
from enum import Enum
import re
from datetime import datetime, timedelta
from credenciais import usuario, senha, bwin_id, user_data_dir
from telegram_bot import TelegramBot, TelegramBotErro
from utils import *
from exceptions import ErroCotaForaIntervalo
import asyncio
from match_of_interest import MatchOfInterest, HomeAway
import pickle
from math import floor

class Period(Enum):
    FIRST_HALF = 1
    SECOND_HALF = 2

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
        self.inserted_fixture_ids = []
        self.bet_ids = []
        self.sure_bet_made = False
        self.varios_jogos = True
        self.saldo_inicio_dia = 0.0
        self.aposta_fechada = False
        self.ja_conferiu_resultado = True
        #self.meta_ganho = 0.0
        self.hora_ultima_aposta = ''
        self.perda_acumulada = None
        self.meta_ganho = None
        self.ganhou = False
        self.estilo_jogo = None
        self.qt_apostas_feitas = None
        self.odds = []
        self.odds_clicadas = []
        self.perdas_acumuladas = 0
        self.indice_jogo_atual = 0
        self.qt_jogos_paralelos = None
        # será um dict com : { id_aposta: 'id_aposta', qt_jogos_ganhos: qt_jogos_ganhos, saldo: saldo, ativo: True }
        self.jogos_feitos = []
        self.payout = None
        # aqui vai ser True se o jogo em questão já estiver com mais de um gol de vantagem
        self.id_partida_atual = None
        self.jogo_apostado_em_empate = False
        self.aposta_mesmo_jogo = False
        self.id_partida_apostar_novamente = ''
        self.teste = False
        self.id_partida_anterior = None
        self.next_option_name = ''
        self.aposta_ja_era = False
        self.jogos_de_interesse = set()
        self.next_option_id = ''
        self.segunda_aposta_jogo = True
        self.mercados_restantes = []
        self.pausar_ate = None
        self.payout_jogo_1 = None
        self.payout_jogo_2 = None
        self.payout_jogo_3 = None
        self.payout_jogo_4 = None
        self.controle_acima_abaixo = 1
        self.horario_ultima_checagem = None
        self.times_para_apostas_over = dict()
        self.target_odd = 0.0
        return

    def acessa(self, site):         
        carregou_site = False
        while not carregou_site:
            try:
                self.driver_path = 'chromedriver.exe'
                self.options = Options()
                self.options.add_argument('--ignore-certificate-errors')
                self.options.add_argument('--ignore-ssl-errors')
                self.options.add_argument("--disable-extensions")
                self.options.add_argument("--dns-prefetch-disable")
                self.options.add_argument("--disable-gpu")          
                self.options.add_argument('--no-sandbox')      
                self.options.add_argument("--force-device-scale-factor=0.6")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                self.options.page_load_strategy = 'eager'
                # self.options.add_argument('--disk-cache-size')                
                self.options.add_argument(f"user-data-dir=C:\\Users\\anderson.morais\\AppData\\Local\\Google\\Chrome\\virtual_bet_data\\")    
                self.chrome = webdriver.Chrome( service=ChromeService(executable_path=self.driver_path), options=self.options)
                # definimos quanto um script vai esperar pela resposta
                self.chrome.get(site)
                self.chrome.maximize_window()
                #self.chrome.fullscreen_window()                

                carregou_site = True
            except Exception as e:
                print(e)
                sleep(5)

    def sair(self):
        print('saindo do chrome')
        self.chrome.quit()        
        exit()

    async def get(self, url):
        n_errors = 0
        while True:
            if n_errors == 10:
                try:
                    await self.telegram_bot_erro.envia_mensagem('sistema travado no método get')
                except:
                    pass
            try:
                result = self.chrome.execute_script(url)
                return result
            except:
                n_errors += 1
                self.testa_sessao()
                sleep(1)

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
                        if self.event_url != '':
                            self.chrome.get(self.event_url)
                        else:
                            self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                            self.chrome.maximize_window()
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

                input_login_text = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'userId' )  ))
                input_login_text = input_login_text.get_property('value')                

                input_login = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'userId' )  )) 

                while input_login_text != usuario:
                    input_login.clear()
                    sleep(1)
                    input_login.send_keys(usuario)    

                    input_login_text = WebDriverWait(self.chrome, 10).until(
                        EC.element_to_be_clickable((By.ID, 'userId' )  ))
                    input_login_text = input_login_text.get_property('value')    

                    

                print('achou campo login')

                input_password_text = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.NAME, 'password' )  ))
                input_password_text = input_password_text.get_property('value')
                
                input_password = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.NAME, 'password' )  )) 
                
                while input_password_text != senha:
                    input_password.clear()
                    sleep(1)
                    input_password.send_keys(senha)

                    input_password_text = WebDriverWait(self.chrome, 10).until(
                        EC.element_to_be_clickable((By.NAME, 'password' )  ))
                    input_password_text = input_password_text.get_property('value')

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

                sleep(5)         

                count = 0

                while count < 5:
                    try:
                         # aqui vou tentar buscar algo da API pra ver se logou de verdade
                        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        if not jogos_abertos['summary']['hasError']:
                            print('logou com sucesso')
                            if self.event_url != '':
                                self.chrome.get(self.event_url)
                            else:
                                self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                self.chrome.maximize_window()
                            break
                    except:
                        sleep(3)
                        count += 1

                if count == 5:
                    raise Exception()               

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
                #self.chrome.fullscreen_window()
                print(e)
                if tentativas == 5:
                    self.telegram_bot.envia_mensagem('SISTEMA TRAVADO NO LOGIN')

    def formata_nome_evento( self, nome_time_1, nome_time_2, id_evento ):     
        nome_time_1 = nome_time_1.replace('(', '')
        nome_time_1 = nome_time_1.replace(')', '')
        nome_time_1 = nome_time_1.replace('/', '-')
        nome_time_1 = nome_time_1.replace(' ', '-')
        nome_time_2 = nome_time_2.replace('(', '')
        nome_time_2 = nome_time_2.replace(')', '')
        nome_time_2 = nome_time_2.replace('/', '-')
        nome_time_2 = nome_time_2.replace(' ', '-')
        nome_evento = nome_time_1.lower() + '-' + nome_time_2.lower()
        nome_evento = nome_evento[:48]
        return nome_evento + '-' + id_evento
  
    def le_saldo(self):        
        leu_saldo = False
        contador_de_trava = 0
        while not leu_saldo:
            try:
                saldo_request = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/api/balance?forceFresh=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")
                self.saldo = float(saldo_request['balance']['accountBalance'])
                leu_saldo = True
            except Exception as e:
                sleep(5)
                print(e)
                contador_de_trava += 1
                if contador_de_trava % 10 == 5:
                    self.testa_sessao()
                    self.telegram_bot_erro.envia_mensagem('SISTEMA POSSIVELMENTE TRAVADO AO LER SALDO.')
                    self.chrome.refresh()
                print('Não foi possível ler saldo. Tentando de novo...')

    async def insere_valor(self, id_jogo):
        jogos_abertos = None

        try:
            print('entrou no insere valor')

            if self.valor_aposta < 0.1:
                self.valor_aposta = 0.1

            input_valor = WebDriverWait(self.chrome, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
            input_valor.clear()
            input_valor.send_keys(f'{self.valor_aposta:.2f}')
                        
            sleep(0.2)

            botao_aposta = WebDriverWait(self.chrome, 20).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
            botao_aposta.click()     

            sleep(0.2)

            botao_fechar = WebDriverWait(self.chrome, 60).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions.ng-star-inserted button' ) ))                 
            botao_fechar.click() 

            # while jogos_abertos['summary']['openBetsCount'] == len( self.inserted_fixture_ids ):
            #     jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            #     sleep(5)
            return True     
        except Exception as e:
            print(e)
            self.testa_sessao()
            self.tempo_pausa = 10
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                sleep(0.5)
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')            
            return False

    def testa_sessao(self):
        print('testando sessão...')
        try:
            self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-close-i.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
        except Exception as e:
            print(e)
            print('Erro ao tentar fechar banner')
        try:
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if not jogos_abertos['summary']['hasError']:
                print('sessão ativa')
        except:
            print('sessão expirada. tentando login novamente.')
            try:
                if self.event_url != '':
                    self.chrome.get(self.event_url)
                else:
                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                self.chrome.maximize_window()
                #self.chrome.fullscreen_window()
            except Exception as e:
                print(e)
            finally:
                self.faz_login()

    def placar_mudou(self):
        try:
            placar = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ms-scoreboard .score-counter"))) 
            placar_final = f"{placar[0].get_property('innerText')}:{placar[1].get_property('innerText')}"

            print(placar_final)

            periodo = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ms-scoreboard ms-live-timer"))) 
            
            print(periodo.get_property('innerText'))
            periodo_final = periodo.get_property('innerText').split('•')[0].strip()
            
            if self.bet_type == 0:
                if placar_final != self.placar or periodo_final != self.periodo:
                    return True
            else:
                if periodo_final != self.periodo:
                    return True
            return False        
        except Exception as e:
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')        

            try:
                self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
            except:                        
                print('Erro ao tentar fechar banner')
            try:
                bet = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                bet = bet['betslip']

                if bet['state'] != 'Open':
                    return True
            except:
                self.testa_sessao()
            print(e)
            return False

    async def busca_odds_fim_jogo_sem_gol(self):

        if not await self.is_logged_in():
            self.faz_login()        

        self.apostas_paralelas = self.read_array_from_disk('apostas_paralelas.json')
        self.next_bet_index = self.le_de_arquivo('next_bet_index.txt', 'int')
        self.tempo_pausa = 90
        self.first_message_after_bet = False
        self.bet_slip_number = self.le_de_arquivo('bet_slip_number_2.txt', 'string')                               
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado_2.txt', 'boolean')
        self.varios_jogos = False        
        self.fator_multiplicador = 0.0007723
        self.teste = True        
        self.only_favorites = False
        self.odd_de_corte = 1.25
        self.odd_inferior_para_apostar = 1.25
        self.gastos = self.le_de_arquivo('gastos.txt', 'float')
        self.odd_superior_para_apostar = 1.35
        self.tolerancia_perdas = 6
        self.usar_tolerancia_perdas = False
        self.market_name = None
        self.bet_type = self.le_de_arquivo('bet_type.txt', 'int')
        self.horario_ultima_checagem = datetime.now()
        self.bets_made = dict()
        self.favorite_fixture = self.le_de_arquivo('favorite_fixture_2.txt', 'string')
        self.placar = self.le_de_arquivo('placar_2.txt', 'string')
        self.periodo = self.le_de_arquivo('periodo_2.txt', 'string')
        self.event_url = self.le_de_arquivo('event_url_2.txt', 'string')
        self.numero_erros_global = 0

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                  

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id_2.txt', f'{self.chrome.service.process.pid}', 'w' ) 

        if self.event_url != '':
            try: 
                self.chrome.get( self.event_url )
                self.chrome.maximize_window()

                bet = await self.get(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")                            
                bet = bet['betslip']
                
                if bet != None and bet['state'] != 'Open':
                    self.bet_slip_number = ''
                    self.escreve_em_arquivo('bet_slip_number_2.txt', '', 'w')
                else:
                    print('======== Há apostas em aberto na API =========')
            except Exception as e:
                print('erro ao navegar pro jogo')   

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None
            bet = None

            self.escreve_em_arquivo('last_time_check_2.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            if diferenca_tempo.total_seconds() >= 600:
                if self.bet_slip_number != '':

                    bet = await self.get(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")                            
                    bet = bet['betslip']
                    
                    if bet != None and bet['state'] != 'Open':
                        self.bet_slip_number = ''
                        self.escreve_em_arquivo('bet_slip_number_2.txt', '', 'w')
                    else:
                        print('======== Há apostas em aberto na API =========')
                        
                self.horario_ultima_checagem = datetime.now()
            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')        

            try:
                self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
            except:                        
                print('Erro ao tentar fechar banner')

            try:     
                if self.bet_slip_number != '':     

                    if self.placar_mudou():
                        sleep( 20 )

                        bet = await self.get(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']                        

                        if bet != None and bet['state'] == 'Open':
                            print('======== Há apostas em aberto na API =========')
                            print( datetime.now() )                                                     
                            continue
                    else:
                        print('Há apostas em aberto...')
                        print( datetime.now() )
                        sleep( 10 )                            
                        continue

                try:                                     
                    if not self.ja_conferiu_resultado and not self.varios_jogos and bet != None and bet['state'] != 'Open':                                                        
                        
                        print('Conferindo resultado da última aposta.') 
                        # primeiro verificamos se a última aposta foi vitoriosa                                                    
                        self.bet_slip_number = ''
                        self.escreve_em_arquivo('bet_slip_number_2.txt', '', 'w')

                        self.favorite_fixture = ''
                        self.escreve_em_arquivo('favorite_fixture_2.txt', self.favorite_fixture, 'w')

                        self.event_url = ''
                        self.escreve_em_arquivo('event_url_2.txt', self.event_url, 'w')

                        self.placar = ''
                        self.escreve_em_arquivo('placar_2.txt', self.placar, 'w')

                        self.periodo = ''
                        self.escreve_em_arquivo('periodo_2.txt', self.periodo, 'w')

                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = bet

                        early_payout = ultimo_jogo['isEarlyPayout']

                        if ultimo_jogo['state'] == 'Canceled':

                            print('aposta cancelada')
                            
                            valor_ultima_aposta = float( ultimo_jogo['stake']['value'] )                                    

                            self.apostas_paralelas[self.next_bet_index] = valor_ultima_aposta

                            try:
                                await self.telegram_bot_erro.envia_mensagem(f'Aposta cancelada na pool {self.next_bet_index+1}!') 
                                
                                self.primeiro_alerta_depois_do_jogo = False   
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')      
                            
                        elif ultimo_jogo['state'] == 'Won' and not early_payout:                                 

                            boost_payout = None
                            try:
                                boost_payout = float( ultimo_jogo['bestOddsGuaranteedInformation']['fixedPriceWinnings']['value'] )
                            except:
                                print('sem boost payout')

                            if boost_payout:
                                valor_ganho = boost_payout
                            else:
                                valor_ganho = float( ultimo_jogo['payout']['value'] )

                            self.apostas_paralelas[self.next_bet_index] = valor_ganho

                            try:
                                #if self.saldo > self.saldo_inicio_dia:                                        
                                
                                await self.telegram_bot_erro.envia_mensagem(f'GANHOU na pool {self.next_bet_index+1}! {valor_ganho:.2f}\nLucro das pools: {(sum(self.apostas_paralelas)-self.gastos):.2f}\n{self.apostas_paralelas}') 
                                
                                self.primeiro_alerta_depois_do_jogo = False   

                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')      

                            self.next_bet_index += 1                         
    
                        elif ultimo_jogo['state'] == 'Lost':
                            self.apostas_paralelas[self.next_bet_index] = 1.0    

                            self.gastos += 1.0
                            self.escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')                       

                            try:                                
                                await self.telegram_bot_erro.envia_mensagem(f'Perdeu na pool {self.next_bet_index+1}\nLucro das pools: {(sum(self.apostas_paralelas)-self.gastos):.2f}\n{self.apostas_paralelas}')                                                                         
                            except:
                                pass           

                            self.next_bet_index += 1

                        if self.next_bet_index > len( self.apostas_paralelas ) - 1:
                            self.next_bet_index = 0
                        
                        self.save_array_on_disk('apostas_paralelas.json', self.apostas_paralelas)
                        self.escreve_em_arquivo('next_bet_index.txt', f'{self.next_bet_index}', 'w')

                        self.ja_conferiu_resultado = True
                        self.escreve_em_arquivo('ja_conferiu_resultado_2.txt', 'True', 'w')   
                            
                    
                    fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                    print('\n\n--- chamou fixtures de novo ---')

                    if len( fixtures['fixtures'] ) == 0:
                        print('Sem jogos ao vivo...')
                        print(datetime.now())
                        self.tempo_pausa = 7 * 60
                    else:
                        periodos = set()
                        self.tempo_pausa = 90
                        for fixture in fixtures['fixtures']:                               
                            try:
                                periodos.add( fixture['scoreboard']['period'])

                                if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                    continue

                                cronometro = float(fixture['scoreboard']['timer']['seconds']) // 60

                                nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                
                                fixture_id = fixture['id']
                                name = fixture['name']['value']
                                numero_gols_atual = fixture['scoreboard']['score']      
                                score = fixture['scoreboard']['score']      
                                numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                periodo = fixture['scoreboard']['period']
                                periodId = fixture['scoreboard']['periodId']
                                is_running = fixture['scoreboard']['timer']['running']

                                
                                if periodo.lower() in ['não foi iniciado', 'intervalo', 'suspenso']:
                                    continue

                                resultado_partida = None
                                if '1º' in periodo:
                                    resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado do 1º tempo'] ,fixture['optionMarkets'] ) )
                                elif '2º' in periodo:
                                    resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado do 2º tempo'] ,fixture['optionMarkets'] ) )
                                if resultado_partida:
                                    try:
                                        resultado_partida = resultado_partida[0]
                                        odd_time_1_resultado_partida = float( resultado_partida['options'][0]['price']['odds'] ) 
                                        time_1_resultado_partida_option_id = resultado_partida['options'][0]['id']   
                                        odd_empate_resultado_partida = float( resultado_partida['options'][1]['price']['odds'] ) 
                                        empate_resultado_partida_option_id = resultado_partida['options'][1]['id']                               
                                        odd_time_2_resultado_partida = float( resultado_partida['options'][2]['price']['odds'] )   
                                        time_2_resultado_partida_option_id = resultado_partida['options'][2]['id']   

                                        if odd_time_1_resultado_partida >= self.odd_inferior_para_apostar and odd_time_1_resultado_partida <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][0]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_1_resultado_partida, 'option_id' : time_1_resultado_partida_option_id, 'periodo': periodo })
                                        if odd_time_2_resultado_partida >= self.odd_inferior_para_apostar and odd_time_2_resultado_partida <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][2]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_empate_resultado_partida, 'option_id' : empate_resultado_partida_option_id, 'periodo': periodo })
                                        if odd_empate_resultado_partida >= self.odd_inferior_para_apostar and odd_empate_resultado_partida <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][1]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_2_resultado_partida, 'option_id' : time_2_resultado_partida_option_id, 'periodo': periodo })                               

                                    except:
                                        pass     
                                
                                chance_dupla = None
                                if '1º' in periodo:
                                    chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['1º tempo - chance dupla'] ,fixture['optionMarkets'] ) )
                                elif '2º' in periodo:
                                    chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['2º tempo - chance dupla'] ,fixture['optionMarkets'] ) )
                                if chance_dupla:
                                    try:
                                        chance_dupla = chance_dupla[0]
                                        odd_time_1_chance_dupla = float( chance_dupla['options'][0]['price']['odds'] ) 
                                        time_1_chance_dupla_option_id = chance_dupla['options'][0]['id']                               
                                        odd_time_2_chance_dupla = float( chance_dupla['options'][1]['price']['odds'] )   
                                        time_2_chance_dupla_option_id = chance_dupla['options'][1]['id']   
                                        odd_um_outro_chance_dupla = float( chance_dupla['options'][2]['price']['odds'] )   
                                        um_outro_chance_dupla_option_id = chance_dupla['options'][2]['id']   

                                        if odd_time_1_chance_dupla >= self.odd_inferior_para_apostar and odd_time_1_chance_dupla <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': chance_dupla['name']['value'], 'type': 1, 'score': score, 'option_name': chance_dupla['options'][0]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_1_chance_dupla, 'option_id' : time_1_chance_dupla_option_id, 'periodo': periodo })
                                        if odd_time_2_chance_dupla >= self.odd_inferior_para_apostar and odd_time_2_chance_dupla <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': chance_dupla['name']['value'], 'type': 1, 'score': score, 'option_name': chance_dupla['options'][1]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_2_chance_dupla, 'option_id' : time_2_chance_dupla_option_id, 'periodo': periodo })
                                        if odd_um_outro_chance_dupla >= self.odd_inferior_para_apostar and odd_um_outro_chance_dupla <= self.odd_superior_para_apostar:
                                            jogos_aptos.append({ 'market_name': chance_dupla['name']['value'], 'type': 1, 'score': score, 'option_name': chance_dupla['options'][2]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_um_outro_chance_dupla, 'option_id' : um_outro_chance_dupla_option_id, 'periodo': periodo })
                                    except:
                                        pass                              

                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets: 
                                    market_name = option_market['name']['value']
                                    if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                        if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                                                                        
                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                                        
                                    else:
                                        if market_name.lower() in ['total de gols', 'total goals']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                   

                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                
                                for option_market in option_markets: 
                                    market_name = option_market['name']['value']
                                    if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                        if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                                                                        
                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                                        
                                    else:
                                        if market_name.lower() in ['total de gols', 'total goals']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                   

                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                              
                            except Exception as e:                                    
                                print('erro')                                    
                                print(e)   

                        print('favorite fixture ', self.favorite_fixture)                   

                        for combinacao in array_mensagem_telegram:
                            mensagem_telegram += combinacao['texto']                    

                        print(periodos)

                        jogos_aptos_ordenado = list( sorted(jogos_aptos, key=lambda el: ( el['type'], el['odd'] ) ))

                        if len(jogos_aptos_ordenado) == 0:
                            print('--- SEM JOGOS ELEGÍVEIS ---')

                            print(datetime.now())

                            sleep( self.tempo_pausa)
                            continue                     
                        
                        # caso haja algum jogo no cupom a gente vai tentar limpar
                        try:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            sleep(0.5)
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        except Exception as e:
                            print('Não conseguiu limpar os jogos...')
                            print(e)

                        self.numero_apostas_feitas = 0         

                        for jogo_apto in jogos_aptos_ordenado:        

                            print( jogo_apto )                     

                            if jogo_apto['type'] == 0:
                                bet_made = await self.make_bet_under(jogo_apto)
                            elif jogo_apto['type'] == 1:                                
                                bet_made = await self.make_bet_under(jogo_apto)
                            else:
                                bet_made = await self.make_bet_under(jogo_apto)
                            
                            if bet_made and not self.varios_jogos:

                                nome_evento = jogo_apto['nome_evento']
                                self.event_url = f'https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0'
                                self.escreve_em_arquivo('event_url_2.txt', self.event_url, 'w')

                                self.placar = jogo_apto['score']
                                self.escreve_em_arquivo('placar_2.txt', self.placar, 'w')

                                self.periodo = jogo_apto['periodo']
                                self.escreve_em_arquivo('periodo_2.txt', self.periodo, 'w')

                                self.bet_type = jogo_apto['type']
                                self.escreve_em_arquivo('bet_type.txt', f'{self.bet_type}', 'w')
                                
                                jogo_aberto = None                                       
                                jogos_ja_inseridos.append( f"{jogo_apto['fixture_id']}{jogo_apto['periodo']}" )                                
                                
                                jogo_aberto = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                if len( jogo_aberto['betslips'] ) > 0:
                                    self.bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                    self.escreve_em_arquivo('bet_slip_number_2.txt', self.bet_slip_number, 'w')                        

                                self.ja_conferiu_resultado = False
                                self.escreve_em_arquivo('ja_conferiu_resultado_2.txt', 'False', 'w')

                                self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                       

                                self.primeiro_alerta_depois_do_jogo = True
                                self.primeiro_alerta_sem_jogos_elegiveis = True   

                                odd_corte = float( jogo_apto['odd'] )
                                print( odd_corte )
                                try:
                                    await self.telegram_bot.envia_mensagem(f"Aposta no pool {self.next_bet_index+1} Valor da aposta: R$ {self.valor_aposta:.2f}")                             
                                except Exception as e:
                                    print(e)
                                    print('não foi possível enviar mensagem ao telegram.')
                                break  
                           
                except ErroCotaForaIntervalo as e:
                    # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                    # então vamos excluir tudo no botão da lixeira
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    #quando limpar as apostas o número de apostas feitas vai pra zero
                    self.numero_apostas_feitas = 0
                    deu_erro = True
                    self.tempo_pausa = 1
                    print(e)
                except Exception as e:
                    print('erro laço interno')
                    deu_erro = True
                    self.numero_apostas_feitas = 0
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    self.numero_apostas_feitas = 0
                    print(e)                         
                    self.testa_sessao()
                    self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(30)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                print('erro no laço principal')
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()
    
    async def pools_apostas_simultaneas(self):

        if not await self.is_logged_in():
            self.faz_login()        

        self.apostas_paralelas = self.read_array_from_disk('apostas_paralelas.json')
        self.next_bet_index = self.le_de_arquivo('next_bet_index.txt', 'int')
        self.tempo_pausa = 90
        self.first_message_after_bet = False
        self.bet_slip_number = self.le_de_arquivo('bet_slip_number_2.txt', 'string')                               
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado_2.txt', 'boolean')
        self.varios_jogos = True        
        self.fator_multiplicador = 0.0007723
        self.teste = False        
        self.only_favorites = False
        self.odd_de_corte = 1.2
        self.odd_inferior_para_apostar = 1.2
        self.gastos = self.le_de_arquivo('gastos.txt', 'float')
        self.jogos_inseridos = self.read_array_from_disk('jogos_inseridos.json')
        self.odd_superior_para_apostar = 1.3
        self.tolerancia_perdas = 6
        self.usar_tolerancia_perdas = True        
        self.available_indexes = self.read_array_from_disk('available_indexes.json')
        self.market_name = None
        self.bet_type = self.le_de_arquivo('bet_type.txt', 'int')
        self.horario_ultima_checagem = datetime.now()
        self.bets_made = self.read_set_from_disk('bets_made.pkl')        
        self.favorite_fixture = self.le_de_arquivo('favorite_fixture_2.txt', 'string')
        self.placar = self.le_de_arquivo('placar_2.txt', 'string')
        self.periodo = self.le_de_arquivo('periodo_2.txt', 'string')
        self.event_url = self.le_de_arquivo('event_url_2.txt', 'string')
        self.numero_erros_global = 0
        self.restart_pool = False

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                  

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id_2.txt', f'{self.chrome.service.process.pid}', 'w' )  

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None
            bet = None

            self.escreve_em_arquivo('last_time_check_2.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')        

            try:
                self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
            except:                        
                print('Erro ao tentar fechar banner')

            try:     

                if len( self.bets_made ) > 0:
                    for bet_number, pool_index in self.bets_made.copy().items():

                        print(f'analisando cupom {bet_number} da pool {pool_index+1}')
                        bet = await self.get(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={bet_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']

                        if bet['state'] != 'Open':
                            del self.bets_made[bet_number]
                            self.save_set_on_disk('bets_made.pkl', self.bets_made )

                            try:
                                self.jogos_inseridos.remove(bet['bets'][0]['fixture']['compoundId'])
                            except:
                                pass

                            if bet['state'] == 'Lost':

                                if self.restart_pool:
                                    self.apostas_paralelas[ pool_index ] = 1.0
                                    self.gastos += 1.0

                                    if pool_index not in self.available_indexes:
                                        self.available_indexes.append( pool_index )
                                else:
                                    self.apostas_paralelas[ pool_index ] = 0.0

                                lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                try:
                                    await self.telegram_bot_erro.envia_mensagem(f'perdeu na pool {pool_index+1}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                except:
                                    pass
                                
                            elif bet['state'] == 'Won':

                                boost_payout = None
                                try:
                                    boost_payout = float( bet['bestOddsGuaranteedInformation']['fixedPriceWinnings']['value'] )
                                except:
                                    print('sem boost payout')

                                if boost_payout:
                                    valor_ganho = boost_payout
                                else:
                                    valor_ganho = float( bet['payout']['value'] )
                                
                                self.apostas_paralelas[ pool_index ] = valor_ganho

                                lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                try:
                                    await self.telegram_bot_erro.envia_mensagem(f'ganhou na pool {pool_index+1}\nvalor: {valor_ganho:.2f}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                except:
                                    pass

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   
                            else:
                                valor_ultima_aposta = float( bet['stake']['value'])  
                                self.apostas_paralelas[ pool_index ] = valor_ultima_aposta

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   

                        self.save_array_on_disk('available_indexes.json', self.available_indexes)    
                        self.save_array_on_disk('apostas_paralelas.json', self.apostas_paralelas)

                if self.get_available_index() == -1:
                    print('todas as pools estão ocupadas')
                    sleep(3 * 60)
                    continue                     
                    
                fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                print('\n\n--- chamou fixtures de novo ---')

                if len( fixtures['fixtures'] ) == 0:
                    print('Sem jogos ao vivo...')
                    print(datetime.now())
                    self.tempo_pausa = 7 * 60
                else:
                    periodos = set()
                    self.tempo_pausa = 90
                    for fixture in fixtures['fixtures']:                               
                        try:
                            periodos.add( fixture['scoreboard']['period'])

                            if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                continue

                            cronometro = float(fixture['scoreboard']['timer']['seconds']) // 60

                            nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                            
                            fixture_id = fixture['id']
                            name = fixture['name']['value']
                            numero_gols_atual = fixture['scoreboard']['score']      
                            score = fixture['scoreboard']['score']      
                            numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                            periodo = fixture['scoreboard']['period']
                            periodId = fixture['scoreboard']['periodId']
                            is_running = fixture['scoreboard']['timer']['running']

                            
                            if periodo.lower() in ['não foi iniciado', 'intervalo', 'suspenso']:
                                continue

                            resultado_partida = None
                            if '1º' in periodo:
                                resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado do 1º tempo'] ,fixture['optionMarkets'] ) )
                            elif '2º' in periodo:
                                resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado do 2º tempo'] ,fixture['optionMarkets'] ) )
                            if resultado_partida:
                                try:
                                    resultado_partida = resultado_partida[0]
                                    odd_time_1_resultado_partida = float( resultado_partida['options'][0]['price']['odds'] ) 
                                    time_1_resultado_partida_option_id = resultado_partida['options'][0]['id']   
                                    odd_empate_resultado_partida = float( resultado_partida['options'][1]['price']['odds'] ) 
                                    empate_resultado_partida_option_id = resultado_partida['options'][1]['id']                               
                                    odd_time_2_resultado_partida = float( resultado_partida['options'][2]['price']['odds'] )   
                                    time_2_resultado_partida_option_id = resultado_partida['options'][2]['id']   

                                    if odd_time_1_resultado_partida >= self.odd_inferior_para_apostar and odd_time_1_resultado_partida <= self.odd_superior_para_apostar:
                                        jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][0]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_1_resultado_partida, 'option_id' : time_1_resultado_partida_option_id, 'periodo': periodo })
                                    if odd_time_2_resultado_partida >= self.odd_inferior_para_apostar and odd_time_2_resultado_partida <= self.odd_superior_para_apostar:
                                        jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][2]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_2_resultado_partida, 'option_id' : time_2_resultado_partida_option_id, 'periodo': periodo })
                                    if odd_empate_resultado_partida >= self.odd_inferior_para_apostar and odd_empate_resultado_partida <= self.odd_superior_para_apostar:
                                        jogos_aptos.append({ 'market_name': resultado_partida['name']['value'], 'type': 2, 'score': score, 'option_name': resultado_partida['options'][1]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_empate_resultado_partida, 'option_id' : empate_resultado_partida_option_id, 'periodo': periodo })                               

                                except:
                                    pass     
                            
                            chance_dupla = None
                            if '1º' in periodo:
                                chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['1º tempo - chance dupla'] ,fixture['optionMarkets'] ) )
                            elif '2º' in periodo:
                                chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['2º tempo - chance dupla'] ,fixture['optionMarkets'] ) )
                            if chance_dupla:
                                try:
                                    chance_dupla = chance_dupla[0]
                                    odd_time_1_chance_dupla = float( chance_dupla['options'][0]['price']['odds'] ) 
                                    time_1_chance_dupla_option_id = chance_dupla['options'][0]['id']                               
                                    odd_time_2_chance_dupla = float( chance_dupla['options'][1]['price']['odds'] )   
                                    time_2_chance_dupla_option_id = chance_dupla['options'][1]['id']   

                                    if odd_time_1_chance_dupla >= self.odd_inferior_para_apostar and odd_time_1_chance_dupla <= self.odd_superior_para_apostar and odd_time_1_chance_dupla < odd_time_2_chance_dupla:
                                        jogos_aptos.append({ 'market_name': chance_dupla['name']['value'], 'type': 1, 'score': score, 'option_name': chance_dupla['options'][0]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_1_chance_dupla, 'option_id' : time_1_chance_dupla_option_id, 'periodo': periodo })
                                    if odd_time_2_chance_dupla >= self.odd_inferior_para_apostar and odd_time_2_chance_dupla <= self.odd_superior_para_apostar and odd_time_2_chance_dupla < odd_time_1_chance_dupla:
                                        jogos_aptos.append({ 'market_name': chance_dupla['name']['value'], 'type': 1, 'score': score, 'option_name': chance_dupla['options'][1]['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd_time_2_chance_dupla, 'option_id' : time_2_chance_dupla_option_id, 'periodo': periodo })                                    
                                except:
                                    pass                              

                            option_markets = fixture['optionMarkets']
                            for option_market in option_markets: 
                                market_name = option_market['name']['value']
                                if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                    if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                                                                        
                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                                    
                                else:
                                    if market_name.lower() in ['total de gols', 'total goals']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                   

                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                            
                            for option_market in option_markets: 
                                market_name = option_market['name']['value']
                                if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                    if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                                                                        
                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                                    
                                else:
                                    if market_name.lower() in ['total de gols', 'total goals']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                   

                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                            
                        except Exception as e:                                    
                            print('erro')                                    
                            print(e)   

                    print('favorite fixture ', self.favorite_fixture)                   

                    for combinacao in array_mensagem_telegram:
                        mensagem_telegram += combinacao['texto']                    

                    print(periodos)

                    jogos_aptos_ordenado = list( sorted(jogos_aptos, key=lambda el: ( el['type'], el['odd'] ) ))

                    if len(jogos_aptos_ordenado) == 0:
                        print('--- SEM JOGOS ELEGÍVEIS ---')

                        print(datetime.now())

                        sleep( 2 * 60 )
                        continue                     
                    
                    # caso haja algum jogo no cupom a gente vai tentar limpar
                    try:
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        sleep(0.5)
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    except Exception as e:
                        print('Não conseguiu limpar os jogos...')
                        print(e)

                    self.numero_apostas_feitas = 0         

                    for jogo_apto in jogos_aptos_ordenado:        

                        if jogo_apto['fixture_id'] in self.jogos_inseridos:   
                            print('jogo já inserido')
                            continue  

                        if self.get_available_index() == -1:
                            print('sem pools livres no momento')
                            break  

                        print( jogo_apto )              

                        if jogo_apto['type'] == 0:
                            bet_made = await self.make_bet_under(jogo_apto)
                        elif jogo_apto['type'] == 1:                                
                            bet_made = await self.make_bet_under(jogo_apto)
                        else:
                            bet_made = await self.make_bet_under(jogo_apto)
                        
                        if bet_made:
                                                        
                            jogo_aberto = None                                       
                            self.jogos_inseridos.append( f"{jogo_apto['fixture_id']}" )                                
                            pool_index = None

                            self.save_array_on_disk('jogos_inseridos.json', self.jogos_inseridos)
                            
                            jogo_aberto = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            
                            if len( jogo_aberto['betslips'] ) > 0:
                                bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                pool_index = self.get_available_index()                                
                                print(pool_index)
                                self.bets_made[bet_slip_number] = pool_index   
                                self.save_set_on_disk('bets_made.pkl', self.bets_made )
                                self.available_indexes.remove(pool_index)        
                                self.save_array_on_disk('available_indexes.json', self.available_indexes )

                                print(self.available_indexes)                     

                            self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                       

                            self.primeiro_alerta_depois_do_jogo = True
                            self.primeiro_alerta_sem_jogos_elegiveis = True   

                            try:
                                await self.telegram_bot.envia_mensagem(f"Aposta no pool {pool_index+1} Valor da aposta: R$ {self.valor_aposta:.2f}")                             
                            except Exception as e:
                                print(e)
                                print('não foi possível enviar mensagem ao telegram.')

                            if not self.varios_jogos:
                                break 
                        else:
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                sleep(0.5)
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)
                
                if not deu_erro:
                    sleep( 2 * 60 )
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                print('erro no laço principal')
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()

        
    async def pools_apostas_simultaneas_martingale(self):

        if not await self.is_logged_in():
            self.faz_login()        

        self.apostas_paralelas = self.read_array_from_disk('apostas_paralelas.json')
        self.next_bet_index = self.le_de_arquivo('next_bet_index.txt', 'int')
        self.tempo_pausa = 90
        self.first_message_after_bet = False
        self.bet_slip_number = self.le_de_arquivo('bet_slip_number_2.txt', 'string')                               
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado_2.txt', 'boolean')
        self.varios_jogos = True        
        self.fator_multiplicador = 0.0007723
        self.teste = False        
        self.only_favorites = False
        self.odd_de_corte = 1.6
        self.odd_inferior_para_apostar = 1.6
        self.gastos = self.le_de_arquivo('gastos.txt', 'float')
        self.ganhos = self.le_de_arquivo('ganhos.txt', 'float')
        self.jogos_inseridos = self.read_array_from_disk('jogos_inseridos.json')
        self.odd_superior_para_apostar = 1.75
        self.tolerancia_perdas = 2
        self.maior_lucro_pool = self.le_de_arquivo('maior_lucro_pool.txt', 'float')
        self.usar_tolerancia_perdas = True        
        self.available_indexes = self.read_array_from_disk('available_indexes.json')
        self.market_name = None
        self.bet_type = self.le_de_arquivo('bet_type.txt', 'int')
        self.horario_ultima_checagem = datetime.now()
        self.bets_made = self.read_set_from_disk('bets_made.pkl')        
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.pool_data = self.read_array_from_disk('pool_data.json')        
        self.favorite_fixture = self.le_de_arquivo('favorite_fixture_2.txt', 'string')
        self.placar = self.le_de_arquivo('placar_2.txt', 'string')
        self.periodo = self.le_de_arquivo('periodo_2.txt', 'string')
        self.event_url = self.le_de_arquivo('event_url_2.txt', 'string')
        self.numero_erros_global = 0
        self.restart_pool = False

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                  

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id_2.txt', f'{self.chrome.service.process.pid}', 'w' )  

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None
            bet = None

            self.escreve_em_arquivo('last_time_check_2.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\nlucro: {self.lucro_pool:.2f}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')        

            try:
                self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
            except:                        
                print('Erro ao tentar fechar banner')

            try:     

                if len( self.bets_made ) > 0:
                    for bet_number, pool_index in self.bets_made.copy().items():

                        print(f'analisando cupom {bet_number} da pool {pool_index+1}')
                        bet = await self.get(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslip?betslipId={bet_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']

                        if bet['state'] != 'Open':
                            del self.bets_made[bet_number]
                            self.save_set_on_disk('bets_made.pkl', self.bets_made )

                            try:
                                self.jogos_inseridos.remove(bet['bets'][0]['fixture']['compoundId'])
                            except Exception as e:
                                print(e)

                            self.lucro_pool = 0

                            if bet['state'] == 'Lost':            
                                print('perdeu')

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )

                                self.apostas_paralelas[pool_index] -= float( bet['stake']['value']) 
                                self.save_array_on_disk('apostas_paralelas.json', self.apostas_paralelas)

                                self.pool_data[pool_index]['perda_acumulada'] += float( bet['stake']['value'])                                 

                                self.save_array_on_disk('pool_data.json', self.pool_data)

                                if self.pool_data[pool_index]['qt_apostas_feitas'] == self.tolerancia_perdas:
                                    # diferenca = 5 - self.apostas_paralelas[pool_index]
                                    # if diferenca > 0:
                                    #     self.apostas_paralelas[pool_index] += diferenca
                                    #     self.gastos += diferenca
                                    self.pool_data[pool_index]['qt_apostas_feitas'] = 0
                                    self.pool_data[pool_index]['perda_acumulada'] = 0
                                # if self.pool_data[pool_index]['qt_apostas_feitas'] > 4:
                                #     try:
                                #         await self.telegram_bot.envia_mensagem(f'perdeu {self.pool_data[pool_index]["qt_apostas_feitas"]} na pool {pool_index+1}')
                                #     except Exception as e:
                                #         print(e)

                                self.lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                # try:
                                #     await self.telegram_bot_erro.envia_mensagem(f'perdeu na pool {pool_index+1}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                # except Exception as e:
                                #     print(e)
                                
                            elif bet['state'] == 'Won':
                                print('ganhou')
                                boost_payout = None
                                try:
                                    boost_payout = float( bet['bestOddsGuaranteedInformation']['fixedPriceWinnings']['value'] )
                                except:
                                    print('sem boost payout')

                                if boost_payout:
                                    valor_ganho = boost_payout - float( bet['stake']['value'])  
                                else:
                                    valor_ganho = float( bet['payout']['value'] ) - float( bet['stake']['value'])  
                                
                                self.apostas_paralelas[ pool_index ] += valor_ganho
                                self.pool_data[pool_index]['perda_acumulada'] = 0
                                self.pool_data[pool_index]['qt_apostas_feitas'] = 0

                                self.lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                # try:
                                #     await self.telegram_bot_erro.envia_mensagem(f'ganhou na pool {pool_index+1}\nvalor: {valor_ganho:.2f}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                # except Exception as e:
                                #     print(e)

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   
                            else:
                                print('aposta cancelada')
                                
                                self.pool_data[pool_index]['qt_apostas_feitas'] -= 1

                                # try:
                                #     await self.telegram_bot_erro.envia_mensagem(f'aposta cancelada na pool {pool_index+1}\nvalor: {valor_ganho:.2f}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                # except Exception as e:
                                #     print(e)

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   

                            if self.lucro_pool > self.maior_lucro_pool:
                                self.maior_lucro_pool = self.lucro_pool
                                self.escreve_em_arquivo('maior_lucro_pool.txt', f'{self.maior_lucro_pool:.2f}', 'w')

                                try:
                                    await self.telegram_bot_erro.envia_mensagem(f'aumento no lucro {self.maior_lucro_pool:.2f}')
                                except Exception as e:
                                    print(e)


                        self.save_array_on_disk('available_indexes.json', self.available_indexes)    
                        self.save_array_on_disk('apostas_paralelas.json', self.apostas_paralelas)
                        self.save_array_on_disk('pool_data.json', self.pool_data)
                        self.escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')

                if self.get_available_index() == -1:
                    print('todas as pools estão ocupadas')
                    sleep(3 * 60)
                    continue                     
                    
                fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                print('\n\n--- chamou fixtures de novo ---')

                if len( fixtures['fixtures'] ) == 0:
                    print('Sem jogos ao vivo...')
                    print(datetime.now())
                    self.tempo_pausa = 7 * 60
                else:
                    periodos = set()
                    self.tempo_pausa = 90
                    for fixture in fixtures['fixtures']:                               
                        try:
                            periodos.add( fixture['scoreboard']['period'])

                            if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                continue

                            cronometro = float(fixture['scoreboard']['timer']['seconds']) // 60

                            nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                            
                            fixture_id = fixture['id']
                            name = fixture['name']['value']
                            numero_gols_atual = fixture['scoreboard']['score']      
                            score = fixture['scoreboard']['score']      
                            numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                            periodo = fixture['scoreboard']['period']
                            periodId = fixture['scoreboard']['periodId']
                            is_running = fixture['scoreboard']['timer']['running']

                            
                            if periodo.lower() in ['não foi iniciado', 'intervalo', 'suspenso']:
                                continue
                            
                            option_markets = fixture['optionMarkets']
                            for option_market in option_markets: 
                                market_name = option_market['name']['value']
                                if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                    if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                                                                        
                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                                    
                                else:
                                    if market_name.lower() in ['total de gols', 'total goals']:
                                        for option in option_market['options']:                                                        
                                            if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                odd = float(option['price']['odds'])
                                                option_id = option['id']                                                   

                                                if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                    jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                            
                            
                        except Exception as e:                                    
                            print('erro')                                    
                            print(e)   

                    print('favorite fixture ', self.favorite_fixture)                   

                    for combinacao in array_mensagem_telegram:
                        mensagem_telegram += combinacao['texto']                    

                    print(periodos)

                    jogos_aptos_ordenado = list( sorted(jogos_aptos, key=lambda el: ( el['type'], el['odd'] ) ))

                    if len(jogos_aptos_ordenado) == 0:
                        print('--- SEM JOGOS ELEGÍVEIS ---')

                        print(datetime.now())

                        sleep( 2 * 60 )
                        continue                     
                    
                    # caso haja algum jogo no cupom a gente vai tentar limpar
                    try:
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        sleep(0.5)
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    except Exception as e:
                        print('Não conseguiu limpar os jogos...')
                        print(e)

                    self.numero_apostas_feitas = 0         

                    for jogo_apto in jogos_aptos_ordenado:        

                        if jogo_apto['fixture_id'] in self.jogos_inseridos:   
                            print('jogo já inserido')
                            continue  

                        if self.get_available_index() == -1:
                            print('sem pools livres no momento')
                            break  

                        print( jogo_apto )              

                        if jogo_apto['type'] == 0:
                            bet_made = await self.make_bet_under_martingale(jogo_apto)
                        elif jogo_apto['type'] == 1:                                
                            bet_made = await self.make_bet_under_martingale(jogo_apto)
                        else:
                            bet_made = await self.make_bet_under_martingale(jogo_apto)
                        
                        if bet_made:
                                                        
                            jogo_aberto = None                                       
                            self.jogos_inseridos.append( f"{jogo_apto['fixture_id']}" )                                
                            pool_index = None

                            self.save_array_on_disk('jogos_inseridos.json', self.jogos_inseridos)
                            
                            jogo_aberto = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            
                            if len( jogo_aberto['betslips'] ) > 0:
                                bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                pool_index = self.get_available_index()                                
                                print(pool_index)
                                self.bets_made[bet_slip_number] = pool_index   
                                self.save_set_on_disk('bets_made.pkl', self.bets_made )
                                self.available_indexes.remove(pool_index)        
                                self.save_array_on_disk('available_indexes.json', self.available_indexes )

                                self.pool_data[pool_index]['qt_apostas_feitas'] += 1
                                self.save_array_on_disk('pool_data.json', self.pool_data)

                                print(self.available_indexes)                     

                            self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                       

                            self.primeiro_alerta_depois_do_jogo = True
                            self.primeiro_alerta_sem_jogos_elegiveis = True   

                            # try:
                            #     await self.telegram_bot.envia_mensagem(f"Aposta no pool {pool_index+1} Valor da aposta: R$ {self.valor_aposta:.2f}")                             
                            # except Exception as e:
                            #     print(e)
                            #     print('não foi possível enviar mensagem ao telegram.')

                            if not self.varios_jogos:
                                break 
                        else:
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                sleep(0.5)
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)
                
                if not deu_erro:
                    sleep( 2 * 60 )
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                print('erro no laço principal')
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()


    def get_available_index(self):
        if len( self.available_indexes ) == 0:
            return -1
        return self.available_indexes[0]

    def get_bet_odd(self, option_id):
        print('get_bet_odd')
        cota = None
        #cota2 = None
        try:                   
            cota = WebDriverWait(self.chrome, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "bs-digital-pick-odds > div") )) 
            cota = float( cota.get_property('innerText') )
        except Exception as e:
            print(e)
            print('não consegui pegar a odd do sumário')
            raise Exception('Erro ao capturar odd')

        # try:
        #     cota2 = WebDriverWait(self.chrome, 10).until(
        #                 EC.presence_of_element_located((By.CSS_SELECTOR, f"ms-event-pick[data-test-option-id='{option_id}'] > div > div:nth-child(2)") )) 
        #     cota2 = float( cota2.get_property('innerText') )
        # except Exception as e:
        #     print('não conseguiu pegar odd do ms-event-pick')
        #     raise Exception('Erro ao capturar odd')
        
        if cota == None:
            raise Exception('Odds diferem')
        
        if cota < self.odd_inferior_para_apostar or cota > self.odd_superior_para_apostar:
            print('cota fora do intervalo')
            
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                        

            raise Exception('Odd fora do intervalo')
        
        self.cota = cota
        return cota
    
    def calcula_valor_aposta_martingale(self, cota):
        print('calcula_valor_aposta_martingale')
        self.cota = cota
        print(self.cota)

        try:
            self.valor_aposta = ( self.pool_data[ self.get_available_index() ]['perda_acumulada'] + self.meta_ganho ) / ( cota - 1 )                                      
        except Exception as e:
            print(e)

        if self.teste:
            self.valor_aposta = 0.1

        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')   
    
    def calcula_valor_aposta(self, cota):

        self.cota = cota
        print(self.cota)

        self.valor_aposta = self.apostas_paralelas[ self.get_available_index() ]                                          

        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')        

    async def make_bet_under(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id = jogo_apto['option_id']
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
        except Exception as e:
            print('Não conseguiu limpar os jogos...')
            print(e)

        try:
            
            try: 
                self.chrome.get( f'https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0')
                self.chrome.maximize_window()
                #self.chrome.fullscreen_window()
                
            except Exception as e:
                print('erro ao navegar pro jogo')
                raise e
            # vamos pegar o mercado de resultas                                    

            #quer dizer que o mercado de gols é no primeiro tempo
            clicou = False
            index = 0
            while not clicou and index < 10:
                try:
                    if '1º' in jogo_apto['market_name']:
                        mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()                                                         
                        empate = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True 
                    elif '2º' in jogo_apto['market_name']:                                                
                        mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()                                                       
                        empate = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True       
                    else:                                                                                   
                        empate = WebDriverWait(self.chrome, 10).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True              
                except Exception as e:
                    index += 1                

            if not clicou:
                try:
                    mercado_expandido = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Total de Gols']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                    mercado_expandido.click()
                except:
                    print('sem mercado')
                    return False

                clicou = False
                index = 0
                while not clicou and index < 10:
                    try:
                        if '1º' in jogo_apto['market_name']:
                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()                                                         
                            empate = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True 
                        elif '2º' in jogo_apto['market_name']:                                                
                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()                                                       
                            empate = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True       
                        else:                                                                                   
                            empate = WebDriverWait(self.chrome, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True              
                    except Exception as e:
                        index += 1                      
            
            sleep(1)    

            cota = None
            try:
                cota = self.get_bet_odd(option_id)
            except:
                return False
            
            if cota == None:
                return False

            self.calcula_valor_aposta(cota)

            aposta_feita = await self.insere_valor(None)
            return aposta_feita   
        except:
            return False            

    
    async def make_bet_under_martingale(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id = jogo_apto['option_id']
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
        except Exception as e:
            print('Não conseguiu limpar os jogos...')
            print(e)

        try:
            
            try: 
                self.chrome.get( f'https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0')
                self.chrome.maximize_window()
                #self.chrome.fullscreen_window()
                
            except Exception as e:
                print('erro ao navegar pro jogo')
                raise e
            # vamos pegar o mercado de resultas                                    

            #quer dizer que o mercado de gols é no primeiro tempo
            clicou = False
            index = 0
            while not clicou and index < 10:
                try:
                    if '1º' in jogo_apto['market_name']:
                        mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()                                                         
                        empate = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True 
                    elif '2º' in jogo_apto['market_name']:                                                
                        mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()                                                       
                        empate = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True       
                    else:                                                                                   
                        empate = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                        empate.click()     
                        clicou = True              
                except Exception as e:
                    index += 1                

            if not clicou:
                try:
                    mercado_expandido = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Total de Gols']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                    mercado_expandido.click()
                except:
                    print('sem mercado')
                    return False

                clicou = False
                index = 0
                while not clicou and index < 10:
                    try:
                        if '1º' in jogo_apto['market_name']:
                            mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()                                                         
                            empate = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True 
                        elif '2º' in jogo_apto['market_name']:                                                
                            mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()                                                       
                            empate = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True       
                        else:                                                                                   
                            empate = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                            empate.click()     
                            clicou = True              
                    except Exception as e:
                        index += 1                      
            
            sleep(1)    

            cota = None
            try:
                cota = self.get_bet_odd(option_id)
            except:
                return False
            
            if cota == None:
                return False

            self.calcula_valor_aposta_martingale(cota)

            aposta_feita = await self.insere_valor(None)
            return aposta_feita   
        except:
            return False            


    def le_de_arquivo(self, nome_arquivo, tipo):
        with open(nome_arquivo, 'r') as f:
            if tipo == 'int':
                return int( f.read() )
            elif tipo == 'float':
                return float( f.read() )
            elif tipo == 'boolean':
                valor = f.read()
                return True if valor == 'True' else False
            elif tipo == 'string':
                return f.read()
            
    def escreve_em_arquivo(self, nome_arquivo, valor, tipo_escrita):
        with open(nome_arquivo, tipo_escrita) as f:
            f.write(valor)

    def save_set_on_disk(self, nome_arquivo, my_set):                
        try:
            with open(nome_arquivo, 'wb') as fp:
                pickle.dump(my_set, fp) 
        except:
            print('erro ao salvar dict')
            pass

    def read_set_from_disk(self, nome_arquivo):        
        try:
            with open(nome_arquivo, 'rb') as fp:
                return pickle.load(fp)            
        except Exception as e:
            print(e)
            print('erro ao ler dict')
            return dict()

    def save_array_on_disk(self, nome_arquivo, array):        
        with open(nome_arquivo, "w") as fp:
            json.dump(array, fp)

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list 

    def get_option_id_over(self, fixture_id, option_markets, target_market, target_odd):
        for option_market in option_markets:   
            if option_market['name']['value'].lower() in ['total de gols', 'total goals']:
                for option in option_market['options']:
                    if option['name']['value'] == target_market:      
                        option_id = option['id']                                                                                                                                                                                                                                 
                        self.times_para_apostas_over[fixture_id] = { 'option_id': option_id, 'target_odd': target_odd, 'bet_made': False }
                        return
                    
    def get_option_odd(self, option_markets, option_id):
        for option_market in option_markets:   
            if option_market['name']['value'].lower() in ['total de gols', 'total goals']:
                for option in option_market['options']:
                    if option_id == option['id']:
                        return float(option['price']['odds'])
        return None
    
    def get_market_quantity(self, option_markets):
        count = 0
        for option_market in option_markets:   
            if option_market['name']['value'].lower() in ['total de gols', 'total goals']:
                count += len( option_market['options'] )
        return count

    def get_option_id(self, fixture_id, option_markets, soma_gols):
        try:
            if self.get_market_quantity(option_markets) < 6:                
                return None
            for option_market in option_markets:   
                if option_market['name']['value'].lower() in ['total de gols', 'total goals']:
                    # não apostamos em jogos que não tenham muitos mercados de under e over, pois
                    # a casa pode não nos oferecer o over
                    for option in option_market['options']:
                        if option['name']['value'] == f'Menos de {soma_gols},5':      
                            option_id = option['id']                                                                                                      
                            odd = float(option['price']['odds'])                                                                                                                           
                            return option_id
            return None
        except Exception as e:
            print(e)
            return None

    async def is_logged_in(self):        
        for i in range(3):       
            try:                
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if not jogos_abertos['summary']['hasError']:
                    print('logou com sucesso')
                    return True                
            except:                
                pass
            sleep(1)
        return False

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

    def find_no_goal_odd( self, option_markets, soma_gols ):
        market = list( filter( lambda e: e['name']['value'].lower() == '1º tempo - total de gols', option_markets ) )
        #print(market)
        for m in market:            
            option = list( filter( lambda e: e['name']['value'].lower() == f'menos de {soma_gols},5', m['options'] ) )
            for o in option:
                return [float(o['price']['odds']), o['id'], m['name']['value'].lower()]

        market = list( filter( lambda e: e['name']['value'].lower() == 'total de gols', option_markets ) )
        #print(market)
        for m in market:                
            option = list( filter( lambda e: e['name']['value'].lower() == f'menos de {soma_gols},5', m['options'] ) )
            for o in option:
                return [float(o['price']['odds']), o['id'], m['name']['value'].lower()]
            
        return None

    def find_next_goal_odd_and_option_id( self, option_markets, soma_gols ):        
        market = list( filter( lambda e: e['name']['value'].lower() == '1º tempo - total de gols', option_markets ) )
        #print(market)
        for m in market:            
            option = list( filter( lambda e: e['name']['value'].lower() == f'menos de {soma_gols},5', m['options'] ) )
            for o in option:
                return [float(o['price']['odds']), o['id'], m['name']['value'].lower()]

        market = list( filter( lambda e: e['name']['value'].lower() == 'total de gols', option_markets ) )
        #print(market)
        for m in market:                
            option = list( filter( lambda e: e['name']['value'].lower() == f'menos de {soma_gols},5', m['options'] ) )
            for o in option:
                return [float(o['price']['odds']), o['id'], m['name']['value'].lower()]

        return None                                   

    def find_market(self, option_markets ):       
        for i in range(1, 10, 1):
            market = list( filter( lambda e: e['name']['value'].lower() == f'1º tempo - {i}ª equipe a marcar', option_markets  ) )
            if market != None and len( market ) > 0:
                return market[0]
            if market == None:
                for i in range(1, 10, 1):
                    market = list( filter( lambda e: e['name']['value'].lower() == f'{i}ª equipe a marcar', option_markets  ) )
                    if market != None and len( market ) > 0:
                        return market[0]
        return None

    def save_array_on_disk(self, nome_arquivo, array):        
        with open(nome_arquivo, "w") as fp:
            json.dump(array, fp)

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list              

    async def make_bet(self, nome_evento, option_id ):
        try:            
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        

            self.chrome.get(f"https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0")
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window()    
                                                        
            result = WebDriverWait(self.chrome, 10).until(
            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
            result.click()     
           
            sleep(1)    
                                    
            cota = WebDriverWait(self.chrome, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
            cota = float( cota.get_property('innerText') )

            if cota < 2.8 and cota > 3.9:
                 raise ErroCotaForaIntervalo('cota fora do intervalo')

            self.cota = cota

            self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01                                
            
            self.valor_aposta = 0.1            

            aposta_feita = await self.insere_valor(None)
            return aposta_feita   
        except ErroCotaForaIntervalo as e:
            print(e)
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
            return False
        except Exception as e:
            print('Algo deu errado')                     
            print(e)
            self.testa_sessao()
            try:
                await self.telegram_bot_erro.envia_mensagem(e)
            except:
                pass
            # vou colocar pra voltar pra página inicial
            self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window()
            self.numero_apostas_feitas = 0
            self.tempo_pausa = 10   
            return False             

    async def make_bet_next_score(self, jogo_apto ):
        nome_evento = jogo_apto['nome_evento']
        market_name = jogo_apto['market_name']
        option_id = jogo_apto['option_id']
        try:            
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        

            self.chrome.get(f"https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0")
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window()    

            market_founded = False

            if '1º tempo - ' in market_name.lower():
                clicou = False
                index = 0
                while not clicou:
                    try:
                        mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()  

                        result = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                        result.click() 

                        clicou = True 
                        market_founded = True
                    except IndexError:
                        print('sem mais em aberto')
                        break                        
                    except TimeoutException:
                        index +=1 
                #/ancestor::div[@class='option-group-name clickable'][position() = 1]

                if not market_founded:                

                    option_name_to_expand = market_name
                    try:
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()
                    except:
                        option_name_to_expand = market_name.split('-')[1].strip()
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()

                    clicou = False
                    index = 0
                    while not clicou:
                        try:
                            mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()  

                            result = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                            result.click() 

                            clicou = True 
                        except IndexError:
                            print('sem mais em aberto')
                            break                        
                        except TimeoutException:
                            index +=1 
                        
            elif '2º tempo - ' in market_name.lower():
                clicou = False
                index = 0
                while not clicou:
                    try:
                        mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()  

                        result = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                        result.click() 

                        clicou = True 
                        market_founded = True
                    except IndexError:
                        print('sem mais em aberto')
                        break                        
                    except TimeoutException:
                        index +=1 
                #/ancestor::div[@class='option-group-name clickable'][position() = 1]

                if not market_founded:
                    option_name_to_expand = market_name
                    try:
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()
                    except:
                        option_name_to_expand = market_name.split('-')[1].strip()
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()

                    clicou = False
                    index = 0
                    while not clicou:
                        try:
                            mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                                EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                            #EC.presence_of_all_elements_located  
                            mercado_1_tempo[index].click()  

                            result = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                            result.click() 

                            clicou = True 
                        except IndexError:
                            print('sem mais em aberto')
                            break                        
                        except TimeoutException:
                            index +=1 
            else:
                try:
                    result = WebDriverWait(self.chrome, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                    result.click()
                except TimeoutException:
                    # se não clicar é porque o mercado está oculto, vamos tentar expandi-lo

                    option_name_to_expand = market_name
                    try:
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()
                    except:
                        option_name_to_expand = market_name.split('-')[1].strip()
                        mercado_expandido = WebDriverWait(self.chrome, 2).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{option_name_to_expand}']/ancestor::div[@class='option-group-name clickable'][position() = 1]" ) ))                                         
                        mercado_expandido.click()                

                    result = WebDriverWait(self.chrome, 3).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                    result.click()
             
            sleep(1)                                

            cota = None
            try:
                cota = self.get_bet_odd(option_id)                
            except:
                return False
            
            if cota == None:
                return False

            self.calcula_valor_aposta(cota)                             

            aposta_feita = await self.insere_valor(None)
            return aposta_feita   
        except ErroCotaForaIntervalo as e:
            print(e)
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
            return False
        except Exception as e:
            print('Algo deu errado')                     
            print(e)
            self.testa_sessao()
            try:
                await self.telegram_bot_erro.envia_mensagem(e)
            except:
                pass
            # vou colocar pra voltar pra página inicial
            self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window()
            self.numero_apostas_feitas = 0
            self.tempo_pausa = 10   
            return False             

    async def make_bet_2(self, nome_evento, periodo, option_id):
        try:
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        

            self.chrome.get(f"https://sports.sportingbet.com/pt-br/sports/eventos/{nome_evento}?market=0")
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window() 


            if periodo in ['1º T', '1º Tempo', '1º tempo']:
                clicou = False
                index = 0
                while not clicou:
                    try:
                        mercado_1_tempo = WebDriverWait(self.chrome, 2).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                        #EC.presence_of_all_elements_located  
                        mercado_1_tempo[index].click()  

                        result = WebDriverWait(self.chrome, 2).until(
                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                        result.click() 

                        clicou = True 
                    except IndexError:
                        print('sem mais em aberto')
                        break                        
                    except TimeoutException:
                        index +=1 
            else:
                try:
                    result = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                         
                    result.click() 

                    clicou = True 
                except IndexError:
                    print('sem mais em aberto')                    
                except TimeoutException:
                    index +=1 

            sleep(1)    
                                    
            try:
                cota2 = WebDriverWait(self.chrome, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".betslip-pick-odds__value") )) 
                cota2 = float( cota2.get_property('innerText') )
            except Exception as e:
                print('não conseguiu pegar odd do sumário')
                raise e
            
            print('cota 2 ', cota2)
            
            try:
                cota = WebDriverWait(self.chrome, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"ms-event-pick[data-test-option-id='{option_id}'] > div > div:nth-child(2)") )) 
                cota = float( cota.get_property('innerText') )
            except Exception as e:
                print('não conseguiu pegar odd do ms-event-pick')
                raise e

            print('cota: ', cota)
            
            if cota < self.limite_inferior or cota > self.limite_superior or cota2 < self.limite_inferior or cota2 > self.limite_superior:
                raise Exception('odd fora do intervalo')

            self.cota = cota

            if not self.varios_jogos:
                self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01      

                if self.qt_apostas_feitas_txt > self.tolerancia_perdas - 1:
                    self.valor_aposta = 0.1       
            else:
                self.valor_aposta = self.meta_ganho                   
            
            if self.teste:
                self.valor_aposta = 0.1            

            aposta_feita = await self.insere_valor(None)
            return aposta_feita
        except Exception as e:
            print('Algo deu errado')                     
            print(e)
            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
            sleep(0.5)
            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            self.testa_sessao()
            try:
                await self.telegram_bot_erro.envia_mensagem(e)
            except:
                pass
            # vou colocar pra voltar pra página inicial
            self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
            self.chrome.maximize_window()
            #self.chrome.fullscreen_window()
            self.numero_apostas_feitas = 0
            self.tempo_pausa = 10   
            return False

if __name__ == '__main__':

    try:
        chrome = ChromeAuto(numero_apostas=200, numero_jogos_por_aposta=10)
        chrome.acessa('https://sports.sportingbet.com/pt-br/sports')                    
        asyncio.run( chrome.pools_apostas_simultaneas_martingale() )
    except Exception as e:
        print(e)        
        # chrome.sair()
        # exit()
    # parâmetros: mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria, qt_jogos_paralelos
    #chrome.altas_odds_empate( None, 6, 10, 1, True, False, None )

    #asyncio.run(  )
    #chrome.duas_zebras('Mais de 0,5', 3, 4, 1, True, False, 100.0)
    #chrome.quatro_zebras('Mais de 0,5', 3, 4, 1, True, False, 100.0)