        
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
