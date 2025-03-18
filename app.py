from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from utils import escreve_em_arquivo, le_de_arquivo
import time
import sys
from enum import Enum
import re
from datetime import datetime, timedelta
from credenciais import usuario, senha, bwin_id, user_data_dir, base_url
from telegram_bot import TelegramBot, TelegramBotErro
from utils import *
from exceptions import ErroCotaForaIntervalo
import asyncio
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
        self.primeiro_alerta_depois_do_jogo = True
        self.numero_erros_global = 0
        self.tempo_pausa = None
        self.primeiro_alerta_sem_jogos_elegiveis = True
        self.numero_apostas_feitas = 0
        self.inserted_fixture_ids = []
        self.bet_ids = []
        self.only_messages = False
        self.sure_bet_made = False
        self.varios_jogos = True
        self.saldo_inicio_dia = 0.0
        self.aposta_fechada = False
        self.ja_conferiu_resultado = True        
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
                self.options.add_argument("--force-device-scale-factor=0.8")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                self.options.page_load_strategy = 'eager'
                # self.options.add_argument('--disk-cache-size')                
                self.options.add_argument(f"user-data-dir={user_data_dir}")    
                
                self.chrome = webdriver.Chrome( service=ChromeService(executable_path=self.driver_path), options=self.options)
                # definimos quanto um script vai esperar pela resposta
                self.chrome.get(site)
                self.chrome.maximize_window()
                #self.chrome.fullscreen_window()                

                carregou_site = True
            except Exception as e:
                print(e)
                sleep(5)

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
                self.numero_erros_global = 0
                return result
            except Exception as e:
                print(e)
                await self.increment_global_errors()            
                n_errors += 1
                await self.testa_sessao()
                sleep(1)

    def faz_logout(self):
        print('fazendo logout')

        try:
            WebDriverWait(self.chrome, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'vn-h-avatar-balance' ))).click()
            
            sleep(1)
            
            WebDriverWait(self.chrome, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'vn-am-logout' ))).click()
        except Exception as e:
            print(e)
            print('Erro ao fazer logout')

    async def faz_login(self):
        print('faz login')

        #return input()
        # preciso verificar se já está logado
        sleep(2)        

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        url_acesso = f'{base_url}/sports'

        tentativas = 0
        fez_login_com_sucesso = False
        while not fez_login_com_sucesso:
            try:
                try:
                    jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                    if jogos_abertos['summary']['liveBetsCount']:
                        print('logou com sucesso')
                        self.numero_erros_global = 0
                        if self.event_url != '':
                            self.navigate_to('https://sports.sportingbet.bet.br/pt-br/sports/minhas-apostas/em-aberto')
                        else:
                            self.navigate_to(f'{base_url}/sports')                            
                        return True
                except Exception as e:
                    await self.increment_global_errors()
                    print('não está logado')
                    if url_acesso == f'{base_url}/sports':
                        url_acesso = f'{base_url}/labelhost/login'
                    else:
                        url_acesso = f'{base_url}/sports'
                    self.navigate_to(url_acesso)  

                vezes_fechar_banner = 0        

                while vezes_fechar_banner < 5:
                    try:
                        self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
                    except Exception as e:
                        print('Erro ao tentar fechar banner')
                        print(e)
                        self.numero_erros_global += 1
                    vezes_fechar_banner += 1
                    sleep(0.5)

                # self.chrome.switch_to.default_content()
                if url_acesso == f'{base_url}/sports':
                    try: 
                        botao_login = WebDriverWait(self.chrome, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, f"a[href='https://www.sportingbet.bet.br/pt-br/labelhost/login']" )  )) 
                        botao_login.click()
                        self.numero_erros_global = 0
                    except Exception as e:
                        await self.increment_global_errors()
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
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'label[for="rememberMe"]' )  ))              
                remember_me.click()

                print('clicou no remember me')

                sleep(1)

                botao_login = WebDriverWait(self.chrome, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="login w-100 btn btn-primary login-v3__login-btn"]' )  )) 
                sleep(1)

                print('achou botaão de login')                
                
                botao_login.click()

                print('clicou no login')              

                sleep(5)         

                count = 0

                while count < 5:
                    try:
                        # aqui vou tentar buscar algo da API pra ver se logou de verdade
                        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        if not jogos_abertos['summary']['hasError']:
                            print('logou com sucesso')
                            self.numero_erros_global = 0                            
                            self.navigate_to('https://sports.sportingbet.bet.br/pt-br/sports/minhas-apostas/em-aberto')                            
                            return True
                    except Exception as e:
                        print(e)
                        await self.increment_global_errors()
                        sleep(3)
                        count += 1

                if count == 5:
                    await self.increment_global_errors()
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
                
                return True
            except Exception as e:
                print('exception no login')
                print(e)                
                await self.increment_global_errors()
                tentativas += 1
                if url_acesso == f'{base_url}/sports':
                    url_acesso = f'{base_url}/labelhost/login'
                else:
                    url_acesso = f'{base_url}/sports'
                self.navigate_to(url_acesso)                                
                
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

    async def insere_valor(self, id_jogo):
        jogos_abertos = None
        self.was_localization_error = False

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

            count = 0
            while count < 15:
                try:
                    WebDriverWait(self.chrome, 1).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.geo-comply-button button") )).click()
                    # se ele achou essa merda é porque foi erro de localização, então vou deslogar e logar de novo
                    self.was_localization_error = True
                    return False
                except:
                    pass

                try:   
                    botao_fechar = WebDriverWait(self.chrome, 1).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions.ng-star-inserted button' ) ))                 
                    botao_fechar.click() 
                    return True
                except:
                    pass
                count += 1
            # while jogos_abertos['summary']['openBetsCount'] == len( self.inserted_fixture_ids ):
            #     jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            #     sleep(5)
            return False
        except Exception as e:
            print(e)
            await self.testa_sessao()
            self.tempo_pausa = 10
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                sleep(0.5)
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')            
            return False

    async def testa_sessao(self):
        print('testando sessão...')
        try:
            self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-close-i.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
        except Exception as e:
            print(e)
            print('Erro ao tentar fechar banner')
        try:
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if not jogos_abertos['summary']['hasError']:
                self.numero_erros_global = 0
                print('sessão ativa')
            
        except:
            await self.increment_global_errors()
            print('sessão expirada. tentando login novamente.')            
            await self.faz_login()

    async def placar_mudou(self):
        try:
            placar = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ms-scoreboard .score-counter"))) 
            placar_final = f"{placar[0].get_property('innerText')}:{placar[1].get_property('innerText')}"

            print(placar_final)

            periodo = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ms-scoreboard ms-live-timer"))) 
            
            print(periodo.get_property('innerText'))
            periodo_final = periodo.get_property('innerText').split('•')[0].strip()
            
            if placar_final != self.placar or periodo_final != self.periodo:
                return True
            return False        
        except Exception as e:
            try:
                bet = self.chrome.execute_script(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                bet = bet['betslip']

                if bet['state'] != 'Open':
                    return True
            except:
                await self.testa_sessao()
            print(e)
            return False

    def navigate_to(self, url):         
        try: 
            self.chrome.get(url)
            self.chrome.maximize_window()
        except Exception as e:
            print(e)
            print('erro ao navegar pro jogo')
            escreve_em_arquivo('last_time_check.txt', 'erro_aposta', 'w' )
            self.chrome.quit()
        
        sleep(3)

        if self.numero_apostas_feitas == 0:
        
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
                self.chrome.execute_script("var botao = document.querySelector('.message-close'); if (botao) { botao.click(); }")                    
            except:                        
                print('Erro ao tentar fechar roleta')
            
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                sleep(1)
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except Exception as e:
                print('Não conseguiu limpar os jogos...')
                print(e)

    async def increment_global_errors(self):
        self.numero_erros_global += 1
        if self.numero_erros_global == 10:
            try:
                await self.telegram_bot_erro.envia_mensagem('SEVERAL ERRORS.')
            except:
                pass
   
    async def true_bets_after_two_greens(self):

        try:
            self.localization_errors = 0
            self.was_localization_error = False
            self.tempo_pausa = 90
            self.times_favoritos = []        
            self.first_message_after_bet = False
            self.ganho_real_a_partir_de_qual_aposta = 3
            self.qt_greens_seguidos = le_de_arquivo('qt_greens_seguidos.txt', 'int')
            self.same_match_bet = le_de_arquivo('same_match_bet.txt', 'boolean')
            self.bet_slip_number = le_de_arquivo('bet_slip_number.txt', 'string')
            self.soma_odds = le_de_arquivo('soma_odds.txt', 'float')
            self.meta_ganho = le_de_arquivo('meta_ganho.txt', 'float')
            self.perda_acumulada = le_de_arquivo('perda_acumulada.txt', 'float')  
            self.qt_apostas = le_de_arquivo('qt_apostas.txt', 'int')
            self.is_bet_lost = le_de_arquivo('is_bet_lost.txt', 'boolean')
            self.maior_saldo = le_de_arquivo('maior_saldo.txt', 'float')
            self.qt_apostas_feitas_txt = le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')
            self.saldo = le_de_arquivo('saldo.txt', 'float')
            self.ja_conferiu_resultado = le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
            self.varios_jogos = False        
            self.meta_progressiva = True
            self.fator_multiplicador = 0.001374
            self.quit_on_next_win = False
            self.teste = False
            self.limite_inferior = 2.8
            self.only_favorites = False
            self.odd_de_corte = 1.5
            self.odd_inferior_para_apostar = 1.5
            self.odd_superior_para_apostar = 1.65
            self.tolerancia_perdas = 6
            self.usar_tolerancia_perdas = False
            self.controle_over_under = le_de_arquivo('controle_over_under.txt', 'int')        
            self.only_men_professional = False
            self.is_for_real = le_de_arquivo('is_for_real.txt', 'boolean')
            self.gastos = le_de_arquivo('gastos.txt', 'float')
            self.ganhos = le_de_arquivo('ganhos.txt', 'float')
            self.market_name = None
            self.horario_ultima_checagem = datetime.now()
            self.bets_made = dict()
            self.ultima_checagem_aposta_aberta = datetime.now()
            self.favorite_fixture = le_de_arquivo('favorite_fixture.txt', 'string')
            self.placar = le_de_arquivo('placar.txt', 'string')
            self.periodo = le_de_arquivo('periodo.txt', 'string')
            self.event_url = le_de_arquivo('event_url.txt', 'string')
            self.qt_vezes_perdida_aposta_1 = le_de_arquivo('qt_vezes_perdida_aposta_1.txt', 'int')
            self.qt_apostas_feitas_1 = le_de_arquivo('qt_apostas_feitas_1.txt', 'int')
            self.qt_true_bets_made = le_de_arquivo('qt_true_bets_made.txt', 'int')
            self.numero_erros_global = 0
            self.maior_meta_ganho = le_de_arquivo('maior_meta_ganho.txt', 'float')
            self.primeiro_alerta_sem_jogos_ao_vivo = True
            numeros_jogos_filtrados = 0
        except Exception as e:
            print(e)
            print('erro ao ler algum arquivo')

        if not await self.is_logged_in():
            await self.faz_login()        

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                   

        if self.meta_ganho == 0:
            self.meta_ganho = self.saldo * self.fator_multiplicador
            escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')

        self.print_info()

        print('proceso do chrome ', self.chrome.service.process.pid)
        escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' ) 

        if self.bet_slip_number != '':            
            try:
                bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                bet = bet['betslip']                
                if bet != None and bet['state'] != 'Open':
                    self.bet_slip_number = ''
                    escreve_em_arquivo('bet_slip_number.txt', '', 'w')
                else:
                    print('======== Há apostas em aberto na API =========')
                    try: 
                        self.navigate_to( self.event_url )                
                    except Exception as e:
                        await self.increment_global_errors()
                        print('Erro ao navegar pro jogo.') 
            except Exception as e:
                print(e)
                await self.increment_global_errors()
                await self.testa_sessao()

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

            escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            diferenca_tempo = datetime.now() - self.ultima_checagem_aposta_aberta
            if diferenca_tempo.total_seconds() >= 300:
                if self.bet_slip_number != '':                                        
                    try:
                        bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']                           
                        if bet != None and bet['state'] != 'Open':
                            self.bet_slip_number = ''
                            escreve_em_arquivo('bet_slip_number.txt', '', 'w')
                        else:
                            print('======== Há apostas em aberto na API =========')
                            self.chrome.refresh()
                    except Exception as e:
                        print(e)
                        await self.testa_sessao()
                    self.ultima_checagem_aposta_aberta = datetime.now()

            try:     
                if self.bet_slip_number != '':     

                    if await self.placar_mudou():
                        sleep( 20 )
                        leu_bet = False
                        while not leu_bet:
                            try:
                                bet = self.chrome.execute_script(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                                bet = bet['betslip']
                                leu_bet = True
                            except:                                
                                await self.testa_sessao()
                                sleep(10)

                        if bet != None and bet['state'] == 'Open':
                            print('======== Há apostas em aberto na API =========')                            
                            print( datetime.now() )                                
                            self.chrome.refresh()                     
                            continue
                    else:
                        self.continuar_na_sessao_click()
                        print('Há apostas em aberto...')
                        print( datetime.now() )
                        sleep( 10 )                            
                        continue

                try:                                     
                    if not self.ja_conferiu_resultado and not self.varios_jogos and bet != None and bet['state'] != 'Open':                                                        

                        mensagem_telegram = 'Perdeu.'
                        
                        print('Conferindo resultado da última aposta.')
                        self.ja_conferiu_resultado = True
                        escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')    
                        # primeiro verificamos se a última aposta foi vitoriosa                                                    
                        self.bet_slip_number = ''
                        escreve_em_arquivo('bet_slip_number.txt', '', 'w')

                        if self.usar_tolerancia_perdas and self.qt_apostas_feitas_txt % self.tolerancia_perdas == 0 and self.qt_apostas_feitas_txt != 0:
                            self.perda_acumulada = 0.0
                            escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                        self.favorite_fixture = ''
                        escreve_em_arquivo('favorite_fixture.txt', self.favorite_fixture, 'w')

                        self.event_url = ''
                        escreve_em_arquivo('event_url.txt', self.event_url, 'w')

                        self.placar = ''
                        escreve_em_arquivo('placar.txt', self.placar, 'w')

                        self.periodo = ''
                        escreve_em_arquivo('periodo.txt', self.periodo, 'w')

                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = bet

                        early_payout = ultimo_jogo['isEarlyPayout']

                        if ultimo_jogo['state'] == 'Canceled':

                            mensagem_telegram = 'Aposta cancelada.'

                            print('aposta cancelada')

                            if self.is_for_real:
                                self.qt_true_bets_made -= 1
                                escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                            self.qt_apostas_feitas_txt -= 1
                            escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')
                            
                            valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                            self.perda_acumulada -= valor_ultima_aposta      
                            escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                            self.saldo += valor_ultima_aposta
                            escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')                                                                                             
                            
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

                            self.saldo += valor_ganho
                            escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w') 

                            self.controle_over_under = 0
                            escreve_em_arquivo('controle_over_under.txt', '0', 'w')


                            if self.is_for_real:
                                self.qt_true_bets_made = 0
                                escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')                     

                            self.qt_greens_seguidos += 1
                            escreve_em_arquivo('qt_greens_seguidos.txt', f'{self.qt_greens_seguidos}', 'w')

                            self.perda_acumulada -= valor_ganho                                    

                            if self.perda_acumulada < 0:
                                self.perda_acumulada = 0

                            escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')          

                            if self.meta_progressiva and self.is_for_real:
                                self.meta_ganho = self.saldo * self.fator_multiplicador 
                                escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                
                                print(f'Meta de ganho: R$ {self.meta_ganho:.2f}')   
                                                       
                            mensagem_telegram = f"GANHOU. \n{self.saldo:.2f} Meta de ganho: {self.meta_ganho:.2f}"                            

                            if self.quit_on_next_win:     
                                try:
                                    #if self.saldo > self.saldo_inicio_dia:                                        
                                    
                                    await self.telegram_bot_erro.envia_mensagem(f'{mensagem_telegram}! {self.saldo:.2f}\nSaindo...')                                      

                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')  
                                escreve_em_arquivo('last_time_check.txt', 'sair', 'w' )
                                self.chrome.quit()
                                exit()                             

                            self.qt_apostas_feitas_txt = 0
                            escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w') 
                        
                        elif ultimo_jogo['state'] == 'Lost':
                            self.qt_greens_seguidos = 0
                            escreve_em_arquivo('qt_greens_seguidos.txt', '0', 'w')

                        
                        try:
                            await self.telegram_bot_erro.envia_mensagem(mensagem_telegram)                                      
                        except Exception as e:
                            print(e)
                            print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---') 
                
                    fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                    print('\n\n--- chamou fixtures de novo ---')

                    self.maior_odd = 0.0
                    self.maior_odd_corte = 0.0

                    if len( fixtures['fixtures'] ) == 0:
                        print('Sem jogos ao vivo...')
                        print(datetime.now())                      
                        if self.primeiro_alerta_sem_jogos_ao_vivo:
                            try:                           
                                await self.telegram_bot.envia_mensagem('Sem jogos ao vivo.')                                      
                                self.primeiro_alerta_sem_jogos_ao_vivo = False    
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                         
                        sleep(5 * 60)
                    else:
                        periodos = set()
                        self.tempo_pausa = 90
                        for fixture in fixtures['fixtures']:                               
                            try:
                                periodos.add( fixture['scoreboard']['period'])

                                if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                    continue

                                nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                
                                fixture_id = fixture['id']
                                name = fixture['name']['value']
                                numero_gols_atual = fixture['scoreboard']['score']      
                                score = fixture['scoreboard']['score']      
                                numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                periodo = fixture['scoreboard']['period']
                                periodId = fixture['scoreboard']['periodId']
                                is_running = fixture['scoreboard']['timer']['running']

                                cronometro = float(fixture['scoreboard']['timer']['seconds']) // 60

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
                                                    # [float(o['price']['odds']), o['id'], m['name']['value'].lower()]
                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                        #mercado_over = self.find_no_goal_odd( option_markets, numero_gols_atual )
                                                        
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                    else:
                                        if market_name.lower() in ['total de gols', 'total goals']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Mais de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                   

                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                        #mercado_over = self.find_no_goal_odd( option_markets, numero_gols_atual )                                                        
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })

                            except Exception as e:                                    
                                print('erro')                                    
                                print(e)   

                        print('favorite fixture ', self.favorite_fixture)                   

                        for combinacao in array_mensagem_telegram:
                            mensagem_telegram += combinacao['texto']                    

                        print(periodos)

                        jogos_aptos_ordenado = list( sorted(jogos_aptos, key=lambda el: ( el['type'], -el['odd'] ) ))

                        if len(jogos_aptos_ordenado) == 0:
                            print('--- SEM JOGOS ELEGÍVEIS ---')

                            print(datetime.now())
                            if self.primeiro_alerta_sem_jogos_elegiveis:
                                try:
                                    await self.telegram_bot.envia_mensagem("Sem jogos elegíveis.")                             
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                except Exception as e:
                                    print(e)
                                    print('Não foi possível enviar mensagem ao telegram.')

                            sleep( self.tempo_pausa)
                            continue                     
                        
                        # caso haja algum jogo no cupom a gente vai tentar limpar
                        try:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            sleep(1)
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        except Exception as e:
                            print('Não conseguiu limpar os jogos...')
                            print(e)

                        self.numero_apostas_feitas = 0                                 

                        tentar_mesmo_jogo = False

                        qt_jogos_aptos = len( jogos_aptos_ordenado)
                        index = 0

                        while index < qt_jogos_aptos:
                            
                            jogo_apto = jogos_aptos_ordenado[index]

                            print( jogo_apto )                     

                            bet_made = False

                            if jogo_apto['type'] in [0, 1]:
                                bet_made = await self.make_bet_under_atg(jogo_apto)
                            
                            if bet_made and not self.varios_jogos:

                                self.localization_errors = 0
                                
                                self.controle_over_under += 1
                                escreve_em_arquivo('controle_over_under.txt', f'{self.controle_over_under}', 'w')

                                nome_evento = jogo_apto['nome_evento']
                                self.event_url = f'{base_url}/sports/eventos/{nome_evento}?market=3'
                                escreve_em_arquivo('event_url.txt', self.event_url, 'w')

                                self.placar = jogo_apto['score']
                                escreve_em_arquivo('placar.txt', self.placar, 'w')

                                self.periodo = jogo_apto['periodo']
                                escreve_em_arquivo('periodo.txt', self.periodo, 'w')

                                
                                jogo_aberto = None                                       
                                jogos_ja_inseridos.append( f"{jogo_apto['fixture_id']}{jogo_apto['periodo']}" )
                                bet = None
                                
                                jogo_aberto = await self.get(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                if len( jogo_aberto['betslips'] ) > 0:
                                    self.bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                    escreve_em_arquivo('bet_slip_number.txt', self.bet_slip_number, 'w')                                                                                        

                                    bet = jogo_aberto['betslips'][0]       
                                    
                                self.qt_apostas_feitas_txt += 1
                                escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')  

                                if self.qt_apostas_feitas_txt == 1:
                                    self.qt_apostas_feitas_1 += 1
                                    escreve_em_arquivo('qt_apostas_feitas_1.txt', f'{self.qt_apostas_feitas_1}', 'w')

                                self.qt_apostas += 1
                                escreve_em_arquivo('qt_apostas.txt', f'{self.qt_apostas}', 'w') 

                                self.soma_odds += self.cota
                                escreve_em_arquivo('soma_odds.txt', f'{self.soma_odds}', 'w')                                

                                self.ja_conferiu_resultado = False
                                escreve_em_arquivo('ja_conferiu_resultado.txt', 'False', 'w')

                                self.gastos += self.valor_aposta
                                escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')

                                if self.is_for_real:
                                    self.qt_true_bets_made += 1
                                    escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                                self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                                                          

                                self.saldo -= self.valor_aposta
                                escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
                                
                                self.is_bet_lost = False

                                self.saldo_antes_aposta = self.saldo
                                escreve_em_arquivo('saldo_antes_aposta.txt', f'{self.saldo:.2f}', 'w')

                                self.perda_acumulada += self.valor_aposta
                                escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                                self.primeiro_alerta_depois_do_jogo = True
                                self.primeiro_alerta_sem_jogos_elegiveis = True   
                                self.primeiro_alerta_sem_jogos_ao_vivo = True

                                try:
                                    await self.telegram_bot.envia_mensagem(f"Valor: R$ {self.valor_aposta:.2f} True bets: {self.qt_true_bets_made}")                             
                                except Exception as e:
                                    print(e)
                                    print('Não foi possível enviar mensagem ao telegram.')                               

                                if not self.varios_jogos:
                                    break

                            elif not bet_made and not self.varios_jogos:
                                try:                                   

                                    if self.was_localization_error:
                                        tentar_mesmo_jogo = True

                                        self.localization_errors += 1
                                    else:
                                        index += 1

                                    if self.localization_errors > 3:
                                        self.faz_logout()

                                        sleep(1)
                                        self.numero_apostas_feitas = 0
                                        escreve_em_arquivo('last_time_check.txt', 'erro_aposta', 'w' )
                                        self.chrome.quit()
                                        exit()
                                except Exception as e:
                                    # não achou o elemento, deve ter sido outro erro qualquer, não vou sair
                                    print(e)
                                    tentar_mesmo_jogo = False                                    
                                    index += 1

                                
                           
                except ErroCotaForaIntervalo as e:
                    # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                    # então vamos excluir tudo no botão da lixeira
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    sleep(1)
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    #quando limpar as apostas o número de apostas feitas vai pra zero
                    self.numero_apostas_feitas = 0
                    deu_erro = True
                    self.tempo_pausa = 1
                    print(e)
                except Exception as e:
                    print('erro laço interno')
                    deu_erro = True                    
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    sleep(1)
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    self.numero_apostas_feitas = 0
                    print(e)                         
                    await self.testa_sessao()
                    self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(30)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                await self.testa_sessao()
            except Exception as e:
                print('erro no laço principal')
                self.numero_apostas_feitas = 0
                print(e)
                await self.testa_sessao()

    def continuar_na_sessao_click(self):
        try:
            botao = WebDriverWait(self.chrome, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Continuar na Sessão']")))
            botao.click()
        except:
            print('não achou continuar na sessão')         

    def print_info(self):
        print(f"Meta de ganho: {self.meta_ganho:.2f}")
        print(f"Quantidade de apostas feitas: {self.qt_apostas_feitas_txt}")
        print(f"Qt true bets made: {self.qt_true_bets_made}")
        print(f"Qt greens seguidos: {self.qt_greens_seguidos}")
        print(f"Perda acumulada: {self.perda_acumulada:.2f}")
        print(f"Saldo: {self.saldo:.2f}")

    def get_bet_odd(self, option_id):
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
        
        if cota == None:
            raise Exception('Odds diferem')
        
        self.cota = cota
        return cota
            
    def calcula_valor_aposta_atg(self, cota):

        self.cota = cota

        if self.qt_greens_seguidos == 2 and self.qt_true_bets_made == 0:
            self.perda_acumulada = 0.0
            escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

        self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01 

        if self.qt_greens_seguidos >= 2:
            self.is_for_real = True
        else:
            self.is_for_real = False
            self.valor_aposta = 0.1                                                   

        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')           

        escreve_em_arquivo('is_for_real.txt', f'{self.is_for_real}', 'w')        

        if self.teste or self.valor_aposta > self.saldo:
            self.valor_aposta = 0.1
    
    async def make_bet_under_atg(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id = jogo_apto['option_id']
        period = jogo_apto['periodo']

        try:
            self.navigate_to(f'{base_url}/sports/eventos/{nome_evento}?market=3')

            if period == '1º T':
                clicou = False
                index = 0
                while not clicou and index < 3:
                    try:                    
                        mercado_1_tempo = WebDriverWait(self.chrome, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::div/ancestor::li"))) 
                        mercado_1_tempo[index].click()                                                            
                        break                 
                    except Exception as e:
                        print(e)                         

                    try:                    
                        mercado_1_tempo = WebDriverWait(self.chrome, 5).until(
                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1st Half']/ancestor::div/ancestor::li"))) 
                        mercado_1_tempo[index].click()                                                            
                        break                 
                    except Exception as e:
                        print(e)
                        index += 1   
                

            odd = WebDriverWait(self.chrome, 5).until(
                EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]/descendant::span' ) ))
            
            # vou tentar converter pra inteiro pra ver se o mercado está disponível
            try:
                float( odd.get_property('innerText'))
            except Exception as e:
                print(e)
                return False

            clicou = False
            index = 0
            while not clicou and index < 5:
                try:                                                                                                                        
                    empate = WebDriverWait(self.chrome, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                                 
                    empate.click()     
                    break                   
                except Exception as e:
                    index += 1                   
            
            sleep(0.5)    

            cota = None
            try:
                cota = self.get_bet_odd(option_id)
                if cota < self.odd_inferior_para_apostar or cota > self.odd_superior_para_apostar:
                    print('cota fora do intervalo')
                    return False
            except:
                return False
            
            if cota == None:
                return False

            self.calcula_valor_aposta_atg(cota)

            aposta_feita = await self.insere_valor(None)
            return aposta_feita   
        except:
            return False            
   
    async def is_logged_in(self):        
        for i in range(3):       
            try:                
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if not jogos_abertos['summary']['hasError']:
                    print('Está logado.')
                    return True                
            except:                
                pass
            sleep(1)
        return False

if __name__ == '__main__':

    print(sys.argv)

    try:
        chrome = ChromeAuto(numero_apostas=200, numero_jogos_por_aposta=10)
        if '-om' in sys.argv:
            chrome.only_messages = True
        escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )
        chrome.acessa(f'{base_url}/sports')                    
        asyncio.run( chrome.true_bets_after_two_greens() )
    except Exception as e:
        print(e)