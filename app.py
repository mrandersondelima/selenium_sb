from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from dutching import calcula_dutching
import time
import json
from datetime import datetime, timedelta
from credenciais import usuario, senha, bwin_id
from telegram_bot import TelegramBot, TelegramBotErro
from utils import *
from exceptions import ErroCotaForaIntervalo
import asyncio
from match_of_interest import MatchOfInterest, HomeAway
import pickle
from math import floor

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
                self.options.add_argument("--force-device-scale-factor=1")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                self.options.page_load_strategy = 'eager'
                # self.options.add_argument('--disk-cache-size')                
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
        print('saindo do chrome')
        self.chrome.quit()        
        exit()

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

                count = 0

                while count < 5:
                    try:
                         # aqui vou tentar buscar algo da API pra ver se logou de verdade
                        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                        if jogos_abertos['summary']['liveBetsCount']:
                            print('logou com sucesso')
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
                self.chrome.fullscreen_window()
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

    def atualiza_mercados_restantes(self, mercado):
        print('atualizando mercados')
        mercado = int( mercado[8] )

        self.mercados_restantes = []
        for i in range(mercado):
            self.mercados_restantes.append( f'Mais de {i},5' )

    def insere_valor_zebra(self, indice_jogo):
        jogos_abertos = None

        try:
            print('entrou no insere valor')

            if self.valor_aposta < 1:
                self.valor_aposta = 1

            if self.teste:
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
                raise Exception('erro ao clicar no botão de aposta')
                    
            sleep(0.2)
            
            try:
                botao_fechar = WebDriverWait(self.chrome, 20).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                botao_fechar.click() 

            except:
                # se ele não clicou no botão de fechar aposta é porque provavelmente ela não foi feita
                raise Exception('erro ao clicar no botão de fechar')          
                
                # verificamos se há apostas em aberto
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=1"); return await d.json();')
            

            while jogos_abertos['summary']['openBetsCount'] == indice_jogo:
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=1"); return await d.json();')
                sleep(2)

            if jogos_abertos['summary']['openBetsCount'] > indice_jogo:
                try:
                    if indice_jogo == 3:
                        self.qt_apostas_feitas += 1
                        self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')     
                        self.ja_conferiu_resultado = False
                        self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'False', 'w')    
                        self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")
                        self.telegram_bot.envia_mensagem(f"APOSTA {self.qt_apostas_feitas} REALIZADA.")    
                        self.payout_jogo_1 = None
                        self.payout_jogo_2 = None
                        self.payout_jogo_3 = None
                        self.payout_jogo_4 = None                    
                    
                    self.perda_acumulada += self.valor_aposta
                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')                        

                    self.primeiro_alerta_depois_do_jogo = True
                    self.primeiro_alerta_sem_jogos_elegiveis = True
                    self.le_saldo()

                    self.saldo_antes_aposta = self.saldo
                    # if id_jogo:
                    #     self.jogos_inseridos.append(f"{id_jogo['id']}{id_jogo['tempo']}{id_jogo['mercado']}")
                    #     self.save_array_on_disk('jogos_inseridos.txt', self.jogos_inseridos)
                    self.numero_apostas_feitas = 0
                except Exception as e:
                    print(e)
                return True
            else:
                # deu algum erro maluco, limpamos a aposta e esperamos o próximo laço
                self.testa_sessao()
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
                return False

        except Exception as e:
            print(e)
            self.testa_sessao()
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')            
            return False

        return

    async def insere_valor(self, id_jogo):
        jogos_abertos = None

        try:
            print('entrou no insere valor')

            if self.valor_aposta < 0.1:
                self.valor_aposta = 0.1

            if self.teste:
                self.valor_aposta = 0.1
    
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
                raise Exception('erro ao clicar no botão de aposta')
                    
            sleep(0.2)
            
            try:
                botao_fechar = WebDriverWait(self.chrome, 60).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                botao_fechar.click() 

            except:
                # se ele não clicou no botão de fechar aposta é porque provavelmente ela não foi feita
                raise Exception('erro ao clicar no botão de fechar')       

            # verificamos se há apostas em aberto
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

            while jogos_abertos['summary']['openBetsCount'] == self.qt_apostas_mesmo_jogo:
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                sleep(2)

            if jogos_abertos['summary']['openBetsCount'] > self.qt_apostas_mesmo_jogo:
                try:
                    self.qt_apostas_feitas += 1
                    self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')    

                    if self.aposta_mesmo_jogo:
                        self.qt_apostas_mesmo_jogo += 1                
                    else:
                        self.qt_apostas_mesmo_jogo = 1

                    self.aposta_mesmo_jogo = False
                    self.escreve_em_arquivo('aposta_mesmo_jogo.txt', 'False', 'w')

                    self.escreve_em_arquivo('qt_apostas_mesmo_jogo.txt', f'{self.qt_apostas_mesmo_jogo}', 'w')

                    self.ja_conferiu_resultado = False
                    self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'False', 'w')

                    self.perda_acumulada += self.valor_aposta
                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")

                    self.controle_acima_abaixo = 1
                    self.escreve_em_arquivo('controle_acima_abaixo.txt', f'{self.controle_acima_abaixo}', 'w')

                    self.aposta_ja_era = False
                    self.escreve_em_arquivo('aposta_ja_era.txt', 'False', 'w')                        

                    self.saldo -= self.valor_aposta

                    if self.qt_apostas_feitas >= 1:
                        try:                    
                            await self.telegram_bot.envia_mensagem(f"APOSTA {self.qt_apostas_feitas} REALIZADA.")
                            self.horario_ultima_checagem = datetime.now()
                        except Exception as e:
                            print(e)

                    self.primeiro_alerta_depois_do_jogo = True
                    self.primeiro_alerta_sem_jogos_elegiveis = True   

                    self.atualiza_mercados_restantes(id_jogo['nome_mercado'])      
                    self.save_array_on_disk('mercados_restantes.json', self.mercados_restantes)  

                    self.id_partida_atual = id_jogo['fixture_id']         
                    self.escreve_em_arquivo('id_partida_atual.txt', self.id_partida_atual, 'w')

                    self.saldo_antes_aposta = self.saldo
                    self.escreve_em_arquivo('saldo_antes_aposta.txt', f'{self.saldo:.2f}', 'w')
                    # if id_jogo:
                    #     self.jogos_inseridos.append(f"{id_jogo['id']}{id_jogo['tempo']}{id_jogo['mercado']}")
                    #     self.save_array_on_disk('jogos_inseridos.txt', self.jogos_inseridos)
                    self.numero_apostas_feitas = 0
                except Exception as e:
                    print(e)
                return True
            else:
                # deu algum erro maluco, limpamos a aposta e esperamos o próximo laço
                self.testa_sessao()
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
                return False

        except Exception as e:
            print(e)
            self.testa_sessao()
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')            
            return False

        return

    async def insere_valor_favorito(self, aposta_certa):
        jogos_abertos = None

        try:
            # verificamos se há apostas em aberto
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

            qt_jogos_abertos = jogos_abertos['summary']['openBetsCount']

            print('entrou no insere valor')

            if self.valor_aposta < 0.1:
                self.valor_aposta = 0.1

            if self.teste:
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
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
            botao_fechar.click()     

            while jogos_abertos['summary']['openBetsCount'] == qt_jogos_abertos:
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                sleep(2)

            self.perda_acumulada += self.valor_aposta
            self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')

            self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")                   

            self.saldo -= self.valor_aposta

            try:                    
                if not aposta_certa:
                    await self.telegram_bot.envia_mensagem(f"APOSTA REALIZADA.")
                else:
                    await self.telegram_bot.envia_mensagem(f"APOSTA CERTA REALIZADA.")
                self.horario_ultima_checagem = datetime.now()
            except Exception as e:
                print(e)

            self.primeiro_alerta_depois_do_jogo = True
            self.primeiro_alerta_sem_jogos_elegiveis = True

            return True
        except Exception as e:
            print(e)
            self.testa_sessao()
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
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
                self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                self.chrome.maximize_window()
                self.chrome.fullscreen_window()
            except Exception as e:
                print(e)
            finally:
                self.faz_login()

    
    async def handicap(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):

        try:    
            banner = WebDriverWait(self.chrome, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f'/html/body/div[6]/div[2]/div/vn-overlay-messages/vn-content-messages/div/vn-content-message/div/span' ) ))   
                                                                                                        
            banner.click()
        except:
            print('erro ao fechar banner')

        try:    
            banner = WebDriverWait(self.chrome, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f'/html/body/div[3]/div[2]/div/vn-overlay-messages/vn-content-messages/div/vn-content-message/div/span' ) ))                                                                                                           
            banner.click()                                              
        except:
            print('erro ao fechar banner')

        try:    
            banner = WebDriverWait(self.chrome, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f'/html/body/div[5]/div[2]/div/vn-overlay-messages/vn-content-messages/div/vn-content-message/div/span' ) ))                                                                                                           
            banner.click()
        except:
            print('erro ao fechar banner')



        self.tempo_pausa = 3 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste
        saldo_inicial = 644.29
        self.le_saldo()      
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.valor_aposta = self.meta_ganho
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.controle_acima_abaixo = 1

        print('valor aposta ', self.valor_aposta )
        print('teste ', self.teste)

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")

                if jogos_abertos['summary']['liveBetsCount'] >= 1:
                
                    print('Há apostas ao vivo.')
                    print(datetime.now())                    

                    self.tempo_pausa = 60 * 5
                    if self.saldo_antes_aposta == 0.0:
                        self.saldo_antes_aposta = self.saldo
                elif jogos_abertos['summary']['openBetsCount'] >= 1:
                
                    print('Há apostas abertas.')
                    print(datetime.now())                    

                    self.tempo_pausa = 60 * 10
                    if self.saldo_antes_aposta == 0.0:
                        self.saldo_antes_aposta = self.saldo
                else:                    
                    try:                                     
                        if not self.ja_conferiu_resultado:
                            print('Conferindo resultado da última aposta.')
                            self.ja_conferiu_resultado = True
                            self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')    

                            if not self.aposta_mesmo_jogo:
                                # primeiro verificamos se a última aposta foi vitoriosa                    
                                ultimo_jogo = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=Settled', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } } ); return await d.json();")
                                
                                # só vai modificar o valor da aposta se tivermos perdido a última aposta
                                ultimo_jogo = ultimo_jogo['betslips'][0]

                                early_payout = ultimo_jogo['isEarlyPayout']

                                if ultimo_jogo['state'] == 'Canceled':

                                    print('aposta cancelada')

                                    self.qt_apostas_feitas -= 1
                                    self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')
                                    
                                    valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                                    self.perda_acumulada -= valor_ultima_aposta                                                                       

                                    self.valor_aposta -= self.perda_acumulada
                                    
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                                    
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

                                    if self.qt_apostas_feitas >= 1:
                                        self.perda_acumulada = 0.0      

                                        try:
                                            #if self.saldo > self.saldo_inicio_dia:

                                                    # atualiza o valor da meta de ganho uma vez que ganhou
                                            self.meta_ganho = self.saldo * 0.015 if not self.teste else valor_aposta #0.000325                                
                                            
                                            self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                
                                            print('meta ganho ', self.meta_ganho)

                                            await self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo:.2f}')
                                            self.primeiro_alerta_depois_do_jogo = False   
                                            #self.saldo_inicio_dia = self.saldo
                                            #self.escreve_em_arquivo('saldo_inicio_dia.txt', f'{self.saldo_inicio_dia:.2f}', 'w')
                                            #self.horario_ultima_checagem = datetime.now()
                                            #else:
                                            #    await self.telegram_bot_erro.envia_mensagem(f'RECUPEROU! {self.saldo}')
                                        except Exception as e:
                                            print(e)
                                            print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')

                                    else:
                                        valor_ganho_ultima_aposta = float( ultimo_jogo['maxPayout']['value'] )
                                        if self.perda_acumulada >= valor_ganho_ultima_aposta:
                                            self.perda_acumulada -= valor_ganho_ultima_aposta
                                        else:
                                            self.perda_acumulada = 0.0
                                                                   
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
 
                                    self.qt_apostas_feitas = 0
                                    self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')                                    
                                    # while self.saldo <= self.saldo_antes_aposta:
                                    #     self.le_saldo()
                                    #     contador += 1
                                    #     if contador % 10 == 0:
                                    #         try:
                                    #             await self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                    #         except:
                                    #             pass
                                    #         self.horario_ultima_checagem = datetime.now()
                                    #         # self.chrome.quit()
                                    #         # exit()

                                   
                            # with open('meta_ganho.txt', 'w') as f:
                            #    f.write(f'{self.valor_aposta:.2f}')                                    

                                    
                        
                                    #print(f'META DE GANHO: R$ {self.meta_ganho:.2f}')

                        # if self.teste:
                        #     self.valor_aposta = valor_aposta

                        data_inicio = datetime.now() + timedelta(hours=3, minutes=3)
                        data_inicio = data_inicio.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        data_fim = datetime.now() + timedelta(hours=5, minutes=3)
                        data_fim = data_fim.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&state=Upcoming&skip=0&take=50&offerMapping=Filtered&sortBy=StartDate&sportIds=4&from={data_inicio}&to={data_fim}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                    

                        print('--- chamou fixtures de novo ---')

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 5 * 60
                            
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4:
                                        continue

                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                                                                                               
                                    start_date = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z') - timedelta(hours=3)
                                    start_date_datetime = start_date
                                    start_date = start_date.strftime('%Y-%m-%dT%H:%M')

                                    e_apto = False

                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:                                             
                                        if 'resultado da partida' in option_market['name']['value'].lower():    
                                            options = option_market['options'] 
                                            odd_casa = float( options[0]['price']['odds'])
                                            odd_fora = float( options[2]['price']['odds'])
                                            if odd_casa < 1.4 or odd_fora < 1.4:                                                
                                                e_apto = True
                                                break

                                    if not e_apto:
                                        continue                                    
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:   
                                        
                                        if 'handicap' in option_market['name']['value'].lower() and 'resultado final' in option_market['name']['value'].lower():    
                                            options = option_market['options']
                                            for option in options:
                                                print(option['name']['value'])
                                                print(option['price']['odds'])
                                                option_id = option['id']
                                                if self.qt_apostas_feitas % 2 == 0:
                                                    if ( '(2)' in option['name']['value'] or '(3)' in option['name']['value'] or '(4)' in option['name']['value'] ) and float( option['price']['odds'] ) >= 2.0 and 'handicap x' not in option['name']['value'].lower() and 'handicap tie' not in option['name']['value']:
                                                        jogos_aptos.append({ 'start_date': start_date_datetime, 'nome_evento': nome_evento, 'odd': float( option['price']['odds'] ), 'option_id' : option_id })                                                     
                                                else:
                                                    if ( '(-2)' in option['name']['value'] or '(-3)' in option['name']['value'] ) and float( option['price']['odds'] ) >= 2.0 and 'handicap x' not in option['name']['value'].lower() and 'handicap tie' not in option['name']['value']:
                                                        jogos_aptos.append({ 'start_date': start_date_datetime, 'nome_evento': nome_evento, 'odd': float( option['price']['odds'] ), 'option_id' : option_id })                                                     
                                                # if '(-2)' in option['name']['value'] and float( option['price']['odds'] ) >= 2.0 and 'handicap x' not in option['name']['value'].lower():
                                                #     jogos_aptos.append({ 'start_date': start_date_datetime, 'nome_evento': nome_evento, 'odd': float( option['price']['odds'] ), 'option_id' : option_id })   
                                                
                                                       
                                except Exception as e:                                    
                                    print('erro')                                    
                                    print(e)                                

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['start_date'], el['odd'] ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:       
                                    try:
                                        await self.telegram_bot.envia_mensagem('Sem jogos elegíveis.')  
                                        self.horario_ultima_checagem = datetime.now()                           
                                    except Exception as e:
                                        print(e)
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                sleep(60 * 10)
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)

                            self.numero_apostas_feitas = 0

                            for jogo_apto in jogos_aptos_ordenado:

                                if self.varios_jogos:
                                    self.valor_aposta = valor_aposta

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if self.varios_jogos and f"{jogo_apto['id']}{jogo_apto['tempo']}{jogo_apto['mercado']}" in self.jogos_inseridos:
                                    print(f"aposta já inserida para o jogo {jogo_apto['id']} no tempo {jogo_apto['tempo']} no mercado {jogo_apto['mercado']}")
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca
                                  
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] + '?market=5')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e
                                                                        

                                    empate = WebDriverWait(self.chrome, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_apto["option_id"]}"]' ) ))                                     
                                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                    empate.click() 
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1                                 

                                    if self.numero_apostas_feitas == 1:
                                        print('quebrou o laço aqui')
                                        break                                

                                except Exception as e:
                                    print('Algo deu errado')  
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()
                                    self.numero_apostas_feitas = 0

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(10)

                                    sleep(5)                       

                            if self.numero_apostas_feitas == 1:     
                                # print('vai pegar a cota')                       
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                cota = float( cota.get_property('innerText') )

                                if cota < 2:
                                    raise ErroCotaForaIntervalo('cota fora do intervalo')

                                # if self.qt_apostas_feitas >= 0:
                                #self.valor_aposta = self.meta_ganho + self.perda_acumulada
                                # else:
                                #     self.valor_aposta = 1
                                
                                self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01                                

                                print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                if not self.teste and self.valor_aposta > self.saldo:
                                    self.valor_aposta = 0.1

                                await self.insere_valor(jogo_apto)
                                
                            else:
                                print(datetime.now())
                        
                        print()
                        
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
                        if self.numero_erros_global >= 10:                           
                            self.testa_sessao()
                        self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
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
              

    async def busca_odds_fim_jogo_sem_gol(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):

        self.tempo_pausa = 3 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste
        saldo_inicial = 644.29
        self.le_saldo()      
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.valor_aposta = self.meta_ganho
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.controle_acima_abaixo = self.le_de_arquivo('controle_acima_abaixo.txt', 'int')

        print('valor aposta ', self.valor_aposta )
        print('teste ', self.teste)

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")

                self.aposta_ja_era_metodo(limite_inferior, limite_superior)

                if jogos_abertos['summary']['openBetsCount'] >= 1 and not self.aposta_ja_era:
                
                    print('Há apostas em aberto...')
                    print(datetime.now())                                        

                    self.tempo_pausa = 60 * 3
                    if self.saldo_antes_aposta == 0.0:
                        self.saldo_antes_aposta = self.saldo
                else:                    
                    try:                                     
                        if not self.ja_conferiu_resultado:                                                        

                            if not self.aposta_mesmo_jogo:
                                print('Conferindo resultado da última aposta.')
                                self.ja_conferiu_resultado = True
                                self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')    
                                # primeiro verificamos se a última aposta foi vitoriosa                    
                                ultimo_jogo = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=Settled', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } } ); return await d.json();")
                                
                                # só vai modificar o valor da aposta se tivermos perdido a última aposta
                                ultimo_jogo = ultimo_jogo['betslips'][0]

                                early_payout = ultimo_jogo['isEarlyPayout']

                                if ultimo_jogo['state'] == 'Canceled':

                                    print('aposta cancelada')

                                    self.qt_apostas_feitas -= 1
                                    self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')
                                    
                                    valor_ultima_aposta = float( ultimo_jogo['stake']['value'])                                    

                                    self.perda_acumulada -= valor_ultima_aposta                                                                       

                                    self.valor_aposta -= self.perda_acumulada
                                    
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                                    
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

                                    self.perda_acumulada = 0.0      

                                    try:
                                        #if self.saldo > self.saldo_inicio_dia:

                                                # atualiza o valor da meta de ganho uma vez que ganhou
                                        self.meta_ganho = self.saldo * 0.003922 if not self.teste else valor_aposta #0.000325                                
                                        
                                        self.escreve_em_arquivo('meta_ganho.txt', f'{self.meta_ganho:.2f}', 'w')                                
                                        print('meta ganho ', self.meta_ganho)

                                        await self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo:.2f}')
                                        self.primeiro_alerta_depois_do_jogo = False   
                                        #self.saldo_inicio_dia = self.saldo
                                        #self.escreve_em_arquivo('saldo_inicio_dia.txt', f'{self.saldo_inicio_dia:.2f}', 'w')
                                        #self.horario_ultima_checagem = datetime.now()
                                        #else:
                                        #    await self.telegram_bot_erro.envia_mensagem(f'RECUPEROU! {self.saldo}')
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')

                                                                   
                                    self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
 
                                    self.qt_apostas_feitas = 0
                                    self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')                                    
                                    # while self.saldo <= self.saldo_antes_aposta:
                                    #     self.le_saldo()
                                    #     contador += 1
                                    #     if contador % 10 == 0:
                                    #         try:
                                    #             await self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                    #         except:
                                    #             pass
                                    #         self.horario_ultima_checagem = datetime.now()
                                    #         # self.chrome.quit()
                                    #         # exit()

                                   
                            # with open('meta_ganho.txt', 'w') as f:
                            #    f.write(f'{self.valor_aposta:.2f}')                                    

                                    
                        
                                    #print(f'META DE GANHO: R$ {self.meta_ganho:.2f}')

                        # if self.teste:
                        #     self.valor_aposta = valor_aposta
                        
                        fixtures = { 'fixtures': [] }

                        if self.aposta_mesmo_jogo:
                            jogo_aberto = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&scoreboardMode=Full&fixtureIds={self.id_partida_atual}&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                               
                            fixtures['fixtures'].append( jogo_aberto['fixture'] )
                        else:
                            fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                        print('--- chamou fixtures de novo ---')

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 5 * 60
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                        continue

                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                    
                                    fixture_id = fixture['id']
                                    name = fixture['name']['value']
                                    numero_gols_atual = fixture['scoreboard']['score']      
                                    placar = fixture['scoreboard']['score']      
                                    numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                    periodo = fixture['scoreboard']['period']
                                    periodId = fixture['scoreboard']['periodId']
                                    is_running = fixture['scoreboard']['timer']['running']
                                    
                                    if self.aposta_mesmo_jogo:
                                        if fixture['id'] != self.id_partida_atual:
                                            continue                                    

                                    if not is_running:
                                        continue

                                    resultado_partida = fixture['optionMarkets'][0]['options']
                                    odd_time_1 = float( resultado_partida[0]['price']['odds'] )
                                    odd_time_2 = float( resultado_partida[2]['price']['odds'] )                                 

                                    cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:                                             

                                        if periodo == '1º T':
                                            if option_market['name']['value'].lower() == '1º tempo - total de gols':
                                                #print(option_market['name']['value'].lower())
                                                print(nome_evento)
                                                odd = 1
                                                option_id = '0'           
                                                mercado = ''     
                                                nome_mercado = ''               
                                                achou_mercado = False             
                                                primeiro_ou_segundo_tempo = 1
                                                for option in option_market['options']:                                                    
                                                    for gols in range(0, 5):
                                                        mercado = option['name']['value']
                                                        if mercado == f'Mais de {gols},5':      
                                                            nome_mercado = option['name']['value']                                                      
                                                            option_id = option['id']
                                                            odd = float(option['price']['odds'])    
                                                            print(option['name']['value'], odd)
                                                        
                                                        if odd >= limite_inferior and odd <= limite_superior:        
                                                            achou_mercado = True
                                                            break
                                                    if achou_mercado:
                                                        break
                                                    
                                                if achou_mercado and self.controle_acima_abaixo == 0:                                                    
                                                    mercado = mercado.replace('Mais de ', 'Menos de ')
                                                    for option in option_market['options']:                                                    
                                                        for gols in range(0, 5):                                                            
                                                            if option['name']['value'] == mercado:                                                            
                                                                option_id = option['id']
                                                                odd = float(option['price']['odds'])    
                                                                print(option['name']['value'], odd)

                                                    primeiro_ou_segundo_tempo = 1
                                                        
                                                if achou_mercado:                                                    
                                                    jogos_aptos.append({ 'cronometro': cronometro, 'fixture_id': fixture_id, 'nome_evento': nome_evento, 'nome_mercado': nome_mercado, 'odd': odd, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo, 'option_id' : option_id })                                                     

                                        # else:
                                        #     #print(option_market['name']['value'])
                                        #     option_market_name = option_market['name']['value']
                                        #     if option_market_name.lower() in ['total goals', 'total de gols']:                                                    
                                        #         print(nome_evento)
                                        #         odd = 1
                                        #         option_id = '0'           
                                        #         mercado = ''                    
                                        #         achou_mercado = False             
                                        #         primeiro_ou_segundo_tempo = 2
                                        #         for option in option_market['options']:                                                    
                                        #             for gols in range(0, 10):
                                        #                 mercado = option['name']['value']
                                        #                 if mercado == f'Mais de {gols},5':                                                            
                                        #                     option_id = option['id']
                                        #                     odd = float(option['price']['odds'])    
                                        #                     print(option['name']['value'], odd)
                                                        
                                        #                 if odd >= 2 and odd <= 2.3:        
                                        #                     achou_mercado = True
                                        #                     break
                                        #             if achou_mercado:
                                        #                 break
                                                    
                                        #         if achou_mercado and self.controle_acima_abaixo == 0:                                                    
                                        #             mercado = mercado.replace('Mais de ', 'Menos de ')
                                        #             for option in option_market['options']:                                                    
                                        #                 for gols in range(0, 5):                                                            
                                        #                     if option['name']['value'] == mercado:                                                            
                                        #                         option_id = option['id']
                                        #                         odd = float(option['price']['odds'])    
                                        #                         print(option['name']['value'], odd)

                                        #             primeiro_ou_segundo_tempo = 1
                                                        
                                        #         if achou_mercado:                                                    
                                        #             jogos_aptos.append({ 'cronometro': cronometro, 'nome_evento': nome_evento, 'odd': odd, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo, 'option_id' : option_id })                                                     
                                                       
                                except Exception as e:                                    
                                    print('erro')                                    
                                    print(e)                                

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['cronometro'] ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if self.aposta_mesmo_jogo:
                                jogos_aptos_ordenado = list( filter( lambda el: el['fixture_id'] == self.id_partida_atual, jogos_aptos_ordenado ) )

                            print(jogos_aptos_ordenado)

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:       
                                    try:
                                        await self.telegram_bot.envia_mensagem('Sem jogos elegíveis.')  
                                        self.horario_ultima_checagem = datetime.now()                           
                                    except Exception as e:
                                        print(e)
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                sleep(60 * 3)
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)

                            self.numero_apostas_feitas = 0

                            for jogo_apto in jogos_aptos_ordenado:

                                if self.varios_jogos:
                                    self.valor_aposta = valor_aposta

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if self.varios_jogos and f"{jogo_apto['id']}{jogo_apto['tempo']}{jogo_apto['mercado']}" in self.jogos_inseridos:
                                    print(f"aposta já inserida para o jogo {jogo_apto['id']} no tempo {jogo_apto['tempo']} no mercado {jogo_apto['mercado']}")
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca
                                  
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] + '?market=3')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e
                                    # vamos pegar o mercado de resultas                                    

                                    #quer dizer que o mercado de gols é no primeiro tempo
                                    # try:
                                    #     if jogo_apto['periodo'] in ['1º T', '1º Tempo', '1º tempo']:
                                    #         mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                    #             EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a"))) 
                                    #         EC.presence_of_all_elements_located  
                                    #         mercado_1_tempo.click()                                      
                                    # except Exception as e:
                                    #     print('mercados bloqueados')
                                    #     self.numero_erros_global += 1
                                    #     deu_erro = True
                                    #     raise e
                                    # vamos pegar o mercado de resultas          

                                    try:
                                        mercados_1_tempo = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_all_elements_located((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a")))

                                        for mercado_1_tempo in mercados_1_tempo:    
                                            try:                                                                                     
                                                mercado_1_tempo.click()

                                                empate = WebDriverWait(self.chrome, 2).until(
                                                    EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_apto["option_id"]}"]' ) ))                                     
                                                # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                                empate.click() 
                                                break
                                            except:
                                                pass                                            
                                    except Exception as e:
                                        print('mercados bloqueados')
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise e                                       
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1                                 

                                    if self.numero_apostas_feitas == 1:
                                        print('quebrou o laço aqui')
                                        break                                

                                except Exception as e:
                                    print('Algo deu errado')  
                                    deu_erro = True
                                    print(e)
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(e)
                                    except:
                                        pass
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()
                                    self.numero_apostas_feitas = 0

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(10)

                                    sleep(5)                       

                            if self.numero_apostas_feitas == 1:     
                                # print('vai pegar a cota')                       
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                cota = float( cota.get_property('innerText') )

                                # if cota < 2 or cota > 3:
                                #     raise ErroCotaForaIntervalo('cota fora do intervalo')

                                # if self.qt_apostas_feitas > 1:
                                #     self.perda_acumulada = 0.0             
                                #     self.escreve_em_arquivo('perda_acumulada.txt', '0.0', 'w')    
                                #     self.qt_apostas_feitas = 0
                                #     self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')    

                                
                                #self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01                                
                                #self.valor_aposta = 1.0 + self.perda_acumulada

                                # if self.qt_apostas_feitas >= 2:
                                self.valor_aposta = ( ( self.perda_acumulada + self.meta_ganho ) / ( cota - 1 ) ) + 0.01                                
                                # else:
                                #     self.valor_aposta = 0.1

                                print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                if self.teste or self.valor_aposta > self.saldo:
                                    self.valor_aposta = 0.1

                                await self.insere_valor(jogo_apto)
                                
                            else:
                                print(datetime.now())
                        
                        print()
                        
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
                        if self.numero_erros_global >= 10:                           
                            self.testa_sessao()
                        self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
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

    async def atualiza_payouts(self, apostas):       
        
        v = [0, 0, 0, 0]

        for i, bet in enumerate( apostas ):
            betSlipNumber = bet['betSlipNumber']
            c_2 = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/CashoutCheckAndSubscribe?betNumbers={betSlipNumber}&source=mybets&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")
            c_4 = c_2['earlyPayouts'][0]
            
            v[i] =  float(c_4['earlyPayoutValue'])

        payout_jogo_1_temp = v[0]
        payout_jogo_2_temp = v[1]
        payout_jogo_3_temp = v[2]
        payout_jogo_4_temp = v[3]
        
        # se payout é None, então simplesmente setamos o payout
        if not self.payout_jogo_1:
            self.payout_jogo_1 = payout_jogo_1_temp
        else:
            # se o valor que tinha no payout for menor do que o valor atual, é porque o payout aumentou
            if self.payout_jogo_1 < payout_jogo_1_temp and payout_jogo_1_temp > 3:
                await self.telegram_bot.envia_mensagem(f'Payout do Jogo 1 aumentou de {self.payout_jogo_1} para {payout_jogo_1_temp}')
            self.payout_jogo_1 = payout_jogo_1_temp

        if not self.payout_jogo_2:
            self.payout_jogo_2 = payout_jogo_2_temp
        else:
            # se o valor que tinha no payout for menor do que o valor atual, é porque o payout aumentou
            if self.payout_jogo_2 < payout_jogo_2_temp and payout_jogo_2_temp > 3:
                await self.telegram_bot.envia_mensagem(f'Payout do Jogo 2 aumentou de {self.payout_jogo_2} para {payout_jogo_2_temp}')
            self.payout_jogo_2 = payout_jogo_2_temp

        if not self.payout_jogo_3:
            self.payout_jogo_3 = payout_jogo_3_temp
        else:
            # se o valor que tinha no payout for menor do que o valor atual, é porque o payout aumentou
            if self.payout_jogo_3 < payout_jogo_3_temp and payout_jogo_3_temp > 3:
                await self.telegram_bot.envia_mensagem(f'Payout do Jogo 3 aumentou de {self.payout_jogo_3} para {payout_jogo_3_temp}')
            self.payout_jogo_3 = payout_jogo_3_temp

        if not self.payout_jogo_4:
            self.payout_jogo_4 = payout_jogo_4_temp
        else:
            # se o valor que tinha no payout for menor do que o valor atual, é porque o payout aumentou
            if self.payout_jogo_4 < payout_jogo_4_temp and payout_jogo_4_temp > 3:
                await self.telegram_bot.envia_mensagem(f'Payout do Jogo 4 aumentou de {self.payout_jogo_4} para {payout_jogo_4_temp}')
            self.payout_jogo_4 = payout_jogo_4_temp


    async def duas_zebras(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 5 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste
        saldo_inicial = 644.29
        self.le_saldo()
        self.saldo_inicio_dia = self.saldo
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')

        print(f'meta de ganho: {self.meta_ganho}\nperda acumulada: {self.perda_acumulada}')

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")

                if jogos_abertos['summary']['openBetsCount'] >= 1:

                    if jogos_abertos['summary']['liveBetsCount'] > 0:
                        self.atualiza_payouts(jogos_abertos['betslips'])
 
                    print('Há apostas em aberto...')
                    print(datetime.now())                    
                    self.tempo_pausa = 5 * 60

                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        self.le_saldo()     

                        if not self.ja_conferiu_resultado:                            
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimos_dois_jogos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=2', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } } ); return await d.json();")
                            
                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            jogo_1 = ultimos_dois_jogos['betslips'][0]
                            jogo_2 = ultimos_dois_jogos['betslips'][1]               

                            early_payout_1 = jogo_1['isEarlyPayout']         
                            early_payout_2 = jogo_2['isEarlyPayout']         

                            # se um foi cancelado o outro obviamente também foi
                            if jogo_1['state'] == 'Canceled':
                                self.qt_apostas_feitas -= 1
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')
                                
                                valor_ultima_aposta_1 = float( jogo_1['stake']['value'])

                                valor_ultima_aposta_2 = float( jogo_2['stake']['value'])
                                
                                self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')                                   

                                self.perda_acumulada -= ( valor_ultima_aposta_1 + valor_ultima_aposta_2 )
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                                
                            elif jogo_1['state'] == 'Won' and not early_payout_1 or jogo_2['state'] == 'Won' and not early_payout_2:                                 
                                    
                                contador = 0
                                self.qt_apostas_feitas = 0
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')
                                while self.saldo <= self.saldo_antes_aposta:
                                    self.le_saldo()
                                    contador += 1
                                    if contador % 10 == 0:
                                        await self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                        # self.chrome.quit()
                                        # exit()

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                # self.valor_aposta = self.saldo * 0.00216 if not teste else valor_aposta #0.000325
                                # with open('meta_ganho.txt', 'w') as f:
                                #     f.write(f'{self.valor_aposta:.2f}')
                                self.perda_acumulada = 0.0
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')                                

                                if self.primeiro_alerta_depois_do_jogo:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo}\nMETA DE GANHO: {self.meta_ganho:.2f}')
                                        self.primeiro_alerta_depois_do_jogo = False   
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')

                            self.ja_conferiu_resultado = True
                            self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')

                        if self.teste:
                            self.valor_aposta = valor_aposta

                        data_inicio = datetime.now() + timedelta(hours=3, minutes=3)
                        data_inicio = data_inicio.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        data_fim = datetime.now() + timedelta(hours=12, minutes=3)
                        data_fim = data_fim.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&state=Upcoming&skip=0&take=100&offerCategories=Gridable&offerMapping=Filtered&sortBy=StartDate&sportIds=4&from={data_inicio}&to={data_fim}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                    
                                                                                    
                        print('--- chamou fixtures de novo ---')

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert'] or fixture['scoreboard']['periodId'] != 0:
                                        continue
                                    
                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )                                   

                                    print('nome evento', nome_evento )                               
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:     
                                        if option_market['name']['value'].lower() in ['resultado da partida', 'match result']:

                                            print('entrou no resultado da partida')

                                            time_casa = option_market['options'][0]
                                            empate = option_market['options'][1]
                                            time_2 = option_market['options'][2]

                                            odd_time_casa = float(time_casa['price']['odds'])
                                            odd_empate = float(empate['price']['odds'])
                                            odd_time_fora = float(time_fora['price']['odds'])

                                            mercado_time_casa_id = time_casa['id']
                                            mercado_empate_id = empate['id']
                                            mercado_time_fora_id = time_fora['id']

                                            hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')

                                            mercado_empate_escolhido = None
                                            mercado_time_escolhido = None
                                            odd_empate_escolhido = None
                                            odd_time_escolhido = None

                                            if odd_time_casa >= 2 and odd_time_fora > odd_time_casa:
                                                mercado_empate_escolhido = mercado_empate_id
                                                mercado_time_escolhido = mercado_time_fora_id
                                                odd_empate_escolhido = odd_empate
                                                odd_time_escolhido = odd_time_fora
                                            elif odd_time_fora >=2 and odd_time_casa > odd_time_fora:
                                                mercado_empate_escolhido = mercado_empate_id
                                                mercado_time_escolhido = mercado_time_casa_id
                                                odd_empate_escolhido = odd_empate
                                                odd_time_escolhido = odd_time_casa

                                            if mercado_empate_escolhido:
                                                jogos_aptos.append({ 'nome_evento': nome_evento, 'hora_inicio': hora_inicio, 'mercado_empate_escolhido': mercado_empate_escolhido, 'mercado_time_escolhido': mercado_time_escolhido, 'odd_empate_escolhido': odd_empate_escolhido, 'odd_time_escolhido': odd_time_escolhido })
                                         
                                except Exception as e:                                    
                                    print(e)    

                            print(jogos_aptos)      

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['hora_inicio'], -el['odd_time_escolhido'], -el['odd_empate_escolhido']  ))
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 2:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)

                            self.numero_apostas_feitas = 0

                            jogo_1 = jogos_aptos_ordenado[0]
                            jogo_2 = jogos_aptos_ordenado[1]

                            odd_aposta_1 = jogo_1['odd_empate_escolhido'] * jogo_2['odd_time_escolhido']
                            odd_aposta_2 = jogo_1['odd_time_escolhido'] * jogo_2['odd_empate_escolhido']

                            self.pausar_ate = jogo_1['hora_inicio']                            

                            # aqui vamos chamar a função de dutching
                            valores_apostas = calcula_dutching( [odd_aposta_1, odd_aposta_2 ], self.meta_ganho + self.perda_acumulada )
                            print( valores_apostas )
                            print(f'perda acumulada + meta ganho: {self.meta_ganho + self.perda_acumulada}')

                            # tenta limpar alguma aposta que possa estar no cupom
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except:
                                print('Não conseguiu limpar o cupom...')
                                print(e)

                            for i in range(2):                                

                                try:                                                                      
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_1['nome_evento'] + '?market=0')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e

                                    try:               
                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_1["mercado_empate_escolhido" if i == 0 else "mercado_time_escolhido"]}"]' ) ))                                     
                                        # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                        mercado.click() 
                                    except Exception as e:
                                        print('Erro ao clicar no mercado')
                                        raise e
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1               

                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_2['nome_evento'] + '?market=0')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e

                                    try:               
                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_2["mercado_time_escolhido" if i == 0 else "mercado_empate_escolhido"]}"]' ) ))                                     
                                        # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                        mercado.click() 
                                    except Exception as e:
                                        print('Erro ao clicar no mercado')
                                        raise e
                                    
                                    self.numero_apostas_feitas += 1 

                                    sleep(1)  

                                    if self.numero_apostas_feitas == 2:
                                        print('vai pegar a cota')                       
                                        cota = WebDriverWait(self.chrome, 10).until(
                                                    EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                        cota = float( cota.get_property('innerText') )
                                        
                                        self.valor_aposta = valores_apostas[i]

                                        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                        if self.valor_aposta > self.saldo and not self.teste:
                                            try:
                                                await self.telegram_bot_erro.envia_mensagem('MIOU')
                                            except:
                                                print('Não foi possível enviar mensagem ao telegram.')
                                            self.chrome.quit()
                                            exit()

                                        self.insere_valor_zebra(i)                                

                                except Exception as e:
                                    print('Algo deu errado')  
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'Algo deu errado ao fazer a {i+1} aposta.')
                                    except Exception as e:
                                        print(e)
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.numero_apostas_feitas = 0
                                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                    self.testa_sessao()

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(5)

                                    sleep(5)                       
                        
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
                        deu_erro = True
                        self.numero_apostas_feitas = 0
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:                           
                            self.testa_sessao()
                        self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()
   
    async def quatro_zebras(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 5 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste
        saldo_inicial = 644.29
        self.le_saldo()
        self.saldo_inicio_dia = self.saldo
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')

        print(f'meta de ganho: {self.meta_ganho}\nperda acumulada: {self.perda_acumulada}')

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=4&typeFilter=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")

                if jogos_abertos['summary']['openBetsCount'] >= 1:

                    if jogos_abertos['summary']['liveBetsCount'] > 0:
                        self.atualiza_payouts(jogos_abertos['betslips'])
 
                    print('Há apostas em aberto...')
                    print(datetime.now())                    
                    self.tempo_pausa = 5 * 60

                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        self.le_saldo()     

                        if not self.ja_conferiu_resultado:                            
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimos_quatro_jogos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=4&typeFilter=2', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } } ); return await d.json();")
                            
                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            jogo_1 = ultimos_quatro_jogos['betslips'][0]
                            jogo_2 = ultimos_quatro_jogos['betslips'][1]               
                            jogo_3 = ultimos_quatro_jogos['betslips'][2]    
                            jogo_4 = ultimos_quatro_jogos['betslips'][3]    

                            early_payout_1 = jogo_1['isEarlyPayout']         
                            early_payout_2 = jogo_2['isEarlyPayout']         
                            early_payout_3 = jogo_3['isEarlyPayout']    
                            early_payout_4 = jogo_4['isEarlyPayout']    

                            # se um foi cancelado o outro obviamente também foi
                            if jogo_1['state'] == 'Canceled':
                                self.qt_apostas_feitas -= 1
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')
                                
                                valor_ultima_aposta_1 = float( jogo_1['stake']['value'])

                                valor_ultima_aposta_2 = float( jogo_2['stake']['value'])

                                valor_ultima_aposta_3 = float( jogo_3['stake']['value'])

                                valor_ultima_aposta_4 = float( jogo_4['stake']['value'])
                                
                                self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')                                   

                                self.perda_acumulada -= ( valor_ultima_aposta_1 + valor_ultima_aposta_2 + valor_ultima_aposta_3 + valor_ultima_aposta_4 )
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')
                                
                            elif jogo_1['state'] == 'Won' and not early_payout_1 or jogo_2['state'] == 'Won' and not early_payout_2 or jogo_3['state'] == 'Won' and not early_payout_3 or jogo_4['state'] == 'Won' and not early_payout_4:                                 
                                    
                                contador = 0
                                self.qt_apostas_feitas = 0
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')
                                while self.saldo <= self.saldo_antes_aposta:
                                    self.le_saldo()
                                    contador += 1
                                    if contador % 10 == 0:
                                        await self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                        # self.chrome.quit()
                                        # exit()

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                # self.valor_aposta = self.saldo * 0.00216 if not teste else valor_aposta #0.000325
                                # with open('meta_ganho.txt', 'w') as f:
                                #     f.write(f'{self.valor_aposta:.2f}')
                                self.perda_acumulada = 0.0
                                self.escreve_em_arquivo('perda_acumulada.txt', f'{self.perda_acumulada:.2f}', 'w')                                

                                if self.primeiro_alerta_depois_do_jogo:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo}\nMETA DE GANHO: {self.meta_ganho:.2f}')
                                        self.primeiro_alerta_depois_do_jogo = False   
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')

                            self.ja_conferiu_resultado = True
                            self.escreve_em_arquivo('ja_conferiu_resultado.txt', 'True', 'w')

                        if self.teste:
                            self.valor_aposta = valor_aposta

                        data_inicio = datetime.now() + timedelta(hours=3, minutes=3)
                        data_inicio = data_inicio.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        data_fim = datetime.now() + timedelta(hours=12, minutes=3)
                        data_fim = data_fim.strftime('%Y-%m-%dT%H:%M:%S.000Z' )

                        fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&state=Upcoming&skip=0&take=100&offerCategories=Gridable&offerMapping=Filtered&sortBy=StartDate&sportIds=4&from={data_inicio}&to={data_fim}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                    
                                                                                    
                        print('--- chamou fixtures de novo ---')

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert'] or fixture['scoreboard']['periodId'] != 0:
                                        continue
                                    
                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )                                   

                                    print('nome evento', nome_evento )                               
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:     
                                        if option_market['name']['value'].lower() in ['resultado da partida', 'match result']:

                                            print('entrou no resultado da partida')

                                            time_casa = option_market['options'][0]
                                            empate = option_market['options'][1]
                                            time_fora = option_market['options'][2]

                                            odd_time_casa = float(time_casa['price']['odds'])
                                            odd_empate = float(empate['price']['odds'])
                                            odd_time_fora = float(time_fora['price']['odds'])

                                            mercado_time_casa_id = time_casa['id']
                                            mercado_empate_id = empate['id']
                                            mercado_time_fora_id = time_fora['id']

                                            hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')

                                            mercado_empate_escolhido = None
                                            mercado_time_escolhido = None
                                            odd_empate_escolhido = None
                                            odd_time_escolhido = None

                                            if odd_time_casa >= 2 and odd_time_fora > odd_time_casa:
                                                mercado_empate_escolhido = mercado_empate_id
                                                mercado_time_escolhido = mercado_time_fora_id
                                                odd_empate_escolhido = odd_empate
                                                odd_time_escolhido = odd_time_fora
                                            elif odd_time_fora >=2 and odd_time_casa > odd_time_fora:
                                                mercado_empate_escolhido = mercado_empate_id
                                                mercado_time_escolhido = mercado_time_casa_id
                                                odd_empate_escolhido = odd_empate
                                                odd_time_escolhido = odd_time_casa

                                            if mercado_empate_escolhido:
                                                jogos_aptos.append({ 'nome_evento': nome_evento, 'hora_inicio': hora_inicio, 'mercado_empate_escolhido': mercado_empate_escolhido, 'mercado_time_escolhido': mercado_time_escolhido, 'odd_empate_escolhido': odd_empate_escolhido, 'odd_time_escolhido': odd_time_escolhido })
                                         
                                except Exception as e:                                    
                                    print(e)    

                            print(jogos_aptos)      

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['hora_inicio'], -el['odd_time_escolhido'], -el['odd_empate_escolhido']  ))
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 2:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)

                            self.numero_apostas_feitas = 0

                            jogo_1 = jogos_aptos_ordenado[0]
                            jogo_2 = jogos_aptos_ordenado[1]

                            odd_aposta_1 = jogo_1['odd_empate_escolhido'] * jogo_2['odd_time_escolhido']
                            odd_aposta_2 = jogo_1['odd_time_escolhido'] * jogo_2['odd_empate_escolhido']
                            odd_aposta_3 = jogo_1['odd_empate_escolhido'] * jogo_2['odd_empate_escolhido']
                            odd_aposta_4 = jogo_1['odd_time_escolhido'] * jogo_2['odd_time_escolhido']
                            
                            # aqui vamos chamar a função de dutching
                            valores_apostas = calcula_dutching( [odd_aposta_1, odd_aposta_2, odd_aposta_3, odd_aposta_4 ], self.meta_ganho + self.perda_acumulada )
                            print( valores_apostas )
                            print(f'perda acumulada + meta ganho: {self.meta_ganho + self.perda_acumulada}')

                            apostas = [ ['mercado_empate_escolhido', 'mercado_time_escolhido'],
                                       ['mercado_time_escolhido','mercado_empate_escolhido'],
                                       ['mercado_empate_escolhido','mercado_empate_escolhido'],
                                       ['mercado_time_escolhido','mercado_time_escolhido'] ]
                            

                            # tenta limpar alguma aposta que possa estar no cupom
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except:
                                print('Não conseguiu limpar o cupom...')
                                print(e)

                            for i in range(4):                                

                                try:                                                                      
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_1['nome_evento'] + '?market=0')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e                                    

                                    try:               
                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_1[apostas[i][0]]}"]' ) ))                                     
                                        # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                        mercado.click() 
                                    except Exception as e:
                                        print('Erro ao clicar no mercado')
                                        raise e
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1               

                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_2['nome_evento'] + '?market=0')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e

                                    try:               
                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_2[apostas[i][1]]}"]' ) ))                                     
                                        # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                        mercado.click() 
                                    except Exception as e:
                                        print('Erro ao clicar no mercado')
                                        raise e
                                    
                                    self.numero_apostas_feitas += 1 

                                    sleep(1)  

                                    if self.numero_apostas_feitas == 2:
                                        print('vai pegar a cota')                       
                                        cota = WebDriverWait(self.chrome, 10).until(
                                                    EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                        cota = float( cota.get_property('innerText') )
                                        
                                        self.valor_aposta = valores_apostas[i]

                                        print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                        if self.valor_aposta > self.saldo and not self.teste:
                                            try:
                                                await self.telegram_bot_erro.envia_mensagem('MIOU')
                                            except:
                                                print('Não foi possível enviar mensagem ao telegram.')
                                            self.chrome.quit()
                                            exit()

                                        self.insere_valor_zebra(i)                                

                                except Exception as e:
                                    print('Algo deu errado')  
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem(f'Algo deu errado ao fazer a {i+1} aposta.')
                                    except Exception as e:
                                        print(e)
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.numero_apostas_feitas = 0
                                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                    self.testa_sessao()

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(5)

                                    sleep(5)                       
                        
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
                        deu_erro = True
                        self.numero_apostas_feitas = 0
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:                           
                            self.testa_sessao()
                        self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()


    async def zebra_empate_dutching(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 5 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste
        saldo_inicial = 644.29
        self.le_saldo()
        self.saldo_inicio_dia = self.saldo
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } }); return await d.json();")

                if jogos_abertos['summary']['openBetsCount'] >= 1:
                
                    print('Há apostas em aberto...')
                    print(datetime.now())                    

                    self.tempo_pausa = 3 * 60
                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        self.le_saldo()     

                        
                        # primeiro verificamos se a última aposta foi vitoriosa                    
                        ultimos_jogos = self.chrome.execute_script("let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=2&typeFilter=2', { headers: { 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' } } ); return await d.json();")
                        
                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        jogo_1 = ultimos_jogos['betslips'][0]
                        jogo_2 = ultimos_jogos['betslips'][1]

                        if jogo_1['state'] == 'Won' or jogo_2['state'] == 'Won':
                            # aqui o saldo deve ser maior do que depois da aposta, do contrário não estamos pegando o valor correto
                            try:
                                await self.telegram_bot_erro.envia_mensagem(f'GREEN DEPOIS DE {self.qt_apostas_feitas} APOSTAS.')
                            except Exception as e:
                                print(e)
                                
                            contador = 0
                            self.qt_apostas_feitas = 0
                            while self.saldo <= self.saldo_antes_aposta:
                                self.le_saldo()
                                contador += 1
                                if contador % 10 == 0:
                                    await self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                    # self.chrome.quit()
                                    # exit()

                            #atualiza o valor da meta de ganho uma vez que ganhou
                            self.valor_aposta = self.saldo * 0.00216 if not teste else valor_aposta #0.000325
                            with open('meta_ganho.txt', 'w') as f:
                                f.write(f'{self.valor_aposta:.2f}')
                            with open('perda_acumulada.txt', 'w') as f:
                                f.write('0.00')

                            if self.primeiro_alerta_depois_do_jogo:
                                try:
                                    await self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo}\nMETA DE GANHO: {self.valor_aposta:.2f}')
                                    self.primeiro_alerta_depois_do_jogo = False   
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                            
                            print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')

                        else:                                                        
                            perda_acumulada = None
                            with open('perda_acumulada.txt', 'r') as f:
                                perda_acumulada = float( f.read() )
                                    
                            print(f'valor perdido acumulado {perda_acumulada}')
                                
                            with open('meta_ganho.txt', 'r') as f:
                                self.valor_aposta = float( f.read() )
                            self.valor_aposta += perda_acumulada                            
                            
                        if self.teste:
                            self.valor_aposta = valor_aposta

                        fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&state=Upcoming&skip=0&take=100&offerCategories=Gridable&offerMapping=Filtered&sortBy=StartDate&sportIds=4', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                    
                                                                                    
                        print('--- chamou fixtures de novo ---')

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                        continue
                                    
                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                    
                                    numero_gols_atual = fixture['scoreboard']['score']                                
                                    numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                    periodo = '2º T'
                                    periodId = fixture['scoreboard']['periodId']
                                    is_running = fixture['scoreboard']['timer']['running']                                  
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:     
                                        if option_market['name']['value'] == 'Resultado da Partida' or option_market['name']['value'] == 'Match Result':
                                            for option in option_market['options']:    
                                                if option['name']['value'] == 'X':
                                                    continue      
                                                odd = float(option['price']['odds'])  
                                                option_id = option['id']                                       
                                                option_name = option['name']['value']                                                             
                                                
                                                confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                
                                                primeiro_ou_segundo_tempo = '2T'

                                                cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                        
                                                id = fixture['id']

                                                print( option_name, odd)

                                                if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                    jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': option['name']['value'], 'time': fixture['participants'][0]['name']['value'],'odd': odd, 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo, 'option_id' : option_id })
                                                    print(f'{odd} {nome_evento} {primeiro_ou_segundo_tempo}')
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')  
                                         
                                except Exception as e:
                                    print('erro')
                                    print(fixture)
                                    print(e)    

                            print(jogos_aptos)      

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['hora_inicio'], el['odd'] ))
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                if maior_odd < 2.5 :
                                    print('odds abaixo de 2.5')
                                    sleep(2 * 60)
                                else:
                                    sleep(60)
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)

                            self.numero_apostas_feitas = 0

                            # tenta limpar alguma aposta que possa estar no cupom
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except:
                                print('Não conseguiu limpar o cupom...')
                                print(e)

                            for jogo_apto in jogos_aptos_ordenado:                                

                                if self.varios_jogos:
                                    self.valor_aposta = valor_aposta

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if self.varios_jogos and f"{jogo_apto['id']}{jogo_apto['tempo']}{jogo_apto['mercado']}" in self.jogos_inseridos:
                                    print(f"aposta já inserida para o jogo {jogo_apto['id']} no tempo {jogo_apto['tempo']} no mercado {jogo_apto['mercado']}")
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca                                    
                                  
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] + '?market=0')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e
                                    # vamos pegar o mercado de resultas                                    

                                    #quer dizer que o mercado de gols é no primeiro tempo
                                    try:
                                        if jogo_apto['periodo'] == '1º T' or jogo_apto['periodo'] == '1º Tempo':
                                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a")))                                                    
                                            mercado_1_tempo.click()                                      
                                    except Exception as e:
                                        print('mercados bloqueados')
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise e
                                    # vamos pegar o mercado de resultas                         
                                                                        
                                    empate = WebDriverWait(self.chrome, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_apto["option_id"]}"]' ) ))                                     
                                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                    empate.click() 
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1                                 

                                    if self.numero_apostas_feitas == 2 and not self.varios_jogos:
                                        print('quebrou o laço aqui')
                                        break                                
                                    elif self.numero_apostas_feitas == 2 and self.varios_jogos:
                                        print('não quebrou o laço')
                                        cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                        cota = float( cota.get_property('innerText') )

                                        if cota < limite_inferior or cota > limite_superior:
                                            raise ErroCotaForaIntervalo

                                        self.valor_aposta = self.valor_aposta

                                        
                                        self.insere_valor(jogo_apto)

                                except Exception as e:
                                    print('Algo deu errado')  
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()
                                    self.numero_apostas_feitas = 0

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(10)

                                    sleep(5)                       

                            if self.numero_apostas_feitas == 2:     
                                print('vai pegar a cota')                       
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                cota = float( cota.get_property('innerText') )

                                if cota < 9 or cota > 16:
                                    raise ErroCotaForaIntervalo('cota fora do intervalo')
                                
                                self.valor_aposta = ( self.valor_aposta / ( cota - 1 ) ) + 0.01

                                print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                if self.valor_aposta > self.saldo:
                                    try:
                                        await self.telegram_bot_erro.envia_mensagem('MIOU')
                                    except:
                                        print('Não foi possível enviar mensagem ao telegram.')
                                    self.chrome.quit()
                                    exit()

                                self.insere_valor(jogo_apto)
                                
                            else:
                                print(datetime.now())
                        
                        print()
                        
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
                        deu_erro = True
                        self.numero_apostas_feitas = 0
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:                           
                            self.testa_sessao()
                        self.tempo_pausa = 1
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
            except Exception as e:
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()


    def partida_ja_era(self):
        if self.id_partida_atual == '' or not self.id_partida_atual:
            return
        try:
            jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&scoreboardMode=Full&fixtureIds={self.id_partida_atual}"); return await d.json();')

            placar = jogo_aberto['fixture']['scoreboard']['score']

            gols_casa = int(placar.split(':')[0])
            gols_fora = int(placar.split(':')[1])

            # if abs( gols_casa - gols_fora ) == 1 and self.jogo_apostado_em_empate:
            #     self.aposta_mesmo_jogo = True
            #     self.escreve_em_arquivo('aposta_mesmo_jogo.txt', 'True', 'w' )
            #     self.jogo_apostado_em_empate = False
            #     self.escreve_em_arquivo('jogo_apostado_em_empate.txt', 'False', 'w' )
            #     self.perdeu_ultimo_jogo = True
            #     self.escreve_em_arquivo('perdeu_ultimo_jogo.txt', 'True', 'w' )

            if abs( gols_casa - gols_fora ) >= 2:
                print('perdeu aposta na prática')
                self.perdeu_ultimo_jogo = True
                self.escreve_em_arquivo('perdeu_ultimo_jogo.txt', 'True', 'w' )
                 
                try:
                    self.jogos_inseridos.discard(self.id_partida_atual)
                    self.save_set_on_disk('jogos_inseridos.txt', self.jogos_inseridos)
                except Exception as e:
                    print(e)
                self.id_partida_anterior = self.id_partida_atual
                self.escreve_em_arquivo('id_partida_anterior.txt', self.id_partida_anterior, 'w')
                self.id_partida_atual = ''
                self.escreve_em_arquivo('id_partida_atual.txt', '', 'w')
        except Exception as e:   
            self.testa_sessao()    
            print(e)                 
            print('erro no método partida_ja_era')

    def aposta_ja_era_metodo(self, limite_inferior, limite_superior):

        print('chamou aposta_ja_era_metodo')
        try:
            jogos_abertos = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")

            if jogos_abertos['summary']['openBetsCount'] == 0:
                self.aposta_ja_era = True
                self.escreve_em_arquivo('aposta_ja_era.txt', 'True', 'w')
                self.next_option_name = ''
                self.escreve_em_arquivo('next_option_name.txt', '', 'w')
                self.next_option_id = ''
                self.escreve_em_arquivo('next_option_id.txt', '', 'w')
                self.id_partida_atual = ''
                self.escreve_em_arquivo('id_partida_atual.txt', '', 'w')
                self.aposta_mesmo_jogo = False
                self.escreve_em_arquivo('aposta_mesmo_jogo.txt', 'False', 'w')
                self.qt_apostas_mesmo_jogo = 0
                self.escreve_em_arquivo('qt_apostas_mesmo_jogo.txt', '0', 'w')
                self.mercados_restantes = []
                self.save_array_on_disk('mercados_restantes.json', self.mercados_restantes)
                return
            
            self.qt_apostas_mesmo_jogo = jogos_abertos['summary']['openBetsCount']
            self.escreve_em_arquivo('qt_apostas_mesmo_jogo.txt', f'{self.qt_apostas_mesmo_jogo}', 'w')

            if len( self.mercados_restantes ) == 0:
                return

            jogo_aberto = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&scoreboardMode=Full&fixtureIds={self.id_partida_atual}&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")

            fixture = jogo_aberto['fixture']
            periodo = fixture['scoreboard']['period']
            periodId = fixture['scoreboard']['periodId']
            is_running = fixture['scoreboard']['timer']['running']

            if not is_running:
                self.qt_apostas_mesmo_jogo = 0
                self.escreve_em_arquivo('qt_apostas_mesmo_jogo.txt', f'{self.qt_apostas_mesmo_jogo}', 'w')
                return
                
            option_markets = fixture['optionMarkets']
            for option_market in option_markets:     
                if periodo == '1º T':
                    if option_market['name']['value'].lower() == '1º tempo - total de gols':
                        for option in option_market['options']:   
                            if option['name']['value'] == self.mercados_restantes[-1]:
                                odd = float(option['price']['odds'])
                                print(odd)
                                self.next_option_id = option['id']
                                self.escreve_em_arquivo('next_option_id.txt', f'{self.next_option_id}', 'w')
                                if odd >= limite_inferior and odd <= limite_superior:
                                    self.aposta_ja_era = True         
                                    self.escreve_em_arquivo('aposta_ja_era.txt', 'True', 'w')
                                    self.aposta_mesmo_jogo = True
                                    self.escreve_em_arquivo('aposta_mesmo_jogo.txt', 'True', 'w')                                    
                                    return                              
        except Exception as e:
            self.testa_sessao()            

    async def altas_odds_empate(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 3 * 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        self.teste = teste
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        saldo_inicial = 644.29
        self.le_saldo()
        self.saldo_inicio_dia = self.saldo
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')
        print('id partida atual ', self.id_partida_atual)
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')
        print('perdeu último jogo ', self.perdeu_ultimo_jogo)
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')
        print('jogos inseridos ', self.jogos_inseridos)
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')
        self.id_partida_anterior = self.le_de_arquivo('id_partida_anterior.txt', 'string')

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

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
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

                if jogos_abertos['summary']['openBetsCount'] >= 1 and not self.perdeu_ultimo_jogo:

                    # vamos ver se a partida já era
                    self.partida_ja_era()

                    if self.perdeu_ultimo_jogo:
                        self.tempo_pausa = 0
                
                    print('Há apostas em aberto...')
                    print(datetime.now())

                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        self.le_saldo()           
                        try:
                            self.jogos_inseridos.discard( self.id_partida_atual )
                            self.save_set_on_disk( 'jogos_inseridos.txt', self.jogos_inseridos)
                            if self.id_partida_atual != '' and self.id_partida_atual is not None:
                                self.id_partida_anterior = self.id_partida_atual
                                self.escreve_em_arquivo('id_partida_anterior.txt', self.id_partida_anterior, 'w')
                                self.id_partida_atual = ''
                                self.escreve_em_arquivo('id_partida_atual.txt', '', 'w')
                        except Exception as e:
                            print(e)

                        if not self.varios_jogos:
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')

                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = ultimo_jogo['betslips'][0]

                            early_payout = ultimo_jogo['isEarlyPayout']

                            print('early_payout ', early_payout)

                            # se perdeu último jogo é True então é porque ainda há um jogo aberto mas que já perdemos na prática
                            if self.perdeu_ultimo_jogo or early_payout or ultimo_jogo['state'] == 'Lost':
                                perda_acumulada = None
                                with open('perda_acumulada.txt', 'r') as f:
                                    perda_acumulada = float( f.read() )
                                        
                                print(f'valor perdido acumulado {perda_acumulada}')
                                 
                                with open('meta_ganho.txt', 'r') as f:
                                    self.valor_aposta = float( f.read() )

                                self.valor_aposta += perda_acumulada

                                print(f'valor da aposta com perda acumulada: {self.valor_aposta}')

                            elif ultimo_jogo['state'] == 'Canceled':
                                self.qt_apostas_feitas -= 1
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', f'{self.qt_apostas_feitas}', 'w')
                                
                                valor_ultima_aposta = float( ultimo_jogo['stake']['value'])
                                
                                perda_acumulada = None
                                with open('perda_acumulada.txt', 'r') as f:
                                    perda_acumulada = float( f.read() )                                    

                                perda_acumulada -= valor_ultima_aposta

                                self.valor_aposta -= perda_acumulada
                                
                                with open('perda_acumulada.txt', 'w') as f:
                                    f.write(f'{perda_acumulada:.2f}')                               
                                
                            elif ultimo_jogo['state'] == 'Won' and not early_payout:                                 
                                # aqui o saldo deve ser maior do que depois da aposta, do contrário não estamos pegando o valor correto
                                contador = 0
                                self.qt_apostas_feitas = 0
                                self.perdeu_ultimo_jogo = False                                
                                self.escreve_em_arquivo('perdeu_ultimo_jogo.txt', 'False', 'w')
                                self.escreve_em_arquivo('qt_apostas_feitas.txt', '0', 'w')
                                try:
                                    self.jogos_inseridos.discard(self.id_partida_atual)
                                    self.save_set_on_disk('jogos_inseridos.txt', self.jogos_inseridos)
                                except Exception as e:
                                    print(e)
                                self.id_partida_atual = ''
                                self.escreve_em_arquivo('id_partida_atual.txt', '', 'w')
                                while self.saldo <= self.saldo_antes_aposta:
                                    self.le_saldo()
                                    contador += 1
                                    if contador % 10 == 0:
                                        self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                self.valor_aposta = self.saldo * 0.00417
                                with open('meta_ganho.txt', 'w') as f:
                                    f.write(f'{self.valor_aposta:.2f}')
                                with open('perda_acumulada.txt', 'w') as f:
                                    f.write('0.00')

                                if self.primeiro_alerta_depois_do_jogo:
                                    try:
                                        self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo}\nMETA DE GANHO: {self.valor_aposta:.2f}')
                                        self.primeiro_alerta_depois_do_jogo = False   
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                              
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                        else:
                            self.le_saldo()
                            if self.saldo > saldo_inicial:
                                self.telegram_bot_erro.envia_mensagem('ganho real')
                                self.chrome.quit()
                                exit()
                        
                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1"); return await d.json();')                                   

                        
                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:                               
                                try:
                                    if fixture['scoreboard']['sportId'] != 4:
                                        continue
                                    
                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                    
                                    placar = fixture['scoreboard']['score']
                                    gols_casa = int(placar.split(':')[0])
                                    gols_fora = int(placar.split(':')[1])
                                    
                                    if abs( gols_casa - gols_fora ) > 1:
                                        continue

                                    # se chegar aqui é porque a gente pensou que o jogo que tínahmos apostado tinha mais de um
                                    # gol de vantagem, mas o VAR provavelmente anulou o gol
                                    if fixture['id'] == self.id_partida_anterior:
                                        self.perdeu_ultimo_jogo = False
                                        self.escreve_em_arquivo('perdeu_ultimo_jogo.txt', 'False', 'w')
                                        self.id_partida_atual = self.id_partida_anterior
                                        self.escreve_em_arquivo('id_partida_atual.txt', self.id_partida_atual, 'w')
                                        break

                                    periodo = fixture['scoreboard']['period']
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:    

                                        if option_market['name']['value'] == 'Resultado da Partida' or option_market['name']['value'] == 'Match Result':
                                            for option in option_market['options']:
                                                # faço um for pra saber em qual mercado posso apostar que vai me retornar a odd que eu quero
                                                #for n_gols in range( 3 ):

                                                if option['name']['value'] == 'X':      
                                                    option_id = option['id']                                              
                                                    confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                    odd = float(option['price']['odds'])
                                                    print( odd )

                                                    cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                    hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                            
                                                    id = fixture['id']                                                

                                                    if odd >= limite_inferior and odd <= limite_superior:
                                                        jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': 'X', 'time': fixture['participants'][0]['name']['value'],'odd': odd, 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'periodo': periodo, 'option_id': option_id, 'placar': placar })
                                                        print(f'{odd} {nome_evento} {periodo}')
                                                        odds.append(f'{odd} {confronto} {periodo} {cronometro}')
                                        
                                except Exception as e:
                                    print(e)          

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( -el['cronometro'], el['odd'],  ) )
                            # aqui vou fazer um laço pelos jogos aptos 
                            # e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())                                
                                sleep(2.5 * 60)                                
                                continue                     
                            
                            # caso haja algum jogo no cupom a gente vai tentar limpar
                            try:
                                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            except Exception as e:
                                print('Não conseguiu limpar os jogos...')
                                print(e)


                            for jogo_apto in jogos_aptos_ordenado:

                                self.numero_apostas_feitas = 0

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if self.varios_jogos and f"{jogo_apto['id']}{jogo_apto['tempo']}{jogo_apto['mercado']}" in self.jogos_inseridos:
                                    print(f"aposta já inserida para o jogo {jogo_apto['id']} no tempo {jogo_apto['tempo']} no mercado {jogo_apto['mercado']}")
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca

                                    # tenta limpar alguma aposta que possa estar no cupom
                                    try:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                    except:
                                        print('Não conseguiu limpar o cupom...')
                                        print(e)
                                  
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] )
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e
                                    # vamos pegar o mercado de resultas                                    
                                    empate = WebDriverWait(self.chrome, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, f'//ms-event-pick[@data-test-option-id="{jogo_apto["option_id"]}"]' ) )) 
                                    # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
                                    empate.click()  
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1                                 

                                    if self.numero_apostas_feitas == 1 and not self.varios_jogos:
                                        print('quebrou o laço aqui')
                                        break                                
                                    elif self.numero_apostas_feitas == 1 and self.varios_jogos:
                                        print('não quebrou o laço')
                                        cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                        cota = float( cota.get_property('innerText') )

                                        if cota < limite_inferior or cota > limite_superior:
                                            raise ErroCotaForaIntervalo

                                        self.valor_aposta = self.valor_aposta
                                        
                                        self.insere_valor(jogo_apto)

                                except Exception as e:
                                    print('Algo deu errado')  
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()
                                    self.numero_apostas_feitas = 0

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(10)

                                    sleep(5)                       

                            if self.numero_apostas_feitas == 1:     
                                print('vai pegar a cota')                       
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                cota = float( cota.get_property('innerText') )

                                if cota < limite_inferior or cota > limite_superior:
                                    raise ErroCotaForaIntervalo('cota fora do intervalo')
                                
                                self.valor_aposta = ( self.valor_aposta / ( cota - 1 ) ) + 0.01

                                print(f'cota: {cota}\nvalor_aposta: {self.valor_aposta}')

                                if self.valor_aposta > self.saldo:
                                    try:
                                        self.telegram_bot_erro.envia_mensagem('MIOU')
                                    except:
                                        print('Não foi possível enviar mensagem ao telegram.')
                                    self.chrome.quit()
                                    exit()

                                self.insere_valor(jogo_apto)
                                
                            else:
                                print(datetime.now())
                        
                        print()
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        self.numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(5)
                        print(e)
                    except Exception as e:
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            self.numero_apostas_feitas = 0
                            self.testa_sessao()
                            sleep(5)
                        pass
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
                sleep(10)
            except Exception as e:
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()
                sleep(10)

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

    def save_set_on_disk(self, nome_arquivo, set):                
        string = ''
        for el in set:
            string += f'{el};'
        with open(nome_arquivo, 'w') as fp:
            fp.write(string[:-1])

    def read_set_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'r') as fp:
            string_array = fp.read().split(';')
            return set( string_array )

    def save_array_on_disk(self, nome_arquivo, array):        
        with open(nome_arquivo, "w") as fp:
            json.dump(array, fp)

    def read_array_from_disk(self, nome_arquivo):
        with open(nome_arquivo, 'rb') as fp:
            n_list = json.load(fp)
            return n_list 

    def is_bet_open(self, bet_number):
        print('verificando se aposta está aberta')
        try:
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=20&typeFilter=1"); return await d.json();')
            for jogo in jogos_abertos['betslips']:
                if jogo['betSlipNumber'] == bet_number:
                    if jogo['state'] == 'Open':
                        print('aposta aberta')
                        return True
                    else:
                        print('aposta liquidada')
                        return False
        except Exception as e:
            self.testa_sessao()
            print(e)          
            return True            
        
    
    def is_bet_won(self, bet_number):
        jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=20&typeFilter=2"); return await d.json();')
        for jogo in jogos_abertos['betslips']:
            if jogo['betSlipNumber'] == bet_number:
                if jogo['state'] == 'Won':
                    print('aposta ganhou')
                    self.payout = jogo['payout']['value']
                    try:
                        self.telegram_bot_erro.envia_mensagem(f'ganhou aposta, {self.payout:.2f}')
                    except Exception as e:
                        print(e)
                    return True
                else:
                    print('aposta perdeu')
                    return False
        return False

    def is_game_running(self, fixture_id):
        print('verificando se jogo ainda está rolando')
        try:
            fixture = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixture-view?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&offerMapping=All&scoreboardMode=Full&fixtureIds={fixture_id}', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")            
            if fixture.get('fixture') != None:
                return True
            return False
        except:
            self.testa_sessao()    
            return True
                

    def busca_odds_1_5_varios_jogos(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria, qt_jogos_paralelos):
        self.tempo_pausa = 60
        jogos_aptos = []
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        saldo_inicial = 644.29
        self.le_saldo()
        self.saldo_inicio_dia = self.saldo
        self.qt_apostas_feitas = None
        # guarda o índice do array
        self.indice_jogo_atual = self.le_de_arquivo('indice_jogo_atual.txt', 'int')
        self.jogos_feitos = self.read_array_from_disk('jogos_feitos.json')
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')
        self.qt_jogos_paralelos = qt_jogos_paralelos

        if len( self.jogos_feitos ) == 0:
            self.jogos_feitos = [None for i in range(self.qt_jogos_paralelos)]

        print(self.jogos_feitos)
        

        while True:
            maior_odd = 0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

            algum_ativo = False
            for jogo in self.jogos_feitos:
                if jogo:
                    if jogo['ativo']:
                        algum_ativo = True
                else:
                    algum_ativo = True

            if not algum_ativo:
                self.telegram_bot_erro.envia_mensagem('nenhuma aposta ativa')
                self.chrome.quit()
                exit()

            diferenca_tempo = datetime.now() - self.horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\n')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                self.horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:               
                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')

                if jogos_abertos['summary']['openBetsCount'] >= 1 and not self.varios_jogos:
                
                    print('Há apostas em aberto...')
                    print(datetime.now())

                    if self.qt_apostas_feitas == None:
                        self.qt_apostas_feitas = self.quantidade_apostas_feitas() + 1

                    self.tempo_pausa = 2 * 60
                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        if self.qt_apostas_feitas == None:
                            self.qt_apostas_feitas = self.quantidade_apostas_feitas()
                        self.le_saldo()           

                        if not self.varios_jogos:
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                            
                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = ultimo_jogo['betslips'][0]

                            if ultimo_jogo['state'] == 'Lost':                            
                                
                                perda_acumulada = None
                                with open('perda_acumulada.txt', 'r') as f:
                                    perda_acumulada = float( f.read() )
                                        
                                print(f'valor perdido acumulado {perda_acumulada}')
                                 
                                with open('meta_ganho.txt', 'r') as f:
                                    self.valor_aposta = float( f.read() )

                                self.valor_aposta += perda_acumulada

                            elif ultimo_jogo['state'] == 'Canceled':
                                self.qt_apostas_feitas -= 1
                                
                                valor_ultima_aposta = float( ultimo_jogo['stake']['value'])
                                
                                perda_acumulada = None
                                with open('perda_acumulada.txt', 'r') as f:
                                    perda_acumulada = float( f.read() )                                    

                                perda_acumulada -= valor_ultima_aposta

                                self.valor_aposta -= perda_acumulada
                                
                                with open('perda_acumulada.txt', 'w') as f:
                                    f.write(f'{perda_acumulada:.2f}')                               
                                
                            else:                                 
                                # aqui o saldo deve ser maior do que depois da aposta, do contrário não estamos pegando o valor correto
                                contador = 0
                                self.qt_apostas_feitas = 0
                                while self.saldo <= self.saldo_antes_aposta:
                                    self.le_saldo()
                                    contador += 1
                                    if contador % 10 == 0:
                                        self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                        # self.chrome.quit()
                                        # exit()

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                self.valor_aposta = self.saldo * 0.003 if not teste else valor_aposta #0.000325
                                with open('meta_ganho.txt', 'w') as f:
                                    f.write(f'{self.valor_aposta:.2f}')
                                with open('perda_acumulada.txt', 'w') as f:
                                    f.write('0.00')

                                if self.primeiro_alerta_depois_do_jogo:
                                    try:
                                        self.telegram_bot_erro.envia_mensagem(f'GANHOU! {self.saldo}\nMETA DE GANHO: {self.valor_aposta:.2f}')
                                        self.primeiro_alerta_depois_do_jogo = False   
                                    except Exception as e:
                                        print(e)
                                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                              
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                        else:
                            self.le_saldo()

                        if teste:
                            self.valor_aposta = valor_aposta

                        alguma_aposta_disponivel = False
                        for jogo in self.jogos_feitos:
                            if jogo:
                                if not self.is_bet_open(jogo['id_aposta']) and jogo['ativo']:
                                    alguma_aposta_disponivel = True
                                    break
                            else:
                                alguma_aposta_disponivel = True
                                break
                        
                        if not alguma_aposta_disponivel:
                            print('todas as apostas estão abertas')
                            sleep(60)
                            continue
                        else:
                            print('há apostas disponíveis')
                        
                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1"); return await d.json();')                                   
                        

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:         
                      
                                try:

                                    if fixture['scoreboard']['sportId'] != 4:
                                        continue
                                    nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                    
                                    numero_gols_atual = fixture['scoreboard']['score']                                
                                    numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                               
                                    periodo = fixture['scoreboard']['period']
                                    
                                    option_markets = fixture['optionMarkets']
                                    for option_market in option_markets:     
                                        if periodo == '1º T':
                                            if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                for option in option_market['options']:
                                                    # faço um for pra saber em qual mercado posso apostar que vai me retornar a odd que eu quero
                                                    #for n_gols in range( 3 ):

                                                    if option['name']['value'] == f'Menos de {numero_gols_atual},5':                                                    
                                                        confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                        odd = float(option['price']['odds'])
                                                        print( odd )
                                                        primeiro_ou_segundo_tempo = ''
                                                        mercado = option['name']['value']
                                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                            primeiro_ou_segundo_tempo = '1T'
                                                        else:
                                                            primeiro_ou_segundo_tempo = '2T'

                                                        cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                        hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                
                                                        id = fixture['id']

                                                        if odd < maior_odd and odd > 1.25 and f"{fixture['id']}{primeiro_ou_segundo_tempo}{mercado}" not in self.jogos_inseridos:
                                                            maior_odd = odd
                                                    

                                                        if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}{mercado}" not in self.jogos_inseridos:
                                                            jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': option['name']['value'], 'time': fixture['participants'][0]['name']['value'],'odd': odd, 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo, 'mercado': mercado })
                                                            print(f'{odd} {nome_evento} {primeiro_ou_segundo_tempo}')
                                                            odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')  
                                        else:
                                            if option_market['name']['value'] == 'Total de gols':
                                                for option in option_market['options']:
                                                    #for n_gols in range( 3 ):
                                                    if option['name']['value'] == f'Menos de {numero_gols_atual},5':
                                                        confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                        odd = float(option['price']['odds'])
                                                        primeiro_ou_segundo_tempo = ''
                                                        mercado = option['name']['value']
                                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                            primeiro_ou_segundo_tempo = '1T'
                                                        else:
                                                            primeiro_ou_segundo_tempo = '2T'

                                                        cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                        hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                
                                                        id = fixture['id']

                                                        if odd < maior_odd and odd > 1.25 and f"{fixture['id']}{primeiro_ou_segundo_tempo}{mercado}" not in self.jogos_inseridos:
                                                            maior_odd = odd
                                                    

                                                        if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}{mercado}" not in self.jogos_inseridos:
                                                            jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': option['name']['value'], 'time': fixture['participants'][0]['name']['value'],'odd': odd, 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo })
                                                            print(f'{odd} {nome_evento} {primeiro_ou_segundo_tempo}')
                                                            odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')  
                                except Exception as e:
                                    print(e)          

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], -el['cronometro'], el['odd']  ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada


                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                if maior_odd > 1.4 :
                                    print('odds acima de 1.4')
                                    sleep(2 * 60)
                                else:
                                    sleep(30)
                                continue                     
                        

                            for jogo_apto in jogos_aptos_ordenado:

                                # caso haja algum jogo no cupom a gente vai tentar limpar
                                try:
                                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                except Exception as e:
                                    print('Não conseguiu limpar os jogos...')
                                    print(e)


                                self.numero_apostas_feitas = 0

                                if self.varios_jogos:
                                    self.valor_aposta = valor_aposta

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if self.varios_jogos and f"{jogo_apto['id']}{jogo_apto['tempo']}{jogo_apto['mercado']}" in self.jogos_inseridos:
                                    print(f"aposta já inserida para o jogo {jogo_apto['id']} no tempo {jogo_apto['tempo']} no mercado {jogo_apto['mercado']}")
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca

                                    # tenta limpar alguma aposta que possa estar no cupom
                                    try:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                    except:
                                        print('Não conseguiu limpar o cupom...')
                                        print(e)
                                  
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] + '?market=2')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                        
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e
                                    # vamos pegar o mercado de resultas                                    

                                    #quer dizer que o mercado de gols é no primeiro tempo
                                    try:
                                        if jogo_apto['periodo'] == '1º T' or jogo_apto['periodo'] == '1º Tempo':
                                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º Tempo']/ancestor::a")))                                                    
                                            mercado_1_tempo.click()                                      
                                    except Exception as e:
                                        print('mercados bloqueados')
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise e

                                    mais_1_meio = WebDriverWait(self.chrome, 10).until(
                                        EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{jogo_apto['mercado']}']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                    mais_1_meio.click()  
                                    
                                    sleep(1)    

                                    self.numero_apostas_feitas += 1                                 

                                    if self.numero_apostas_feitas == 1 and not self.varios_jogos:
                                        print('quebrou o laço aqui')
                                        break                                
                                    elif self.numero_apostas_feitas == 1 and self.varios_jogos:
                                        print('não quebrou o laço')
                                        cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                        cota = float( cota.get_property('innerText') )

                                        if cota < limite_inferior or cota > limite_superior:
                                            raise ErroCotaForaIntervalo
                                        
                                        if self.indice_jogo_atual == self.qt_jogos_paralelos:
                                            self.indice_jogo_atual = 0

                                        # o valor da aposta aqui vai ser o valor que está armazenado no saldo do jogo atual
                                        if self.jogos_feitos[self.indice_jogo_atual] == None:
                                        # se não existir o jogo para esse índice é porque está començando agora
                                            self.jogos_feitos[self.indice_jogo_atual] = { 'id_aposta': None, 'qt_jogos_ganhos': 0, 'saldo': 1, 'ativo': True }

                                            self.valor_aposta = self.jogos_feitos[self.indice_jogo_atual]['saldo']
                                            print('passou aqui 1')
                                            self.insere_valor(jogo_apto)
                                        else:
                                            # vamos ver se a aposta está ativa ou se já perdeu
                                            counter = 0
                                            while counter < self.qt_jogos_paralelos:
                                                id_aposta = self.jogos_feitos[self.indice_jogo_atual]['id_aposta']
                                                # verificamos se essa posta ainda está aberta
                                                if self.is_bet_open(id_aposta):
                                                    self.indice_jogo_atual += 1
                                                    if self.indice_jogo_atual == self.qt_jogos_paralelos:
                                                        self.indice_jogo_atual = 0
                                                    counter += 1
                                                    continue
                                                else:
                                                    # vamos ver se a aposta foi vitoriasa
                                                    if self.is_bet_won(id_aposta):
                                                        self.jogos_feitos[self.indice_jogo_atual]['qt_jogos_ganhos'] += 1
                                                        self.jogos_feitos[self.indice_jogo_atual]['saldo'] = self.payout
                                                        self.jogos_feitos[self.indice_jogo_atual]['id_aposta'] = None

                                                        self.valor_aposta = self.jogos_feitos[self.indice_jogo_atual]['saldo']    
                                                        self.insere_valor(jogo_apto)  
                                                        break
                                                    else:
                                                        self.jogos_feitos[self.indice_jogo_atual]['qt_jogos_ganhos'] = 0
                                                        self.jogos_feitos[self.indice_jogo_atual]['saldo'] = 0
                                                        self.jogos_feitos[self.indice_jogo_atual]['id_aposta'] = None
                                                        self.jogos_feitos[self.indice_jogo_atual]['ativo'] = False

                                                        self.indice_jogo_atual += 1
                                                        if self.indice_jogo_atual == self.qt_jogos_paralelos:
                                                            self.indice_jogo_atual = 0
                                                        counter += 1
                                                        continue

                                                    self.save_array_on_disk('jogos_feitos.json', self.jogos_feitos)

                                except Exception as e:
                                    print('Algo deu errado')  
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')
                                    self.chrome.maximize_window()
                                    self.chrome.fullscreen_window()
                                    self.numero_apostas_feitas = 0

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                                                                
                                        self.numero_apostas_feitas = 0
                                        self.testa_sessao()
                                        sleep(10)

                                    sleep(5)                       

                        
                        print()
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        self.numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(5)
                        print(e)
                    except Exception as e:
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            self.numero_apostas_feitas = 0
                            self.testa_sessao()
                            sleep(5)
                        pass
                
                if not deu_erro:
                    sleep(60)
            except KeyError as e:
                self.numero_apostas_feitas = 0
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
                sleep(10)
            except Exception as e:
                self.numero_apostas_feitas = 0
                print(e)
                self.testa_sessao()
                sleep(10)
   
    async def faz_aposta(self, url, option_id, target_odd, soma_gols):
        try:            
            self.chrome.get( f'https://sports.sportingbet.com/pt-br/sports/eventos/{url}?market=3')
            self.chrome.maximize_window()
            self.chrome.fullscreen_window()            

            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...') 

            gols_1 = 0
            gols_2 = 0
            try:
                gols_1 = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="main-view"]/ng-component/ms-header/ms-header-content/ms-scoreboard/ms-pair-game-scoreboard/div/div[1]/div[1]/ms-score-card/span[1]/span/div[1]' )))   
                gols_1 = int( gols_1.get_property('innerText') )
            except Exception as e:
                print(e)

            try:
                gols_2 = WebDriverWait(self.chrome, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="main-view"]/ng-component/ms-header/ms-header-content/ms-scoreboard/ms-pair-game-scoreboard/div/div[1]/div[1]/ms-score-card/span[3]/span/div[1]' )))    
                gols_2 = int( gols_2.get_property('innerText') )  
            except Exception as e:
                print(e)

            # vamos ter certeza de que o número de gols é o que a API diz que é
            if target_odd == None and ( gols_1 + gols_2 ) != soma_gols:
                return False

            mercado = WebDriverWait(self.chrome, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//ms-event-pick[@data-test-option-id='{option_id}']" ) ))                                     
            # f"//*[normalize-space(text()) = 'X']/ancestor::div/ancestor::ms-event-pick"
            mercado.click()             

            odd = WebDriverWait(self.chrome, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
            odd = float( odd.get_property('innerText') )

            if target_odd == None:
                valor_da_primeira_aposta = 10.1 / odd

                if valor_da_primeira_aposta >= 9.8:
                    return False

                self.valor_aposta = valor_da_primeira_aposta
                sobra = 10 - valor_da_primeira_aposta
                self.target_odd = 10.1 / sobra
                
            else:
                if odd < target_odd:
                    try:
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    except:
                        print('Não conseguiu limpar os jogos...')
                    return False
            
                self.valor_aposta = 10.1 / target_odd

            return await self.insere_valor_favorito(target_odd)                                              
        except Exception as e:
            print(e)
            print('Erro no faz aposta')  
            self.testa_sessao()
            return False
        
    async def faz_apostas_over(self, fixture):
        pass

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
    
    async def favoritos_para_virar(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):

        self.tempo_pausa = 2.5 * 60        
        self.horario_ultima_checagem = datetime.now()
        self.times_favoritos = []        
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        self.teste = teste     

        self.times_para_apostas_over = None
        try:
            with open('times_para_apostas_over.pkl', 'rb') as inp:
                self.times_para_apostas_over = pickle.load(inp)
        except:
            print('sem arquivo criado')
        if self.times_para_apostas_over == None:
            self.times_para_apostas_over = dict()
        
        self.le_saldo()      
        self.qt_apostas_feitas = self.le_de_arquivo('qt_apostas_feitas.txt', 'int' )        
        self.id_partida_atual = self.le_de_arquivo('id_partida_atual.txt', 'string')        
        self.perdeu_ultimo_jogo = self.le_de_arquivo('perdeu_ultimo_jogo.txt', 'boolean')        
        self.jogos_inseridos = self.read_set_from_disk('jogos_inseridos.txt')        
        self.jogo_apostado_em_empate = self.le_de_arquivo('jogo_apostado_em_empate.txt', 'boolean')        
        self.aposta_ja_era = self.le_de_arquivo('aposta_ja_era.txt', 'boolean')
        self.segunda_aposta_jogo = self.le_de_arquivo('segunda_aposta_jogo.txt', 'boolean')
        self.next_option_name = self.le_de_arquivo('next_option_name.txt', 'string')        
        self.next_option_id = self.le_de_arquivo('next_option_id.txt', 'string')
        self.aposta_mesmo_jogo = self.le_de_arquivo('aposta_mesmo_jogo.txt', 'boolean')
        self.qt_apostas_mesmo_jogo = self.le_de_arquivo('qt_apostas_mesmo_jogo.txt', 'int')
        self.mercados_restantes = self.read_array_from_disk('mercados_restantes.json')
        self.ja_conferiu_resultado = self.le_de_arquivo('ja_conferiu_resultado.txt', 'boolean')
        self.meta_ganho = self.le_de_arquivo('meta_ganho.txt', 'float')
        self.valor_aposta = self.meta_ganho
        self.perda_acumulada = self.le_de_arquivo('perda_acumulada.txt', 'float')
        self.controle_acima_abaixo = self.le_de_arquivo('controle_acima_abaixo.txt', 'int')

        print('valor aposta ', self.valor_aposta )
        print('teste ', self.teste)

        while True:
            # for bet_id in self.bet_ids.copy():                                
            #     if not self.is_bet_open(bet_id):
            #         self.bet_ids.remove(bet_id)               

            deu_erro = False
            fixtures = None

            try:
                jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                self.bet_ids = jogo_aberto['summary']['betNumbers']

                self.inserted_fixture_ids = []
                for open_event in jogo_aberto['summary']['openEvents']:
                    self.inserted_fixture_ids.append(open_event)
            except:
                self.testa_sessao()            

            for key in self.times_para_apostas_over.copy():
                if key not in self.inserted_fixture_ids:
                    self.times_para_apostas_over.pop(key)

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
                fixtures = self.chrome.execute_script(f"let d = await fetch('https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=200&offerCategories=Gridable&offerMapping=Filtered&sortBy=StartDate&sportIds=4&forceFresh=1', {{ headers: {{ 'Pragma': 'no-cache', 'Cache-Control': 'no-cache' }} }}); return await d.json();")                                   

                print('\n--- chamou fixtures de novo ---\n')
                print(datetime.now())

                if len( fixtures['fixtures'] ) == 0:
                    print('Sem jogos ao vivo...')
                    print(datetime.now())
                    self.tempo_pausa = 10 * 60
                else:
                    aposta_feita = False
                    is_any_target_odd_close = False
                    for fixture in fixtures['fixtures']:          
                        try:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        except:
                            print('Não conseguiu limpar os jogos...')                        
                        try:
                            fixture_id = fixture['id']
                            gols_casa = int( fixture['scoreboard']['score'].split(':')[0])
                            gols_fora = int( fixture['scoreboard']['score'].split(':')[1])
                            soma_gols = gols_casa + gols_fora
                            periodo = fixture['scoreboard']['period']

                            if fixture['scoreboard']['sportId'] != 4 or not fixture['liveAlert']:
                                continue       

                            nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )

                            if fixture_id in self.inserted_fixture_ids:       
                                aposta_over = self.times_para_apostas_over.get(fixture_id)
                                option_odd = self.get_option_odd(fixture['optionMarkets'], aposta_over['option_id'] )
                                if aposta_over and not aposta_over['bet_made']:
                                    print(f'========= {nome_evento}') 
                                    print('actual odd ', option_odd )
                                    print('target odd ', aposta_over['target_odd'] )
                                    if option_odd and periodo.lower() != 'intervalo' and abs( option_odd - aposta_over['target_odd'] ) < 0.5:
                                        is_any_target_odd_close = True                                        
                                if aposta_over and option_odd and not aposta_over['bet_made'] and option_odd >= float( aposta_over['target_odd'] ):
                                    aposta_feita = await self.faz_aposta(nome_evento, aposta_over['option_id'], aposta_over['target_odd'], soma_gols ) 
                                    if aposta_feita:
                                        aposta_over['bet_made'] = True
                                continue                   
                            
                            name = fixture['name']['value']
                            numero_gols_atual = fixture['scoreboard']['score']      
                            placar = fixture['scoreboard']['score']      
                            numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])                                       
                            
                            periodId = fixture['scoreboard']['periodId']
                            is_running = fixture['scoreboard']['timer']['running']
                            cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0

                            # time_1 = fixture['participants'][0]
                            # time_1_nome = time_1['name']['value']
                            # time_1_id = time_1['id']
                            # time_2 = fixture['participants'][1]
                            # time_2_nome = time_2['name']['value']                                                                      
                            # time_2_id = time_2['id']

                            # resultado_partida = list( filter(  lambda el: el['name']['value'].lower() in ['resultado da partida', 'match result'] ,fixture['optionMarkets'] ) )

                            # resultado_partida = resultado_partida[0]
                            # odd_time_1_resultado_partida = float( resultado_partida['options'][0]['price']['odds'] ) 
                            # time_1_resultado_partida_option_id = resultado_partida['options'][0]['id']                               
                            # odd_time_2_resultado_partida = float( resultado_partida['options'][2]['price']['odds'] )   
                            # time_2_resultado_partida_option_id = resultado_partida['options'][2]['id']      

                            # chance_dupla = list( filter(  lambda el: el['name']['value'].lower() in ['chance dupla'] ,fixture['optionMarkets'] ) )

                            # chance_dupla = chance_dupla[0]
                            # odd_time_1_chance_dupla = float( chance_dupla['options'][0]['price']['odds'] )       
                            # time_1_chance_dupla_option_id = chance_dupla['options'][0]['id']                         
                            # odd_time_2_chance_dupla = float( chance_dupla['options'][1]['price']['odds'] )
                            # time_2_chance_dupla_option_id = chance_dupla['options'][1]['id']               
                            aposta_feita = False                            
                            if soma_gols >= 1:
                                tempo_de_gol = floor( cronometro / soma_gols )
                                # print('tempo de gol ', tempo_de_gol)
                                # print('gols ', soma_gols)
                                # print('cronometro ', cronometro)
                                if tempo_de_gol <= 15:                                    
                                    option_markets = fixture['optionMarkets']
                                    for n in range(4, 1, -1):
                                        option_id = self.get_option_id(fixture_id, option_markets, soma_gols+n)
                                        #print(option_id)
                                        if option_id:
                                            option_odd = self.get_option_odd(option_markets, option_id)
                                            if option_odd >= 1.30:
                                                aposta_feita = await self.faz_aposta(nome_evento, option_id, None, soma_gols)                                
                                                if aposta_feita:
                                                    jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                                    bet_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                                    self.bet_ids.append(bet_number)
                                                    self.get_option_id_over(fixture_id, option_markets, f'Mais de {soma_gols+n},5', self.target_odd)                                            
                                                    break
                                        # else:
                                        #     option_id = self.get_option_id(fixture_id, option_markets, soma_gols+(n-1))
                                        #     print(option_id)
                                        #     if option_id:
                                        #         option_odd = self.get_option_odd(option_markets, option_id)
                                        #         if option_odd >= 1.70:
                                        #             aposta_feita = await self.faz_aposta(nome_evento, option_id, None, soma_gols)                                
                                        #             if aposta_feita:
                                        #                 jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                                        #                 bet_number = jogo_aberto['betslips'][0]['betSlipNumber']
                                        #                 self.bet_ids.append(bet_number)
                                        #                 self.get_option_id_over(fixture_id, option_markets, f'Mais de {soma_gols+1},5', self.target_odd)                                            
                                        #                 continue
                                        #         else:
                                        #             print('odd muito baixa. pulando...')


                            # jogo = self.jogos_de_interesse.get(fixture_id)
                            # aposta_feita = False
                            # if jogo != None and not jogo.bet_made:
                            #     if jogo.home_away == HomeAway.Home:                                                                            
                            #         if odd_time_1_chance_dupla >= 1.5 and odd_time_1_chance_dupla < 2:
                            #             aposta_feita = await self.faz_aposta(nome_evento, time_1_chance_dupla_option_id)
                            #         elif odd_time_1_resultado_partida >= 1.5 and odd_time_1_resultado_partida < 2:
                            #             aposta_feita = await self.faz_aposta(nome_evento, time_1_resultado_partida_option_id)
                            #     elif jogo.home_away == HomeAway.Away:                                    
                            #         if odd_time_2_chance_dupla >= 1.5 and odd_time_2_chance_dupla < 2:
                            #             aposta_feita = await self.faz_aposta(nome_evento, time_2_chance_dupla_option_id)
                            #         elif odd_time_2_resultado_partida >= 1.5 and odd_time_2_resultado_partida < 2:
                            #             aposta_feita = await self.faz_aposta(nome_evento, time_2_resultado_partida_option_id)  
                            #     if aposta_feita:
                            #         jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            #         bet_number = jogo_aberto['betslips'][0]['betSlipNumber']
                            #         jogo.bet_made = True
                            #         jogo.bet_number = bet_number
                            #         continue

                            #print(time_1_nome, numero_gols_atual)

                            # if numero_gols_atual != 0 and abs( gols_casa - gols_fora ) > 1 or cronometro > 50:
                            #     continue                                                        

                            # if not is_running:
                            #     continue         
                            
                            
                            # if odd_time_2_chance_dupla >= 4:                                                                
                            #     aposta_feita = await self.faz_aposta(nome_evento, time_2_chance_dupla_option_id)                                
                            # elif odd_time_1_chance_dupla >= 4:
                            #     aposta_feita = await self.faz_aposta(nome_evento, time_1_chance_dupla_option_id)                                
                            # if aposta_feita:
                            #     jogo_aberto = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                            #     bet_number = jogo_aberto['betslips'][0]['betSlipNumber']
                            #     self.bet_ids.append(bet_number)
                            #     self.inserted_fixture_ids.append(fixture_id)                                                              
                        except IndexError as index_error:
                            print(index_error)
                            continue
                        except Exception as e:                                    
                            self.testa_sessao()
                            print(e)

                    with open('times_para_apostas_over.pkl', 'wb') as outp:
                        pickle.dump(self.times_para_apostas_over, outp, pickle.HIGHEST_PROTOCOL )

            except KeyboardInterrupt as e:                
                chrome.sair()
            except Exception as e:                
                deu_erro = True                
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                self.numero_apostas_feitas = 0
                print(e)                
                self.testa_sessao()
                self.tempo_pausa = 1    

            if is_any_target_odd_close:
                print('target odd is close')
                self.tempo_pausa = 30
            else:
                self.tempo_pausa = 2.5 * 60        

            
            
            if not deu_erro:
                print('Esperando...')
                sleep(self.tempo_pausa)                

if __name__ == '__main__':

    try:
        chrome = ChromeAuto(numero_apostas=200, numero_jogos_por_aposta=10)
        chrome.acessa('https://sports.sportingbet.com/pt-br/sports')            
        chrome.faz_login()     
        asyncio.run( chrome.favoritos_para_virar('Mais de 0,5', 2.0, 2.5, 1.00, False, False, 100.0))
    except Exception as e:
        print(e)        
        chrome.sair()
        exit()
    # parâmetros: mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria, qt_jogos_paralelos
    #chrome.altas_odds_empate( None, 6, 10, 1, True, False, None )

    #asyncio.run( chrome.busca_odds_fim_jogo_sem_gol('Mais de 0,5', 2, 2.3, 1.00, False, False, 100.0) )
    #chrome.duas_zebras('Mais de 0,5', 3, 4, 1, True, False, 100.0)
    #chrome.quatro_zebras('Mais de 0,5', 3, 4, 1, True, False, 100.0)