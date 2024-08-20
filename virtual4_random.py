from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import traceback
import random
from time import sleep
import pause
import os
from datetime import datetime, timedelta
from credenciais import usuario, senha
from telegram_bot import TelegramBot, TelegramBotErro
from utils import *
from analisador_resultados_3 import numero_gols
from dutching import calcula_dutching
import sys
import json

import asyncio

class ChromeAuto():
    def __init__(self):        
        self.saldo = 0
        self.game_url = ''
        self.saldo_inicial = 0
        self.valor_aposta = self.saldo_inicial / 10
        self.meta = self.saldo_inicial + self.valor_aposta
        self.saldo_antes_aposta = 0.0
        self.aposta_fechada = False
        self.telegram_bot = TelegramBot()
        self.telegram_bot_erro = TelegramBotErro()                             
        self.primeiro_alerta_depois_do_jogo = True
        self.numero_erros_global = 0
        self.tempo_pausa = None
        self.primeiro_alerta_sem_jogos_elegiveis = True
        self.saldo_inicio_dia = 0.0
        self.aposta_fechada = False
        self.meta_ganho = 0.0
        self.hora_ultima_aposta = ''
        self.ganhou = False
        self.qt_apostas_feitas = [0,0,0,0,0]
        self.qt_apostas_feitas_txt = 0
        self.numero_overs_seguidos = 0
        self.numero_unders_seguidos = 0
        self.perda_acumulada = 0.0
        self.meta_ganho = 0.0
        self.graphic_chrome = None
        self.aposta_com_erro = False        
        self.is_for_real = False
        self.maior_saldo = 0.0
        self.hora_jogo = None
        self.qt_real_bets = 0
        self.url = None
        self.game_index = 0
        self.bet_id = None
        self.ultimo_resultado = None
        return
    
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

    def refresh_page(self):
        print('refresh page')
        try:
            action = ActionChains(self.chrome)
            action.key_down(Keys.CONTROL).send_keys(Keys.F5).key_up(Keys.CONTROL).perform()
            action.move_to_element( WebDriverWait(self.chrome, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))).send_keys(Keys.F5).perform()
        except Exception as e:
            print(e)

    def create_graphic_chrome(self):
        driver_path = 'chromedriver.exe'
        options = Options()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument("--dns-prefetch-disable")                     
        options.add_argument("--force-device-scale-factor=0.7")                                
        options.add_argument("--log-level=3") 
        options.add_argument("--no-sandbox")
        options.add_argument("--silent")
        options.add_argument("user-data-dir=C:\\Users\\anderson.morais\\AppData\\Local\\Google\\Chrome\\bet_data\\")
        options.page_load_strategy = 'eager'            
        return webdriver.Chrome( service=ChromeService(executable_path=driver_path), options=options) 

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
                self.options.add_argument('--headless')
                self.options.add_argument("--force-device-scale-factor=0.7")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                self.options.page_load_strategy = 'eager'            
                self.chrome = webdriver.Chrome( service=ChromeService(executable_path=self.driver_path), options=self.options)                
                
                # definimos quanto um script vai esperar pela resposta
                self.chrome.get(site)
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()                

                carregou_site = True
            except Exception as e:
                print(e)
                sleep(5)

    def sair(self):
        self.chrome.quit()

    async def get(self, web_driver, url):
        n_errors = 0
        while True:
            if n_errors > 10:
                try:
                    await self.telegram_bot_erro.envia_mensagem('sistema travado no método get')
                except:
                    pass
            try:
                result = web_driver.execute_script(url)
                return result
            except:
                n_errors += 1
                await self.testa_sessao()
                sleep(1)

    def clica_horario_jogo(self, horario_jogo):

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        self.fecha_banners()

        try:
            horario = WebDriverWait(self.graphic_chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, horario_jogo)))
            horario.click()
            sleep(0.5)
            horario.click()
            sleep(0.5)
            print('clicou no jogo')
            return True
        except Exception as e:
            print('erro no clica horário jogo')
            print(e) 
            return False

    async def testa_sessao(self):
        print('testando sessão...')
        try:
            jogos_abertos = self.graphic_chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if not jogos_abertos['summary']['hasError']:
                print('sessão ativa')
                self.graphic_chrome.get(self.game_url)
                self.graphic_chrome.maximize_window()
                self.graphic_chrome.fullscreen_window()
        except:
            print('sessão expirada. tentando login novamente.')
            try:
                try:
                    await self.telegram_bot_erro.envia_mensagem('sessão expirada')
                except:
                    traceback.print_exc()
                self.graphic_chrome.get('https://sports.sportingbet.com/pt-br/sports')
                self.graphic_chrome.maximize_window()
                self.graphic_chrome.fullscreen_window()
                return self.faz_login()
            except Exception as e:
                try:
                    await self.telegram_bot_erro.envia_mensagem('exception no testa sessão')
                except:
                    traceback.print_exc()
                print(e)
            finally:
                self.graphic_chrome.get('https://sports.sportingbet.com/pt-br/sports')
                self.graphic_chrome.maximize_window()
                self.graphic_chrome.fullscreen_window()
                return self.faz_login()

    def espera_resultado_jogo_sem_aposta(self, horario_jogo):

        try:
            horario = horario_jogo
            print('HORÁRIO',  horario )
            print('Esperando resultado da partida sem aposta...')
            #self.telegram_bot.envia_mensagem(f'esperando resultado aposta {horario}\nnumero reds: {self.numero_reds}')
            hora = int(horario.split(':')[0])
            minuto = int(horario.split(':')[1])
            now = datetime.today()  
            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)

            pause.until( hora_do_jogo + timedelta(minutes=1, seconds=10)  )
        except:
            print('algo saiu errado no espera resultado sem aposta')
                    
    async def espera_resultado_over_under(self, porcentagem, index_range):
        return await self.espera_resultado_over_under_um_jogo(porcentagem, index_range)
        
    async def return_next_open_bet_schedule(self, betslip):
        if betslip['state'] != 'Open':
            return None
        for bet in betslip['bets']:
            if bet['state'] == 'Open':
                temp = datetime.strptime( bet['fixture']['date'], '%Y-%m-%dT%H:%M:%SZ' ) - timedelta(hours=3)
                return temp.strftime('%H:%M')
        return None
        
    async def espera_resultado(self):
        
        try:                     
            while True:    

                sleep(5)

                jogos_abertos = await self.get(self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

                if jogos_abertos['summary']['openBetsCount'] == 0:
                    aposta_fechada = await self.get( self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                    if aposta_fechada['betslips'][0]['state'] == 'Won':
                        self.saldo += float( aposta_fechada['betslips'][0]['payout']['value'] )
                        return True
                    else:
                        return False  

                horario = await self.return_next_open_bet_schedule(jogos_abertos['betslips'][0])

                if horario == None:
                    aposta_fechada = await self.get( self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                    if aposta_fechada['betslips'][0]['state'] == 'Won':
                        self.saldo += float( aposta_fechada['betslips'][0]['payout']['value'] )
                        return True
                    else:
                        return False    
                else:
                    print('HORÁRIO',  horario )
                    print('Esperando resultado da partida...')
                    hora = int(horario.split(':')[0])
                    minuto = int(horario.split(':')[1])
                    now = datetime.today()  
                    hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
                    pause.until( hora_do_jogo + timedelta(minutes=1, seconds=30)  )                   
               
        except Exception as e:
            traceback.print_exc()
            await self.testa_sessao()
            print('Algo saiu errada no espera_resultado')   
            return False
    
    async def espera_resultado_over_under_dois_jogos(self, porcentagem):

        try:

                           
            jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')    

            bets = jogos_abertos['betslips'][0]['bets']

            horario_jogo = bets[0]['fixture']['date']

            horario_jogo = datetime.strptime( horario_jogo, '%Y-%m-%dT%H:%M:%SZ' )
            horario_jogo = horario_jogo - timedelta(hours=3)
            horario_jogo_string = horario_jogo.strftime( '%H:%M' )

            print('HORÁRIO',  horario_jogo_string )
            print('Esperando resultado da partida...')
            hora = int(horario_jogo_string.split(':')[0])
            minuto = int(horario_jogo_string.split(':')[1])
            now = datetime.today()  
            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
            pause.until( hora_do_jogo + timedelta(minutes=1, seconds=30)  )
            '''saldo = self.chrome.find_element(By.XPATH, '/html/body/vn-app/vn-dynamic-layout-single-slot[2]/vn-header/header/nav/vn-header-section[2]/vn-h-avatar-balance/vn-h-balance/div[2]')
            saldo.click()'''
            
            jogos_abertos = None
               
            jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

            jogo_encerrado = None
            mercado_ultima_aposta = None

            if jogos_abertos['summary']['openBetsCount'] == 0:


                jogo_encerrado = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                mercado_ultima_aposta = jogo_encerrado['betslips'][0]['bets'][0]['option']['name']

                if mercado_ultima_aposta == 'Acima de 2.5':
                    self.numero_unders_seguidos = 1
                    self.numero_overs_seguidos = 0
                else:
                    self.numero_overs_seguidos = 1
                    self.numero_unders_seguidos = 0
                return

            bet_1 = jogos_abertos['betslips'][0]['bets'][0]['state']

            count = 0
            while bet_1 == 'Open':
                print('ainda não apurou resultado')
                count += 1

                if count == 20:
                    try:
                        await self.telegram_bot_erro.envia_mensagem('sistema travado na apuração do resultado')
                    except:
                        pass

                sleep(1)

                jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['openBetsCount'] > 0:
                    bet_1 = jogos_abertos['betslips'][0]['bets'][0]['state']
                else:

                    jogo_encerrado = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                    mercado_ultima_aposta = jogo_encerrado['betslips'][0]['bets'][0]['option']['name']

                    if mercado_ultima_aposta == 'Acima de 2.5':
                        self.numero_unders_seguidos = 1
                        self.numero_overs_seguidos = 0
                    else:
                        self.numero_overs_seguidos = 1
                        self.numero_unders_seguidos = 0
                    return

            
            #segunda aposta
            jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')


            bets = jogos_abertos['betslips'][0]['bets']

            horario_jogo = bets[1]['fixture']['date']

            horario_jogo = datetime.strptime( horario_jogo, '%Y-%m-%dT%H:%M:%SZ' )
            horario_jogo = horario_jogo - timedelta(hours=3)
            horario_jogo_string = horario_jogo.strftime( '%H:%M' )

            print('HORÁRIO',  horario_jogo_string )
            print('Esperando resultado da partida...')
            hora = int(horario_jogo_string.split(':')[0])
            minuto = int(horario_jogo_string.split(':')[1])
            now = datetime.today()  
            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
            pause.until( hora_do_jogo + timedelta(minutes=1, seconds=30)  )
            '''saldo = self.chrome.find_element(By.XPATH, '/html/body/vn-app/vn-dynamic-layout-single-slot[2]/vn-header/header/nav/vn-header-section[2]/vn-h-avatar-balance/vn-h-balance/div[2]')
            saldo.click()'''
            
            jogos_abertos = None

            
            jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')


            while jogos_abertos['summary']['openBetsCount'] > 0:        
                jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')


            jogos_encerrados = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=2"); return await d.json();')
            jogo_encerrado = jogos_encerrados['betslips'][0]

            if jogo_encerrado['state'] == 'Won':             

                valor_ganho = float( jogo_encerrado['payout']['value'] )          

                self.saldo += valor_ganho
                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
                print(f'saldo depois do resultado {self.saldo:.2f}' )                    

                self.meta_ganho = self.saldo * porcentagem if porcentagem != None else self.meta_ganho
                self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')   
                if valor_ganho > self.perda_acumulada:                                        
                    self.perda_acumulada = 0.0
                    await self.telegram_bot_erro.envia_mensagem(f'ganhou!\nsaldo: {self.saldo:.2f}')
                else:
                    self.perda_acumulada -= valor_ganho             
                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')   

                self.qt_apostas_feitas = 0
                self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')     
                self.numero_unders_seguidos = 1
                self.numero_overs_seguidos = 0                     
            else:
                jogo_encerrado = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                mercado_ultima_aposta = jogo_encerrado['betslips'][0]['bets'][0]['option']['name']

                if mercado_ultima_aposta == 'Acima de 2.5':
                    self.numero_unders_seguidos = 1
                    self.numero_overs_seguidos = 0
                else:
                    self.numero_overs_seguidos = 1
                    self.numero_unders_seguidos = 0
                return
        except Exception as e:
            print(e)
            await self.testa_sessao()
            print('Algo saiu errada no espera_resultado')

    def faz_login(self):
        print('faz login')      

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        url_acesso = 'https://sports.sportingbet.com/pt-br/sports'

        tentativas = 0
        fez_login_com_sucesso = False
        while not fez_login_com_sucesso:
            try:
                try:
                    jogos_abertos = self.graphic_chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                    if not jogos_abertos['summary']['hasError']:
                        print('logou com sucesso')
                        self.graphic_chrome.get(self.game_url)
                        self.graphic_chrome.maximize_window()
                        self.graphic_chrome.fullscreen_window()   
                        return 
                except Exception as e:
                    print('não está logado')

                vezes_fechar_banner = 0        

                while vezes_fechar_banner < 5:
                    try:
                        self.fecha_banners()
                    except:
                        print('Erro ao tentar fechar banner')
                        traceback.print_exc()                        
                    vezes_fechar_banner += 1
                    sleep(1)

                # self.graphic_chrome.switch_to.default_content()
                if url_acesso == 'https://sports.sportingbet.com/pt-br/sports':
                    try: 
                        botao_login = WebDriverWait(self.graphic_chrome, 5).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='https://www.sportingbet.com/pt-br/labelhost/login']" )  )) 
                        botao_login.click()
                    except Exception as e:
                        # se não encontrar botão de login é porque já está logado
                        print('não encontrou o botão de login')
                        traceback.print_exc()
                        raise Exception()

                input_login = WebDriverWait(self.graphic_chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'userId' )  )) 
                input_login.clear()
                input_login.send_keys(usuario)         

                print('achou campo login')
                
                input_password = WebDriverWait(self.graphic_chrome, 10).until(
                    EC.element_to_be_clickable((By.NAME, 'password' )  )) 
                input_password.clear()
                input_password.send_keys(senha)

                print('achou campo senha')

                remember_me = WebDriverWait(self.graphic_chrome, 10).until(
                    EC.element_to_be_clickable((By.ID, 'rememberMe' )  ))
                remember_me.click()

                print('clicou no remember me')

                sleep(1)

                botao_login = WebDriverWait(self.graphic_chrome, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="login w-100 btn btn-primary"]' )  )) 
                sleep(1)

                print('achou botaão de login')
                
                botao_login.click()

                print('clicou no login')            
               
                erro = False
                while True:
                    try:
                        jogos_abertos = self.graphic_chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        if not jogos_abertos['summary']['hasError']:
                            self.graphic_chrome.get(self.game_url)
                            self.graphic_chrome.maximize_window()
                            self.graphic_chrome.fullscreen_window()   
                            return
                    except:
                        try:
                            if url_acesso == 'https://sports.sportingbet.com/pt-br/sports': 
                                WebDriverWait(self.graphic_chrome, 1).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, '.theme-error-i.ng-star-inserted' )  ))
                                erro = True
                                break
                            else:
                                WebDriverWait(self.graphic_chrome, 1).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, '.theme-error-i' )  ))
                                erro = True
                                break
                        except:
                            sleep(1)
                            
                
                if erro:
                    raise Exception()

                # aqui vou tentar buscar algo da API pra ver se logou de verdade
                jogos_abertos = self.graphic_chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if not jogos_abertos['summary']['hasError']:
                    print('logou com sucesso') 
                    self.graphic_chrome.get(self.game_url)
                    self.graphic_chrome.maximize_window()
                    self.graphic_chrome.fullscreen_window()   
                    return              
                try:
                    cookies = WebDriverWait(self.graphic_chrome, 10).until(
                        EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler' ) )) 
                    cookies.click() 
                except Exception as e:
                    print('erro ao clicar no botão dos cookies')
                    traceback.print_exc()

                fez_login_com_sucesso = True

                try:
                    self.fecha_banners()
                except Exception as e:
                    traceback.print_exc()
                    print('Erro ao tentar fechar banner')

            except Exception as e:
                print(e)
                print('erro aleatório')
                tentativas += 1
                if url_acesso == 'https://sports.sportingbet.com/pt-br/sports':
                    url_acesso = 'https://sports.sportingbet.com/pt-br/labelhost/login'
                else:
                    url_acesso = 'https://sports.sportingbet.com/pt-br/sports'
                self.graphic_chrome.get(url_acesso)
                self.graphic_chrome.maximize_window()
                self.graphic_chrome.fullscreen_window()
                traceback.print_exc()

    async def insere_valor_dutching(self, id_jogo):
        jogos_abertos = None
        apostou = False

        self.fecha_banners()

        while not apostou:
            try:
                print('entrou no insere valor')

                if self.valor_aposta < 0.1:
                    self.valor_aposta = 0.1

                #self.valor_aposta = 0.1
        
                clicou = False
                count = 0
                while not clicou and count < 5:
                    try:                
                        valor_do_campo = f'{self.valor_aposta:.2f}'.replace('.', ',')
                        input_field = WebDriverWait(self.graphic_chrome, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
                        input_field.send_keys(u'\ue009' + u'\ue003')                    
                        input_field.send_keys(valor_do_campo)                    

                        sleep(0.5)      

                        input_field = WebDriverWait(self.graphic_chrome, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') ))                                   

                        valor_input = input_field.get_attribute('value').strip()
                        print('valor input ', valor_input)
                        while valor_input != valor_do_campo: 
                            input_field.send_keys(u'\ue009' + u'\ue003')                    
                            input_field.send_keys(valor_do_campo)
                            sleep(0.5)

                        clicou = True
                    except Exception as e:
                        count += 1                        
                
                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return False
                            
                sleep(0.2)

                clicou = False
                count = 0
                while not clicou and count < 5:
                    try:
                        botao_aposta = WebDriverWait(self.graphic_chrome, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                        botao_aposta.click()    
                        clicou = True 
                    except:
                        count += 1

                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return False
                        
                sleep(1)

                count = 0

                jogos_abertos = await self.get(self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

                while jogos_abertos['summary']['openBetsCount'] == 0 and count < 5:                    
                    try:
                        botao_aposta = WebDriverWait(self.graphic_chrome, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                        botao_aposta.click()    
                        clicou = True 
                    except:
                        count += 1
                    finally:
                        jogos_abertos = await self.get(self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        sleep(2)

                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return False

                clicou = False
                count = 0
                while not clicou and count < 5:
                    try:
                        botao_fechar = WebDriverWait(self.graphic_chrome, 60).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions.ng-star-inserted button' ) )) 
                        botao_fechar.click() 
                        clicou = True
                    except:
                        count += 1
                        # se ele não clicou no botão de fechar aposta é porque provavelmente ela não foi feita
                        print('erro ao clicar no botão de fechar')              

                if count == 5:
                    await self.testa_sessao()   
                    self.aposta_com_erro = True
                    return False  

                apostou = True
                return True

            except Exception as e:
                print('erro no insere valor')
                self.aposta_com_erro = True
                print(e)
                await self.testa_sessao()
                #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
                try:
                    self.graphic_chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.graphic_chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
                return False
    
    async def le_saldo(self):        
        leu_saldo = False        
        while not leu_saldo:
            try:
                saldo_request = self.graphic_chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/pt-br/api/balance?forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
                self.saldo = float(saldo_request['balance']['accountBalance'])
                leu_saldo = True
            except Exception as e:
                sleep(5)
                print(e)                
                await self.testa_sessao()                
                self.graphic_chrome.refresh()
                print('Não foi possível ler saldo. Tentando de novo...')

    
    def disable_quickedit(self):
        if not os.name == 'posix':
            try:
                import msvcrt
                import ctypes
                kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
                device = r'\\.\CONIN$'
                with open(device, 'r') as con:
                    hCon = msvcrt.get_osfhandle(con.fileno())
                    kernel32.SetConsoleMode(hCon, 0x0080)
            except Exception as e:
                print('Cannot disable QuickEdit mode! ' + str(e))
                print('.. As a consequence the script might be automatically\
                paused on Windows terminal')

    def define_hora_jogo(self, hora_jogo_atual):
        hora = int(hora_jogo_atual.split(':')[0])
        minuto = int(hora_jogo_atual.split(':')[1])
        now = datetime.today()  
        hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
        hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=3)
        hora_jogo_atual =  hora_jogo_atual_datetime.strftime("%H:%M")
        return hora_jogo_atual
    
    async def is_bet_open(self):
        return False
        print('verificando se aposta há apostas abertas')
        jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
        if jogos_abertos['summary']['openBetsCount'] > 0:
            return True
        return False
    
    async def proximo_horario(self, hora_atual):
        
        jogos = None
        for i in range(2):
            jogos = await self.get(self.chrome, f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/sports?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&scheduleSize=10', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
            sleep(2)

        futebol_virtual = None

        for sport in jogos:
            if int( sport['sport']['id'] ) == 101:
                futebol_virtual = sport['competitions']
                break

        horarios_proximos_jogos = list( map( lambda e: self.return_hour(e['startDate']), futebol_virtual[self.game_index]['schedule'] ) ) 
        try:
            match_index = horarios_proximos_jogos.index(hora_atual)
            return horarios_proximos_jogos[match_index + 1]
        except:
            return horarios_proximos_jogos[0]

    def proximo_horario_disponivel(self, hora_atual):

        hora = int(hora_atual.split(':')[0])
        minuto = int(hora_atual.split(':')[1])
        now = datetime.today()  
        hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
        hora_datetime = hora_do_jogo   
        hora = hora_datetime.strftime( '%H:%M' )      

        first_time = True

        # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
        while True:
            self.fecha_banners()
            if first_time:
                hora_temp = hora
                hora_datetime_temp = hora_datetime
                while True:
                    try:
                        horario = WebDriverWait(self.chrome, 10).until(
                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{hora_temp}']")))
                        horario.click()
                        sleep(0.5)
                        horario.click()
                        sleep(0.5)
                        print(f'clicou no jogo {hora_temp}')
                        break
                    except:
                        print(f'erro ao clicar no horário {hora_temp}')  
                        self.chrome.refresh()
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()
                        hora_datetime_temp = hora_datetime_temp + timedelta(minutes=1)
                        hora_temp = hora_datetime_temp.strftime( '%H:%M' )    

            try:
                horario = WebDriverWait(self.chrome, 5).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{hora}']")))
                horario.click()
                sleep(0.5)
                horario.click()
                sleep(0.5)
                print(f'clicou no jogo {hora}')
                return hora
            except:
                print(f'erro ao clicar no horário {hora}')
                hora_datetime = hora_datetime + timedelta(minutes=1)
                hora = hora_datetime.strftime( '%H:%M' )      

    def fecha_banners(self):
        try:
            self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
        except:
            traceback.print_exc()        

        try:
            self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
        except Exception as e:                        
            traceback.print_exc()  

    def save_array_on_disk(self, file_name, array):        
        with open(file_name, "w") as fp:
            json.dump(array, fp)

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list   
        
    async def make_bets(self):
       
        # self.graphic_chrome.get(self.game_url)
        # self.graphic_chrome.maximize_window()
        # self.graphic_chrome.fullscreen_window()               

        try:
            while True:                       

                try:
                    self.graphic_chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.graphic_chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) {confirmacao.click(); }")                        
                except Exception as e:                        
                    print('Não conseguiu limpar os jogos...')
                    traceback.print_exc()   

                n_combinados = 3

                for i in range(n_combinados):          

                    self.fecha_banners()                                

                    self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')   

                    clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{self.hora_jogo}']")                  

                    count = 0
                    while not clicou and count < 3:                        
                        try:
                            self.fecha_banners()
                            await self.testa_sessao()
                            self.graphic_chrome.refresh()
                            self.graphic_chrome.maximize_window()
                            self.graphic_chrome.fullscreen_window()                 

                            clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{self.hora_jogo}']")                        
                        except:
                            sleep(1)                       
                            count += 1

                    if count == 3:                                             
                        raise Exception('raise exception 3')
                
                    self.options_market = ['Abaixo de 2.5', 'Acima de 2.5']
                    self.options_market_index = [0,0,0,1,1]
                    self.index = random.randint(0,4)

                    clicou = False
                    count = 0
                    while not clicou and count < 3:
                        try:
                            clique_odd_acima_1_meio = WebDriverWait(self.graphic_chrome, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{self.options_market[self.options_market_index[self.index]]}']/ancestor::ms-event-pick")))
                            clique_odd_acima_1_meio.click()
                            clicou = True
                        except Exception as e:
                            count += 1                        
                            self.fecha_banners()                                               
                            traceback.print_exc() 

                    if count == 3:
                        raise Exception('raise exception 4')

                    count = 0
                    texto = ''
                    while 'total de gols' not in texto.lower() and count < 20:
                        try:                        
                            if i == 0:
                                cupom = WebDriverWait(self.graphic_chrome, 5).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, f".betslip-digital-pick__line-1.ng-star-inserted" ) ))
                            else:
                                cupom = WebDriverWait(self.graphic_chrome, 5).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, f"bs-digital-combo-bet-pick:nth-child({i+1}) .betslip-digital-pick__line-1.ng-star-inserted" ) ))
                            if cupom != None and cupom.get_property('innerText') != None:
                                texto = cupom.get_property('innerText').lower().strip()
                                print(texto)
                        except:             
                            self.fecha_banners()             
                            count += 1

                    if count == 20:                                
                        raise Exception('raise exception 5')
                    
                    if i < n_combinados - 1:
                        self.hora_jogo = await self.proximo_horario(self.hora_jogo) 

                cota = WebDriverWait(self.graphic_chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                cota = float( cota.get_property('innerText') )

                self.valor_aposta = ( ( self.meta_ganho + self.perda_acumulada ) / ( cota - 1.0 ) ) + 0.01

                if self.valor_aposta < 0.1:
                    self.valor_aposta = 0.1

                self.valor_aposta = 0.1                           

                aposta_realizada = await self.insere_valor_dutching(None)

                if aposta_realizada:                           
                    jogo_aberto = await self.get(self.graphic_chrome, f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                    self.bet_id = jogo_aberto['betslips'][0]['betSlipNumber']                            
                    self.perda_acumulada += self.valor_aposta      
                    self.saldo -= self.valor_aposta           
                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                    self.qt_apostas_feitas_txt = self.le_de_arquivo('qt_apostas_feitas_txt.txt', 'int')
                    self.qt_apostas_feitas_txt += 1

                    if self.qt_apostas_feitas_txt % 5 == 0:
                        try:
                            await self.telegram_bot.envia_mensagem(f'aposta {self.qt_apostas_feitas_txt} realizada')
                        except:
                            print('erro ao enviar mensagem')

                    self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', f'{self.qt_apostas_feitas_txt}', 'w')

                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")

                    self.primeiro_alerta_depois_do_jogo = True
                    self.primeiro_alerta_sem_jogos_elegiveis = True            

                    self.qt_apostas_feitas[self.game_index] += 1
                    self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas )

                    # try:                                                                   
                    #     await self.telegram_bot.envia_mensagem(f"APOSTA {self.qt_apostas_feitas[self.game_index]} REALIZADA {self.url.split('/')[-1]}")
                    # except:
                    #     print('não conseguiu enviar mensagem')                        

                    ganhou_aposta = await self.espera_resultado()                    
                    if ganhou_aposta:      
                        print('ganhou')
                        self.perda_acumulada = 0.0
                        self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')
                        try:
                            await self.telegram_bot_erro.envia_mensagem(f"ganhou depois de {self.qt_apostas_feitas_txt} apostas\nsaldo: {self.saldo:.2f}\n{self.url.split('/')[-1]}")
                        except:
                            traceback.print_exc()
                        self.qt_apostas_feitas[self.game_index] = 0
                        self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', '0', 'w')
                        self.qt_apostas_feitas_txt = 0
                        # self.meta_ganho = 0.01 * self.saldo
                        # self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')
                        self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas)
                        #self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
                        self.qt_sem_dois_gols = 0
                        #self.graphic_chrome.quit()
                        return
                    else:
                        print('perdeu')   
                        return

                else:
                    print('ocorreu um erro ao fazer aposta')
                    raise Exception('erro ao fazer aposta')      

        except Exception as e:
            try:
                await self.telegram_bot_erro.envia_mensagem(f"exception no main loop {self.url.split('/')[-1]}")
            except:
                pass
            traceback.print_exc()
            print('exception no main loop')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) { confirmacao.click(); }")                        
            except Exception as e:
                print('Não conseguiu limpar os jogos...')
                traceback.print_exc()
            await self.testa_sessao()
            self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
            self.aposta_com_erro = True
            self.is_for_real = False
            self.numero_unders_seguidos = 0
            self.numero_overs_seguidos = 0    
            self.qt_apostas_feitas[self.game_index] = 0
            self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas)
            self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
            return
                       
    async def padroes(self):
        print('under over under')
        self.qt_apostas_feitas = self.read_array_from_disk('qt_apostas_feitas.json')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')   
        await self.le_saldo()
        self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')                  
        
        url_champions_cup = self.game_url
        if self.saldo == 0.0:
            self.le_saldo()
            self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')

        #self.chrome.get(url_champions_cup)
        #self.chrome.maximize_window()
        #self.chrome.fullscreen_window()
    
        jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
        if jogos_abertos['summary']['openBetsCount'] > 0:                                 
            ganhou_aposta = await self.espera_resultado_over_under(0.00466, len( jogos_abertos['betslips'][0]['bets'] ) )
            if ganhou_aposta:                    
                self.qt_apostas_feitas[self.game_index] = 0
                self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas)
                self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')
                try:
                    await self.telegram_bot_erro.envia_mensagem(f"ganhou depois de {self.qt_apostas_feitas[self.game_index]} {self.url.split('/')[-1]}")
                except:
                    traceback.print_exc()
            else:
                print('perdeu')

        qt_sem_dois_gols = 0   

        while True:                  
            horarios_apostas = ['', '', '']     
            try:
                telegram = TelegramBotErro()

                numero_gols_ = None
                anterior = None
                qt_intercalados = 0
                qt_under = 0
                qt_over = 0                    
                qt_sem_dois_gols = 0  

                ultimo_mercado = 'over'

                self.chrome.refresh()
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()

                while True:
                    if not self.hora_jogo:
                        self.hora_jogo = self.proximo_horario_disponivel( datetime.now().strftime('%H:%M') )
                    else:
                        self.hora_jogo = self.proximo_horario(self.hora_jogo)
                    self.espera_resultado_jogo_sem_aposta(self.hora_jogo)                    
                    #champions_cup_start_date_string = self.define_hora_jogo(champions_cup_start_date_string)
                    numero_gols_ = numero_gols(self.url)
                    if numero_gols_ == None:
                        anterior = None
                        qt_intercalados = 1
                        qt_sem_dois_gols = 0
                        qt_under = 0
                        qt_over = 0
                        try:
                            await telegram.envia_mensagem(f"erro no {self.url.split('/')[-1]}")
                        except Exception as e:
                            traceback.print_exc() 
                    else:
                        if numero_gols_ != 2:
                            qt_sem_dois_gols += 1
                        else:
                            if qt_sem_dois_gols >= 6 and qt_sem_dois_gols <= 9:
                                try:
                                    await telegram.envia_mensagem(f"dois gols depois de {qt_sem_dois_gols} {self.url.split('/')[-1]}")
                                except Exception as e:
                                    traceback.print_exc() 
                            qt_sem_dois_gols = 0
                        # if anterior == None:
                        #     anterior = numero_gols_
                        #     qt_intercalados += 1
                        #     if numero_gols_ < 3:
                        #         qt_under = 1
                        #         qt_over = 0
                        #     else:
                        #         qt_over = 1
                        #         qt_under = 0
                        # else:
                        #     if numero_gols_ > 2 and anterior <= 2 or numero_gols_ <= 2 and anterior > 2:
                        #         if numero_gols_ > 2:
                        #             ultimo_mercado = 'over'
                        #         else:
                        #             ultimo_mercado = 'under'
                        #         qt_intercalados += 1
                        #     else:
                        #         qt_intercalados = 1

                        #     if numero_gols_ < 3:
                        #         if anterior < 3:
                        #             qt_under += 1
                        #         else:
                        #             qt_under = 1
                        #             qt_over = 0

                        #     if numero_gols_ > 2:
                        #         if anterior > 2:
                        #             qt_over +=1 
                        #         else:
                        #             qt_over = 1
                        #             qt_under = 0
                            
                        #     anterior = numero_gols_
                        # print('qt_intercalados ', qt_intercalados)                        
                        # print('qt_under ', qt_under)
                        
                    try:
                        if qt_sem_dois_gols % 5 == 0 and qt_sem_dois_gols != 0:
                            await telegram.envia_mensagem(f"{qt_sem_dois_gols} jogo sem dois gols {self.url.split('/')[-1]}")
                    except:
                        traceback.print_exc() 
                    # print('qt_over ', qt_over)

                    print(f'sequência de jogos sem dois gols: {qt_sem_dois_gols}')

                    if qt_sem_dois_gols >= 17: 
                        self.bet_being_made = self.le_de_arquivo('bet_being_made.txt', 'boolean')
                        if not self.bet_being_made:
                            self.escreve_em_arquivo('bet_being_made.txt', 'True', 'w')
                            break     

                # await self.le_saldo()          

                # self.meta_ganho = self.saldo * 0.0008735

                while True:
                    
                    self.chrome.refresh()
                    self.chrome.maximize_window()
                    self.chrome.fullscreen_window()

                    qt_under = 1              

                    is_first_time = True

                    tipo_aposta = None

                    mercados = [['Abaixo de 2.5', 'Abaixo de 2.5', 'Abaixo de 2.5'], 
                                ['Acima de 2.5', 'Abaixo de 2.5', 'Acima de 2.5'], 
                                ['Abaixo de 2.5', 'Acima de 2.5', 'Abaixo de 2.5']]

                    # if qt_intercalados >= 4:
                    #     mercados[0] = 'Acima de 2.5' if ultimo_mercado == 'under' else 'Abaixo de 2.5'
                    #     mercados[1] = 'Abaixo de 2.5' if ultimo_mercado == 'under' else 'Acima de 2.5'
                    #     tipo_aposta = 'intercalado'
                    # if qt_under >= 1:
                    #     mercados[0] = 'Abaixo de 2.5'
                    #     mercados[1] = 'Abaixo de 2.5'
                    #     mercados[2] = 'Abaixo de 2.5'
                    #     tipo_aposta = 'under'
                    # elif qt_over == 4:
                    #     mercados[0] = 'Acima de 2.5'
                    #     mercados[1] = 'Acima de 2.5'
                    #     tipo_aposta = 'over'                          

                    try:
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) {confirmacao.click(); }")                        
                    except Exception as e:                        
                        print('Não conseguiu limpar os jogos...')
                        traceback.print_exc()             

                    self.fecha_banners()                    

                    index_range = 3

                    if qt_under >= 1:
                        index_range = 3
                    elif qt_over >= 4:
                        index_range = 3

                    horario_jogo = None
                    data_test_option_id = ''
                    mercado_anterior = ''

                    jogos_odds = [{'under': 0.0, 'over': 0.0 },{'under': 0.0, 'over': 0.0 },{'under': 0.0, 'over': 0.0 }]

                    odds_dutching = [0,0,0]
                    valores_apostas = [0.0, 0.0, 0.0]

                    self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')

                    for j in range(1):
                        horario_jogo = None
                        data_test_option_id = ''
                        for i in range(1):
                            mercado = i % 3                     
                            
                            if j == 0:
                                if horario_jogo == None:
                                    horario_jogo = self.proximo_horario( self.hora_jogo )
                                else:
                                    horario_jogo = self.proximo_horario( self.hora_jogo )            
                                horarios_apostas[i] = horario_jogo
                            else:
                                horario_jogo = horarios_apostas[i]        

                            clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")

                            # find_data_test_option_id = False
                            # while not find_data_test_option_id:
                            #     try:
                            #         if data_test_option_id == '':
                            #             temp = WebDriverWait(self.chrome, 10).until(
                            #                         EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '2']/ancestor::ms-event-pick")))
                            #             data_test_option_id = temp.get_attribute('data-test-option-id')
                            #             print( data_test_option_id)
                            #             find_data_test_option_id = True
                            #         else:
                            #             temp = WebDriverWait(self.chrome, 10).until(
                            #                         EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '2']/ancestor::ms-event-pick")))
                            #             data_test_option_id_atual = temp.get_attribute('data-test-option-id')
                            #             while data_test_option_id == data_test_option_id_atual:
                            #                 print( data_test_option_id_atual)
                            #                 clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")     
                            #                 temp = WebDriverWait(self.chrome, 10).until(
                            #                         EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '2']/ancestor::ms-event-pick")))
                            #                 data_test_option_id_atual = temp.get_attribute('data-test-option-id')      
                            #             find_data_test_option_id = True                                                                       
                            #     except:
                            #         sleep(1)
                            #         pass

                            count = 0
                            while not clicou and count < 3:                        
                                try:
                                    self.fecha_banners()
                                    await self.testa_sessao()
                                    self.chrome.refresh()
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()                 

                                    clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")
                                    count += 1
                                except:
                                    sleep(1)
                                    pass                        
                            
                            if count == 3:             
                                horario_jogo = self.proximo_horario_disponivel(horario_jogo)                                
                            
                            count = 0
                            while not clicou and count < 3:                        
                                try:
                                    self.fecha_banners()
                                    await self.testa_sessao()
                                    self.chrome.refresh()
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()                 

                                    clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{horario_jogo}']")
                                    count += 1
                                except:
                                    sleep(1)
                                    pass     

                            if count == 3:                                             
                                await self.testa_sessao()
                                raise Exception('raise exception 3')
                        
                            clicou = False
                            count = 0
                            while not clicou and count < 3:
                                try:
                                    clique_odd_acima_1_meio = WebDriverWait(self.chrome, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '2']/ancestor::ms-event-pick")))
                                    clique_odd_acima_1_meio.click()
                                    clicou = True

                                    if j == 0:
                                        try:
                                            odd_acima_2_meio = WebDriverWait(self.chrome, 10).until(
                                                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = '2']/following-sibling::div")))
                                            print('odd ', odd_acima_2_meio.get_property('innerText'))

                                            odd_abaixo_2_meio = WebDriverWait(self.chrome, 10).until(
                                                    EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Abaixo de 2.5']/following-sibling::div")))
                                            print('odd ', odd_abaixo_2_meio.get_property('innerText'))
                                            
                                            jogos_odds[i]['over'] = float( odd_acima_2_meio.get_property('innerText') )
                                            jogos_odds[i]['under'] = float( odd_abaixo_2_meio.get_property('innerText') )
                                        except:
                                            pass

                                except Exception as e:
                                    count += 1
                                    try:
                                        self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
                                    except:
                                        traceback.print_exc() 
                                    print('exception 3')
                                    traceback.print_exc() 

                            if count == 3:
                                await self.testa_sessao()
                                raise Exception('raise exception 4')

                            count = 0
                            texto = ''
                            while 'total de gols' not in texto.lower() and count < 50:
                                try:
                                    if i == 0:
                                        cupom = WebDriverWait(self.chrome, 10).until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR, f".betslip-digital-pick__line-1.ng-star-inserted" ) ))
                                    else:
                                        cupom = WebDriverWait(self.chrome, 10).until(
                                                EC.presence_of_element_located((By.CSS_SELECTOR, f"bs-digital-combo-bet-pick:nth-child({i+1}) .betslip-digital-pick__line-1.ng-star-inserted" ) ))
                                    if cupom != None and cupom.get_property('innerText') != None:
                                        texto = cupom.get_property('innerText').lower().strip()
                                        print(texto)
                                except:                            
                                    sleep(1)
                                    count += 1

                            if count == 50:                                
                                await self.testa_sessao()
                                raise Exception('raise exception 5')
                            
                            hora = int(horario_jogo.split(':')[0])
                            minuto = int(horario_jogo.split(':')[1])
                            now = datetime.today()  
                            hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
                            hora_jogo_atual_datetime = hora_do_jogo + timedelta(minutes=3)
                            horario_jogo = hora_jogo_atual_datetime.strftime("%H:%M")

                        odds_dutching[0] = jogos_odds[0]['under'] * jogos_odds[1]['under'] * jogos_odds[2]['under']
                        odds_dutching[1] = jogos_odds[0]['over'] * jogos_odds[1]['under'] * jogos_odds[2]['over']
                        odds_dutching[2] = jogos_odds[0]['under'] * jogos_odds[1]['over'] * jogos_odds[2]['under']

                        # print(odds_dutching)

                        # valores_apostas = calcula_dutching( odds_dutching, 2.0 )

                        # print(valores_apostas)

                    cota = WebDriverWait(self.chrome, 10).until(
                                                EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                    cota = float( cota.get_property('innerText') )

                    jogo_encerrado = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                    if jogo_encerrado['betslips'][0]['state'] == 'Won':
                        self.qt_apostas_feitas = 0
                        self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')
                        self.perda_acumulada = 0.0
                        self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')

                    self.valor_aposta = ( ( self.meta_ganho + self.perda_acumulada ) / ( cota - 1.0 ) ) + 0.01

                    if self.valor_aposta < 0.1:
                        self.valor_aposta = 0.1                

                    if self.valor_aposta > self.saldo:
                        self.valor_aposta = 0.1
                        self.perda_acumulada = 0.0
                        self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada}', 'w')                  

                    aposta_realizada = await self.insere_valor_dutching(None)
    
                    try:
                        if aposta_realizada:                           
                            jogo_aberto = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            self.bet_id = jogo_aberto['betslips'][0]['betSlipNumber']                            
                            self.perda_acumulada += self.valor_aposta                 
                            self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                            self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")
                            self.horario_ultima_checagem = datetime.now()

                            self.primeiro_alerta_depois_do_jogo = True
                            self.primeiro_alerta_sem_jogos_elegiveis = True            

                            self.qt_apostas_feitas[self.game_index] += 1
                            self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas )

                            try:                                                                   
                                await self.telegram_bot.envia_mensagem(f"APOSTA {self.qt_apostas_feitas[self.game_index]} REALIZADA {self.url.split('/')[-1]}")
                            except:
                                pass  

                            ganhou_aposta = await self.espera_resultado_over_under(0.00466, index_range)
                            if ganhou_aposta:      
                                print('ganhou')
                                self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')
                                try:
                                    await self.telegram_bot_erro.envia_mensagem(f'ganhou depois de {self.qt_apostas_feitas[self.game_index]} apostas')
                                except:
                                    traceback.print_exc()
                                self.qt_apostas_feitas[self.game_index] = 0
                                self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas)
                                self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
                                qt_sem_dois_gols = 0
                                break
                            else:
                                print('perdeu')
                        else:
                            print('ocorreu um erro ao fazer aposta')
                    except:
                        traceback.print_exc()                

            except Exception as e:
                try:
                    await self.telegram_bot_erro.envia_mensagem(f"exception no main loop {self.url.split('/')[-1]}")
                except:
                    pass
                traceback.print_exc()
                print('exception no main loop')
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) { confirmacao.click(); }")                        
                except Exception as e:
                    print('Não conseguiu limpar os jogos...')
                    traceback.print_exc()
                await self.testa_sessao()
                self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
                self.aposta_com_erro = True
                self.is_for_real = False
                self.numero_unders_seguidos = 0
                self.numero_overs_seguidos = 0           
 

                       
    async def dois_overs_depois_dois_overs(self):
        print('under over under')
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')   
        self.is_for_real = self.le_de_arquivo('is_for_real.txt', 'boolean')
        self.numero_overs_seguidos = self.le_de_arquivo('numero_overs_seguidos.txt', 'int')
        self.numero_unders_seguidos = self.le_de_arquivo('numero_unders_seguidos.txt', 'int')
        self.mercado = self.le_de_arquivo('mercado.txt', 'string')
        self.maior_saldo = self.le_de_arquivo('maior_saldo.txt', 'float')
        self.qt_real_bets = self.le_de_arquivo('qt_real_bets.txt', 'int')
        await self.le_saldo()
        self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')                  
        
        url_champions_cup = self.game_url
        if self.saldo == 0.0:
            self.le_saldo()
            self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')
            if self.maior_saldo < self.saldo:
                self.maior_saldo = self.saldo
                self.escreve_em_arquivo('maior_saldo.txt', f'{self.maior_saldo:.2f}', 'w')

        self.chrome.get(url_champions_cup)
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()
    
        jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
        if jogos_abertos['summary']['openBetsCount'] > 0:            
            self.mercado = jogos_abertos['betslips'][0]['bets'][0]['option']['name']            
            await self.espera_resultado_over_under(0.00466)

        while True:           
            
            try:
                self.escreve_em_arquivo('is_for_real.txt', f'{self.is_for_real}', 'w')
                self.escreve_em_arquivo('numero_overs_seguidos.txt', f'{self.numero_overs_seguidos}', 'w')
                self.escreve_em_arquivo('numero_unders_seguidos.txt', f'{self.numero_unders_seguidos}', 'w')
                self.escreve_em_arquivo('mercado.txt', f'{self.mercado}', 'w')

                print(f'numero overs: {self.numero_overs_seguidos}\nnumero unders: {self.numero_unders_seguidos}')
                print(f'is_for_real: {self.is_for_real}\nmercado: {self.mercado}')

                jogos = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/sports?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&scheduleSize=10', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")

                futebol_virtual = None

                for sport in jogos:
                    if int( sport['sport']['id'] ) == 101:
                        futebol_virtual = sport['competitions']
                        break

                champions_id = futebol_virtual[self.game_index]['competition']['id']

                print('champions id ', champions_id)

                index_jogo = 0
                
                proximo_jogo_champions_cup = None
                for i in range(3):
                    proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&scheduleSize=10'); return await d.json();")
                    sleep(2)

                champions_cup_start_date = proximo_jogo_champions_cup['schedule'][index_jogo]['startDate']
                champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )

                index_jogo = 0

                id_jogos_champions_cup = list( map( lambda el: el['id'], proximo_jogo_champions_cup['schedule'] ) )

                print('id_jogos_champions_cup ', id_jogos_champions_cup)

                while champions_cup_start_date < datetime.now():                                                      

                    proximo_jogo_champions_cup = proximo_jogo_champions_cup['schedule'][index_jogo]
                    champions_id = futebol_virtual[self.game_index]['competition']['id']                
                    
                    proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date = proximo_jogo_champions_cup['fixture']['startDate']
                    champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                    champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )                             

                    index_jogo += 1      

                telegram = TelegramBotErro()

                numero_gols_ = None
                anterior = None
                qt_intercalados = 0
                qt_under = 0
                qt_over = 0

                ultimo_mercado = 'over'

                while True:
                    self.espera_resultado_jogo_sem_aposta(champions_cup_start_date_string)                    
                    champions_cup_start_date_string = self.define_hora_jogo(champions_cup_start_date_string)
                    numero_gols_ = numero_gols(self.url)
                    if numero_gols_ == None:
                        anterior = None
                        qt_intercalados = 1
                        qt_under = 0
                        qt_over = 0
                        try:
                            await telegram.envia_mensagem(f"erro no {self.url.split('/')[-1]}")
                        except Exception as e:
                            traceback.print_exc() 
                    else:
                        if anterior == None:
                            anterior = numero_gols_
                            qt_intercalados += 1
                            if numero_gols_ < 3:
                                qt_under = 1
                                qt_over = 0
                            else:
                                qt_over = 1
                                qt_under = 0
                        else:
                            if numero_gols_ > 2 and anterior <= 2 or numero_gols_ <= 2 and anterior > 2:
                                if numero_gols_ > 2:
                                    ultimo_mercado = 'over'
                                else:
                                    ultimo_mercado = 'under'
                                qt_intercalados += 1
                            else:
                                qt_intercalados = 1

                            if numero_gols_ < 3:
                                if anterior < 3:
                                    qt_under += 1
                                else:
                                    qt_under = 1
                                    qt_over = 0

                            if numero_gols_ > 2:
                                if anterior > 2:
                                    qt_over +=1 
                                else:
                                    qt_over = 1
                                    qt_under = 0
                            
                            anterior = numero_gols_
                        print('qt_intercalados ', qt_intercalados)                        
                        print('qt_under ', qt_under)
                        print('qt_over ', qt_over)
                        if qt_intercalados in [4, 5] or qt_over in [4, 5] or qt_under in [4, 5]: 
                            if not await self.is_bet_open():
                                break                               

                for i in range(3):                
                    jogos = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/sports?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&scheduleSize=10', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
                    sleep(2)                
                
                competition = None

                for sport in jogos:
                    if int( sport['sport']['id'] ) == 101:
                        competition = sport['competitions']
                        break

                horarios_proximos_jogos = list( map( lambda e: e['startDate'], competition[self.game_index]['schedule'] ) )

                champions_id = futebol_virtual[self.game_index]['competition']['id']

                print('champions id ', champions_id)

                index_jogo = 0                
                
                proximo_jogo_champions_cup = None
                for i in range(3):
                    proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&scheduleSize=10'); return await d.json();")
                    sleep(2)

                champions_cup_start_date = proximo_jogo_champions_cup['schedule'][index_jogo]['startDate']
                champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )

                index_jogo = 0

                id_jogos_champions_cup = list( map( lambda el: el['id'], proximo_jogo_champions_cup['schedule'] ) )

                while champions_cup_start_date < datetime.now():                                                      

                    proximo_jogo_champions_cup = proximo_jogo_champions_cup['schedule'][index_jogo]
                    champions_id = futebol_virtual[self.game_index]['competition']['id']                
                    
                    proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date = proximo_jogo_champions_cup['fixture']['startDate']
                    champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                    champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )                             

                    index_jogo += 1                      

                proximo_jogo_champions_cup_2 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                champions_cup_start_date_2 = proximo_jogo_champions_cup_2['fixture']['startDate']
                champions_cup_start_date_2 = datetime.strptime( champions_cup_start_date_2, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date_2 = champions_cup_start_date_2 - timedelta(hours=3)
                champions_cup_start_date_string_2 = champions_cup_start_date_2.strftime( '%H:%M' )                

                while champions_cup_start_date_2 <= champions_cup_start_date:
                    proximo_jogo_champions_cup_2 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date_2 = proximo_jogo_champions_cup_2['fixture']['startDate']
                    champions_cup_start_date_2 = datetime.strptime( champions_cup_start_date_2, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date_2 = champions_cup_start_date_2 - timedelta(hours=3)
                    champions_cup_start_date_string_2 = champions_cup_start_date_2.strftime( '%H:%M' )                    

                    index_jogo += 1 
                
                proximo_jogo_champions_cup_3 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                champions_cup_start_date_3 = proximo_jogo_champions_cup_3['fixture']['startDate']
                champions_cup_start_date_3 = datetime.strptime( champions_cup_start_date_3, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date_3 = champions_cup_start_date_3 - timedelta(hours=3)
                champions_cup_start_date_string_3 = champions_cup_start_date_3.strftime( '%H:%M' )                

                while champions_cup_start_date_3 <= champions_cup_start_date_2:
                    proximo_jogo_champions_cup_3 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date_3 = proximo_jogo_champions_cup_3['fixture']['startDate']
                    champions_cup_start_date_3 = datetime.strptime( champions_cup_start_date_3, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date_3 = champions_cup_start_date_3 - timedelta(hours=3)
                    champions_cup_start_date_string_3 = champions_cup_start_date_3.strftime( '%H:%M' )                    

                    index_jogo += 1

                proximo_jogo_champions_cup_4 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                champions_cup_start_date_4 = proximo_jogo_champions_cup_4['fixture']['startDate']
                champions_cup_start_date_4 = datetime.strptime( champions_cup_start_date_4, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date_4 = champions_cup_start_date_4 - timedelta(hours=3)
                champions_cup_start_date_string_4 = champions_cup_start_date_4.strftime( '%H:%M' )                

                while champions_cup_start_date_4 <= champions_cup_start_date_3:
                    proximo_jogo_champions_cup_4 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date_4 = proximo_jogo_champions_cup_4['fixture']['startDate']
                    champions_cup_start_date_4 = datetime.strptime( champions_cup_start_date_4, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date_4 = champions_cup_start_date_4 - timedelta(hours=3)
                    champions_cup_start_date_string_4 = champions_cup_start_date_4.strftime( '%H:%M' )                    

                    index_jogo += 1 

                proximo_jogo_champions_cup_5 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                champions_cup_start_date_5 = proximo_jogo_champions_cup_5['fixture']['startDate']
                champions_cup_start_date_5 = datetime.strptime( champions_cup_start_date_5, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date_5 = champions_cup_start_date_5 - timedelta(hours=3)
                champions_cup_start_date_string_5 = champions_cup_start_date_5.strftime( '%H:%M' )                

                while champions_cup_start_date_5 <= champions_cup_start_date_4:
                    proximo_jogo_champions_cup_5 = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date_5 = proximo_jogo_champions_cup_5['fixture']['startDate']
                    champions_cup_start_date_5 = datetime.strptime( champions_cup_start_date_5, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date_5 = champions_cup_start_date_5 - timedelta(hours=3)
                    champions_cup_start_date_string_5 = champions_cup_start_date_5.strftime( '%H:%M' )                    

                    index_jogo += 1 

                print('leu os jogos')

                mercado_par = None
                mercado_impar = None
                tipo_aposta = None

                if qt_intercalados >= 4:
                    mercado_par = 'Acima de 2.5' if ultimo_mercado == 'under' else 'Abaixo de 2.5'
                    mercado_impar = 'Abaixo de 2.5' if ultimo_mercado == 'under' else 'Acima de 2.5'
                    tipo_aposta = 'intercalado'
                elif qt_under >= 4:
                    mercado_par = 'Abaixo de 2.5'
                    mercado_impar = 'Abaixo de 2.5'
                    tipo_aposta = 'under'
                else:
                    mercado_par = 'Acima de 2.5'
                    mercado_impar = 'Acima de 2.5'
                    tipo_aposta = 'over'

                print('pegando primeiro mercado')
              
                for option_market in proximo_jogo_champions_cup['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():                        
                        proximo_jogo_champions_cup = option_market['options']
                        break

                proximo_jogo_champions_cup_option = None

                for option in proximo_jogo_champions_cup:                    
                    if option['name']['value'] == mercado_par or option['name']['value'] == mercado_par.replace(',', '.'):
                        proximo_jogo_champions_cup_option = option
                        break

                if not proximo_jogo_champions_cup_option:
                    print('não há proximo_jogo_champions_cup_option')
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict = dict()
                jogo_champions_cup_dict['horario'] = champions_cup_start_date_string                
                jogo_champions_cup_dict['optionid'] = proximo_jogo_champions_cup_option['id']
                jogo_champions_cup_dict['odd'] = float( proximo_jogo_champions_cup_option['price']['odds'] )                  

                print('pegando segundo mercado')

                for option_market in proximo_jogo_champions_cup_2['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_2 = option_market['options']
                        break

                proximo_jogo_champions_cup_2_option = None    

                for option in proximo_jogo_champions_cup_2:
                    if option['name']['value'] == mercado_impar or option['name']['value'] == mercado_impar.replace(',', '.'):
                        proximo_jogo_champions_cup_2_option = option
                        break

                if not proximo_jogo_champions_cup_2_option:
                    print('não há proximo_jogo_champions_cup_2_option')
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_2 = dict()
                jogo_champions_cup_dict_2['horario'] = champions_cup_start_date_string_2                
                jogo_champions_cup_dict_2['optionid'] = proximo_jogo_champions_cup_2_option['id']
                jogo_champions_cup_dict_2['odd'] = float( proximo_jogo_champions_cup_2_option['price']['odds'] ) 

                print('pegando terceiro mercado') 

                for option_market in proximo_jogo_champions_cup_3['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_3 = option_market['options']
                        break

                proximo_jogo_champions_cup_3_option = None

                for option in proximo_jogo_champions_cup_3:
                    if option['name']['value'] == mercado_par or option['name']['value'] == mercado_par.replace(',', '.'):
                        proximo_jogo_champions_cup_3_option = option
                        break

                if not proximo_jogo_champions_cup_3_option:
                    print('não há proximo_jogo_champions_cup_3_option')
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_3 = dict()
                jogo_champions_cup_dict_3['horario'] = champions_cup_start_date_string_3                
                jogo_champions_cup_dict_3['optionid'] = proximo_jogo_champions_cup_3_option['id']
                jogo_champions_cup_dict_3['odd'] = float( proximo_jogo_champions_cup_3_option['price']['odds'] )  

                print('pegando quarto mercado')

                for option_market in proximo_jogo_champions_cup_4['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_4 = option_market['options']
                        break

                proximo_jogo_champions_cup_4_option = None

                for option in proximo_jogo_champions_cup_4:
                    if option['name']['value'] == mercado_impar or option['name']['value'] == mercado_impar.replace(',', '.'):
                        proximo_jogo_champions_cup_4_option = option
                        break

                if not proximo_jogo_champions_cup_4_option:
                    print('não há proximo_jogo_champions_cup_4_option')
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_4 = dict()
                jogo_champions_cup_dict_4['horario'] = champions_cup_start_date_string_4                
                jogo_champions_cup_dict_4['optionid'] = proximo_jogo_champions_cup_4_option['id']
                jogo_champions_cup_dict_4['odd'] = float( proximo_jogo_champions_cup_4_option['price']['odds'] )        

                print('pegando quinto mercado')       

                for option_market in proximo_jogo_champions_cup_5['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_5 = option_market['options']
                        break

                proximo_jogo_champions_cup_5_option = None

                for option in proximo_jogo_champions_cup_5:
                    if option['name']['value'] == mercado_impar or option['name']['value'] == mercado_impar.replace(',', '.'):
                        proximo_jogo_champions_cup_5_option = option
                        break

                if not proximo_jogo_champions_cup_5_option:
                    print('não há proximo_jogo_champions_cup_5_option')
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_5 = dict()
                jogo_champions_cup_dict_5['horario'] = champions_cup_start_date_string_5                
                jogo_champions_cup_dict_5['optionid'] = proximo_jogo_champions_cup_5_option['id']
                jogo_champions_cup_dict_5['odd'] = float( proximo_jogo_champions_cup_5_option['price']['odds'] )                

                print('pegou os mercados')                

                try:
                    self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
                except:
                    traceback.print_exc() 

                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) {confirmacao.click(); }")                        
                except Exception as e:                        
                    print('Não conseguiu limpar os jogos...')
                    traceback.print_exc()             

                try:
                    self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
                except Exception as e:                        
                    traceback.print_exc()          

                index_range = 4

                if qt_under >= 4:
                    index_range = 5
                elif qt_over >= 4:
                    index_range = 3

                for i in range(index_range):
                    if i == 1:
                        champions_cup_start_date_string = champions_cup_start_date_string_2 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_2                    
                    elif i == 2:
                        champions_cup_start_date_string = champions_cup_start_date_string_3 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_3            
                    elif i == 3:        
                        champions_cup_start_date_string = champions_cup_start_date_string_4 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_4      
                    elif i == 4:      
                        champions_cup_start_date_string = champions_cup_start_date_string_5 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_5      

                    clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{champions_cup_start_date_string}']")
                    count = 0
                    while not clicou and count < 5:
                        await self.testa_sessao()
                        self.chrome.get(url_champions_cup)
                        self.chrome.maximize_window()
                        self.chrome.fullscreen_window()

                        sleep(2)

                        try:
                            self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
                        except:
                            traceback.print_exc() 

                        try:
                            self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
                        except Exception as e:                        
                            traceback.print_exc()   

                        clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{champions_cup_start_date_string}']")
                        count += 1
                    
                    if count == 5:             
                        await self.testa_sessao()
                        raise Exception('raise exception 3')

                    c_option = jogo_champions_cup_dict['optionid']
                    
                    clicou = False
                    count = 0
                    while not clicou and count < 5:
                        try:
                            option = WebDriverWait(self.chrome, 10).until(
                                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{c_option}"]' ) ))
                            option.click()
                            clicou = True
                        except Exception as e:
                            count += 1
                            try:
                                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
                            except:
                                traceback.print_exc() 
                            print('exception 3')
                            traceback.print_exc() 

                    if count == 5:
                        await self.testa_sessao()
                        raise Exception('raise exception 4')

                    sleep(1)

                    count = 0
                    texto = ''
                    while 'acima/abaixo' not in texto.lower() and count < 10:
                        try:
                            if i == 0:
                                cupom = WebDriverWait(self.chrome, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, f".betslip-digital-pick__line-1.ng-star-inserted" ) ))
                            else:
                                cupom = WebDriverWait(self.chrome, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, f"bs-digital-combo-bet-pick:nth-child({i+1}) .betslip-digital-pick__line-1.ng-star-inserted" ) ))
                            if cupom != None and cupom.get_property('innerText') != None:
                                texto = cupom.get_property('innerText').lower().strip()
                                print(texto)
                        except Exception as e:
                            traceback.print_exc()
                            sleep(0.5)
                            count += 1

                    if count == 10:
                        self.chrome.get_screenshot_as_file(f'{datetime.now()}.png')
                        await self.testa_sessao()
                        raise Exception('raise exception 5')

                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                cota = float( cota.get_property('innerText') )

                self.valor_aposta = ( self.meta_ganho + self.perda_acumulada ) / ( cota -1 ) + 0.01                

                if self.valor_aposta < 0.1:
                    self.valor_aposta = 0.1

                jogo_encerrado = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                if jogo_encerrado['betslips'][0]['state'] == 'Won':
                    self.qt_apostas_feitas = 0
                    self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')

                if self.qt_apostas_feitas > 0:
                    self.valor_aposta = 0.1
                else:
                    self.qt_real_bets += 1
                    self.escreve_em_arquivo('qt_real_bets.txt', f'{self.qt_real_bets}', 'w')
                    if self.qt_real_bets > 1 and self.qt_real_bets <= 4 :
                        self.valor_aposta = 0.1

                if self.valor_aposta > self.saldo:
                    self.valor_aposta = 0.1
                    self.perda_acumulada = 0.0
                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada}', 'w')

                self.valor_aposta = 0.1
                aposta_realizda = await self.insere_valor_dutching(None)
   
                try:
                    if aposta_realizda:
                        await self.telegram_bot.envia_mensagem(f'APOSTA {self.qt_apostas_feitas} REALIZADA')
                except:
                    traceback.print_exc()

                self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")
                self.horario_ultima_checagem = datetime.now()

                self.primeiro_alerta_depois_do_jogo = True
                self.primeiro_alerta_sem_jogos_elegiveis = True                    

                self.saldo_antes_aposta = self.saldo
                self.escreve_em_arquivo('saldo_antes_aposta.txt', f'{self.saldo_antes_aposta:.2f}', 'w')
                self.numero_apostas_feitas = 0


                ganhou_aposta = await self.espera_resultado_over_under(0.00466)
                if ganhou_aposta:
                    self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')
                    try:
                        await self.telegram_bot_erro.envia_mensagem(f'ganhou {tipo_aposta}')
                    except:
                        traceback.print_exc()

            except Exception as e:
                try:
                    await self.telegram_bot_erro.envia_mensagem('exception no main loop')
                except:
                    pass
                traceback.print_exc()
                print('exception no main loop')
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) { confirmacao.click(); }")                        
                except Exception as e:
                    print('Não conseguiu limpar os jogos...')
                    traceback.print_exc()
                await self.testa_sessao()
                self.aposta_com_erro = True
                self.is_for_real = False
                self.numero_unders_seguidos = 0
                self.numero_overs_seguidos = 0           

    def teste(self):
        self.chrome.get('https://sports.sportingbet.com/pt-br/sports') 
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()
        sleep(5)
        self.chrome.refresh()

    def return_hour(self, start_date):        
        temp = datetime.strptime( start_date, '%Y-%m-%dT%H:%M:%SZ' )
        temp = temp - timedelta(hours=3)
        return temp.strftime( '%H:%M' )

    async def analisa(self):

        self.qt_apostas_feitas = self.read_array_from_disk('qt_apostas_feitas.json')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')         

        telegram = TelegramBotErro()

        # self.graphic_chrome = self.create_graphic_chrome()

        # self.graphic_chrome.get(self.game_url)
        # self.graphic_chrome.maximize_window()
        # self.graphic_chrome.fullscreen_window()
        self.horario_ultima_checagem = datetime.now()

        # self.faz_login()

        # input()

        while True:

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    await telegram.envia_mensagem(f"SISTEMA RODANDO. {self.hora_ultima_aposta} {self.url.split('/')[-1]}")
                except:
                    pass                    
                self.horario_ultima_checagem = datetime.now()

            try:
                numero_gols_ = None                                         

                jogos = None
                for i in range(2):
                    jogos = await self.get(self.chrome, f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/sports?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&scheduleSize=10', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
                    sleep(2)

                futebol_virtual = None

                for sport in jogos:
                    if int( sport['sport']['id'] ) == 101:
                        futebol_virtual = sport['competitions']
                        break

                horarios_proximos_jogos = list( map( lambda e: self.return_hour(e['startDate']), futebol_virtual[self.game_index]['schedule'] ) )
                
                print(horarios_proximos_jogos)

                horario_jogo = horarios_proximos_jogos[0]

                hora = int(horario_jogo.split(':')[0])
                minuto = int(horario_jogo.split(':')[1])
                now = datetime.today()  
                hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
                
                index = 1
                while hora_do_jogo <= now:
                    print(f'pulando hora do jogo {horario_jogo}')
                    horario_jogo = horarios_proximos_jogos[index]

                    hora = int(horario_jogo.split(':')[0])
                    minuto = int(horario_jogo.split(':')[1])
                    now = datetime.today()  
                    hora_do_jogo = datetime( now.year, now.month, now.day, hora, minuto, 0)
                    index += 1
                          
                    
                # try:
                #     if self.qt_sem_dois_gols % 5 == 0 and self.qt_sem_dois_gols >= 10:
                #         await telegram.envia_mensagem(f"{self.qt_sem_dois_gols} jogo sem dois gols {self.url.split('/')[-1]}")
                # except:
                #     traceback.print_exc()                 
                self.hora_jogo = horario_jogo
                print('próximo horário ', self.hora_jogo)
                # aqui vou ter que abrir outra instância do webdriver, dessa vez sem o headless
                # precisamos armazenar o valor do horário do próximo jogo para ter certeza de que o algoritmo não vai pular nenhum
                
                if not self.graphic_chrome:
                    self.graphic_chrome = self.create_graphic_chrome()
                    self.graphic_chrome.get(self.game_url)
                    self.graphic_chrome.maximize_window()
                    self.graphic_chrome.fullscreen_window()  
                    self.faz_login()

                    self.graphic_chrome.get(self.game_url)
                    self.graphic_chrome.maximize_window()
                    self.graphic_chrome.fullscreen_window()  

                    await self.le_saldo()

                    ganhou_aposta = await self.espera_resultado()                    
                    if ganhou_aposta:      
                        print('ganhou')
                        self.perda_acumulada = 0.0
                        self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')
                        try:
                            await self.telegram_bot_erro.envia_mensagem(f"ganhou depois de {self.qt_apostas_feitas_txt} apostas\nsaldo: {self.saldo:.2f}\n{self.url.split('/')[-1]}")
                        except:
                            traceback.print_exc()
                        self.qt_apostas_feitas[self.game_index] = 0
                        self.escreve_em_arquivo('qt_apostas_feitas_txt.txt', '0', 'w')
                        # self.meta_ganho = 0.0035 * self.saldo
                        # self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')
                        self.save_array_on_disk('qt_apostas_feitas.json', self.qt_apostas_feitas)
                        #self.escreve_em_arquivo('bet_being_made.txt', 'False', 'w')
                        self.qt_sem_dois_gols = 0
                        #self.graphic_chrome.quit()
                    else:
                        print('perdeu')  
                    continue

                await self.make_bets()
              
            except:
                traceback.print_exc()    

if __name__ == '__main__': 
    chrome = None

    chrome = ChromeAuto() 
    chrome.disable_quickedit()
    
    chrome.url = sys.argv[1]
    chrome.game_index = int( sys.argv[2] )
    chrome.game_url = sys.argv[3]
    chrome.qt_sem_dois_gols = -1

    print( f'game index {chrome.game_index}\n' )
    
    while True:        
        try:
            chrome.acessa('https://sports.sportingbet.com/pt-br/sports')    
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run( chrome.analisa())             
        except Exception as e:            
            chrome = ChromeAuto() 
            chrome.url = sys.argv[1]
            chrome.game_index = int( sys.argv[2] )
            chrome.game_url = sys.argv[3]
            chrome.disable_quickedit()
            traceback.print_exc() 