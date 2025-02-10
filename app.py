from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pause
from dutching import calcula_dutching
import time
import json
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

    def qt_apostas_restantes(self, meta_ganho, perda_acumulada, banca, odd):
        qt_apostas = 0
        banca_restante = banca
        
        valor_aposta = ( meta_ganho + perda_acumulada ) / (odd-1) if ( meta_ganho + perda_acumulada ) / (odd-1) >= 0.1 else 0.1

        while valor_aposta <= banca_restante:            
            qt_apostas += 1
            perda_acumulada += valor_aposta
            banca_restante -= valor_aposta
            valor_aposta = ( meta_ganho + perda_acumulada ) / (odd-1) if ( meta_ganho + perda_acumulada ) / (odd-1) >= 0.1 else 0.1

        return qt_apostas

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
                self.numero_erros_global = 0
                return result
            except Exception as e:
                print(e)
                await self.increment_global_errors()            
                n_errors += 1
                await self.testa_sessao()
                sleep(1)

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
                        return
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
                    sleep(1)

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

                # remember_me = WebDriverWait(self.chrome, 10).until(
                #     EC.element_to_be_clickable((By.ID, 'rememberMe' )  ))
                # remember_me.click()

                # print('clicou no remember me')

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
                            if self.event_url != '':
                                self.navigate_to('https://sports.sportingbet.bet.br/pt-br/sports/minhas-apostas/em-aberto')
                            else:
                                self.navigate_to(f'{base_url}/sports')                                
                            break
                    except:
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

            except Exception as e:
                print('erro aleatório')
                await self.increment_global_errors()
                tentativas += 1
                if url_acesso == f'{base_url}/sports':
                    url_acesso = f'{base_url}/labelhost/login'
                else:
                    url_acesso = f'{base_url}/sports'
                self.navigate_to(url_acesso)                                
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
  
    async def le_saldo(self):        
        leu_saldo = False
        contador_de_trava = 0
        while not leu_saldo:
            try:
                saldo = WebDriverWait(self.chrome, 20).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'user-balance') ))
                saldo = saldo.get_property('innerText')
                numeros = re.findall( r"\d+", saldo )
                if len(numeros) == 2:
                    self.saldo = float(  f'{numeros[0]}.{numeros[1]}' )
                elif len(numeros) == 3:
                    self.saldo = float( f'{numeros[0]}{numeros[1]}.{numeros[2]}' )
                print('saldo ', self.saldo)
                leu_saldo = True
            except Exception as e:
                sleep(5)
                print(e)
                contador_de_trava += 1
                if contador_de_trava % 10 == 5:
                    await self.testa_sessao()
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
            #     jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            #     sleep(5)
            return True     
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

    async def bet_lost(self):
        try:
            placares = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "ms-stats-value > div:last-child")))
            periodos = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.mybets-scoreboard_info-period-info")))
            p_jogo_1, p_jogo_2, p_jogo_3 = [ p.get_property('innerText') for p in periodos]
            
            if '1' in p_jogo_1:
                if int( placares[0].get_property('innerText') ) + int( placares[1].get_property('innerText') ) > 2:
                    return True 
            if '1' in p_jogo_2:
                if int( placares[2].get_property('innerText') ) + int( placares[3].get_property('innerText') ) > 2:
                    return True 
            if '1' in p_jogo_3:
                if int( placares[4].get_property('innerText') ) + int( placares[5].get_property('innerText') ) > 2:
                    return True 
            return False
        except Exception as e:
            return False
            print(e)

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
            print('erro ao navegar pro jogo')
            raise e
        
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

    async def busca_odds_fim_jogo_sem_gol(self):

        self.tempo_pausa = 90
        self.times_favoritos = []        
        self.first_message_after_bet = False
        self.same_match_bet = self.le_de_arquivo('same_match_bet.txt', 'boolean')
        self.bet_slip_number = self.le_de_arquivo('bet_slip_number.txt', 'string')
        self.soma_odds = self.le_de_arquivo('soma_odds.txt', 'float')
        self.qt_apostas = self.le_de_arquivo('qt_apostas.txt', 'int')
        self.is_bet_lost = self.le_de_arquivo('is_bet_lost.txt', 'boolean')
        self.maior_saldo = self.le_de_arquivo('maior_saldo.txt', 'float')
        self.saldo = self.le_de_arquivo('saldo.txt', 'float')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
        self.varios_jogos = False        
        self.meta_progressiva = True
        self.fator_multiplicador = 0.00138
        self.quit_on_next_win = False
        self.teste = False
        self.limite_inferior = 2.8
        self.only_favorites = False
        self.odd_de_corte = 1.5
        self.odd_inferior_para_apostar = 1.5
        self.odd_superior_para_apostar = 1.65
        self.tolerancia_perdas = 6
        self.usar_tolerancia_perdas = False
        self.controle_over_under = self.le_de_arquivo('controle_over_under.txt', 'int')        
        self.only_men_professional = False
        self.is_for_real = self.le_de_arquivo('is_for_real.txt', 'boolean')
        self.gastos = self.le_de_arquivo('gastos.txt', 'float')
        self.ganhos = self.le_de_arquivo('ganhos.txt', 'float')
        self.market_name = None
        self.horario_ultima_checagem = datetime.now()
        self.bets_made = dict()
        self.ultima_checagem_aposta_aberta = datetime.now()
        self.favorite_fixture = self.le_de_arquivo('favorite_fixture.txt', 'string')
        self.placar = self.le_de_arquivo('placar.txt', 'string')
        self.periodo = self.le_de_arquivo('periodo.txt', 'string')
        self.event_url = self.le_de_arquivo('event_url.txt', 'string')
        self.qt_vezes_perdida_aposta_1 = self.le_de_arquivo('qt_vezes_perdida_aposta_1.txt', 'int')
        self.qt_apostas_feitas_1 = self.le_de_arquivo('qt_apostas_feitas_1.txt', 'int')
        self.qt_true_bets_made = self.le_de_arquivo('qt_true_bets_made.txt', 'int')
        self.numero_erros_global = 0
        self.maior_meta_ganho = self.le_de_arquivo('maior_meta_ganho.txt', 'float')
        self.primeiro_alerta_sem_jogos_ao_vivo = True
        numeros_jogos_filtrados = 0

        if not await self.is_logged_in():
            await self.faz_login()        

        await self.le_saldo()
        # print('saldo: ', self.saldo)

        #self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')

        try:
            self.times_favoritos = self.read_array_from_disk('times_favoritos.json')
        except Exception as e:
            print(e)
            print('erro ao ler array')            
        message_already_sent = []
        self.times_pra_apostar = []          
        matches = []       
        matches_and_options = dict()
        try: 
            with open('matches_and_options.pkl', 'rb') as fp:
                matches_and_options = pickle.load(fp)
        except:
            print('erro ao ler arquivo')
        fixture_id_to_betslip = dict()
        try:
            with open('fixture_id_to_betslip.pkl', 'rb' ) as fp:
                fixture_id_to_betslip = pickle.load(fp)
        except:
            print('erro ao ler arquivo')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.qt_apostas_feitas_txt = self.le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')        

        if self.meta_ganho == 0:
            self.meta_ganho = self.saldo * self.fator_multiplicador
            self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')

        print(f'Meta de ganho: R$ {self.meta_ganho:.2f}')

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' ) 

        if self.event_url != '':            
            try:
                bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                bet = bet['betslip']                
                if bet != None and bet['state'] != 'Open':
                    self.bet_slip_number = ''
                    self.escreve_em_arquivo('bet_slip_number.txt', '', 'w')
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

            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

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
                            self.escreve_em_arquivo('bet_slip_number.txt', '', 'w')
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
                        print('Há apostas em aberto...')
                        print( datetime.now() )
                        sleep( 10 )                            
                        continue

                try:                                     
                    if not self.ja_conferiu_resultado and not self.varios_jogos and bet != None and bet['state'] != 'Open':                                                        

                        if not self.aposta_mesmo_jogo:
                            print('Conferindo resultado da última aposta.')
                            self.ja_conferiu_resultado = True
                            self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')    
                            # primeiro verificamos se a última aposta foi vitoriosa                                                    
                            self.bet_slip_number = ''
                            self.escreve_em_arquivo('bet_slip_number.txt', '', 'w')

                            if self.usar_tolerancia_perdas and self.qt_apostas_feitas_txt % self.tolerancia_perdas == 0 and self.qt_apostas_feitas_txt != 0:
                                self.perda_acumulada = 0.0
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                            self.favorite_fixture = ''
                            self.escreve_em_arquivo('favorite_fixture.txt', self.favorite_fixture, 'w')

                            self.event_url = ''
                            self.escreve_em_arquivo('event_url.txt', self.event_url, 'w')

                            self.placar = ''
                            self.escreve_em_arquivo('placar.txt', self.placar, 'w')

                            self.periodo = ''
                            self.escreve_em_arquivo('periodo.txt', self.periodo, 'w')

                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = bet

                            early_payout = ultimo_jogo['isEarlyPayout']

                            if ultimo_jogo['state'] == 'Canceled':

                                print('aposta cancelada')

                                if self.is_for_real:
                                    self.qt_true_bets_made -= 1
                                    self.escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                                if self.qt_apostas_feitas_txt == 1:
                                    self.qt_apostas_feitas_1 -= 1
                                    self.escreve_em_arquivo('qt_apostas_feitas_1.txt', f'{self.qt_apostas_feitas_1}', 'w')

                                self.qt_apostas_feitas_txt -= 1
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')
                                
                                valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                                self.perda_acumulada -= valor_ultima_aposta      
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                                self.saldo += valor_ultima_aposta
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')                                                                 

                                self.valor_aposta -= self.perda_acumulada                                    

                                
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
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w') 

                                self.controle_over_under = 0
                                self.escreve_em_arquivo('controle_over_under.txt', '0', 'w')

                                # if self.qt_apostas_feitas_txt == 1 or self.is_for_real:
                                #     self.qt_vezes_perdida_aposta_1 = 0
                                #     self.escreve_em_arquivo('qt_vezes_perdida_aposta_1.txt', f'{self.qt_vezes_perdida_aposta_1}', 'w')

                                self.perda_acumulada -= valor_ganho                                    

                                if self.perda_acumulada < 0:
                                    self.perda_acumulada = 0

                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')          

                                if self.meta_progressiva and self.is_for_real:
                                    self.meta_ganho = self.saldo * self.fator_multiplicador     

                                    if self.meta_ganho > self.maior_meta_ganho:                           
                                        self.maior_meta_ganho = self.meta_ganho
                                        self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                
                                        print(f'Meta de ganho: R$ {self.meta_ganho:.2f}')
                                        self.escreve_em_arquivo('maior_meta_ganho.txt', f'{self.maior_meta_ganho:.2f}', 'w')                                

                                texto_mensagem = "RECUPEROU"

                                if self.saldo > self.maior_saldo:
                                    texto_mensagem = "GANHOU"
                                    self.maior_saldo = self.saldo
                                    self.escreve_em_arquivo('maior_saldo.txt', f'{self.maior_saldo:.2f}', 'w') 

                                    if self.quit_on_next_win:     
                                        try:
                                            #if self.saldo > self.saldo_inicio_dia:                                        
                                            
                                            await self.telegram_bot_erro.envia_mensagem(f'{texto_mensagem}! {self.saldo:.2f}\nSaindo...')                                      

                                        except Exception as e:
                                            print(e)
                                            print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')  
                                        self.escreve_em_arquivo('last_time_check.txt', 'sair', 'w' )
                                        self.chrome.quit()
                                        exit() 

                                if self.qt_apostas_feitas_txt in [1, 2, 3]:  

                                    self.qt_true_bets_made = 0
                                    self.escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'{texto_mensagem}! {self.saldo:.2f}\nMeta de ganho: {self.meta_ganho:.2f}')                                      
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                      

                                self.qt_apostas_feitas_txt = 0
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w') 
     
                            elif ultimo_jogo['state'] == 'Lost':
                                if self.qt_apostas_feitas_txt in [1, 2, 3]:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem('Perdeu.')                                                                         
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
                                await self.telegram_bot_erro.envia_mensagem(f'{texto_mensagem}! {self.saldo:.2f}\nMeta de ganho: {self.meta_ganho:.2f}')                                      
                                self.primeiro_alerta_sem_jogos_ao_vivo = False    
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                         
                        sleep(5 * 60)
                        with open('match_of_interest.pkl', 'wb') as fp:
                            pickle.dump({}, fp) 
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

                                for option_market in option_markets: 
                                    market_name = option_market['name']['value']
                                    if periodo in ['1º T', '1º Tempo', '1º tempo']:                                                                                
                                        if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                    
                                                    # [float(o['price']['odds']), o['id'], m['name']['value'].lower()]
                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:   
                                                        #mercado_over = self.find_no_goal_odd( option_markets, numero_gols_atual )
                                                        
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 1, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })
                                    else:
                                        if market_name.lower() in ['total de gols', 'total goals']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                    odd = float(option['price']['odds'])
                                                    option_id = option['id']                                                   

                                                    if odd >= self.odd_inferior_para_apostar and odd < self.odd_superior_para_apostar:
                                                        #mercado_over = self.find_no_goal_odd( option_markets, numero_gols_atual )                                                        
                                                        jogos_aptos.append({ 'market_name': market_name, 'type': 1, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd': odd, 'option_id' : option_id, 'periodo': periodo })

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
                            if self.qt_apostas_feitas_txt in [0, 1, 2] and self.primeiro_alerta_sem_jogos_elegiveis:
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

                        numeros_jogos_filtrados = len( jogos_aptos_ordenado )

                        for jogo_apto in jogos_aptos_ordenado:        

                            print( jogo_apto )                     

                            bet_made = False

                            if jogo_apto['type'] in [0, 1]:
                                bet_made = await self.make_bet_under(jogo_apto)
                            
                            if bet_made and not self.varios_jogos:
                                
                                self.controle_over_under += 1
                                self.escreve_em_arquivo('controle_over_under.txt', f'{self.controle_over_under}', 'w')

                                nome_evento = jogo_apto['nome_evento']
                                self.event_url = f'{base_url}/sports/eventos/{nome_evento}?market=3'
                                self.escreve_em_arquivo('event_url.txt', self.event_url, 'w')

                                self.placar = jogo_apto['score']
                                self.escreve_em_arquivo('placar.txt', self.placar, 'w')

                                self.periodo = jogo_apto['periodo']
                                self.escreve_em_arquivo('periodo.txt', self.periodo, 'w')

                                error = True
                                jogo_aberto = None                                       
                                jogos_ja_inseridos.append( f"{jogo_apto['fixture_id']}{jogo_apto['periodo']}" )
                                bet = None
                                while error:
                                    try:
                                        jogo_aberto = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                        if len( jogo_aberto['betslips'] ) > 0:
                                            self.bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                            self.escreve_em_arquivo('bet_slip_number.txt', self.bet_slip_number, 'w')
                                            error = False                                                
                                    except:
                                        await self.testa_sessao()                                                

                                    bet = jogo_aberto['betslips'][0]       
                                    
                                self.qt_apostas_feitas_txt += 1
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')  

                                self.qt_apostas += 1
                                self.escreve_em_arquivo('qt_apostas.txt', f'{self.qt_apostas}', 'w') 

                                self.soma_odds += self.cota
                                self.escreve_em_arquivo('soma_odds.txt', f'{self.soma_odds}', 'w')                                

                                self.ja_conferiu_resultado = False
                                self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'False', 'w')

                                self.gastos += self.valor_aposta
                                self.escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')

                                if self.qt_apostas_feitas_txt in [1, 2, 3]:

                                    self.qt_apostas_feitas_1 += 1
                                    self.escreve_em_arquivo('qt_apostas_feitas_1.txt', f'{self.qt_apostas_feitas_1}', 'w')

                                    self.qt_true_bets_made += 1
                                    self.escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                                    self.perda_acumulada += self.valor_aposta
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                                    self.primeiro_alerta_depois_do_jogo = True
                                    self.primeiro_alerta_sem_jogos_elegiveis = True   
                                    self.primeiro_alerta_sem_jogos_ao_vivo = True

                                    try:
                                        await self.telegram_bot.envia_mensagem(f"""Odd: {self.cota} Valor da aposta: R$ {self.valor_aposta:.2f}
Saldo: R$ {self.saldo:.2f} Jogos filtrados: {numeros_jogos_filtrados}
Aposta {self.qt_true_bets_made}""")                             
                                    except Exception as e:
                                        print(e)
                                        print('Não foi possível enviar mensagem ao telegram.')

                                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                                                          

                                self.saldo -= self.valor_aposta
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
                                
                                self.is_bet_lost = False

                                self.saldo_antes_aposta = self.saldo
                                self.escreve_em_arquivo('saldo_antes_aposta.txt', f'{self.saldo:.2f}', 'w')

                                if not self.varios_jogos:
                                    break
                           
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
                    self.numero_apostas_feitas = 0
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

    def wait_for_next_fixture_search(self, date):

        while datetime.now() < date:
            print('Esperando tempo para próxima busca...')
            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )
            sleep(5 * 60 )

    def wait_fixture_to_start(self, start_date):
        # 2024-12-26T20:00:00Z
        date = datetime.strptime( start_date, "%Y-%m-%dT%H:%M:%SZ" )
        while datetime.now() + timedelta(hours=3) < date:
            print('Esperando partida iniciar.')
            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )
            sleep(5 * 60 )

        self.match_started = True
        self.escreve_em_arquivo('match_started.txt', 'True', 'w')

    def formata_data(self, date, pattern):        
        return ( datetime.strptime( date, pattern ) - timedelta(hours=3) ).strftime("%d/%m/%Y %Hh%M")
    
    async def geysons_strategy(self):

        try:
            self.tempo_pausa = 90
            self.times_favoritos = []        
            self.first_message_after_bet = False
            # self.jogos_inseridos = self.read_array_from_disk('jogos_inseridos.json')
            # self.same_match_bet = self.le_de_arquivo('same_match_bet.txt', 'boolean')
            self.bet_slip_number = self.le_de_arquivo('bet_slip_number.txt', 'string')
            self.first_match_to_start_date = self.le_de_arquivo('first_match_to_start_date.txt', 'string')
            self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
            self.soma_odds = self.le_de_arquivo('soma_odds.txt', 'float')
            self.qt_apostas = self.le_de_arquivo('qt_apostas.txt', 'int')
            self.qt_apostas_feitas_txt = self.le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')
            # self.is_bet_lost = self.le_de_arquivo('is_bet_lost.txt', 'boolean')
            self.maior_saldo = self.le_de_arquivo('maior_saldo.txt', 'float')
            self.saldo = self.le_de_arquivo('saldo.txt', 'float')
            self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
            self.varios_jogos = False        
            self.meta_progressiva = True
            self.fator_multiplicador = 0.002789
            self.quit_on_next_win = False
            self.teste = False
            self.numero_combinadas = 3
            self.limite_inferior = 2.8
            self.only_favorites = False
            self.odd_de_corte = 1.6
            self.odd_inferior_para_apostar = 1.6
            self.odd_superior_para_apostar = 2
            self.tolerancia_perdas = 6
            self.usar_tolerancia_perdas = False
            self.controle_over_under = self.le_de_arquivo('controle_over_under.txt', 'int')        
            self.only_men_professional = False
            self.is_for_real = self.le_de_arquivo('is_for_real.txt', 'boolean')
            self.gastos = self.le_de_arquivo('gastos.txt', 'float')
            self.ganhos = self.le_de_arquivo('ganhos.txt', 'float')
            self.market_name = None
            self.horario_ultima_checagem = datetime.now()
            self.bets_made = dict()
            self.ultima_checagem_aposta_aberta = datetime.now()
            self.fixture_id = self.le_de_arquivo('fixture_id.txt', 'string')
            self.numero_erros_global = 0
            self.maior_meta_ganho = self.le_de_arquivo('maior_meta_ganho.txt', 'float')
            numeros_jogos_filtrados = 0
            self.match_started = self.le_de_arquivo('match_started.txt', 'boolean')
            self.primeiro_alerta_sem_jogos_ao_vivo = True
        except:
            print('erro ao ler algum arquivo')

        if not await self.is_logged_in():
            await self.faz_login()        

        # await self.le_saldo()
        print('saldo: ', self.saldo)

        # self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')

        try:
            self.times_favoritos = self.read_array_from_disk('times_favoritos.json')
        except Exception as e:
            print(e)
            print('erro ao ler array')            
        message_already_sent = []
        self.times_pra_apostar = []          
        matches = []       
        matches_and_options = dict()
        try: 
            with open('matches_and_options.pkl', 'rb') as fp:
                matches_and_options = pickle.load(fp)
        except:
            print('erro ao ler arquivo')
        fixture_id_to_betslip = dict()
        try:
            with open('fixture_id_to_betslip.pkl', 'rb' ) as fp:
                fixture_id_to_betslip = pickle.load(fp)
        except:
            print('erro ao ler arquivo')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.qt_apostas_feitas_txt = self.le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')        

        if self.meta_ganho == 0:
            self.meta_ganho = self.saldo * self.fator_multiplicador
            self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')

        print(f'Meta de ganho: R$ {self.meta_ganho:.2f}')

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' ) 

        self.navigate_to(f'{base_url}/sports/minhas-apostas/em-aberto') 

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

            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            try:     
                if self.bet_slip_number != '':                                        
                    
                    try:
                        if not self.match_started:
                            self.wait_fixture_to_start( self.first_match_to_start_date)
                        
                        bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']           
                        if bet != None and bet['state'] == 'Open':
                            print('======== Há apostas em aberto na API =========')         
                            
                            print( datetime.now() )                                                        
                            sleep( 2.5 * 60 )
                            continue             
                    except Exception as e:     
                        # se cair aqui pode ter acontecido do jogo não estar ao vivo e vai dar erro na hora de buscar a fixture
                        # então vamos ver se a betslip está aberta
                        await self.testa_sessao()
                        print(e)                        
                        bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']           
                        if bet != None and bet['state'] == 'Open':
                            print('======== Há apostas em aberto na API =========')          
                                   
                            print( datetime.now() )                                                        
                            sleep( 2.5 * 60 )
                            continue                            

                try:                                     
                    if not self.ja_conferiu_resultado and not self.varios_jogos and bet != None and bet['state'] != 'Open':                                                        

                        if not self.aposta_mesmo_jogo:
                            print('Conferindo resultado da última aposta.')
                            self.ja_conferiu_resultado = True
                            self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')    
                            # primeiro verificamos se a última aposta foi vitoriosa                                                    
                            self.bet_slip_number = ''
                            self.escreve_em_arquivo('bet_slip_number.txt', '', 'w')

                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = bet

                            early_payout = ultimo_jogo['isEarlyPayout']

                            if ultimo_jogo['state'] == 'Canceled':

                                print('aposta cancelada')

                                if self.is_for_real:
                                    self.qt_true_bets_made -= 1
                                    self.escreve_em_arquivo('qt_true_bets_made.txt', f'{self.qt_true_bets_made}', 'w')

                                if self.qt_apostas_feitas_txt == 1:
                                    self.qt_apostas_feitas_1 -= 1
                                    self.escreve_em_arquivo('qt_apostas_feitas_1.txt', f'{self.qt_apostas_feitas_1}', 'w')

                                self.qt_apostas_feitas_txt -= 1
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')
                                
                                valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                                self.perda_acumulada -= valor_ultima_aposta      
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                                self.saldo += valor_ultima_aposta
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')                                                                 

                                self.valor_aposta -= self.perda_acumulada                                    

                                
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
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w') 

                                self.controle_over_under = 0
                                self.escreve_em_arquivo('controle_over_under.txt', '0', 'w')

                                # if self.qt_apostas_feitas_txt == 1 or self.is_for_real:
                                #     self.qt_vezes_perdida_aposta_1 = 0
                                #     self.escreve_em_arquivo('qt_vezes_perdida_aposta_1.txt', f'{self.qt_vezes_perdida_aposta_1}', 'w')

                                self.perda_acumulada -= valor_ganho                                    

                                if self.perda_acumulada < 0:
                                    self.perda_acumulada = 0

                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')          

                                if self.meta_progressiva and self.is_for_real:
                                    self.meta_ganho = self.saldo * self.fator_multiplicador     

                                    if self.meta_ganho > self.maior_meta_ganho:                           
                                        self.maior_meta_ganho = self.meta_ganho
                                        self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                
                                        print(f'Meta de ganho: R$ {self.meta_ganho:.2f}')
                                        self.escreve_em_arquivo('maior_meta_ganho.txt', f'{self.maior_meta_ganho:.2f}', 'w')                                

                                texto_mensagem = "GANHOU"

                                if self.quit_on_next_win:     
                                    try:
                                        #if self.saldo > self.saldo_inicio_dia:                                        
                                        
                                        await self.telegram_bot_erro.envia_mensagem(f'{texto_mensagem}! {self.saldo:.2f}\nSaindo...')                                      

                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')  
                                    self.escreve_em_arquivo('last_time_check.txt', 'sair', 'w' )
                                    self.chrome.quit()
                                    exit() 

                                if self.is_for_real:

                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'{texto_mensagem}! {self.saldo:.2f}\nMeta de ganho: {self.meta_ganho:.2f}')                                      
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                      

                                self.qt_apostas_feitas_txt = 0
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w') 
     
                            elif ultimo_jogo['state'] == 'Lost':
                                if self.is_for_real:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem('Perdeu.')                                                                         
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                                                                              

                    data_inicial = ( datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:00.000Z" )
                    data_final = ( datetime.now() + timedelta(hours=9) ).strftime("%Y-%m-%dT%H:%M:00.000Z" )
                    
                    fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixtures?x-bwin-accessid=YTRhMjczYjctNTBlNy00MWZlLTliMGMtMWNkOWQxMThmZTI2&lang=pt-br&country=BR&userCountry=BR&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&fixtureCategories=Gridable,NonGridable,Other,Specials,Outrights&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=None&skip=0&take=50&sortBy=StartDate&from={data_inicial}&to={data_final}&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   
                   
                    print('\n\n--- chamou fixtures de novo ---')

                    self.maior_odd = 0.0
                    self.maior_odd_corte = 0.0

                    if len( fixtures['fixtures'] ) == 0:
                        print('Sem jogos em breve...')                        

                        print(datetime.now())                      
                        if self.primeiro_alerta_sem_jogos_ao_vivo:
                            try:                           
                                await self.telegram_bot.envia_mensagem('Sem jogos em breve...')                                      
                                self.primeiro_alerta_sem_jogos_ao_vivo = False    
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                         
                        self.wait_for_next_fixture_search(datetime.now() + timedelta(minutes=5))
                    else:
                        periodos = set()
                        jogos_aptos.clear()
                        self.tempo_pausa = 90
                        for fixture in fixtures['fixtures']:                               
                            try:
                                periodos.add( fixture['scoreboard']['period'])

                                if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                    continue

                                nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                
                                fixture_id = fixture['id']
                                name = fixture['name']['value']
                                competition = fixture['competition']['name']['value']
                                region = fixture['region']['name']['value']
                                numero_gols_atual = fixture['scoreboard']['score']      
                                score = fixture['scoreboard']['score']      
                                numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                periodo = fixture['scoreboard']['period']
                                periodId = fixture['scoreboard']['periodId']
                                is_running = fixture['scoreboard']['timer']['running']

                                cronometro = float(fixture['scoreboard']['timer']['seconds']) // 60
                                start_date = fixture['startDate']

                                match = None

                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets: 
                                    if option_market['isBetBuilder']:
                                        market_name = option_market['name']['value']                                                                              
                                        if market_name.lower() in ['1º tempo - total de gols', 'total de gols - 1º tempo']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == 'Menos de 2,5' and float( option['price']['odds']) >= 0.1:
                                                    odd_under = float(option['price']['odds'])
                                                    option_id_under = option['id']    
                                                    original_start_date = start_date
                                                    start_date = datetime.strptime( start_date, "%Y-%m-%dT%H:%M:%SZ" )
                                                    start_date = ( start_date - timedelta(hours=3) ).strftime("%d/%m/%Y %Hh%M")                                                
                                                    match = { 'original_start_date': original_start_date, 'region': region, 'competition': competition, 'name': name, 'start_date': start_date, 'market_name': market_name, 'type': 0, 'score': score, 'option_name': option['name']['value'], 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'odd_under': odd_under, 'option_id_under' : option_id_under, 'periodo': periodo }
                                
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets: 
                                    if option_market['isBetBuilder']:
                                        market_name = option_market['name']['value']                                                                              
                                        if market_name.lower() in ['total de gols', 'total goals']:
                                            for option in option_market['options']:                                                        
                                                if option['name']['value'] == 'Mais de 0,5':
                                                    odd_over = float(option['price']['odds'])
                                                    option_id_over = option['id']                                                    
                                                    if match != None:
                                                        match['odd_over'] = odd_over
                                                        match['option_id_over'] = option_id_over    
                                                        match['odd_combinada'] = match['odd_over'] + match['odd_under'] + 0.04 - 1.0                                 

                                if match != None and match.get('odd_over'):
                                    jogos_aptos.append( match )                               

                            except Exception as e:                                    
                                print('erro')                                    
                                print(e)                                                         

                        print(periodos)

                        if len(jogos_aptos) < self.numero_combinadas:
                            print('--- SEM JOGOS ELEGÍVEIS ---')

                            print(datetime.now())
                            if self.primeiro_alerta_sem_jogos_elegiveis:
                                try:
                                    await self.telegram_bot.envia_mensagem("Sem jogos elegíveis.")                             
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                except Exception as e:
                                    print(e)
                                    print('Não foi possível enviar mensagem ao telegram.')

                            self.wait_for_next_fixture_search(datetime.now() + timedelta(minutes=5))
                            continue        
                        try:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            sleep(1)
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        except Exception as e:
                            print('Não conseguiu limpar os jogos...')
                            print(e)

                        self.numero_apostas_feitas = 0                                 

                        jogos_aptos = list( sorted( jogos_aptos, key=lambda e: ( e['original_start_date'], -e['odd_combinada'] )))

                        for jogo_apto in jogos_aptos:        

                            print( jogo_apto )                     

                            bet_made = False

                            if jogo_apto['type'] in [0, 1]:
                                bet_made = await self.make_bet_geyson(jogo_apto)

                            if self.numero_apostas_feitas < self.numero_combinadas:
                                continue
                            
                            if bet_made and not self.varios_jogos:

                                string_matches = ''
                                
                                self.navigate_to(f'{base_url}/sports/minhas-apostas/em-aberto')
                                try:
                                    expandir = WebDriverWait(self.chrome, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "ms-my-bets-betslip-expand") )) 
                                    expandir.click()
                                except:
                                    pass  

                                self.match_started = False
                                self.escreve_em_arquivo('match_started.txt', 'False', 'w')

                                start_date = datetime.strptime( jogo_apto['original_start_date'], "%Y-%m-%dT%H:%M:%SZ" )
                                start_date = ( start_date - timedelta(hours=3) ).strftime("%d/%m/%Y %Hh%M")
                                
                                jogo_aberto = None                                       
                                bet = None

                                jogo_aberto = await self.get(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                                               
                                if len( jogo_aberto['betslips'] ) > 0:                                   

                                    self.bet_slip_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                    self.escreve_em_arquivo('bet_slip_number.txt', self.bet_slip_number, 'w')                                                                                                                     

                                    bet = jogo_aberto['betslips'][0]       

                                    matches_fixture_ids = set( map( lambda e: e['fixture']['compoundId'], bet['bets'] ) )                                    

                                    self.first_match_to_start_date = None
                                    
                                    for fi in matches_fixture_ids:
                                        fixture = await self.get(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixture-view?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&scoreboardMode=Full&fixtureIds={fi}&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                               
                                        name = fixture['fixture']['name']['value']
                                        start_date = self.formata_data( fixture['fixture']['startDate'], "%Y-%m-%dT%H:%M:%SZ" )
                                        region = fixture['fixture']['region']['name']['value']

                                        if not self.first_match_to_start_date:
                                            self.first_match_to_start_date = fixture['fixture']['startDate']
                                            self.escreve_em_arquivo('first_match_to_start_date.txt', self.first_match_to_start_date, 'w')

                                        string_matches += f'{start_date}: {name}, {region}\n'                                        

                                self.qt_apostas_feitas_txt += 1
                                self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')  

                                self.qt_apostas += 1
                                self.escreve_em_arquivo('qt_apostas.txt', f'{self.qt_apostas}', 'w') 

                                self.soma_odds += self.cota
                                self.escreve_em_arquivo('soma_odds.txt', f'{self.soma_odds}', 'w')                                

                                self.ja_conferiu_resultado = False
                                self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'False', 'w')

                                self.gastos += self.valor_aposta
                                self.escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')

                                if self.is_for_real:

                                    self.perda_acumulada += self.valor_aposta
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                                    self.primeiro_alerta_depois_do_jogo = True
                                    self.primeiro_alerta_sem_jogos_elegiveis = True   
                                    self.primeiro_alerta_sem_jogos_ao_vivo = True

                                    try:
                                        await self.telegram_bot.envia_mensagem(f"""{string_matches}
Valor da aposta: R$ {self.valor_aposta:.2f}
Saldo: R$ {self.saldo:.2f}
Aposta {self.qt_apostas_feitas_txt}""")                             
                                    except Exception as e:
                                        print(e)
                                        print('Não foi possível enviar mensagem ao telegram.')

                                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                                                          

                                self.saldo -= self.valor_aposta
                                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
                                
                                self.is_bet_lost = False

                                self.wait_fixture_to_start(self.first_match_to_start_date)                          

                                if not self.varios_jogos:
                                    break
                            elif not bet_made and not self.varios_jogos:
                                self.numero_apostas_feitas = 0
                                self.escreve_em_arquivo('last_time_check.txt', 'erro_aposta', 'w' )
                                self.chrome.quit()
                                exit()
                           
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
                    self.numero_apostas_feitas = 0
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

        
    async def pools_apostas_simultaneas(self):     

        try:
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
            self.odd_superior_para_apostar = 1.29
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
            self.event_url = ''
        except Exception as e:
            print(e)
            print('erro ao ler algum arquivo')

        if not await self.is_logged_in():
            await self.faz_login()   

        self.navigate_to('https://sports.sportingbet.bet.br/pt-br/sports/minhas-apostas/em-aberto')

        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                  

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' )  

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

            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

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
                        bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={bet_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']

                        if bet['state'] != 'Open':
                            del self.bets_made[bet_number]
                            self.save_set_on_disk('bets_made.pkl', self.bets_made )

                            try:
                                self.jogos_inseridos.remove( f"{bet['bets'][0]['fixture']['compoundId']}{bet['bets'][0]['option']['name']}")
                            except:
                                pass

                            valor_ultima_aposta = float( bet['stake']['value'])

                            if bet['state'] == 'Lost':                                

                                if self.restart_pool:
                                    self.apostas_paralelas[ pool_index ] = 1.0
                                    self.gastos += 1.0
                                else:
                                    self.apostas_paralelas[ pool_index ] = 0.1
                                    self.gastos += 0.1

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )

                                lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                if valor_ultima_aposta >= 1:
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

                                if self.apostas_paralelas[ pool_index ] == 0.1:
                                    self.apostas_paralelas[ pool_index ] = 0.1
                                else:
                                    self.apostas_paralelas[ pool_index ] = valor_ganho

                                lucro_pool = sum( self.apostas_paralelas ) - self.gastos

                                if valor_ultima_aposta >= 1:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'ganhou na pool {pool_index+1}\nvalor: {valor_ganho:.2f}\n{self.apostas_paralelas}\nlucro pool: {lucro_pool:.2f}')
                                    except:
                                        pass

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   
                            else:                                
                                self.apostas_paralelas[ pool_index ] = valor_ultima_aposta

                                if pool_index not in self.available_indexes:
                                    self.available_indexes.append( pool_index )   

                        self.save_array_on_disk('available_indexes.json', self.available_indexes)    
                        self.save_array_on_disk('apostas_paralelas.json', self.apostas_paralelas)

                if self.get_available_index() == -1:
                    print('todas as pools estão ocupadas')
                    sleep(5 * 60)
                    continue                                     
                    
                fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                print('\n\n--- chamou fixtures de novo ---')

                if len( fixtures['fixtures'] ) == 0:
                    print('Sem jogos ao vivo...')
                    print(datetime.now())
                    sleep(7 * 60)
                    continue
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
                                if market_name.lower() in ['total de gols', 'total goals']:
                                    for option in option_market['options']:          
                                        if numero_gols_atual in [0, 1] and option['name']['value'] == f'Mais de {numero_gols_atual},5':
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

                        if f"{jogo_apto['fixture_id']}{jogo_apto['option_name']}" in self.jogos_inseridos:   
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
                            self.jogos_inseridos.append( f"{jogo_apto['fixture_id']}{jogo_apto['option_name']}" )                                
                            pool_index = None

                            self.save_array_on_disk('jogos_inseridos.json', self.jogos_inseridos)
                            
                            jogo_aberto = await self.get(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            
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

                            if self.valor_aposta >= 1:
                                try:
                                    await self.telegram_bot.envia_mensagem(f"Aposta no pool {pool_index+1} Valor da aposta: R$ {self.valor_aposta:.2f}")                             
                                except Exception as e:
                                    print(e)
                                    print('não foi possível enviar mensagem ao telegram.')

                            if not self.varios_jogos:
                                break 
                        else:                            
                            self.numero_apostas_feitas = 0
                            self.escreve_em_arquivo('last_time_check.txt', 'erro_aposta', 'w' )
                            self.chrome.quit()
                            exit()                            
                
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
                await self.testa_sessao()


    def find_first_match_to_start_date( self, bet ):        
        return sorted( map( lambda e: e['fixture']['date'], bet['bets'] ))[0]
    
            
    async def pools_apostas_simultaneas_martingale(self):

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
        self.ganhos = self.le_de_arquivo('ganhos.txt', 'float')
        self.jogos_inseridos = self.read_array_from_disk('jogos_inseridos.json')
        self.odd_superior_para_apostar = 1.29
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

        if not await self.is_logged_in():
            await self.faz_login()        


        if self.teste:
            print('=========== MODO DE TESTE ATIVADO ============')                  

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' )  

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

            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

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
                        bet = await self.get(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={bet_number}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")
                        bet = bet['betslip']

                        if bet['state'] != 'Open':
                            del self.bets_made[bet_number]
                            self.save_set_on_disk('bets_made.pkl', self.bets_made )

                            try:
                                self.jogos_inseridos.remove( f"{bet['bets'][0]['fixture']['compoundId']}{bet['bets'][0]['option']['name']}")
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
                                    try:
                                        await self.telegram_bot.envia_mensagem(f'zerando valores na pool {pool_index+1}')
                                    except Exception as e:
                                        print(e)

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

                print(f'Soma das pools: R$ {sum(self.apostas_paralelas):.2f}' )

                if self.get_available_index() == -1:
                    print('todas as pools estão ocupadas')
                    sleep(5 * 60)
                    continue                     
                    
                fixtures = await self.get(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

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
                                if market_name.lower() in ['total de gols', 'total goals']:
                                    for option in option_market['options']:          
                                        if numero_gols_atual in [0, 1] and option['name']['value'] == f'Mais de {numero_gols_atual},5':
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

                        sleep( 2.5 * 60 )
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

                        if f"{jogo_apto['fixture_id']}{jogo_apto['option_name']}" in self.jogos_inseridos:   
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
                            self.jogos_inseridos.append( f"{jogo_apto['fixture_id']}{jogo_apto['option_name']}" )                                
                            pool_index = None

                            self.save_array_on_disk('jogos_inseridos.json', self.jogos_inseridos)
                            
                            jogo_aberto = await self.get(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            
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
                            self.escreve_em_arquivo('last_time_check.txt', 'erro_aposta', 'w' )
                            self.chrome.quit()
                            exit() 
                
                if not deu_erro:
                    sleep( 2.5 * 60 )
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

        
    async def make_bet_under_martingale(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id = jogo_apto['option_id']

        try:
            self.navigate_to(f'{base_url}/sports/eventos/{nome_evento}?market=3')

            clicou = False
            index = 0
            while not clicou and index < 5:
                try:                                                                   
                    # mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                    #     EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                    # #EC.presence_of_all_elements_located  
                    # mercado_1_tempo[index].click()                                                       
                    empate = WebDriverWait(self.chrome, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
            # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                    empate.click()     
                    break                   
                except Exception as e:
                    index += 1                   
            
            sleep(0.5)     

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

        # try:
        #     cota2 = WebDriverWait(self.chrome, 10).until(
        #                 EC.presence_of_element_located((By.CSS_SELECTOR, f"ms-event-pick[data-test-option-id='{option_id}'] > div > div:nth-child(2)") )) 
        #     cota2 = float( cota2.get_property('innerText') )
        # except Exception as e:
        #     print('não conseguiu pegar odd do ms-event-pick')
        #     raise Exception('Erro ao capturar odd')
        
        if cota == None:
            raise Exception('Odds diferem')
        
        # if self.controle_over_under % 2 == 0:
        #     if cota < self.odd_inferior_para_apostar or cota > self.odd_superior_para_apostar:
        #         print('cota fora do intervalo')
                
        #         self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
        #         sleep(0.5)
        #         self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                        

        #         raise Exception('Odd fora do intervalo')
        
        self.cota = cota
        return cota
        
    def get_bet_odd_geyson(self):
        cota = None
        #cota2 = None
        try:                   
            cota = WebDriverWait(self.chrome, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
            cota = float( cota.get_property('innerText') )
        except Exception as e:
            print(e)
            print('não consegui pegar a odd do sumário')
            raise Exception('Erro ao capturar odd')
        
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
    
    def get_available_index(self):
        if len( self.available_indexes ) == 0:
            return -1
        return self.available_indexes[0]
    
    def calcula_valor_aposta_pools(self, cota):

        self.cota = cota
        print(self.cota)

        self.valor_aposta = self.apostas_paralelas[ self.get_available_index() ]                                          

        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}') 
    
    def calcula_valor_aposta(self, cota):

        self.cota = cota

        self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01                                            

        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

        # if self.qt_apostas_feitas_txt in [0, 1, 2]:
        self.is_for_real = True
        # else:
        #     self.is_for_real = False
        #     self.valor_aposta = 0.1

        # if self.qt_apostas_feitas_txt in [3,4]:
        #     self.is_for_real = True   
        # else:
        #     self.is_for_real = False
        #     self.valor_aposta = 0.1

        self.escreve_em_arquivo('is_for_real.txt', f'{self.is_for_real}', 'w')        

        if self.teste or self.valor_aposta > self.saldo:
            self.valor_aposta = 0.1

    
    async def make_bet_geyson(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id_under = jogo_apto['option_id_under']
        odd_under = jogo_apto['odd_under']
        odd_over = jogo_apto['odd_over']
        option_id_over = jogo_apto['option_id_over']

        try:
            self.navigate_to(f'{base_url}/sports/eventos/{nome_evento}?market=3')

            over = WebDriverWait(self.chrome, 15).until(
                EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id_over}"]' ) ))
            
            odd = WebDriverWait(self.chrome, 5).until(
                EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id_over}"]/descendant::span' ) ))
            
            # vou tentar converter pra inteiro pra ver se o mercado está disponível
            try:
                float( odd.get_property('innerText'))
            except Exception as e:
                print(e)
                return False

            over.click()            

            clicou = False
            index = 0
            while not clicou and index < 5:
                try:                    
                    mercado_1_tempo = WebDriverWait(self.chrome, 5).until(
                        EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::div/ancestor::li"))) 
                    mercado_1_tempo[index].click()                                                         
                    empate = WebDriverWait(self.chrome, 2).until(
                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id_under}"]' ) ))                                                 
                    empate.click()     
                    break                 
                except Exception as e:
                    print(e)
                    index += 1                             

            sleep(1)    

            if index == 5:
                return False

            self.numero_apostas_feitas += 1

            if self.numero_apostas_feitas == self.numero_combinadas:

                cota = None
                try:
                    cota = self.get_bet_odd_geyson()
                except:
                    return False
                
                if cota == None:
                    return False

                self.calcula_valor_aposta(cota)

                aposta_feita = await self.insere_valor(None)
                return aposta_feita   
        except:
            return False            


    async def make_bet_under(self, jogo_apto):
        nome_evento = jogo_apto['nome_evento']
        option_id = jogo_apto['option_id']

        try:
            self.navigate_to(f'{base_url}/sports/eventos/{nome_evento}?market=3')

            clicou = False
            index = 0
            while not clicou and index < 5:
                try:                                                                   
                    # mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                    #     EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '2º Tempo']/ancestor::a"))) 
                    # #EC.presence_of_all_elements_located  
                    # mercado_1_tempo[index].click()                                                       
                    empate = WebDriverWait(self.chrome, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{option_id}"]' ) ))                                     
            # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                    empate.click()     
                    break                   
                except Exception as e:
                    index += 1                   
            
            sleep(0.5)    

            cota = None
            try:
                cota = self.get_bet_odd(option_id)
            except:
                return False
            
            if cota == None:
                return False

            self.calcula_valor_aposta_pools(cota)

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

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list         

    async def is_logged_in(self):        
        for i in range(3):       
            try:                
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("{base_url}/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if not jogos_abertos['summary']['hasError']:
                    print('logou com sucesso')
                    return True                
            except:                
                pass
            sleep(1)
        return False
        
    async def gols_fim_jogo_favoritos(self):

        if not await self.is_logged_in():
            await self.faz_login()        

        self.tempo_pausa = 2 * 60        
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []        
        self.first_message_after_bet = False
        self.same_match_bet = self.le_de_arquivo('same_match_bet.txt', 'boolean')
        self.bet_slip_number_1 = self.le_de_arquivo('bet_slip_number_1.txt', 'string')
        self.is_bet_lost = self.le_de_arquivo('is_bet_lost.txt', 'boolean')
        self.maior_saldo = self.le_de_arquivo('maior_saldo.txt', 'float')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
        self.varios_jogos = False        
        self.fator_multiplicador = 0.06858
        self.teste = False
        self.limite_inferior = 2.8
        self.only_favorites = False
        self.limite_superior = 5
        self.tolerancia_perdas = 4
        self.meta_progressiva = True
        self.only_men_professional = False
        self.gastos = self.le_de_arquivo('gastos.txt', 'float')
        self.ganhos = self.le_de_arquivo('ganhos.txt', 'float')
        self.market_name = None
        self.horario_ultima_checagem = datetime.now()
        self.bets_made = dict()
        # chelsea, city, arsenal, liverpool, manchester united, tottenham
        # real madrid, barcelona, atletico de madrid, 
        # boca juniors, river plate
        # milan, internazionale, juventus, roma, napoli 
        # palmeiras, flamengo
        # borussia dortmund, baryern de munique, bayer leverkusen, rb leipzig
        # psg, monaco
        # sporting, benfica, porto
        # psv, feyenoord, ajax, az alkmaar
        favorite_teams = [233686, 233499, 212594, 233665, 212591, 223259, 212592, 207397, 207414, 212598, 212604, 212605, 212600, 
                          212603, 234247, 233407, 206072, 206067, 233408, 212596, 233841, 233847, 211828,
                          233402, 212602,234157, 233406, 234114,233405, 234116,211819 ]
        favorite_competitions = [102838, 102723, 102827, 102696]
        is_any_odd_close = False
        try:
            self.times_favoritos = self.read_array_from_disk('times_favoritos.json')
        except Exception as e:
            print(e)
            print('erro ao ler array')            
        message_already_sent = []
        self.times_pra_apostar = []          
        matches = []       
        matches_and_options = dict()
        try: 
            with open('matches_and_options.pkl', 'rb') as fp:
                matches_and_options = pickle.load(fp)
        except:
            print('erro ao ler arquivo')

        fixture_id_to_betslip = dict()
        try:
            with open('fixture_id_to_betslip.pkl', 'rb' ) as fp:
                fixture_id_to_betslip = pickle.load(fp)
        except:
            print('erro ao ler arquivo')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.qt_apostas_feitas_txt = self.le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')        
        await self.le_saldo()

        if self.meta_ganho == 0:
            self.meta_ganho = self.saldo * self.fator_multiplicador
            self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')

        print('proceso do chrome ', self.chrome.service.process.pid)
        self.escreve_em_arquivo('chrome_process_id.txt', f'{self.chrome.service.process.pid}', 'w' )        

        while True:
            # for bet_id in self.bet_ids.copy():                                
            #     if not self.is_bet_open(bet_id):
            #         self.bet_ids.remove(bet_id)          
            self.escreve_em_arquivo('last_time_check.txt', datetime.now().strftime( '%Y-%m-%d %H:%M' ), 'w' )

            deu_erro = False
            fixtures = None           

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            try:                      

                fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.bet.br/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=150&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                print('\n--- chamou fixtures de novo ---\n')
                print(datetime.now())                

                bet = None
                
                if not self.varios_jogos:
                    bet = self.chrome.execute_script(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number_1}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")

                    bet = bet['betslip']

                    self.inserted_fixture_ids.clear()
                    if bet['state'] == 'Open' and not self.is_bet_lost:
                        self.inserted_fixture_ids.append(bet['bets'][0]['fixture']['compoundId'])

                        # if self.is_fixture_over(bet['bets'][0]['fixture']['compoundId']):
                        #     self.inserted_fixture_ids.clear()

                    if bet['state'] != 'Open' and not self.ja_conferiu_resultado:
                        self.ja_conferiu_resultado = True
                        self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')

                        self.is_bet_lost = True
                        self.escreve_em_arquivo('is_bet_lost.txt', 'True', 'w')

                        self.same_match_bet = False
                        self.escreve_em_arquivo('same_match_bet.txt', 'False', 'w')
                        
                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = bet

                        early_payout = ultimo_jogo['isEarlyPayout']

                        if ultimo_jogo['state'] == 'Lost':
                            try:
                                await self.telegram_bot_erro.envia_mensagem(f"Perdeu! R$ {self.saldo:.2f}\nBalanço: R$ {(self.ganhos-self.gastos):.2f}")
                                self.primeiro_alerta_depois_do_jogo = False   
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')

                            if not matches_and_options[fixture_id]['stats_saved_1_t']:
                                matches_and_options[fixture_id]['market_name'] = '1º tempo - total de gols'
                                #self.save_stats(matches_and_options[fixture_id], fixture_id)
                                matches_and_options[fixture_id]['stats_saved_1_t'] = True
                                print('perdeu jogo no primeiro tempo')
                                
                        elif ultimo_jogo['state'] == 'Canceled':

                            print('aposta cancelada')

                            self.qt_apostas_feitas_txt -= 1
                            self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')
                            
                            valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                            self.perda_acumulada -= valor_ultima_aposta  
                            self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')    

                            self.gastos -= valor_ultima_aposta
                            self.escreve_em_arquivo('gastos.txt', f'{self.gastos:.2f}', 'w')   

                            self.saldo += valor_ultima_aposta               
                            self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
                            
                            
                        elif ultimo_jogo['state'] == 'Won' and not early_payout:                                 
                            # aqui o saldo deve ser maior do que depois da aposta, do contrário não estamos pegando o valor correto
                            # try:
                            #     await self.telegram_bot_erro.envia_mensagem(f'GREEN DEPOIS DE {self.qt_apostas_feitas} APOSTAS.')
                            # except Exception as e:
                            #     print(e)                            
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

                            self.ganhos += valor_ganho
                            self.escreve_em_arquivo('ganhos.txt', f'{self.ganhos:.2f}', 'w')

                            if not matches_and_options[fixture_id]['stats_saved_1_t']:
                                matches_and_options[fixture_id]['market_name'] = '1º tempo - total de gols'
                                #self.save_stats(matches_and_options[fixture_id], fixture_id )
                                matches_and_options[fixture_id]['stats_saved_1_t'] = True
                                print('ganhou jogo no primeiro tempo')

                            # if self.saldo > self.maior_saldo:
                            #     self.maior_saldo = self.saldo
                            #     self.escreve_em_arquivo('maior_saldo.txt', f'{self.maior_saldo:.2f}', 'w')
                            #     try:
                            #         await self.telegram_bot_erro.envia_mensagem(f'Aumento de saldo: {self.maior_saldo:.2f}')
                            #         self.primeiro_alerta_depois_do_jogo = False
                            #     except:
                            #         print('erro ao enviar mensagem ao telegram')
                            # else:                         
                                                            
                            if self.qt_apostas_feitas_txt <= self.tolerancia_perdas:
                                self.perda_acumulada = 0.0
                                self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')
                            else:
                                self.perda_acumulada -= valor_ganho
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                            
                            if self.meta_progressiva:                                
                                self.meta_ganho = self.saldo * self.fator_multiplicador
                                self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                                           

                            aumento_real = 'Recuperou.'
                            if self.saldo > self.maior_saldo:
                                aumento_real = 'GANHOU!'
                                self.maior_saldo = self.saldo
                                self.escreve_em_arquivo('maior_saldo.txt', f'{self.maior_saldo:.2f}', 'w')

                            try:
                                await self.telegram_bot_erro.envia_mensagem(f"{aumento_real}\nSaldo: R$ {self.saldo:.2f}\nBalanço: R$ {self.ganhos-self.gastos:.2f}")
                                self.primeiro_alerta_depois_do_jogo = False   
                                #self.saldo_inicio_dia = self.saldo
                                #self.escreve_em_arquivo('saldo_inicio_dia.txt', f'{self.saldo_inicio_dia:.2f}', 'w')
                                #self.horario_ultima_checagem = datetime.now()
                                #else:
                                #    await self.telegram_bot_erro.envia_mensagem(f'RECUPEROU! {self.saldo}')
                            except Exception as e:
                                print(e)
                                print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')

                            self.qt_apostas_feitas_txt = 0
                            self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')    
                        
                        if self.qt_apostas_feitas_txt % self.tolerancia_perdas == 0:
                            self.perda_acumulada = 0.0  
                            self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')   

                            if self.meta_progressiva:                                
                                self.meta_ganho = self.saldo * self.fator_multiplicador
                                self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w') 

                if len( fixtures['fixtures'] ) == 0:
                    print('Sem jogos ao vivo...')
                    print(datetime.now())
                    self.tempo_pausa = 10 * 60
                    self.times_favoritos.clear()
                    matches_and_options.clear()
                    fixture_id_to_betslip.clear()
                else:
                    self.tempo_pausa = 2 * 60
                    any_match_of_interest = False
                    for fixture in fixtures['fixtures']:                            
                        try:
                            fixture_id = fixture['id']
                            nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )                         
                            gols_casa = int( fixture['scoreboard']['score'].split(':')[0])
                            gols_fora = int( fixture['scoreboard']['score'].split(':')[1])
                            soma_gols = gols_casa + gols_fora
                            periodo = fixture['scoreboard']['period']                                
                            periodId = int( fixture['scoreboard']['periodId'] )

                            if periodo.lower() in ['não foi iniciado', 'suspenso' ]:                               
                                continue

                            if '2' in periodo.lower():
                                #print('jogo no segundo tempo')
                                continue

                            if fixture_id in self.times_favoritos:        
                                print(f"\n{nome_evento}")    

                            if self.only_men_professional:
                                result = re.findall(r"sub-*\d+|reserv.*|femin.*|u-*\d+|women", fixture['participants'][0]['name']['value'].lower())
                                result2 = re.findall(r"sub-*\d+|reserv.*|femin.*|u-*\d+|women", fixture['participants'][1]['name']['value'].lower())
                                
                                if len( result ) > 0 or len( result2 ) > 0:
                                    continue                                                        

                            if soma_gols != 0:                    

                                try:
                                    self.times_favoritos.remove(fixture_id)                                    
                                except:
                                    pass

                                if matches_and_options.get(fixture_id) != None:
                                    market_name = matches_and_options[fixture_id]['market_name']                                    
                                    # aqui eu vou salvar no banco a última odd antes de sair o gol                                    
                                  
                                    if not matches_and_options[fixture_id]['stats_saved_1_t']:
                                        print('saiu gol no jogo')
                                        matches_and_options[fixture_id]['market_name'] = '1º tempo - total de gols'
                                        #self.save_stats(matches_and_options[fixture_id], fixture_id)
                                        matches_and_options[fixture_id]['stats_saved_1_t'] = True

                                continue
                            
                            home_team = list( filter( lambda el: el['properties']['type'] == 'HomeTeam' , fixture['participants']))
                            home_team_name = home_team[0]['name']['value']    
                            away_team = list( filter( lambda el: el['properties']['type'] == 'AwayTeam' , fixture['participants']))
                            away_team_name = away_team[0]['name']['value']
                            
                            name = fixture['name']['value']
                            numero_gols_atual = fixture['scoreboard']['score']      
                            score = fixture['scoreboard']['score']    

                            numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])    
                            
                            periodo = fixture['scoreboard']['period']
                            is_running = fixture['scoreboard']['timer']['running']
                            cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0                            

                            

                            time_1 = fixture['participants'][0]
                            time_1_nome = time_1['name']['value']
                            time_1_id = time_1['id']
                            time_2 = fixture['participants'][1]
                            time_2_nome = time_2['name']['value']                                                                      
                            time_2_id = time_2['id']

                            resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado da partida', 'match result'] ,fixture['optionMarkets'] ) )

                            chance_dupla = list( filter( lambda el: el['name']['value'].lower() in ['chance dupla', 'double chance'], fixture['optionMarkets']))

                            next_goal_odd_and_option_id = self.find_next_goal_odd_and_option_id( fixture['optionMarkets'], soma_gols )                            
                            if next_goal_odd_and_option_id == None:
                                print('jogo não tem mercado')
                                continue

                            #no_goal_odd_and_option_id = self.find_no_goal_odd(fixture['optionMarkets'], soma_gols )

                            next_goal_odd = next_goal_odd_and_option_id[0]
                            next_goal_option_id = next_goal_odd_and_option_id[1]         
                            next_goal_option_name = next_goal_odd_and_option_id[2]     

                            if matches_and_options.get(fixture_id):
                                print(next_goal_odd)
                                if next_goal_odd > matches_and_options[fixture_id]['odd_before_score']:                                    
                                    matches_and_options[fixture_id]['odd_before_score'] = next_goal_odd
                                    print('atualizou odd')

                            if periodo.lower() == 'intervalo':
                                if matches_and_options.get(fixture_id) != None and soma_gols == 0:

                                    # se isso for verdadeiro é porque não saiu gol na primeira etapa, então vou colocar nos stats uma odd de -1
                                    if not matches_and_options[fixture_id]['stats_saved_1_t']:
                                        print('não saiu gol no primeiro tempo')
                                        #self.save_stats({ 'market_name': '1º tempo - total de gols', 'odd_before_score': -1 }, fixture_id )
                                        matches_and_options[fixture_id]['market_name'] = next_goal_option_name
                                        matches_and_options[fixture_id]['odd_before_score'] = next_goal_odd
                                        matches_and_options[fixture_id]['stats_saved_1_t'] = True     
                                continue                              

                            resultado_partida = resultado_partida[0]
                            chance_dupla = chance_dupla[0]
                            odd_time_1_resultado_partida = float( resultado_partida['options'][0]['price']['odds'] ) 
                            odd_time_1_chance_dupla = float( chance_dupla['options'][0]['price']['odds'] )
                            time_1_chance_dupla_option_id = chance_dupla['options'][0]['id']
                            time_1_resultado_partida_option_id = resultado_partida['options'][0]['id']                               
                            odd_time_2_resultado_partida = float( resultado_partida['options'][2]['price']['odds'] )   
                            time_2_resultado_partida_option_id = resultado_partida['options'][2]['id']  
                            odd_time_2_chance_dupla = float( chance_dupla['options'][1]['price']['odds'] )
                            time_2_chance_dupla_option_id = chance_dupla['options'][1]['id']                           
                            
                            if fixture_id in self.inserted_fixture_ids:
                                continue                                

                            if fixture_id in self.times_favoritos:
                                if next_goal_odd >= ( self.limite_inferior - 0.3 ) and next_goal_odd < self.limite_superior and len( self.inserted_fixture_ids ) == 0:
                                    self.tempo_pausa = 60                                                                                      
                                print('odd do mercado: ', next_goal_odd )

                            if ( fixture_id in self.times_favoritos and len( self.inserted_fixture_ids ) == 0 ) or ( fixture_id in self.times_favoritos and self.varios_jogos):
                               
                                aposta_feita = False
                                if next_goal_odd >= self.limite_inferior and next_goal_odd < self.limite_superior and self.bets_made.get(fixture_id+periodo) == None:                                    
                                    aposta_feita = await self.make_bet_2( nome_evento, periodo, next_goal_option_id )                                                                        

                                if aposta_feita:            
                                    self.bets_made[fixture_id+periodo] = True                                 

                                    bet = self.chrome.execute_script(f"let d = await fetch('{base_url}/sports/api/mybets/betslip?betslipId={self.bet_slip_number_1}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }} ); return await d.json();")

                                    bet = bet['betslip']

                                    fixture_id_to_betslip[fixture_id] = self.bet_slip_number_1

                                    self.first_message_after_bet = True                                                                                                        
                                    try:
                                        await self.telegram_bot.envia_mensagem(f"""{bet['bets'][0]['market']['name']}: {bet['bets'][0]['option']['name']}
{gols_casa} - {home_team_name}
{gols_fora} - {away_team_name}
{floor(cronometro)} {periodo}
PERDA ACUMULADA: R$ {self.perda_acumulada:.2f}
APOSTA {self.qt_apostas_feitas_txt}""")
                                    except:
                                        pass
                                    if not self.varios_jogos:
                                        break
                                                # casa_fora_temp = matches_and_options[fixture_id]['casa_fora']
                                                # matches_and_options[fixture_id]['casa_fora'] = 'casa' if casa_fora_temp == 'fora' else 'fora'
                                            # else:
                                            #      await self.make_bet(nome_evento, matches_and_options[fixture_id]['option_id'])

                            if self.only_favorites:
                                if odd_time_1_resultado_partida <= 1.65 and gols_casa == gols_fora:
                                    any_match_of_interest = True
                                    if fixture_id not in self.times_favoritos:                             
                                        matches_and_options[fixture_id] = { 'market_name': next_goal_option_name, 'odd_before_score': next_goal_odd, 'stats_saved_1_t': False, 'stats_saved_2_t': False }
                                        self.times_favoritos.append(fixture_id)                                    
                                elif odd_time_2_resultado_partida <= 1.65 and gols_casa == gols_fora:
                                    any_match_of_interest = True
                                    if fixture_id not in self.times_favoritos:
                                        matches_and_options[fixture_id] = { 'market_name': next_goal_option_name, 'odd_before_score': next_goal_odd, 'stats_saved_1_t': False, 'stats_saved_2_t': False }
                                        self.times_favoritos.append(fixture_id)      
                            else:
                                if fixture_id not in self.times_favoritos:                             
                                    matches_and_options[fixture_id] = { 'market_name': next_goal_option_name, 'odd_before_score': next_goal_odd, 'stats_saved_1_t': False, 'stats_saved_2_t': False }
                                    self.times_favoritos.append(fixture_id)                                    

                       

                            # chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['chance dupla'] ,fixture['optionMarkets'] ) )

                            # chance_dupla = chance_dupla[0]
                            # odd_time_1_chance_dupla = float( chance_dupla['options'][0]['price']['odds'] )       
                            # time_1_chance_dupla_option_id = chance_dupla['options'][0]['id']                         
                            # odd_time_2_chance_dupla = float( chance_dupla['options'][1]['price']['odds'] )
                            # time_2_chance_dupla_option_id = chance_dupla['options'][1]['id']                              
                                                                               
                        except IndexError as index_error:
                            print(index_error)
                            continue
                        except Exception as e:                                    
                            print(e)

                    # aqui vamos fazer a aposta
                    with open('matches_and_options.pkl', 'wb') as fp:
                        pickle.dump(matches_and_options, fp)        
                    with open('fixture_id_to_betslip.pkl', 'wb') as fp:
                        pickle.dump(fixture_id_to_betslip, fp)   
                    self.save_array_on_disk('times_favoritos.json', self.times_favoritos)

            except KeyboardInterrupt as e:                
                self.sair()
            except Exception as e:                
                deu_erro = True                
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                sleep(0.5)
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                self.numero_apostas_feitas = 0
                await self.testa_sessao()
                print(e)                
                self.tempo_pausa = 1                                 

            print('Esperando...')
            sleep(self.tempo_pausa)    

    def save_array_on_disk(self, nome_arquivo, array):        
        with open(nome_arquivo, "w") as fp:
            json.dump(array, fp)

if __name__ == '__main__':

    try:
        chrome = ChromeAuto(numero_apostas=200, numero_jogos_por_aposta=10)
        chrome.acessa(f'{base_url}/sports')                    
        asyncio.run( chrome.geysons_strategy() )
    except Exception as e:
        print(e)