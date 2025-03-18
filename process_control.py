from datetime import datetime
from subprocess import Popen
from time import sleep
import sys
import asyncio
from credenciais import app_path
from utils import le_de_arquivo, escreve_em_arquivo

async def main():
    only_messages = False        

    if '--help' in sys.argv:
        print('Opções:')
        print('-om: somente mensagens serão disparadas para o telegram')
        exit()

    if '-om' in sys.argv:
        only_messages = True        

    parameter = '-om' if only_messages else ''           

    proc = None    
    while True:
        try:            
            last_time_check = None
            try:            
                last_time_check = le_de_arquivo('last_time_check.txt', 'string')    

                if last_time_check == 'sair':
                    exit()
                elif last_time_check == 'erro_aposta':
                    print('tentando matar o processo anterior')
                    try:
                        if proc:
                            Popen(f"taskkill /f /pid {proc.pid}")     
                        chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                        Popen(f"taskkill /f /pid {chrome_process_id} /t")        
                        proc = None                   
                    except KeyboardInterrupt:
                        print('saindo...')
                        exit()
                    except Exception as e:
                        print(e)    

                    sleep(5)

                    proc = await asyncio.create_subprocess_exec("python", r""+app_path, parameter,
                                                    stdout=sys.stdout, stderr=sys.stderr)
            except Exception as e:
                print(e)
                print('tentando matar o processo anterior')
                try:
                    if proc:
                        Popen(f"taskkill /f /pid {proc.pid}")     
                    chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                    proc = None                   
                except KeyboardInterrupt:
                    print('saindo...')
                    exit()
                except Exception as e:
                    print(e)
            
            if last_time_check == 'erro_aposta':
                last_time_check = datetime.now().strftime( '%Y-%m-%d %H:%M' )
                escreve_em_arquivo('last_time_check.txt', last_time_check, 'w')

            last_time_check_datetime = datetime.strptime( last_time_check, '%Y-%m-%d %H:%M' )


            if not proc:
                proc = await asyncio.create_subprocess_exec("python", r""+app_path, parameter,
                                                    stdout=sys.stdout, stderr=sys.stderr)       

            diferenca_tempo = datetime.now() - last_time_check_datetime

            if diferenca_tempo.total_seconds() >= 15 * 60:
                print('tentando matar o processo anterior')
                try:
                    if proc:
                        Popen(f"taskkill /f /pid {proc.pid}")     
                    chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")        
                    proc = None                   
                except KeyboardInterrupt:
                    print('saindo...')
                    exit()
                except Exception as e:
                    print(e)    

                sleep(5)

                proc = await asyncio.create_subprocess_exec("python", r""+app_path, parameter,
                                                    stdout=sys.stdout, stderr=sys.stderr)
                # p = Popen([r"python", r"D:\anderson.morais\Documents\dev\sportingbet4\app.py"], stdout=sys.stdout, stderr=sys.stderr, bufsize=1, universal_newlines=True, stdin=PIPE)
        
            sleep(20)
            first_time = False
        except KeyboardInterrupt:
            print('saindo...')
            exit()
        except Exception as e:
            print('tentando matar o processo anterior')
            try:
                if proc:
                    Popen(f"taskkill /f /pid {proc.pid}")     
                chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                proc = None       
            except KeyboardInterrupt:
                print('saindo...')
                exit()
            except Exception as e:
                print(e) 
asyncio.run(main())

