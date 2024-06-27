from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import pause
import os
from datetime import datetime, timedelta
from credenciais import usuario, senha
from telegram_bot import TelegramBot, TelegramBotErro
from utils import *

import asyncio

class ChromeAuto():
    def __init__(self):        
        self.saldo = 0
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
        self.qt_apostas_feitas = None
        self.numero_overs_seguidos = 0
        self.numero_unders_seguidos = 0
        self.perda_acumulada = 0.0
        self.meta_ganho = 0.0
        self.aposta_com_erro = False        
        self.is_for_real = False
        self.maior_saldo = 0.0
        self.qt_real_bets = 0
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
                self.options.add_argument("--force-device-scale-factor=1")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                self.options.page_load_strategy = 'eager'            
                self.chrome = webdriver.Chrome(options=self.options, service=ChromeService(ChromeDriverManager().install()))                
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

    async def get(self, url):
        n_errors = 0
        while True:
            if n_errors > 10:
                try:
                    await self.telegram_bot_erro.envia_mensagem('sistema travado no método get')
                except:
                    pass
            try:
                result = self.chrome.execute_script(url)
                return result
            except:
                n_errors += 1
                await self.testa_sessao()
                sleep(1)

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
                try:
                    await self.telegram_bot_erro.envia_mensagem('sessão expirada')
                except:
                    pass
                self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()
            except Exception as e:
                try:
                    await self.telegram_bot_erro.envia_mensagem('exception no login')
                except:
                    pass
                print(e)
            finally:
                self.faz_login()
                    
    async def espera_resultado_over_under(self, porcentagem):
        if self.mercado == 'Acima de 2.5':
            return await self.espera_resultado_over_under_um_jogo(porcentagem)
        else:
            return await self.espera_resultado_over_under_um_jogo(porcentagem)
        
        
    async def espera_resultado_over_under_um_jogo(self, porcentagem):

        try:
            #segunda aposta
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


            while jogos_abertos['summary']['openBetsCount'] > 0:        
                jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                sleep(1)

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
                    await self.telegram_bot_erro.envia_mensagem(f'ganhou!\nsaldo: {self.saldo:.2f}\nmeta ganho: {self.meta_ganho:.2f}')                    
                else:
                    self.perda_acumulada -= valor_ganho

                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')   

                if self.qt_apostas_feitas == 1:                    
                    self.qt_real_bets = 0
                    self.escreve_em_arquivo('qt_real_bets.txt', '0', 'w')   

                self.qt_apostas_feitas = 0
                self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')                     

                  
                
                mercado_ultima_aposta = jogo_encerrado['bets'][0]['option']['name']

                if mercado_ultima_aposta == 'Acima de 2.5':
                    self.numero_unders_seguidos = 0
                    self.numero_overs_seguidos = 1
                else:
                    self.numero_overs_seguidos = 0
                    self.numero_unders_seguidos = 1
                return          
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

                sleep(5)         

                # aqui vou tentar buscar algo da API pra ver se logou de verdade
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['liveBetsCount']:
                    print('logou com sucesso')

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
                self.chrome.get_screenshot_as_file('screenshot.png')
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

    async def insere_valor_dutching(self, id_jogo):
        jogos_abertos = None
        apostou = False

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
                        input_field = WebDriverWait(self.chrome, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
                        input_field.send_keys(u'\ue009' + u'\ue003')                    
                        input_field.send_keys(valor_do_campo)                    

                        sleep(0.5)                                        

                        while input_field.get_attribute('value').strip() != valor_do_campo: 
                            input_field.send_keys(u'\ue009' + u'\ue003')                    
                            input_field.send_keys(valor_do_campo)
                            sleep(0.5)

                        clicou = True
                    except Exception as e:
                        try:
                            await self.telegram_bot_erro.envia_mensagem('erro ao inserir valor')
                        except:
                            pass
                        count += 1
                        print('erro ao inserir valor')
                        print(e)
                
                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return
                            
                sleep(0.2)

                clicou = False
                count = 0
                while not clicou and count < 5:
                    try:
                        botao_aposta = WebDriverWait(self.chrome, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                        botao_aposta.click()    
                        clicou = True 
                    except:
                        count += 1
                        print('erro ao clicar no botão de aposta')
                        try:
                            await self.telegram_bot_erro.envia_mensagem('erro ao clicar no botão de aposta')
                        except:
                            pass

                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return
                        
                sleep(1)

                count = 0

                jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

                while jogos_abertos['summary']['openBetsCount'] == 0 and count < 5:                    
                    try:
                        botao_aposta = WebDriverWait(self.chrome, 10).until(
                                EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                        botao_aposta.click()    
                        clicou = True 
                    except:
                        count += 1
                        print('erro ao clicar no botão de aposta')
                        try:
                            await self.telegram_bot_erro.envia_mensagem('erro ao clicar no botão de aposta')
                        except:
                            pass
                    finally:
                        jogos_abertos = await self.get(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                    sleep(2)

                if count == 5:
                    await self.testa_sessao()
                    self.aposta_com_erro = True
                    return

                clicou = False
                count = 0
                while not clicou and count < 5:
                    try:
                        botao_fechar = WebDriverWait(self.chrome, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                        botao_fechar.click() 
                        clicou = True
                    except:
                        count += 1
                        # se ele não clicou no botão de fechar aposta é porque provavelmente ela não foi feita
                        print('erro ao clicar no botão de fechar')     
                        try:
                            await self.telegram_bot_erro.envia_mensagem('erro ao clicar no botão de fechar')
                        except:
                            pass            

                if count == 5:
                    await self.testa_sessao()   
                    self.aposta_com_erro = True
                    return

                self.saldo -= self.valor_aposta
                self.escreve_em_arquivo('saldo.txt', f'{self.saldo:.2f}', 'w')

                self.qt_apostas_feitas += 1
                self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')

                self.perda_acumulada += self.valor_aposta                    
                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                self.is_for_real = False
                self.escreve_em_arquivo('is_for_real.txt', 'False', 'w')

                apostou = True

            except Exception as e:
                print('erro no insere valor')
                self.aposta_com_erro = True
                print(e)
                await self.testa_sessao()
                #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
    
    async def le_saldo(self):        
        leu_saldo = False        
        while not leu_saldo:
            try:
                saldo_request = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/pt-br/api/balance?forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
                self.saldo = float(saldo_request['balance']['accountBalance'])
                leu_saldo = True
            except Exception as e:
                sleep(5)
                print(e)                
                await self.testa_sessao()                
                self.chrome.refresh()
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
        
        url_champions_cup = "https://sports.sportingbet.com/pt-br/sports/virtual/futebol-virtual-101/champions-cup-100199"
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

                champions_id = futebol_virtual[1]['competition']['id']

                index_jogo = 0
                
                proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&scheduleSize=10'); return await d.json();")

                champions_cup_start_date = proximo_jogo_champions_cup['schedule'][index_jogo]['startDate']
                champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )

                index_jogo = 0

                id_jogos_champions_cup = list( map( lambda el: el['id'], proximo_jogo_champions_cup['schedule'] ) )

                while champions_cup_start_date <= datetime.now():                                                      

                    proximo_jogo_champions_cup = proximo_jogo_champions_cup['schedule'][index_jogo]
                    champions_id = futebol_virtual[1]['competition']['id']                
                    
                    proximo_jogo_champions_cup = await self.get(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/virtual/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&sportIds=101&competitionIds={champions_id}&fixtureIds={id_jogos_champions_cup[index_jogo]}&scheduleSize=10'); return await d.json();")

                    champions_cup_start_date = proximo_jogo_champions_cup['fixture']['startDate']
                    champions_cup_start_date = datetime.strptime( champions_cup_start_date, '%Y-%m-%dT%H:%M:%SZ' )
                    champions_cup_start_date = champions_cup_start_date - timedelta(hours=3)
                    champions_cup_start_date_string = champions_cup_start_date.strftime( '%H:%M' )                             

                    index_jogo += 1                      

                if self.numero_overs_seguidos >= 1:
                    self.mercado = 'Acima de 2.5'
                else:
                    self.mercado = 'Abaixo de 2.5'
                self.numero_overs_seguidos = 0
                self.numero_unders_seguidos = 0

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
              
                for option_market in proximo_jogo_champions_cup['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():                        
                        proximo_jogo_champions_cup = option_market['options']
                        break

                proximo_jogo_champions_cup_option = None

                for option in proximo_jogo_champions_cup:                    
                    if option['name']['value'] == self.mercado or option['name']['value'] == self.mercado.replace('.', ','):
                        proximo_jogo_champions_cup_option = option
                        break

                if not proximo_jogo_champions_cup_option:
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict = dict()
                jogo_champions_cup_dict['horario'] = champions_cup_start_date_string                
                jogo_champions_cup_dict['empate'] = dict()
                jogo_champions_cup_dict['empate']['optionid'] = proximo_jogo_champions_cup_option['id']
                jogo_champions_cup_dict['empate']['odd'] = float( proximo_jogo_champions_cup_option['price']['odds'] )  

                for option_market in proximo_jogo_champions_cup_2['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_2 = option_market['options']
                        break

                proximo_jogo_champions_cup_2_option = None    

                for option in proximo_jogo_champions_cup_2:
                    if option['name']['value'] == self.mercado or option['name']['value'] == self.mercado.replace('.', ','):
                        proximo_jogo_champions_cup_2_option = option
                        break

                if not proximo_jogo_champions_cup_2_option:
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_2 = dict()
                jogo_champions_cup_dict_2['horario'] = champions_cup_start_date_string_2                
                jogo_champions_cup_dict_2['empate'] = dict()
                jogo_champions_cup_dict_2['empate']['optionid'] = proximo_jogo_champions_cup_2_option['id']
                jogo_champions_cup_dict_2['empate']['odd'] = float( proximo_jogo_champions_cup_2_option['price']['odds'] )  

                for option_market in proximo_jogo_champions_cup_3['fixture']['optionMarkets']:                    
                    if 'acima/abaixo' in option_market['name']['value'].lower() and 'total de gols' in option_market['name']['value'].lower():
                        proximo_jogo_champions_cup_3 = option_market['options']
                        break

                proximo_jogo_champions_cup_3_option = None

                for option in proximo_jogo_champions_cup_3:
                    if option['name']['value'] == self.mercado or option['name']['value'] == self.mercado.replace('.', ','):
                        proximo_jogo_champions_cup_3_option = option
                        break

                if not proximo_jogo_champions_cup_3_option:
                    self.is_for_real = False
                    continue

                jogo_champions_cup_dict_3 = dict()
                jogo_champions_cup_dict_3['horario'] = champions_cup_start_date_string_3                
                jogo_champions_cup_dict_3['empate'] = dict()
                jogo_champions_cup_dict_3['empate']['optionid'] = proximo_jogo_champions_cup_3_option['id']
                jogo_champions_cup_dict_3['empate']['odd'] = float( proximo_jogo_champions_cup_3_option['price']['odds'] )                                               

                try:
                    self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
                except:
                    print('Erro ao tentar fechar banner')  

                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) {confirmacao.click(); }")                        
                except Exception as e:                        
                    print('Não conseguiu limpar os jogos...')
                    print(e)            

                try:
                    self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
                except Exception as e:                        
                    print(e)           

                numero_jogos = None
                if self.mercado == 'Acima de 2.5':
                    numero_jogos = 1
                else:
                    numero_jogos = 1

                for i in range(numero_jogos):
                    if i == 1:
                        champions_cup_start_date_string = champions_cup_start_date_string_2 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_2                    
                    elif i == 2:
                        champions_cup_start_date_string = champions_cup_start_date_string_3 
                        jogo_champions_cup_dict = jogo_champions_cup_dict_3                    

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
                            print('Erro ao tentar fechar banner')  

                        try:
                            self.chrome.execute_script("var botao = document.querySelector('.ui-icon.theme-ex.ng-star-inserted'); if (botao) { botao.click(); }")                    
                        except Exception as e:                        
                            print(e)  

                        clicou = self.clica_horario_jogo(f"//*[normalize-space(text()) = '{champions_cup_start_date_string}']")
                        count += 1
                    
                    if count == 5:             
                        await self.testa_sessao()
                        raise Exception('raise exception 3')

                    c_option = jogo_champions_cup_dict['empate']['optionid']
                    
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
                                print('Erro ao tentar fechar banner')
                            print('exception 3')
                            print(e)

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

                await self.insere_valor_dutching(None)

                try:                   

                    if self.qt_apostas_feitas == 1 and ( self.qt_real_bets == 1 or self.qt_real_bets > 4 ):
                        try:
                            await self.telegram_bot.envia_mensagem(f'APOSTA REALIZADA')
                        except:
                            pass

                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")
                    self.horario_ultima_checagem = datetime.now()

                    self.primeiro_alerta_depois_do_jogo = True
                    self.primeiro_alerta_sem_jogos_elegiveis = True                    

                    self.saldo_antes_aposta = self.saldo
                    self.escreve_em_arquivo('saldo_antes_aposta.txt', f'{self.saldo_antes_aposta:.2f}', 'w')
                    self.numero_apostas_feitas = 0
                except Exception as e:
                    print(e)

                await self.espera_resultado_over_under(0.00466)
            except Exception as e:
                self.chrome.get_screenshot_as_file(f'{datetime.now()}.png')
                try:
                    await self.telegram_bot_erro.envia_mensagem('exception no main loop')
                except:
                    pass
                print(e)
                print('exception no main loop')
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) { lixeira.click(); }")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) { confirmacao.click(); }")                        
                except Exception as e:
                    print('Não conseguiu limpar os jogos...')
                    print(e)
                await self.testa_sessao()
                self.aposta_com_erro = True
                self.is_for_real = False
                self.numero_unders_seguidos = 0
                self.numero_overs_seguidos = 0           


if __name__ == '__main__': 
    chrome = None

    chrome = ChromeAuto() 
    chrome.disable_quickedit()
    while True:        
        try:
            chrome.acessa('https://sports.sportingbet.com/pt-br/sports')    
            chrome.faz_login()  
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run( chrome.dois_overs_depois_dois_overs())
        except Exception as e:            
            chrome = ChromeAuto() 
            chrome.disable_quickedit()
            print(e)