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
import pickle
import asyncio
import concurrent.futures

hora_jogo_atual = None

# & C:/Python39/python.exe c:/Users/anderson.morais/Documents/dev/sportingbet3/app.py 2 5 4 50 1 20 1 2
class ChromeAuto():
    def __init__(self, numero_apostas=50, numero_jogos_por_aposta=10, apenas_acompanhar=False, is_new_game=True):
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
        self.jogos_inseridos = []
        self.varios_jogos = True
        self.is_new_game = is_new_game
        #self.meta_ganho = 0.0
        self.hora_ultima_aposta = ''
        self.jogos = {'jogos_aleatorios0.pkl': dict(), 
                      'jogos_aleatorios1.pkl': dict(), 
                      'jogos_aleatorios2.pkl': dict(), 
                      'jogos_aleatorios3.pkl':dict(),
                      'jogos_aleatorios4.pkl':dict(),
                      'jogos_aleatorios5.pkl':dict(),
                      'jogos_aleatorios6.pkl':dict(),
                      'jogos_aleatorios7.pkl':dict(),
                      'jogos_aleatorios8.pkl':dict(),
                        'jogos_aleatorios9.pkl': dict()  }
        # self.conn = psycopg2.connect( database='sportingbet', user='postgres', host='localhost', password='postgres', port=5432 )

        # self.cur = self.conn.cursor()
        # self.cur.execute('select * from principal;')
        # rows = self.cur.fetchall()
        # self.conn.commit()
        # self.conn.close()
        # for row in rows:
        #     data_base, meta, valor_por_aposta = row
        #     print(data_base)
        #     print(meta)
        #     print(valor_por_aposta)

        return

    def gera_jogos_aleatorios(self, nome_arquivo):

        if not self.is_new_game:
            try:
                with open(f'{nome_arquivo}', 'rb') as fp:
                    self.jogos_aleatorios = pickle.load(fp)
                if len( self.jogos_aleatorios ) == 0:
                    asyncio.run( self.analisa_resultados() )
                return
            except:            
                print('erro ao ler o arquivo')
                exit()

        for jogo in self.jogos_aleatorios:
            print(jogo)

        if len(self.jogos_aleatorios) > 0:
            return

        valor_maximo = 9586.88

        odds1 = [0, 2.3, 3, 2.8]
        odds2 = [0, 2.3, 3, 2.8]
        odds3 = [0, 2.3, 3,1, 2.7]
        odds4 = [0, 2.15,2.85,3.25]
        odds5 = [0, 2.95,2.7,2.37]
        odds6 = [0, 2.05,2.87,3.5]
        odds7 = [0, 2.1,3,3.2]
        odds8 = [0, 2.37,3.2,2.95]

        CASA_FAVORITO = [1,1,1,1,1,2,2,2,3]
        FORA_FAVORITO = [3,3,3,3,3,2,2,2,1]
        j1 = CASA_FAVORITO
        j2 = CASA_FAVORITO
        j3 = CASA_FAVORITO
        j4 = CASA_FAVORITO
        j5 = CASA_FAVORITO
        j6 = CASA_FAVORITO
        j7 = FORA_FAVORITO
        j8 = CASA_FAVORITO
        j9 = CASA_FAVORITO
        j10 = CASA_FAVORITO

        i = 0

        # jogos_ja_gerados = None
        # with open(f'{nome_arquivo}', 'rb') as fp:
        #     jogos_ja_gerados = pickle.load(fp)
        
        while len(self.jogos_aleatorios) < self.numero_apostas:
            
            while True:
                jogo = []
                for _ in range(self.numero_jogos_por_aposta):
                    jogo.append(randint(0,8))

                soma_empates = jogo.count(5) + jogo.count(6) + jogo.count(7)
                soma_zebra = jogo.count(8)

                if soma_empates in (1, 2, 3, 4, 5) and soma_zebra in (1, 2, 3, 4, 5):
                    break

                # valor_total = odds1[j1[jogo[0]]] * odds2[j2[jogo[1]]] *odds3[j3[jogo[2]]] *odds4[j4[jogo[3]]]*odds5[j5[jogo[4]]]*odds6[j6[jogo[5]]]*odds7[j7[jogo[6]]]*odds8[j8[jogo[7]]]

                # if valor_total >= valor_maximo * 0.15 and valor_total <= valor_maximo * 0.45 and soma_empates <= 4:
                #     break

            jogo = f'{j1[jogo[0]]} {j2[jogo[1]]} {j3[jogo[2]]} {j4[jogo[3]]} {j5[jogo[4]]} {j6[jogo[5]]} {j7[jogo[6]]} {j8[jogo[7]]} {j9[jogo[8]] if len(jogo) > 8 else ""} {j10[jogo[9]] if len(jogo) > 9 else ""}'            
            if self.jogos_aleatorios.get(jogo) == None:
                self.jogos_aleatorios[jogo] = True
                self.jogos[f'jogos_aleatorios{i%10}.pkl'][jogo] = True
                i += 1

        for jogo in self.jogos_aleatorios:
            print(jogo)
        
        for i in range(10):
            with open(f'jogos_aleatorios{i}.pkl', 'wb') as fp:
                pickle.dump(self.jogos[f'jogos_aleatorios{i}.pkl'], fp)

    
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
                self.options.add_argument("--force-device-scale-factor=0.5")                                
                self.options.add_argument("--log-level=3") 
                self.options.add_argument("--silent")
                # self.options.add_argument('--disk-cache-size')    
                print('carregando driver...')            
                self.chrome = webdriver.Chrome(options=self.options, service=ChromeService(ChromeDriverManager().install()))                
                print('driver carregado...')            
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

    def clica_sign_in(self):

        sleep(5)
        #vai tentar clicar no banner na tela
        fechou_banner = False
        numero_tentativas = 10
        clicou_login = False
        while not fechou_banner and numero_tentativas > 0:
            try:
                self.chrome.execute_script("var banner = document.querySelector('.theme-ex').click()")
                fechou_banner = True
                print('fechou banner')
                elem = WebDriverWait(self.chrome, 30).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '.theme-ex' )  )) 
                elem.click()
            except Exception as e:
                numero_tentativas -= 1
                print('não fechou banner')
                sleep(2)
                print(e)

        sleep(2)

        try:
            elem = WebDriverWait(self.chrome, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[href="https://www.sportingbet.com/pt-br/labelhost/login"]' )  )) 
            elem.click()
        except Exception as e:
            self.chrome.execute_script("var banner = document.querySelector('.theme-ex').click()")
            print(e)

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
                    print(e)
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

    
    def faz_apostas(self, nome_arquivo):
        self.chrome.get('https://sports.sportingbet.com/pt-br/sports/favoritos/eventos')
        self.chrome.maximize_window()
        self.chrome.fullscreen_window()

        while len( self.jogos_aleatorios ) > 0:
            jogo_aleatorio, valor = self.jogos_aleatorios.popitem()

            print(f'Gerando jogo {jogo_aleatorio}...')
            jogo_atual = 1
            for j in jogo_aleatorio.split():
                clicou = False                
                while not clicou:
                    try:
                        jogo = WebDriverWait(self.chrome, 20).until(
                                EC.element_to_be_clickable((By.XPATH, f'/html/body/vn-app/vn-dynamic-layout-slot[5]/vn-main/main/div/ms-main/div[1]/ng-scrollbar/div/div/div/div/ms-main-column/div/ms-favourites-dashboard/div[2]/div/ms-grid/div/ms-event-group/ms-event[{jogo_atual}]/div/div/ms-option-group[1]/ms-option[{j}]/ms-event-pick' ) ))                                   
                                                                        
                        jogo.click() 
                        clicou = True   
                        jogo_atual += 1
                        sleep(0.1)
                    except Exception as e:
                        self.is_new_game = False
                        self.chrome.quit()
                        self.acessa('https://sports.sportingbet.com/pt-br/sports')           
                        self.faz_login()  
                        self.gera_jogos_aleatorios(nome_arquivo)   
                        self.faz_apostas(nome_arquivo) 

            fez_aposta = False
            while not fez_aposta:
                try:    
                    self.insere_valor_2()    
                    fez_aposta = True
                except:
                    self.is_new_game = False
                    self.chrome.quit()
                    self.acessa('https://sports.sportingbet.com/pt-br/sports')           
                    self.faz_login()  
                    self.gera_jogos_aleatorios(nome_arquivo)   
                    self.faz_apostas(nome_arquivo)                    

            with open(nome_arquivo, 'wb') as fp:
                pickle.dump(self.jogos_aleatorios, fp)


    def filtro(self, elemento):
        return elemento['scoreboard']['score'] == '0:0'

    def busca_odds_acima_meio_gol(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        times_favoritos = []
        self.varios_jogos = varios_jogos

        while True:
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:

                if self.varios_jogos:
                    conn = self.get_bd_connection()             
                    cur = conn.cursor()

                    data_de_hoje = date.today()

                    cur.execute(f"select * from principal where data_base = '{data_de_hoje}'")
                    rows = cur.fetchall()
                    if len(rows) == 0:
                        cur.execute(f"insert into principal values ('{data_de_hoje}', {self.saldo:.2f}, 1)")
                    else:
                        lixo, valor_banca, lixo2 = rows[0]
                        if self.saldo > float(valor_banca):
                            cur.execute(f"update principal set valor_banca = {self.saldo:.2f} where data_base = '{data_de_hoje}'")
                            self.telegram_bot_erro.envia_mensagem(f'AUMENTO DE SALDO: {self.saldo:.2f}')
                    conn.commit()
                    conn.close()

                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['openBetsCount'] >= 1 and not self.varios_jogos:
                #if False:
                    print('Há apostas em aberto...')
                    print(datetime.now())
                    self.tempo_pausa = 2.5 * 60
                else:
                    try:             
                        self.le_saldo()           

                        if not self.varios_jogos:
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                            
                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = ultimo_jogo['betslips'][0]

                            if ultimo_jogo['state'] == 'Lost':                            
                                self.valor_aposta = float( ultimo_jogo['stake']['value']) * float( ultimo_jogo['totalOdds']['european'] ) + 0.01
                                ''' A LINHA DE BAIXO É PRA NÃO USAR MARTINGALE '''
                                #self.valor_aposta = 2
                                if self.primeiro_alerta_depois_do_jogo:
                                    print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                                    # try:
                                    #     #self.telegram_bot.envia_mensagem('PERDEU.')
                                    # except Exception as e:
                                    #     print(e)
                                    self.primeiro_alerta_depois_do_jogo = False
                            elif ultimo_jogo['state'] == 'Canceled':
                                self.valor_aposta = float( ultimo_jogo['stake']['value']) * ( float( ultimo_jogo['totalOdds']['european'] ) - 1.0 ) + 0.01
                                ''' A LINHA DE BAIXO É PRA NÃO USAR MARTINGALE '''
                                #self.valor_aposta = 2
                                if self.primeiro_alerta_depois_do_jogo:
                                    print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                                    # try:
                                    #     #self.telegram_bot.envia_mensagem('ÚLTIMA APOSTA CANCELADA.')
                                    # except Exception as e:
                                    #     print(e)
                                    self.primeiro_alerta_depois_do_jogo = False
                            else:
                                if self.primeiro_alerta_depois_do_jogo:
                                    # try:
                                    #     #self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                    # except Exception as e:
                                    #     print(e)
                                    #     print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                    self.primeiro_alerta_depois_do_jogo = False                                    
                                # aqui o saldo deve ser maior do que depois da aposta, do contrário não estamos pegando o valor correto
                                contador = 0
                                while self.saldo < self.saldo_antes_aposta:
                                    self.le_saldo()
                                    contador += 1
                                    if contador == 10:
                                        self.telegram_bot_erro.envia_mensagem('SALDO DESATUALIZADO APÓS APOSTA GANHA')
                                        self.chrome.quit()
                                        exit()

                                try:

                                    conn = self.get_bd_connection()             
                                    cur = conn.cursor()

                                    data_de_hoje = date.today()

                                    cur.execute(f"select * from principal where data_base = '{data_de_hoje}'")
                                    rows = cur.fetchall()
                                    if len(rows) == 0:
                                        cur.execute(f"insert into principal values ('{data_de_hoje}', {self.saldo:.2f}, null)")
                                        #data_de_ontem = date.today() - timedelta(days=1)
                                        #cur.execute(f"select banca from principal where data_base = '{data_de_ontem}'")
                                        #banca_ontem = cur.fetchall()
                                        #banca_ontem = float(banca_ontem[0][0])
                                        #ganho_dia = self.saldo - banca_ontem
                                        #mes_atual = int( date.today().strftime('%m'))
                                        #ano_atual = int( date.today().strftime('%Y'))
                                        #ultimo_dia_mes_passado = date( ano_atual, mes_atual, 1 ) - timedelta(days=1)
                                        #cur.execute(f"select banca from principal where data_base = '{ultimo_dia_mes_passado}'")
                                        #banca_ultimo_dia_mes_passado = cur.fetchall()
                                        #banca_ultimo_dia_mes_passado = float( banca_ultimo_dia_mes_passado[0][0])
                                        #ganho_mes = self.saldo - banca_ultimo_dia_mes_passado
                                        #self.telegram_bot.envia_mensagem(f'GANHO DO DIA: R$ {ganho_dia:.2f}\nGANHO DO MÊS: R$ {ganho_mes:.2f}')
                                    else:
                                        ganho_do_dia = self.saldo - float( rows[0][1] )
                                        if ganho_do_dia >= meta_diaria:
                                            self.telegram_bot_erro.envia_mensagem(f'GANHO DO DIA: R$ {ganho_do_dia:.2f}')
                                            self.chrome.quit()
                                            exit(0)
                                    conn.commit()
                                    conn.close()
                                except Exception as e:
                                    print(e)

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                self.valor_aposta = self.saldo * 0.00538
                                # try:
                                #     conn = self.get_bd_connection()
                                #     cur = conn.cursor()

                                #     cur.execute(f"update meta_ganho set valor = ({self.valor_aposta:.2f})")
                                #     conn.commit()
                                #     conn.close()
                                # except Exception as e:
                                #     print('erro ao conectar ao banco')
                                #     print(e)
                                # self.meta_ganho = self.valor_aposta
                                # durante a semana o valor da aposta vai ser sempre o mesmo para fins de teste
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                        
                        if teste:
                            self.valor_aposta = valor_aposta
                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

                        jogos_futuros = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=None&skip=0&take=100&sortBy=StartDate&from={date.today()}T{( datetime.today() + timedelta(hours=3)).strftime("%H:%M:%S")}.000Z&to={( datetime.today() + timedelta(hours=9)).strftime("%H:%M:%S")}.000Z"); return await d.json();')   
                                    

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:

                            # for proximo_jogo in jogos_futuros['fixtures']:
                            #     try:
                            #         fixtures['fixtures'].append(proximo_jogo)
                            #     except Exception as e:
                            #         print(e)


                            self.tempo_pausa = 2.5 * 60
                            for fixture in fixtures['fixtures']:
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                                nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:     
                                    #print(option_market['name']['value'])                    
                                    if option_market['name']['value'] == '1º Tempo - Total de Gols' or option_market['name']['value'] == '2º Tempo - Total de Gols':
                                        #print(option_market['name']['value'])
                                        for option in option_market['options']:
                                            if option['name']['value'] == mercado:
                                                # print(float(fixture['scoreboard']['timer']['seconds']) / 60.0)
                                                # print(option['name']['value'])
                                                # print(float(option['price']['odds']))
                                                confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                odd = float(option['price']['odds'])
                                                primeiro_ou_segundo_tempo = ''
                                                if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                    primeiro_ou_segundo_tempo = '1T'
                                                else:
                                                    primeiro_ou_segundo_tempo = '2T'

                                                cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                                id = fixture['id']
                                                # if odd >= 1.18 and odd < 1.42:
                                                #     odds_3.append(f'{odd} {confronto}')
                                                # elif odd >= 1.42 and odd < 1.6:
                                                #     odds_2.append(f'{odd} {confronto}')

                                                if odd >= limite_inferior and odd <= limite_superior and fixture['scoreboard']['score'] == '0:0' and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                    jogos_aptos.append({ 'nome_evento': nome_evento, 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo })
                                                    print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')                                                

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], el['cronometro'], el['odd']  ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            print(jogos_aptos_ordenado)

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:
                                    # self.telegram_bot.envia_mensagem('SEM JOGOS ELEGÍVEIS')
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                sleep(self.tempo_pausa)
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

                                if self.varios_jogos:
                                    self.valor_aposta = valor_aposta

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if jogo_apto['time'] in jogos_ja_inseridos:
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

                                    # try:
                                    #     aba_procurar = WebDriverWait(self.chrome, 10).until(
                                    #         EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Procurar']/ancestor::a")))
                                    #     aba_procurar.click()
                                    # except Exception as e:
                                    #     deu_erro = True
                                    #     self.numero_erros_global += 1
                                    #     raise e
                                       
                                    # try:
                                    #     input_busca = WebDriverWait(self.chrome, 10).until(
                                    #         EC.presence_of_element_located((By.NAME, "searchField") ))                                                                                
                                    #     input_busca.clear()
                                    #     input_busca.send_keys(jogo_apto['time'])
                                    # except Exception as e:
                                    #     deu_erro = True
                                    #     self.numero_erros_global += 1
                                    #     raise e

                                    # try:
                                    #     actions = ActionChains(self.chrome)
                                    #     actions.send_keys(Keys.ENTER )
                                    #     actions.perform()
                                    
                                    #     jogo_clicavel = WebDriverWait(self.chrome, 10).until(
                                    #         EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='modal-content'] a[class='grid-info-wrapper fixed']")))
                                    #     self.chrome.get( jogo_clicavel.get_property('href') + '?market=2' )
                                    # except Exception as e:
                                    #     deu_erro = True
                                    #     self.numero_erros_global += 1
                                    #     raise e
                                        #raise ErroDeNavegacao
                                    try: 
                                        self.chrome.get( 'https://sports.sportingbet.com/pt-br/sports/eventos/' + jogo_apto['nome_evento'] + '?market=2')
                                        self.chrome.maximize_window()
                                        self.chrome.fullscreen_window()
                                    except Exception as e:
                                        print('erro ao navegar pro jogo')
                                        raise e

                                    # quer dizer que o mercado de gols é no primeiro tempo
                                    try:
                                        if jogo_apto['tempo'] == '1T':
                                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º T']/ancestor::a")))                                                    
                                            mercado_1_tempo.click()
                                        else:
                                            mercado_2_tempo = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '2º T']/ancestor::a")))                                                    
                                            mercado_2_tempo.click()
                                    except Exception as e:
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise e
                                        #raise ErroDeNavegacao

                                    # mais_1_meio = WebDriverWait(self.chrome, 10).until(
                                    #     EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 1,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                    # mais_1_meio.click()  

                                    # vamos verificar se a odd está dentro dos limites ou se estamos clicando em outro local
                                    try:
                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.XPATH, f"//*[normalize-space(text()) = '{mercado}']/following-sibling::div") )) 
                                        mais_meio_odd = float(mais_meio.get_property('innerText'))
                                        print(mais_meio_odd)

                                        if mais_meio_odd < limite_inferior and mais_meio_odd > limite_superior:
                                            raise Exception('ODD FORA DO INTERVALO. SELEÇÃO DE MERCADO INCORRETO.')

                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{mercado}']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                        mais_meio.click()
                                    except Exception as e:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        print(e)
                                        raise Exception

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

                                        self.valor_aposta = ( self.valor_aposta / ( cota - 1 ) ) + 0.01

                                        # if self.valor_aposta > 10:
                                        #     self.valor_aposta = valor_aposta_original / ( cota - 1 )

                                        self.insere_valor(f"{jogo_apto['id']}{jogo_apto['tempo']}")

                                except Exception as e:
                                    # self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    # self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")
                                    print('Algo deu errado')  
                                    #quando limpar as apostas o número de apostas feitas vai pra zero
                                    # numero_apostas_feitas = 0
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://sports.sportingbet.com/pt-br/sports')

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


                                if self.valor_aposta > self.saldo:
                                    try:
                                        self.telegram_bot_erro.envia_mensagem('MIOU')
                                        self.chrome.quit()
                                        exit()
                                    except:
                                        print('Não foi possível enviar mensagem ao telegram.')

                                self.insere_valor(f"{jogo_apto['id']}{jogo_apto['tempo']}")
                                ## print(mensagem_telegram)
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
                        sleep(10)
                        print(e)
                    except Exception as e:
                        print(e)
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            self.numero_apostas_feitas = 0
                            self.testa_sessao()
                            sleep(10)
                        pass
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
                sleep(10)
            except Exception as e:
                print(e)
                self.testa_sessao()
                sleep(10)

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

    def busca_odds_acima_meio_gol_sem_login(self, mercado, limite_inferior, limite_superior ):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        jogos_ja_inseridos = []

        while True:

            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []

            # primeiro verificamos se não há nenhum jogo em aberto              
            fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

            #jogos_futuros = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&statisticsModes=None&skip=0&take=100&sortBy=StartDate&from={date.today()}T{( datetime.today() + timedelta(hours=3)).strftime("%H:%M:%S")}.000Z&to={( datetime.today() + timedelta(hours=9)).strftime("%H:%M:%S")}.000Z"); return await d.json();')   
                        

            if len( fixtures['fixtures'] ) == 0:
                print('Sem jogos ao vivo...')
                print(datetime.now())
                self.tempo_pausa = 10 * 60
            else:
                self.tempo_pausa = 2.5 * 60
                for fixture in fixtures['fixtures']:
                    #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                    option_markets = fixture['optionMarkets']
                    for option_market in option_markets:     
                        #print(option_market['name']['value'])                    
                        if option_market['name']['value'] == '1º Tempo - Total de Gols' or option_market['name']['value'] == '2º Tempo - Total de Gols':
                            #print(option_market['name']['value'])
                            for option in option_market['options']:
                                if option['name']['value'] == mercado:
                                    # print(float(fixture['scoreboard']['timer']['seconds']) / 60.0)
                                    # print(option['name']['value'])
                                    # print(float(option['price']['odds']))
                                    confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                    odd = float(option['price']['odds'])
                                    primeiro_ou_segundo_tempo = ''
                                    if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                        primeiro_ou_segundo_tempo = '1T'
                                    else:
                                        primeiro_ou_segundo_tempo = '2T'

                                    cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                    hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                    id = fixture['id']
                                    # if odd >= 1.18 and odd < 1.42:
                                    #     odds_3.append(f'{odd} {confronto}')
                                    # elif odd >= 1.42 and odd < 1.6:
                                    #     odds_2.append(f'{odd} {confronto}')

                                    if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                        if f"{fixture['participants'][0]['name']['value']}{primeiro_ou_segundo_tempo}" not in jogos_ja_inseridos:
                                            jogos_ja_inseridos.append( f"{fixture['participants'][0]['name']['value']}{primeiro_ou_segundo_tempo}" )
                                            jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo })
                                            print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                                            odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')                                                

                for combinacao in array_mensagem_telegram:
                    mensagem_telegram += combinacao['texto']             

                jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], el['cronometro'], el['odd']  ) )
                # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                if len(jogos_aptos_ordenado) == 0:
                    print('SEM JOGOS ELEGÍVEIS')
                    sleep(self.tempo_pausa)
                else:
                    jogos_enviados = 0
                    for jogo in jogos_aptos_ordenado:
                        self.telegram_bot.envia_mensagem(jogo['time'])   
                        jogos_enviados += 1
                        if jogos_enviados >= 5:
                            break
                    self.chrome.quit()
                    exit(0)

                    sleep(self.tempo_pausa)              
                        

                          


    def quantidade_apostas_feitas(self):
        jogos_feitos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=20&typeFilter=2"); return await d.json();')
        jogos_perdidos = 0
        for jogo_feito in jogos_feitos['betslips']:
            if jogo_feito['state'] == 'Lost':
                jogos_perdidos += 1
            elif jogo_feito['state'] == 'Won':
                break
        return jogos_perdidos
            

    def busca_jogos_perto_de_acabar(self):
        self.tempo_pausa = 1.0 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        times_favoritos = []
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])

        

        while True:
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600 * 2:
                try:
                    self.telegram_bot.envia_mensagem('SISTEMA RODANDO.')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:
                # fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           
                
                # fixtures_filtradas = filter( self.filtro, fixtures['fixtures'] )

                # for fixture in fixtures_filtradas:
                #     option_markets = fixture['optionMarkets']
                #     for option_market in option_markets:                         
                #         if option_market['name']['value'] == 'Resultado da Partida':
                #             nome_time_1 = option_market['options'][0]['name']['value']
                #             odd_time_1 = option_market['options'][0]['price']['odds']
                #             nome_time_2 = option_market['options'][2]['name']['value']
                #             odd_time_2 = option_market['options'][2]['price']['odds']
                #             if not nome_time_1 in times_favoritos: 
                #                 if odd_time_1 < 1.5:
                #                     times_favoritos.append(nome_time_1)
                #             else:
                #                 if odd_time_1 >= 2:
                #                     self.telegram_bot_erro.envia_mensagem(nome_time_1)

                #             if not nome_time_2 in times_favoritos: 
                #                 if odd_time_2 < 1.5:
                #                     times_favoritos.append(nome_time_2)
                #             else:
                #                 if odd_time_2 >= 2:
                #                     self.telegram_bot_erro.envia_mensagem(nome_time_2)

                # print(times_favoritos)

                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if False:
                    print('Há apostas em aberto...')
                    print(datetime.now())
                    self.tempo_pausa = 1.0 * 60
                else:
                    try:
                        # primeiro verificamos se a última aposta foi vitoriosa                    
                        ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                        
                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = ultimo_jogo['betslips'][0]

                        self.le_saldo()

                        if ultimo_jogo['state'] == 'Lost':                            
                            self.valor_aposta = float( ultimo_jogo['stake']['value']) * float( ultimo_jogo['totalOdds']['european'] ) + 0.01
                            ''' A LINHA DE BAIXO É PRA NÃO USAR MARTINGALE '''
                            #self.valor_aposta = 2
                            print(f'META DE GANHO: R$ {self.valor_aposta:.2f}\nESTIMATIVA DE APOSTA: R$ {(self.valor_aposta/4.0):.2f}')
                        else:
                            if self.primeiro_alerta_depois_do_jogo:
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                self.primeiro_alerta_depois_do_jogo = False
                            
                            self.valor_aposta = 10
                            print(f'META DE GANHO: R$ {self.valor_aposta:.2f}\nESTIMATIVA DE APOSTA: R$ {(self.valor_aposta/4.0):.2f}')

                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid=MjcxNjZlZTktOGZkNS00NWJjLTkzYzgtODNkNThkNzZhZDg2&lang=pt-br&country=BR&userCountry=BR&state=Live&take=100&offerMapping=Filtered&sortBy=StartDate&sportIds=4&statisticsModes=None"); return await d.json();')    
                                                                                    
       

                        print()

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 1.0 * 60
                            for fixture in fixtures['fixtures']:
                                #print(fixture['scoreboard']['period'])
                                cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60
                                #print( cronometro )
                                if fixture['scoreboard']['period'] == '1º T' and cronometro >= 35 and cronometro < 45:
                                    #print(fixture['scoreboard']['period'])
                                #     # se for no primemiro tempo, temos que ver se o jogo tem o mercaod de total de gols no primeiro tempo
                                    option_markets = fixture['optionMarkets']
                                    #print(option_markets)

                                    array_odds = []
                                    for option_market in option_markets:                                                                 
                                        
                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                            #print(option_market['name']['value'])
                                            for option in option_market['options']:
                                                if 'mais' in option['name']['value'].lower():                                                    
                                                    #print(option['name']['value'])
                                                    #print(option['price']['odds'] )
                                                    array_odds.append(float(option['price']['odds']))
                                                    
                                            array_odds = sorted(array_odds)
                                            #print(array_odds)

                                            if array_odds[0] >= 3.5:
                                                jogo = { 'time': fixture['participants'][0]['name']['value'], 'cronometro': int(fixture['scoreboard']['timer']['seconds']) // 60 }
                                                if jogo not in jogos_aptos:
                                                    jogos_aptos.append(jogo)
                                elif fixture['scoreboard']['period'] == '2º T' and cronometro >= 80 and cronometro < 90:
                                    #print(fixture['scoreboard']['period'])
                                    
                                    option_markets = fixture['optionMarkets']
                                    
                                    array_odds = []

                                    for option_market in option_markets:                         
                                        if option_market['name']['value'].lower() == 'total de gols':                                           #print(option_market['name']['value'])
                                            
                                            for option in option_market['options']:
                                                if 'mais' in option['name']['value'].lower():                                                    
                                                    #print(option['name']['value'])
                                                    #print(option['price']['odds'] )
                                                    array_odds.append(float(option['price']['odds']))
                                                    
                                            array_odds = sorted(array_odds)
                                            #print(array_odds)

                                            if array_odds[0] >= 3.5:
                                                jogo = { 'time': fixture['participants'][0]['name']['value'], 'cronometro': int(fixture['scoreboard']['timer']['seconds']) // 60 }
                                                if jogo not in jogos_aptos:
                                                    jogos_aptos.append(jogo)
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                            #     option_markets = fixture['optionMarkets']
                            #     for option_market in option_markets:                         
                            #         if option_market['name']['value'] == '1º Tempo - Total de Gols':
                            #             #print(option_market['name']['value'])
                            #             for option in option_market['options']:
                            #                 if option['name']['value'] == 'Mais de 0,5':
                            #                     confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                            #                     odd = float(option['price']['odds'])
                            #                     primeiro_ou_segundo_tempo = ''
                            #                     if option_market['name']['value'] == '1º Tempo - Total de Gols':
                            #                         primeiro_ou_segundo_tempo = '1T'
                            #                     else:
                            #                         primeiro_ou_segundo_tempo = '2T'

                            #                     cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60
                            #                     # if odd >= 1.18 and odd < 1.42:
                            #                     #     odds_3.append(f'{odd} {confronto}')
                            #                     # elif odd >= 1.42 and odd < 1.6:
                            #                     #     odds_2.append(f'{odd} {confronto}')

                            #                     if primeiro_ou_segundo_tempo == '1T' and odd >= 1.5 and odd <= 1.6:
                            #                         jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 1, 'prioridade': 0 })
                            #                         print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                            #                         odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')
                            #                     elif primeiro_ou_segundo_tempo == '2T' and odd >= 1.5 and odd <= 1.6:
                            #                         prioridade = 1
                            #                         if fixture['scoreboard']['period'] == '2º T' or fixture['scoreboard']['period'] == 'Intervalo':
                            #                             prioridade = 0
                            #                         jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 2, 'prioridade': prioridade })
                            #                         print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                            #                         odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')


                            # for combinacao in array_mensagem_telegram:
                            #     mensagem_telegram += combinacao['texto']

                            # # o laço vai sair quando já tiverem dois jogos na combinação      
                            # numero_apostas_feitas = 0                      

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: -el['cronometro'] )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) == 0:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                print(datetime.now())
                                sleep(self.tempo_pausa)
                                continue
                            else:
                                #self.telegram_bot.envia_mensagem(f'{self.valor_aposta:.2f}')

                                for jogo in jogos_aptos_ordenado:
                                    print(f"{jogo['time']} {jogo['cronometro']}")
                                    #self.telegram_bot.envia_mensagem(f"{jogo['time']} {jogo['cronometro']}")
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(10)
                        print(e)
                    except Exception as e:
                        print(e)
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            numero_apostas_feitas = 0
                            self.testa_sessao()
                            sleep(10)
                        pass
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.testa_sessao()
                sleep(10)
            except Exception as e:
                print(e)
                self.testa_sessao()
                sleep(10)

    def busca_odds_abaixo_1_20(self):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        times_favoritos = []
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])

        

        while True:
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600 * 2:
                try:
                    self.telegram_bot.envia_mensagem('SISTEMA RODANDO.')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:
                # fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           
                
                # fixtures_filtradas = filter( self.filtro, fixtures['fixtures'] )

                # for fixture in fixtures_filtradas:
                #     option_markets = fixture['optionMarkets']
                #     for option_market in option_markets:                         
                #         if option_market['name']['value'] == 'Resultado da Partida':
                #             nome_time_1 = option_market['options'][0]['name']['value']
                #             odd_time_1 = option_market['options'][0]['price']['odds']
                #             nome_time_2 = option_market['options'][2]['name']['value']
                #             odd_time_2 = option_market['options'][2]['price']['odds']
                #             if not nome_time_1 in times_favoritos: 
                #                 if odd_time_1 < 1.5:
                #                     times_favoritos.append(nome_time_1)
                #             else:
                #                 if odd_time_1 >= 2:
                #                     self.telegram_bot_erro.envia_mensagem(nome_time_1)

                #             if not nome_time_2 in times_favoritos: 
                #                 if odd_time_2 < 1.5:
                #                     times_favoritos.append(nome_time_2)
                #             else:
                #                 if odd_time_2 >= 2:
                #                     self.telegram_bot_erro.envia_mensagem(nome_time_2)

                # print(times_favoritos)

                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['openBetsCount'] >= 1:
                    print('Há apostas em aberto...')
                    print(datetime.now())
                    self.tempo_pausa = 2.5 * 60
                else:
                    try:
                        # primeiro verificamos se a última aposta foi vitoriosa                    
                        ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                        
                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = ultimo_jogo['betslips'][0]

                        self.le_saldo()

                        if ultimo_jogo['state'] == 'Lost':                            
                            self.valor_aposta = float( ultimo_jogo['stake']['value']) * float( ultimo_jogo['totalOdds']['european'] ) + 0.01
                            if self.primeiro_alerta_depois_do_jogo:
                                print(f'VALOR DA APOSTA: R$ {self.valor_aposta:.2f}')
                                self.primeiro_alerta_depois_do_jogo = False
                        else:
                            if self.primeiro_alerta_depois_do_jogo:
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                self.primeiro_alerta_depois_do_jogo = False
                            
                            self.valor_aposta = 5
                            print(f'VALOR DA APOSTA: R$ {self.valor_aposta:.2f}')

                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

                        print()

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2.5 * 60
                            times_sem_repeticao = set()
                            for fixture in fixtures['fixtures']:
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:                         
                                    #print(option_market['name']['value'])
                                    for option in option_market['options']:
                                        odd = float(option['price']['odds'] )
                                        mercado = option_market['name']['value']
                                        opcao_mercado =  option['name']['value']
                                        cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60

                                        t = re.compile(r'\d{2}:\d{2}')

                                        if odd < 1.55 and odd >= 1.45 and len( t.findall(mercado) ) > 0:
                                            jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],
                                                                'odd': odd, 'mercado': mercado, 'opcao': opcao_mercado, 'cronometro': cronometro })
                                            times_sem_repeticao.add(fixture['participants'][0]['name']['value'])

               
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            jogos_aptos = sorted(jogos_aptos, key=lambda el: ( -el['cronometro'], el['odd'] ) )                                

                            if len(times_sem_repeticao) >= 3:
                                self.telegram_bot.envia_mensagem('JOGOS APTOS')
                            else:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                print(datetime.now())
                                sleep(self.tempo_pausa)
                                continue

                            for jogo_apto in jogos_aptos:
                                print(f"{jogo_apto['time']} {jogo_apto['odd']} {jogo_apto['mercado']} {jogo_apto['opcao']} {jogo_apto['cronometro']}")
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(10)
                        print(e)
                    except Exception as e:
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            numero_apostas_feitas = 0
                            self.chrome.quit()
                            self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                            self.faz_login()
                            sleep(10)
                        pass
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                self.faz_login()
                sleep(10)
            except Exception as e:
                print(e)
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                self.faz_login()
                sleep(10)


    def busca_odds_acima_meio_gol_jogo_unico(self):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        self.valor_aposta = 2
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])        

        while True:
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600 * 2:
                try:
                    self.telegram_bot.envia_mensagem('SISTEMA RODANDO.')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                    sleep(30)
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:

                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['liveBetsCount'] >= 1:
                    print('Há apostas em aberto...')
                    print(datetime.now())
                    self.tempo_pausa = 2.5 * 60
                else:
                    try:
                        # primeiro verificamos se a última aposta foi vitoriosa                    
                        ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                        
                        self.le_saldo()

                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = ultimo_jogo['betslips'][0]
                        if ultimo_jogo['state'] == 'Lost':                            

                            # if float( ultimo_jogo['stake']['value']) == 50:
                            #     self.valor_aposta = 150
                            # else:
                            self.valor_aposta = 2
                            if self.primeiro_alerta_depois_do_jogo:                               
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'PERDEU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                    sleep(30)
                                self.primeiro_alerta_depois_do_jogo = False
                            
                        else:
                            if self.primeiro_alerta_depois_do_jogo:                               
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                    sleep(30)
                                self.primeiro_alerta_depois_do_jogo = False

                                #aqui se o saldo for maior ou igual a 1100, vamos sacar o que tiver passando de 1000
                                # if self.saldo >= 1100:
                                #     resto = self.saldo % 1000
                                #     try:
                                #         self.chrome.get('https://cashier.sportingbet.com/cashier/withdrawal')

                                #     except:
                                #         print('NÃO FOI POSSÍVEL SOLICITAR O SAQUE')
                                    

                            self.valor_aposta = 2
                            print(f'VALOR DA APOSTA: R$ {self.valor_aposta:.2f}')

                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

                        print()

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2.5 * 60
                            for fixture in fixtures['fixtures']:
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:               

                                    if option_market['name']['value'] == 'Total de gols':
                                        for option in option_market['options']:   
                                            odd = float(option['price']['odds'])
                                            if odd >= 2 and odd <= 2.5 and 'Mais' in option['name']['value']:
                                                print(option['name']['value'], option['price']['odds'])

                                    if option_market['name']['value'] == '1º Tempo - Total de Gols' or option_market['name']['value'] == '2º Tempo - Total de Gols':
                                        #print(option_market['name']['value']
                                        for option in option_market['options']:                                            

                                            if option['name']['value'] == 'Mais de 0,5':
                                                confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                odd = float(option['price']['odds'])
                                                primeiro_ou_segundo_tempo = ''
                                                if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                    primeiro_ou_segundo_tempo = '1T'
                                                else:
                                                    primeiro_ou_segundo_tempo = '2T'

                                                cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60
                                                # if odd >= 1.18 and odd < 1.42:
                                                #     odds_3.append(f'{odd} {confronto}')
                                                # elif odd >= 1.42 and odd < 1.6:
                                                #     odds_2.append(f'{odd} {confronto}')

                                                if primeiro_ou_segundo_tempo == '1T' and odd >= 1.42 and odd <= 1.8:
                                                    # and fixture['scoreboard']['score'] == '0:0'
                                                    jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 1, 'prioridade': 0 })
                                                    print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')
                                                elif primeiro_ou_segundo_tempo == '2T' and odd >= 1.42 and odd <= 1.8:
                                                    prioridade = 1
                                                    if fixture['scoreboard']['period'] == '2º T' or fixture['scoreboard']['period'] == 'Intervalo':
                                                        prioridade = 0
                                                    jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 2, 'prioridade': prioridade })
                                                    print(f'{odd} {confronto} {primeiro_ou_segundo_tempo}')
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')


                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']

                            # o laço vai sair quando já tiverem dois jogos na combinação      
                            numero_apostas_feitas = 0                      

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], el['prioridade'], el['odd'] ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 2:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                print(datetime.now())
                                sleep(self.tempo_pausa)
                                continue

                            for jogo_apto in jogos_aptos_ordenado:

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if jogo_apto['time'] in jogos_ja_inseridos:
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca
                                    try:
                                        aba_procurar = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Procurar']/ancestor::a")))
                                        aba_procurar.click()
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception
                                       
                                    try:
                                        input_busca = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.NAME, "searchField") ))                                                                                
                                        input_busca.clear()
                                        input_busca.send_keys(jogo_apto['time'])
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception

                                    try:
                                        actions = ActionChains(self.chrome)
                                        actions.send_keys(Keys.ENTER)
                                        actions.perform()
                                    
                                        jogo_clicavel = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='modal-content'] a[class='grid-info-wrapper fixed']")))
                                        self.chrome.get( jogo_clicavel.get_property('href') + '?market=2' )
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception
                                        #raise ErroDeNavegacao

                                    # quer dizer que o mercado de gols é no primeiro tempo
                                    try:
                                        if jogo_apto['tempo'] == 1:
                                            mercado = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º T']/ancestor::a")))                                                    
                                            mercado.click()
                                        else:              
                                            mercado = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '2º T']/ancestor::a")))                                                    
                                            mercado.click()
                                    except:
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise Exception
                                        #raise ErroDeNavegacao

                                    # mais_1_meio = WebDriverWait(self.chrome, 10).until(
                                    #     EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 1,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                    # mais_1_meio.click()  

                                    # vamos verificar se a odd está dentro dos limites ou se estamos clicando em outro local
                                    try:
                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Mais de 0,5']/following-sibling::div") )) 
                                        mais_meio_odd = float(mais_meio.get_property('innerText'))

                                        if mais_meio_odd < 1.42 or mais_meio_odd > 1.8:
                                            raise Exception('ODD FORA DO INTERVALO. SELEÇÃO DE MERCADO INCORRETO.')

                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 0,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                        mais_meio.click()
                                    except Exception as e:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        print(e)
                                        raise Exception

                                    sleep(1)    

                                    numero_apostas_feitas += 1     
                                    jogos_ja_inseridos.append(jogo_apto['time'])                              

                                    if numero_apostas_feitas == 2:
                                        break                                 
                                except Exception as e:
                                    # self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    # self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")
                                    print('Algo deu errado')  
                                    #quando limpar as apostas o número de apostas feitas vai pra zero
                                    # numero_apostas_feitas = 0
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://www.sportingbet.com')

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                        self.chrome.quit()
                                        numero_apostas_feitas = 0
                                        self.chrome.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                                        self.chrome.clica_sign_in()
                                        self.chrome.faz_login() 
                                        sleep(10)

                                    sleep(5)                       

                            if numero_apostas_feitas == 2:                            
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                try: 
                                    cota = float( cota.get_property('innerText') )
                                except Exception as e:
                                    print('cota fechada para o jogo')
                                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                    print(e)

                                if type(cota) != float and ( cota < 2 or cota > 3.24 ):
                                    raise ErroCotaForaIntervalo

                                self.insere_valor_jogo_unico()
                                
                                ## self.telegram_bot_erro.envia_mensagem(mensagem_telegram)
                                ## print(mensagem_telegram)
                            else:
                                print(datetime.now())
                        
                        print()
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(10)
                        print(e)
                    except Exception as e:
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            numero_apostas_feitas = 0
                            self.chrome.quit()
                            self.chrome.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                            self.chrome.clica_sign_in()
                            self.chrome.faz_login() 
                            sleep(10)
                        print(e)
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                self.telegram_bot_erro.envia_mensagem('KEYERROR')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.chrome.quit()
                self.chrome.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                self.chrome.clica_sign_in()
                self.chrome.faz_login() 
                sleep(10)
            except Exception as e:
                print(e)
                self.chrome.quit()
                self.chrome.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                self.chrome.clica_sign_in()
                self.chrome.faz_login() 
                sleep(10)

    
    def busca_odds_acima_gol_jogo_inteiro(self):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        self.valor_aposta = 2
        nome_time_aposta = None
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])        

        while True:          
            jogos_aptos = []
            jogos_ja_inseridos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600 * 2:
                try:
                    self.telegram_bot.envia_mensagem('SISTEMA RODANDO.')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                    sleep(30)
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except:
                print('Erro ao tentar fechar banner')
                self.numero_erros_global += 1

            # primeiro verificamos se não há nenhum jogo em aberto
            try:

                jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                if jogos_abertos['summary']['liveBetsCount'] >= 1:
                    print('Há apostas em aberto...')
                    print(datetime.now())
                    self.tempo_pausa = 5 * 60
                else:
                    try:
                        # primeiro verificamos se a última aposta foi vitoriosa                    
                        ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                        
                        self.le_saldo()

                        # só vai modificar o valor da aposta se tivermos perdido a última aposta
                        ultimo_jogo = ultimo_jogo['betslips'][0]
                        if ultimo_jogo['state'] == 'Lost':                            

                            # if float( ultimo_jogo['stake']['value']) == 50:
                            #     self.valor_aposta = 150
                            # else:
                            self.valor_aposta = 2
                            if self.primeiro_alerta_depois_do_jogo:                               
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'PERDEU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                    sleep(30)
                                self.primeiro_alerta_depois_do_jogo = False
                            
                        else:
                            if self.primeiro_alerta_depois_do_jogo:                               
                                try:
                                    self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                except Exception as e:
                                    print(e)
                                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                    sleep(30)
                                self.primeiro_alerta_depois_do_jogo = False

                                #aqui se o saldo for maior ou igual a 1100, vamos sacar o que tiver passando de 1000
                                # if self.saldo >= 1100:
                                #     resto = self.saldo % 1000
                                #     try:
                                #         self.chrome.get('https://cashier.sportingbet.com/cashier/withdrawal')

                                #     except:
                                #         print('NÃO FOI POSSÍVEL SOLICITAR O SAQUE')
                                    

                            self.valor_aposta = 2
                            print(f'VALOR DA APOSTA: R$ {self.valor_aposta:.2f}')

                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

                        print()

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2.5 * 60
                            for fixture in fixtures['fixtures']:
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:               

                                    if option_market['name']['value'] == 'Total de gols':
                                        for option in option_market['options']:   
                                            odd = float(option['price']['odds'])
                                            if odd >= 2 and odd <= 2.5 and 'Mais' in option['name']['value']:
                                                cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60
                                                jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'], 'odd':float(option['price']['odds']), 'mercado': option['name']['value'], 'cronometro': cronometro })

                            # o laço vai sair quando já tiverem dois jogos na combinação      
                            numero_apostas_feitas = 0                      

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: (el['odd'], el['cronometro']) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            print(jogos_aptos_ordenado)

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                print(datetime.now())
                                sleep(self.tempo_pausa)
                                continue

                            for jogo_apto in jogos_aptos_ordenado:

                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                if jogo_apto['time'] in jogos_ja_inseridos:
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca
                                    try:
                                        aba_procurar = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Procurar']/ancestor::a")))
                                        aba_procurar.click()
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception
                                       
                                    try:
                                        input_busca = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.NAME, "searchField") ))                                                                                
                                        input_busca.clear()
                                        input_busca.send_keys(jogo_apto['time'])
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception

                                    try:
                                        actions = ActionChains(self.chrome)
                                        actions.send_keys(Keys.ENTER)
                                        actions.perform()
                                    
                                        jogo_clicavel = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='modal-content'] a[class='grid-info-wrapper fixed']")))
                                        self.chrome.get( jogo_clicavel.get_property('href') + '?market=2' )
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception
                                        #raise ErroDeNavegacao

                                    # mais_1_meio = WebDriverWait(self.chrome, 10).until(
                                    #     EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 1,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                    # mais_1_meio.click()  

                                    # vamos verificar se a odd está dentro dos limites ou se estamos clicando em outro local
                                    try:
                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.XPATH, f"//*[normalize-space(text()) = '{jogo_apto['mercado']}']/following-sibling::div") )) 
                                        mercado_odd = float(mercado.get_property('innerText'))

                                        if mercado_odd < 2 or mercado_odd > 2.5:
                                            raise Exception('ODD FORA DO INTERVALO. SELEÇÃO DE MERCADO INCORRETO.')

                                        mercado = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = '{jogo_apto['mercado']}']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                        mercado.click()
                                    except Exception as e:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        print(e)
                                        raise Exception

                                    sleep(1)    

                                    numero_apostas_feitas += 1     
                                    jogos_ja_inseridos.append(jogo_apto['time'])                              

                                    if numero_apostas_feitas == 1:
                                        nome_time_aposta = jogo_apto['time']
                                        break                                 
                                except Exception as e:
                                    # self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    # self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")
                                    print('Algo deu errado')  
                                    #quando limpar as apostas o número de apostas feitas vai pra zero
                                    # numero_apostas_feitas = 0
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://www.sportingbet.com')

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                        self.chrome.quit()
                                        numero_apostas_feitas = 0
                                        self.acessa('https://www.sportingbet.com/pt-br/labelhost/login')                                                
                                        self.faz_login() 
                                        sleep(10)

                                    sleep(5)                       

                            if numero_apostas_feitas == 1:                            
                                cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                try: 
                                    cota = float( cota.get_property('innerText') )
                                except Exception as e:
                                    print('cota fechada para o jogo')
                                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                    print(e)

                                if type(cota) != float and ( cota < 2 or cota > 2.5 ):
                                    raise ErroCotaForaIntervalo

                                self.insere_valor_jogo_unico(nome_time_aposta)
                                
                                ## self.telegram_bot_erro.envia_mensagem(mensagem_telegram)
                                ## print(mensagem_telegram)
                            else:
                                print(datetime.now())
                        
                        print()
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(10)
                        print(e)
                    except Exception as e:
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            numero_apostas_feitas = 0
                            self.chrome.quit()
                            self.acessa('https://www.sportingbet.com/pt-br/labelhost/login')                                    
                            self.faz_login() 
                            sleep(10)
                        print(e)
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                self.telegram_bot_erro.envia_mensagem('KEYERROR')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                self.faz_login() 
                sleep(10)
            except Exception as e:
                print(e)
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login')        
                self.faz_login() 
                sleep(10)


    def testa_retirada(self):
        try:
            
            seta_direita = WebDriverWait(self.chrome, 10).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "theme-right") ))
            print(seta_direita) 
        except Exception as e:
            print(e)

    def busca_odds_acima_meio_gol_multiplos_jogos(self):
        self.tempo_pausa = 2.5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        self.le_saldo()
        saldo_anterior = self.saldo
        self.saldo_inicial = self.saldo
        jogos_ja_inseridos = []
        self.meta = 1873
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])       

        while True:
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            deu_erro = False

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600 * 2:
                self.telegram_bot.envia_mensagem('SISTEMA RODANDO.')
                horario_ultima_checagem = datetime.now()

            # no começo de cada laço ele vai verificar se tem um banner atrapalhando as coisas e vai fechar
            try:
                self.chrome.execute_script("var botao = document.querySelector(\"button[data-aut='button-x-close']\"); if (botao) { botao.click(); }")
            except Exception as e:
                print(e)
                print('Erro ao tentar fechar banner')
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                self.faz_login()
                sleep(10)

            try:    
                saldo_anterior = self.saldo
                self.le_saldo()         
                
                if self.saldo > saldo_anterior:
                    self.telegram_bot_erro.envia_mensagem(f'AUMENTO DE SALDO. R$ {self.saldo}')

                if self.saldo >= self.meta - 0.01:
                    self.telegram_bot_erro.envia_mensagem('META ATINGIDA!')
                    self.sair()
                    exit()

                #jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1&forceFresh=1"); return await d.json();')
                if self.saldo < self.valor_aposta:
                    print('Não há saldo para fazer apostas...')
                    print(datetime.now())
                    self.tempo_pausa = 2.5 * 60
                else:
                    try:                        
                        print(self.saldo)

                        self.valor_aposta = 100

                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

                        print()

                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            self.tempo_pausa = 10 * 60
                        else:
                            self.tempo_pausa = 2.5 * 60
                            for fixture in fixtures['fixtures']:
                                #print( int(fixture['scoreboard']['timer']['seconds']) / 60 )
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:                         
                                    if option_market['name']['value'] == '1º Tempo - Total de Gols' or option_market['name']['value'] == '2º Tempo - Total de Gols':
                                        #print(option_market['name']['value'])
                                        for option in option_market['options']:
                                            if option['name']['value'] == 'Mais de 0,5':
                                                confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                odd = float(option['price']['odds'])
                                                primeiro_ou_segundo_tempo = ''
                                                if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                    primeiro_ou_segundo_tempo = '1T'
                                                else:
                                                    primeiro_ou_segundo_tempo = '2T'

                                                cronometro = int(fixture['scoreboard']['timer']['seconds']) // 60
                                                # if odd >= 1.18 and odd < 1.42:
                                                #     odds_3.append(f'{odd} {confronto}')
                                                # elif odd >= 1.42 and odd < 1.6:
                                                #     odds_2.append(f'{odd} {confronto}')

                                                if primeiro_ou_segundo_tempo == '1T' and odd >= 1.5 and odd <= 1.8:
                                                    jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 1, 'prioridade': 0 })
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')
                                                elif primeiro_ou_segundo_tempo == '2T' and odd >= 1.5 and odd <= 1.8 and fixture['scoreboard']['score'] == '0:0':
                                                    prioridade = 1
                                                    # se o mercado for pro segundo tempo e o jogo está no intervalo ou no segundo tempo a prioridade é mais baixa
                                                    if fixture['scoreboard']['period'] == '2º T' or fixture['scoreboard']['period'] == 'Intervalo':
                                                        prioridade = 0
                                                    jogos_aptos.append({ 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'tempo': 2, 'prioridade': prioridade })
                                                    odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')


                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']

                            # o laço vai sair quando já tiverem dois jogos na combinação      
                            numero_apostas_feitas = 0                      

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], el['prioridade'], el['odd'] ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) == 0:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                print(datetime.now())
                                sleep(self.tempo_pausa)
                                continue

                            for jogo_apto in jogos_aptos_ordenado:
                                # isso pra evitar que o sistema selecione o mesmo jogo com mercados do primeiro e segundo tempo
                                
                                
                                if jogo_apto['time'] + str(jogo_apto['tempo']) in jogos_ja_inseridos:
                                    continue
                                try:
                                    print(jogo_apto)
                                    # clica na aba de busca
                                    try:
                                        aba_procurar = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, f"//*[normalize-space(text()) = 'Procurar']/ancestor::a")))
                                        aba_procurar.click()

                                    except Exception as e:
                                        deu_erro = True
                                        print(e)
                                        self.numero_erros_global += 1
                                        raise Exception
                                    
                                    try:
                                        input_busca = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.NAME, "searchField") ))                                                                                
                                        input_busca.clear()
                                        input_busca.send_keys(jogo_apto['time'])
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception

                                    try:
                                        actions = ActionChains(self.chrome)
                                        actions.send_keys(Keys.ENTER)
                                        actions.perform()
                                    
                                        jogo_clicavel = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[class='modal-content'] a[class='grid-info-wrapper fixed']")))
                                        self.chrome.get( jogo_clicavel.get_property('href') + '?market=2' )
                                    except:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        raise Exception
                                        #raise ErroDeNavegacao

                                    # quer dizer que o mercado de gols é no primeiro tempo
                                    try:
                                        if jogo_apto['tempo'] == 1:
                                            mercado = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º T']/ancestor::a")))                                                    
                                            mercado.click()
                                        else:              
                                            mercado = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '2º T']/ancestor::a")))                                                    
                                            mercado.click()
                                    except:
                                        self.numero_erros_global += 1
                                        deu_erro = True
                                        raise Exception
                                        #raise ErroDeNavegacao

                                    # mais_1_meio = WebDriverWait(self.chrome, 10).until(
                                    #     EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 1,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                    # mais_1_meio.click()  

                                    # vamos verificar se a odd está dentro dos limites ou se estamos clicando em outro local
                                    try:
                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.XPATH, "//*[normalize-space(text()) = 'Mais de 0,5']/following-sibling::div") )) 
                                        mais_meio_odd = float(mais_meio.get_property('innerText'))

                                        if mais_meio_odd < 1.5 or mais_meio_odd > 1.8:
                                            raise Exception('ODD FORA DO INTERVALO. SELEÇÃO DE MERCADO INCORRETO.')

                                        mais_meio = WebDriverWait(self.chrome, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = 'Mais de 0,5']/ancestor::div/ancestor::ms-event-pick" ) )) 
                                        mais_meio.click()
                                    except Exception as e:
                                        deu_erro = True
                                        self.numero_erros_global += 1
                                        print(e)
                                        raise Exception

                                    sleep(1)                   

                                    cota = WebDriverWait(self.chrome, 10).until(
                                            EC.presence_of_element_located((By.CLASS_NAME, "betslip-summary__original-odds") )) 
                                    cota = float( cota.get_property('innerText') )

                                    if cota < 1.5 or cota > 1.8:
                                        raise ErroCotaForaIntervalo

                                    self.insere_valor()    

                                    jogos_ja_inseridos.append(jogo_apto['time'] + str(jogo_apto['tempo']))     

                                    if len(jogos_ja_inseridos) % 4 == 0:
                                        break                           
                                except Exception as e:
                                    # self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                    # self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")
                                    print('Algo deu errado')  
                                    self.numero_erros_global += 1
                                    #quando limpar as apostas o número de apostas feitas vai pra zero
                                    # numero_apostas_feitas = 0
                                    deu_erro = True
                                    print(e)
                                    # vou colocar pra voltar pra página inicial
                                    self.chrome.get('https://www.sportingbet.com')

                                    if self.numero_erros_global >= 10:
                                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                                        self.chrome.quit()
                                        numero_apostas_feitas = 0
                                        self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                                        self.faz_login()
                                        sleep(10)

                                    sleep(10)                       
                        
                        print()
                        
                    except ErroCotaForaIntervalo as e:
                        # pode ter acontecido do mercado ter sumido no momento da aposta ou a cota estar fora o intervalo
                        # então vamos excluir tudo no botão da lixeira
                        self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                        self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                        #quando limpar as apostas o número de apostas feitas vai pra zero
                        numero_apostas_feitas = 0
                        deu_erro = True
                        sleep(10)
                        print(e)
                    except Exception as e:
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            numero_apostas_feitas = 0
                            self.chrome.quit()
                            self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                            self.faz_login()
                            sleep(10)
                        pass
                
                if not deu_erro:
                    sleep(self.tempo_pausa)
            except KeyError as e:
                print('KeyError')
                # se der keyerror eu vou matar o chrome e logar de novo
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                self.faz_login()
                sleep(10)
            except Exception as e:
                print(e)
                self.chrome.quit()
                self.acessa('https://www.sportingbet.com/pt-br/labelhost/login') 
                self.faz_login()
                sleep(10)

    def busca_odds_acima_2_e_meio(self):
        self.tempo_pausa = 3 * 60
        horario_ultima_checagem = datetime.now()
        jogos_aptos = list()
        # for fixture in fixtures['fixtures']:
        #     print(fixture['scoreboard']['score'])

        # print(fixtures['fixtures'])        

        while True:      
            # primeiro verificamos se não há nenhum jogo em aberto

            # fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           
            
            fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&fixtureTypes=Standard&state=Latest&offerMapping=Filtered&sportIds=4&regionIds=&competitionIds=&conferenceIds=&isPriceBoost=false&skip=0&take=200&sortBy=StartDate&from={date.today()}T{( datetime.today() + timedelta(hours=3)).strftime("%H:%M:%S")}.000Z&to={date.today() + timedelta(days=1)}T03:00:00.000Z"); return await d.json();')           
            
            #fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')           

            if len( fixtures['fixtures'] ) == 0:
                print('Sem jogos ao vivo...')
                print(datetime.now())
                self.tempo_pausa = 10 * 60
            else:
                self.tempo_pausa = 3 * 60
                for fixture in fixtures['fixtures']:

                    option_markets = fixture['optionMarkets']
                    for option_market in option_markets: 
                        
                        if option_market['name']['value'].strip() == '1º Tempo - Total de Gols - Exato' or option_market['name']['value'].strip() == '2º Tempo - Total de Gols - Exato':
                            # for option in option_market['options']:
                            #     if option['name']['value'] == 'Mais de 2,5' and float( option['price']['odds']) >= 3.0 :
                            hora_inicio = fixture['startDate']
                            hora_inicio_data = datetime.strptime( hora_inicio, "%Y-%m-%dT%H:%M:%SZ" )
                            hora_inicio = hora_inicio_data - timedelta(hours=3)
                            #         if f"{fixture['participants'][0]['name']['value']} {hora_inicio.strftime('%H:%M:%S')}" not in jogos_aptos:                              
                            if f"{fixture['participants'][0]['name']['value']} {hora_inicio.strftime('%H:%M:%S')}" not in jogos_aptos:
                                jogos_aptos.append(f"{fixture['participants'][0]['name']['value']} {hora_inicio.strftime('%H:%M:%S')}")                         



                # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                print(jogos_aptos)

                for jogo in jogos_aptos:
                    self.telegram_bot.envia_mensagem(jogo)

                jogos_aptos.clear()                        
            print()             
            self.chrome.quit()
            exit(0)
            sleep(self.tempo_pausa)


    def le_saldo(self):        
        leu_saldo = False
        contador_de_trava = 0
        while not leu_saldo:
            sleep(5)
            try:
                saldo_request = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/api/balance?forceFresh=1"); return await d.json();')
                self.saldo = float(saldo_request['balance']['accountBalance'])
                leu_saldo = True
            except Exception as e:
                print(e)
                contador_de_trava += 1
                if contador_de_trava % 10 == 0:
                    self.testa_sessao()
                    self.telegram_bot_erro.envia_mensagem('SISTEMA POSSIVELMENTE TRAVADO AO LER SALDO.')
                    self.chrome.refresh()
                print('Não foi possível ler saldo. Tentando de novo...')

    async def analisa(self, index):
        pass

    async def analisa_resultados(self, index):
        print('analisa resultados')       
        apostas_cachout = dict()
        while True:
            try:
                i = index
                cachout_temp = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=Live"); return await d.json();')                

                ## não tem jogo aberto
                if len(cachout_temp['betslips']) == 0:
                    print('SEM APOSTAS EM ABERTO.')
                    tempo_de_pausa = 60 * 10
                    sleep(tempo_de_pausa)
                    continue

                ## vai modificar o tempo de pausa a depender se há jogo ao vivo ou não
                if cachout_temp['summary']['liveBetsCount'] == 0:
                    print('SEM APOSTAS AO VIVO.')
                    tempo_de_pausa = 60 * 30
                    sleep(tempo_de_pausa)
                    continue
                else:
                    tempo_de_pausa = 60 * 2.5            

                aumentou_algum = False
                mensagem_telegram = ''

                todos_zerados = True
                soma_odds = 0.0

                array_odds = []

                controle = 0

                c = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index={i}&maxItems=6&typeFilter=Live"); return await d.json();')
                cachouts = dict()
                cachouts['betslips'] = c['betslips']
                while controle <= 50:
                    i += 1
                    controle += 1
                    c = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index={i}&maxItems=6&typeFilter=Live"); return await d.json();')
                    cachouts['betslips'].extend(c['betslips'])

                if len( c['betslips'] ) > 0:
                    cachouts['betslips'].extend(c['betslips'])

                for bet in cachouts['betslips']:
                    print(bet['betSlipNumber'])
                    c1 = bet['betSlipNumber']
                    c_2 = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/CashoutCheckAndSubscribe?betNumbers={c1}&source=mybets&forceFresh=1"); return await d.json();')
                    c_4 = c_2['earlyPayouts'][0]

                    bet_number = c_4['betNumber']
                    v =  float(c_4['earlyPayoutValue'])
                    soma_odds += v
                    if apostas_cachout.get(bet_number) is None:
                        apostas_cachout[bet_number] = float( c_4['earlyPayoutValue'] )
                    else:
                        valor_novo = float( c_4['earlyPayoutValue'] )

                        if valor_novo > 0:
                            todos_zerados = False

                        if valor_novo > apostas_cachout.get(bet_number) and valor_novo >= 0.5:
                            aumentou_algum = True
                            valor_antigo = apostas_cachout.get(bet_number)
                            del apostas_cachout[bet_number]
                            apostas_cachout[bet_number] = valor_novo
                            bet_number = bet_number                                                        
                            array_odds.append({ 'betNumber': bet_number, 'oldValue': valor_antigo, 'newValue' : valor_novo })

                array_odds = sorted( array_odds, key=lambda k: k['newValue'], reverse=True )

                mensagem_telegram += f'SOMA DAS ODDS: {soma_odds:.2f}\n'

                print(f'-- soma das odds -- {soma_odds:.2f}')

                for odd in array_odds:
                    mensagem_telegram += f"JOGO {odd['betNumber']} AUMENTOU DE {odd['oldValue']} PARA {odd['newValue']}\n"
                
                if todos_zerados:
                    tempo_de_pausa = 60 

                if aumentou_algum:
                    await self.telegram_bot.envia_mensagem(mensagem_telegram)  
                else:
                    print('Same old, same old...', datetime.now() )                                      
                
                sleep(tempo_de_pausa)
            except Exception as e:
                print(e)
            

        self.chrome.quit()
        exit()

    def insere_valor_jogo_unico(self, nome_time_aposta):
        if self.valor_aposta < 2:
            self.valor_aposta = 2
            
        contador_travamento = 0

        sleep(2)

        while True:   
            try:      
                contador_travamento += 1
                inseriu_valor = False
                while not inseriu_valor:
                    try:
                        input_valor = WebDriverWait(self.chrome, 20).until(
                                EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
                        sleep(2)
                        input_valor.clear()
                        input_valor.send_keys(f'{self.valor_aposta:.2f}')
                        inseriu_valor = True
                    except Exception as e:
                        print(e)
                        self.tempo_pausa = 30
                        sleep(2)
                
            
                sleep(2)

                try:
                    botao_aposta = WebDriverWait(self.chrome, 20).until(
                            EC.element_to_be_clickable((By.CLASS_NAME, 'betslip-place-button' ) )) 
                    botao_aposta.click()     
                except Exception as e:
                    print(e)
                    self.tempo_pausa = 30
                    raise Exception('erro ao clicar no botão de aposta')

                sleep(2) 
                
                try:
                    botao_fechar = WebDriverWait(self.chrome, 20).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, '.betslip-result-actions .btn-primary' ) )) 
                    botao_fechar.click() 
                except Exception as e:
                    print(e)
                    self.tempo_pausa = 30
                    raise Exception('erro ao clicar no botão de fechar')

                numero_apostas_abertas = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
                numero_apostas_abertas = numero_apostas_abertas['summary']['openBetsCount']

                if numero_apostas_abertas > 0:
                    #self.telegram_bot.envia_mensagem('APOSTA REALIZADA.')    
                    self.primeiro_alerta_depois_do_jogo = True    
                    try:
                        self.telegram_bot.envia_mensagem(nome_time_aposta)
                    except Exception as e:
                        print(e)
                        print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---') 
                        sleep(5)   
                    print('--- APOSTA REALIZADA ---')        
                    return

                contador_travamento += 1
                if contador_travamento % 10 == 0:
                    #self.telegram_bot_erro.envia_mensagem('SISTEMA POSSIVELMENTE TRAVADO NO INSERE VALOR!')
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                    self.chrome.quit()
                    self.acessa('https://sports.sportingbet.com/pt-br/sports')        
                    self.faz_login()  
                    #quando limpar as apostas o número de apostas feitas vai pra zero
                    sleep(10)
                    return

            except Exception as e:
                print('tentando limpar os jogos...')
                #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')
                print(e)
                return

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
                self.tempo_pausa = 30
                raise Exception('erro ao inserir valor no campo')
                        
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
                # verificamos se há apostas em aberto
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if jogos_abertos['summary']['openBetsCount'] >= 1:
                if not self.varios_jogos:
                    self.hora_ultima_aposta = datetime.now().strftime("%d/%m/%Y %H:%M")
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
                    self.telegram_bot.envia_mensagem(f'APOSTA {self.quantidade_apostas_feitas() + 1} REALIZADA.')
                # else:                                        
                    #self.telegram_bot.envia_mensagem(f'APOSTA REALIZADA.')
                self.primeiro_alerta_depois_do_jogo = True
                self.primeiro_alerta_sem_jogos_elegiveis = True
                self.le_saldo()
                self.saldo_antes_aposta = self.saldo
                self.jogos_inseridos.append(id_jogo)
                self.numero_apostas_feitas = 0
            else:
                # deu algum erro maluco, limpamos a aposta e esperamos o próximo laço
                self.testa_sessao()
                try:
                    self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                    self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                except:
                    print('Não conseguiu limpar os jogos...')

        except Exception as e:
            self.tempo_pausa = 30
            self.testa_sessao()
            #self.telegram_bot_erro.envia_mensagem('OCORREU UM ERRO AO TENTAR INSERIR VALOR DA APOSTA.')
            try:
                self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
            except:
                print('Não conseguiu limpar os jogos...')
            print(e)

        return
    
    def insere_valor_2(self):
        self.valor_aposta = 0.10
        print('entrou no insere valor')

        if self.valor_aposta < 0.10:
            self.valor_aposta = 0.10


        try:
            input_valor = WebDriverWait(self.chrome, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'stake-input-value') )) 
            input_valor.clear()
            input_valor.send_keys(f'{self.valor_aposta:.2f}')
        except Exception as e:
            self.tempo_pausa = 30
            raise Exception('erro ao inserir valor no campo')
                    
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
            # verificamos se há apostas em aberto
        
        return
    
    def get_bd_connection(self):
        try:
            conn = psycopg2.connect(database = db_name, 
                                user = db_user, 
                                host= db_host,
                                password = db_password,
                                port = db_port)
            return conn
        except:
            print('Erro ao abrir conexão')
    
    def testa_sessao(self):
        print('testando sessão...')
        try:
            self.chrome.execute_script("var botao_fechar = document.querySelector('.ui-icon.theme-close-i.ng-star-inserted'); if (botao_fechar) { botao_fechar.click(); }")
        except Exception as e:
            print('Erro ao tentar fechar banner')
        try:
            jogos_abertos = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=1"); return await d.json();')
            if jogos_abertos['summary']['liveBetsCount']:
                print('sessão ativa')
        except:
            print('sessão expirada. tentando login novamente.')
            self.chrome.quit()
            self.acessa('https://sports.sportingbet.com/pt-br/sports')        
            self.faz_login()

    def busca_odds_fim_jogo_sem_gol(self, mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria):
        self.tempo_pausa = 5 * 60
        jogos_aptos = []
        horario_ultima_checagem = datetime.now()
        self.times_favoritos = []
        times_ja_enviados = []
        self.times_pra_apostar = []
        self.varios_jogos = varios_jogos
        saldo_inicial = 644.29
        self.qt_apostas_feitas = self.quantidade_apostas_feitas()
        

        while True:
            menor_odd = 100.0
            mensagem_telegram = ''
            array_mensagem_telegram = []
            odds = []            
            jogos_aptos = []
            jogos_ja_inseridos = [] 
            deu_erro = False
            fixtures = None

            diferenca_tempo = datetime.now() - horario_ultima_checagem
            if diferenca_tempo.total_seconds() >= 3600:
                try:
                    with open('meta_ganho.txt', 'r') as f:
                        self.telegram_bot.envia_mensagem(f'SISTEMA RODANDO. {self.hora_ultima_aposta}\nMETA DE GANHO: { f.read() }\nGANHO DO DIA: {self.ganho_do_dia:.2f}')
                except Exception as e:
                    print(e)
                    print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')                        
                horario_ultima_checagem = datetime.now()

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
                    self.tempo_pausa = 2 * 60
                    if self.saldo_antes_aposta == 0.0:
                        self.le_saldo()
                        self.saldo_antes_aposta = self.saldo
                else:
                    try:             
                        self.le_saldo()           

                        if not self.varios_jogos:
                            # primeiro verificamos se a última aposta foi vitoriosa                    
                            ultimo_jogo = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/pt-br/sports/api/mybets/betslips?index=1&maxItems=1&typeFilter=2"); return await d.json();')
                            
                            # só vai modificar o valor da aposta se tivermos perdido a última aposta
                            ultimo_jogo = ultimo_jogo['betslips'][0]

                            with open('meta_ganho.txt', 'r') as f:
                                valor_aposta = float( f.read() )

                            if ultimo_jogo['state'] == 'Lost':                            
                                self.valor_aposta = float( ultimo_jogo['stake']['value']) * float( ultimo_jogo['totalOdds']['european'] ) + 0.01
                                valor_perdido = float( ultimo_jogo['stake']['value'] )
                                result_csv = []
                                with open('perda_acumulada.csv', 'r') as f:
                                    csv_reader = csv.reader(f, delimiter=',')
                                    for row in csv_reader:
                                        result_csv = row
                                perda_acumulada = float( result_csv[0] )
                                id_ultimo_jogo = result_csv[1]

                                self.valor_aposta = perda_acumulada + valor_aposta
                                
                                if id_ultimo_jogo != ultimo_jogo['betSlipNumber']:
                                    id_ultimo_jogo = ultimo_jogo['betSlipNumber']
                                    with open('perda_acumulada.csv', 'w') as f:
                                        f.write(f'{ (perda_acumulada + valor_perdido):.2f}' + f',{id_ultimo_jogo}')
                                        
                                    print(f'valor perdido acumulado {(perda_acumulada + valor_perdido)}')
                                 
                                ''' A LINHA DE BAIXO É PRA NÃO USAR MARTINGALE '''
                                #self.valor_aposta = 2
                                # if self.primeiro_alerta_depois_do_jogo:
                                #     print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                                #     try:
                                #         self.telegram_bot.envia_mensagem('PERDEU.')
                                #     except Exception as e:
                                #         print(e)
                                #     self.primeiro_alerta_depois_do_jogo = False
                            elif ultimo_jogo['state'] == 'Canceled':
                                self.qt_apostas_feitas =- 1
                                self.valor_aposta = float( ultimo_jogo['stake']['value']) * ( float( ultimo_jogo['totalOdds']['european'] ) - 1.0 ) + 0.01
                                valor_ultima_aposta = float( ultimo_jogo['stake']['value'])
                                result_csv = []
                                with open('perda_acumulada.csv', 'r') as f:
                                    csv_reader = csv.reader(f, delimiter=',')
                                    for row in csv_reader:
                                        result_csv = row
                                perda_acumulada = float( result_csv[0] )

                                self.valor_aposta = perda_acumulada - valor_ultima_aposta + valor_aposta
                                
                                with open('perda_acumulada.csv', 'w') as f:
                                    f.write(f'{ ( perda_acumulada - valor_ultima_aposta):.2f}' + ',00000')                               
                                
                                
                                ''' A LINHA DE BAIXO É PRA NÃO USAR MARTINGALE '''
                                #self.valor_aposta = 2
                                # if self.primeiro_alerta_depois_do_jogo:
                                #     print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                                #     # try:
                                #     #     #self.telegram_bot.envia_mensagem('ÚLTIMA APOSTA CANCELADA.')
                                #     # except Exception as e:
                                #     #     print(e)
                                #     self.primeiro_alerta_depois_do_jogo = False
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
                                
                                # if self.primeiro_alerta_depois_do_jogo:
                                #     try:
                                #         self.telegram_bot_erro.envia_mensagem(f'GANHOU APOSTA!!! {self.saldo}')
                                #     except Exception as e:
                                #         print(e)
                                #         print('--- NÃO FOI POSSÍVEL ENVIAR MENSAGEM AO TELEGRAM ---')
                                #     self.primeiro_alerta_depois_do_jogo = False   

                                try:

                                    conn = self.get_bd_connection()             
                                    cur = conn.cursor()

                                    data_de_hoje = date.today()

                                    cur.execute(f"select * from principal where data_base = '{data_de_hoje}'")
                                    rows = cur.fetchall()
                                    if len(rows) == 0:
                                        cur.execute(f"insert into principal values ('{data_de_hoje}', {self.saldo:.2f}, null)")
                                        #data_de_ontem = date.today() - timedelta(days=1)
                                        #cur.execute(f"select banca from principal where data_base = '{data_de_ontem}'")
                                        #banca_ontem = cur.fetchall()
                                        #banca_ontem = float(banca_ontem[0][0])
                                        #ganho_dia = self.saldo - banca_ontem
                                        #mes_atual = int( date.today().strftime('%m'))
                                        #ano_atual = int( date.today().strftime('%Y'))
                                        #ultimo_dia_mes_passado = date( ano_atual, mes_atual, 1 ) - timedelta(days=1)
                                        #cur.execute(f"select banca from principal where data_base = '{ultimo_dia_mes_passado}'")
                                        #banca_ultimo_dia_mes_passado = cur.fetchall()
                                        #banca_ultimo_dia_mes_passado = float( banca_ultimo_dia_mes_passado[0][0])
                                        #ganho_mes = self.saldo - banca_ultimo_dia_mes_passado
                                        #self.telegram_bot.envia_mensagem(f'GANHO DO DIA: R$ {ganho_dia:.2f}\nGANHO DO MÊS: R$ {ganho_mes:.2f}')
                                    else:
                                        self.ganho_do_dia = self.saldo - float( rows[0][1] )
                                        # if self.ganho_do_dia >= meta_diaria:
                                        #     self.telegram_bot_erro.envia_mensagem('META DIÁRIA ATINGIDA.')
                                        #     self.chrome.quit()
                                        #     exit(0)
                                    conn.commit()
                                    conn.close()
                                except Exception as e:
                                    print(e)

                                #atualiza o valor da meta de ganho uma vez que ganhou
                                self.valor_aposta = self.saldo * 0.004442 #0.000325
                                with open('meta_ganho.txt', 'w') as f:
                                    f.write(f'{self.valor_aposta:.2f}' + '')
                                with open('perda_acumulada.csv', 'w') as f:
                                    f.write( '0.0,000000' )
                                
                              
                                print(f'META DE GANHO: R$ {self.valor_aposta:.2f}')
                        else:
                            self.le_saldo()
                            if self.saldo > saldo_inicial:
                                self.telegram_bot_erro.envia_mensagem('ganho real')
                                self.chrome.quit()
                                exit()

                        if teste:
                            self.valor_aposta = valor_aposta
                        
                        fixtures = self.chrome.execute_script(f'let d = await fetch("https://sports.sportingbet.com/cds-api/bettingoffer/fixtures?x-bwin-accessid={bwin_id}&lang=pt-br&country=BR&userCountry=BR&state=Live&take=500&offerMapping=Filtered&sortBy=StartDate&sportIds=4"); return await d.json();')                                   
                        
                        if len( fixtures['fixtures'] ) == 0:
                            print('Sem jogos ao vivo...')
                            print(datetime.now())
                            self.tempo_pausa = 10 * 60
                        else:

                            self.tempo_pausa = 2 * 60
                            for fixture in fixtures['fixtures']:
                                nome_evento = self.formata_nome_evento( fixture['participants'][0]['name']['value'], fixture['participants'][1]['name']['value'], fixture['id'] )
                                numero_gols_atual = fixture['scoreboard']['score']
                                try:
                                    numero_gols_atual = sum([int(x) for x in numero_gols_atual.split(':')])
                                except:
                                    print('jogo ainda não iniciou')
                                    continue
                                periodo = fixture['scoreboard']['period']
                                
                                option_markets = fixture['optionMarkets']
                                for option_market in option_markets:     
                                    if periodo == '1º T':
                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                            for option in option_market['options']:
                                                # faço um for pra saber em qual mercado posso apostar que vai me retornar a odd que eu quero
                                                for n_gols in range( 3 ):
                                                    if option['name']['value'] == f'Mais de {numero_gols_atual+ n_gols},5':
                                                        confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                        odd = float(option['price']['odds'])
                                                        primeiro_ou_segundo_tempo = ''
                                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                            primeiro_ou_segundo_tempo = '1T'
                                                        else:
                                                            primeiro_ou_segundo_tempo = '2T'

                                                        cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                        hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                
                                                        id = fixture['id']

                                                        if odd < menor_odd and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                            menor_odd = odd
                                                    

                                                        if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                            jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': option['name']['value'], 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo })
                                                            print(f'{odd} {nome_evento} {primeiro_ou_segundo_tempo}')
                                                            odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')  
                                    else:
                                        if option_market['name']['value'] == 'Total de gols':
                                            for option in option_market['options']:
                                                for n_gols in range( 3 ):
                                                    if option['name']['value'] == f'Mais de {numero_gols_atual+n_gols},5':
                                                    
                                                        confronto = fixture['name']['value'].replace(' ', '_')[0:25]
                                                        odd = float(option['price']['odds'])
                                                        primeiro_ou_segundo_tempo = ''
                                                        if option_market['name']['value'] == '1º Tempo - Total de Gols':
                                                            primeiro_ou_segundo_tempo = '1T'
                                                        else:
                                                            primeiro_ou_segundo_tempo = '2T'

                                                        cronometro = float(fixture['scoreboard']['timer']['seconds']) / 60.0
                                                        hora_inicio = datetime.strptime(fixture['startDate'], '%Y-%m-%dT%H:%M:00Z')
                                
                                                        id = fixture['id']

                                                        if odd < menor_odd and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                            menor_odd = odd
                                                    

                                                        if odd >= limite_inferior and odd <= limite_superior and f"{fixture['id']}{primeiro_ou_segundo_tempo}" not in self.jogos_inseridos:
                                                            jogos_aptos.append({ 'nome_evento': nome_evento, 'mercado': option['name']['value'], 'time': fixture['participants'][0]['name']['value'],'odd':float(option['price']['odds']), 'cronometro': cronometro, 'hora_inicio': hora_inicio, 'id': id, 'tempo': primeiro_ou_segundo_tempo, 'periodo': periodo })
                                                            print(f'{odd} {nome_evento} {primeiro_ou_segundo_tempo}')
                                                            odds.append(f'{odd} {confronto} {primeiro_ou_segundo_tempo} {cronometro}')  
                                          

                            for combinacao in array_mensagem_telegram:
                                mensagem_telegram += combinacao['texto']                    

                            jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( el['tempo'], -el['cronometro'], el['odd']  ) )
                            # aqui vou fazer um laço pelos jogos aptos e tentar inseri-los na aposta combinada

                            if len(jogos_aptos_ordenado) < 1:
                                print('--- SEM JOGOS ELEGÍVEIS ---')
                                if self.primeiro_alerta_sem_jogos_elegiveis:                                    
                                    self.primeiro_alerta_sem_jogos_elegiveis = False
                                print(datetime.now())
                                if menor_odd < 25 :
                                    print('odds abaixo de 25')
                                    sleep(2.5 * 60)
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

                            for jogo_apto in jogos_aptos_ordenado:

                                self.le_saldo()

                                if self.saldo < valor_aposta:
                                    continue

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
                                        if jogo_apto['periodo'] == '1º T':
                                            mercado_1_tempo = WebDriverWait(self.chrome, 10).until(
                                                EC.element_to_be_clickable((By.XPATH, "//*[normalize-space(text()) = '1º T']/ancestor::a")))                                                    
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


                                if self.valor_aposta > self.saldo:
                                    try:
                                        self.telegram_bot_erro.envia_mensagem('MIOU')
                                        self.chrome.quit()
                                        exit()
                                    except:
                                        print('Não foi possível enviar mensagem ao telegram.')

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
                        sleep(10)
                        print(e)
                    except Exception as e:
                        self.numero_apostas_feitas = 0
                        print(e)
                        if self.numero_erros_global >= 10:
                            self.chrome.execute_script("var lixeira = document.querySelector('.betslip-picks-toolbar__remove-all'); if (lixeira) lixeira.click()")
                            self.chrome.execute_script("var confirmacao = document.querySelector('.betslip-picks-toolbar__remove-all--confirm'); if (confirmacao) confirmacao.click()")                        
                            self.numero_apostas_feitas = 0
                            self.testa_sessao()
                            sleep(10)
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

def teste():
    j1 = [ 3.3, 3.1, 2 ]
    j2 = [ 2.2, 3.1, 2.9 ]
    j3 = [ 2.4, 3.1, 2.7 ]
    j4 = [ 2.8, 3, 3.2 ]
    j5 = [ 2.3 ,2.75, 3.1 ]
    j6 = [ 2.9 ,3.2 ,2.15 ]
    j7 = [ 2.35, 3.1 ,2.65 ]
    j8 = [ 2.15, 3.75, 2.55 ]

    resultados_possiveis = []

    jogos_abaixo_50_por_cento = 0

    jogos_entre_20_45_por_cento = 0

    for a in j1:
        for b in j2:
            for c in j3:
                for d in j4:
                    for e in j5:
                        for f in j6:
                            for g in j7:
                                for h in j8:
                                    valor = a * b * c * d * e * f * g * h
                                    if valor < 11702.85 / 2:
                                        jogos_abaixo_50_por_cento += 1
                                    if valor > 11702.85 * 0.14 and valor < 11702.85 * 0.50:
                                        jogos_entre_20_45_por_cento += 1
                                    resultados_possiveis.append(valor)

    
    resultados_possiveis = sorted( resultados_possiveis )
    print( 'Quantidade de jogos ', len( resultados_possiveis ))
    print( 'Menor valor ', resultados_possiveis[0] )
    print( 'Maior valor ', resultados_possiveis[-1] )
    print( 'Jogos abaixo de 50% do valor ', jogos_abaixo_50_por_cento)
    print( 'Jogos entre 14 e 50% ', jogos_entre_20_45_por_cento )

    pass

if __name__ == '__main__':

    #numero_apostas = int(input())
    #numero_jogos_por_aposta = int(input())

    #apenas_analisa = int(input())   

    nome_arquivo = sys.argv[1]
    index = int(sys.argv[2])
    

    chrome = ChromeAuto(numero_apostas=2000, numero_jogos_por_aposta=9, is_new_game=False)
    chrome.acessa('https://sports.sportingbet.com/pt-br/sports')        
     #chrome.clica_sign_in()
    chrome.faz_login()  
    #chrome.busca_odds_acima_meio_gol_sem_login('Mais de 0,5', 1.9, 2.9 )
    #chrome.busca_odds_acima_meio_gol('Mais de 0,5', 1.75, 2.9, 1, False, False, 100.0)
    # parâmetros: mercado, limite_inferior, limite_superior, valor_aposta, teste, varios_jogos, meta_diaria
    #chrome.busca_odds_fim_jogo_sem_gol('Mais de 0,5', 20, 25, 1, False, True, 100.0)


    # if apenas_analisa == 1:
    #chrome.analisa_resultados()
    # elif apenas_analisa == 2:
    chrome.gera_jogos_aleatorios(nome_arquivo)
    chrome.faz_apostas(nome_arquivo)
    #asyncio.run( chrome.analisa_resultados(index=index))
    
    # elif apenas_analisa == 3:
    #     chrome.busca_odds_acima_meio_gol_sem_login('Mais de 0,5', 1.75, 1.9 )
    #     #chrome.busca_odds_acima_meio_gol('Mais de 0,5', 1.75, 1.9, 1, False, False)
    # elif apenas_analisa == 4:
    #     chrome.busca_odds_acima_meio_gol_jogo_unico()
    # elif apenas_analisa == 5:
    #     chrome.busca_odds_acima_gol_jogo_inteiro()
    # elif apenas_analisa == 6:
    #     chrome.busca_odds_acima_2_e_meio()
    #     chrome.testa_retirada()
    # elif apenas_analisa == 7:
    #     chrome.busca_odds_abaixo_1_20()
    # elif apenas_analisa == 8:
    #     chrome.busca_jogos_perto_de_acabar()
    

    
