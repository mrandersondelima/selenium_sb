from datetime import datetime
import pathlib
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep
import sys
import os
import signal
import asyncio
import psutil
from credenciais import app_path

def le_de_arquivo(nome_arquivo, tipo):
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
                        #p = psutil.Process(chrome_process_id)
                        Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                        # for p in p.children(recursive=True):
                        #     print(p.pid)
                        #     Popen(f'taskkill /f /pid {p.pid}')          
                        proc = None                   
                    except KeyboardInterrupt:
                        print('saindo...')
                        exit()
                    except Exception as e:
                        print(e)    

                    sleep(5)

                    proc = await asyncio.create_subprocess_exec("python", r""+app_path, parameter,
                                                    stdout=sys.stdout, stderr=sys.stderr)
            except:
                print('tentando matar o processo anterior')
                try:
                    if proc:
                        Popen(f"taskkill /f /pid {proc.pid}")     
                    chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                    #p = psutil.Process(chrome_process_id)
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                    # for p in p.children(recursive=True):
                    #     print(p.pid)
                    #     Popen(f'taskkill /f /pid {p.pid}')        
                    proc = None                   
                except KeyboardInterrupt:
                    print('saindo...')
                    exit()
                except Exception as e:
                    print(e)
            
            if last_time_check == 'erro_aposta':
                last_time_check = datetime.now().strftime( '%Y-%m-%d %H:%M' )

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
                    #p = psutil.Process(chrome_process_id)
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                    # for p in p.children(recursive=True):
                    #     print(p.pid)
                    #     Popen(f'taskkill /f /pid {p.pid}')          
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
        
            sleep(10)
        except KeyboardInterrupt:
            print('saindo...')
            exit()
        except Exception as e:
            print('tentando matar o processo anterior')
            try:
                if proc:
                    Popen(f"taskkill /f /pid {proc.pid}")     
                chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                #p = psutil.Process(chrome_process_id)
                Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                # for p in p.children(recursive=True):
                #     print(p.pid)
                #     Popen(f'taskkill /f /pid {p.pid}')       
                proc = None       
            except KeyboardInterrupt:
                print('saindo...')
                exit()
            except Exception as e:
                print(e) 
asyncio.run(main())

