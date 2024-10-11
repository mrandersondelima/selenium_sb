from datetime import datetime
import pathlib
from subprocess import PIPE, Popen, TimeoutExpired
from time import sleep
import sys
import os
import signal
import asyncio
import psutil

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
    print('processo pai: ', os.getpid() )
    proc = None
    teste = 0
    while True:
        try:
            teste = True
            last_time_check = None
            try:
                last_time_check = le_de_arquivo('last_time_check.txt', 'string')    
            except:
                print('tentando matar o processo anterior')
                try:
                    Popen(f"taskkill /f /pid {proc.pid}")     
                    chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                    #p = psutil.Process(chrome_process_id)
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                    # for p in p.children(recursive=True):
                    #     print(p.pid)
                    #     Popen(f'taskkill /f /pid {p.pid}')                           
                except Exception as e:
                    print(e)
            
            last_time_check_datetime = datetime.strptime( last_time_check, '%Y-%m-%d %H:%M' )
            

            if not proc:
                proc = await asyncio.create_subprocess_exec("python", r"D:\anderson.morais\Documents\dev\sportingbet4\app.py",
                                                    stdout=sys.stdout, stderr=sys.stderr)       

            diferenca_tempo = datetime.now() - last_time_check_datetime

            if diferenca_tempo.total_seconds() >= 5 * 60:
                print('tentando matar o processo anterior')
                try:
                    Popen(f"taskkill /f /pid {proc.pid}")     
                    chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                    #p = psutil.Process(chrome_process_id)
                    Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                    # for p in p.children(recursive=True):
                    #     print(p.pid)
                    #     Popen(f'taskkill /f /pid {p.pid}')                           
                except Exception as e:
                    print(e)    

                sleep(10)

                proc = await asyncio.create_subprocess_exec("python", r"D:\anderson.morais\Documents\dev\sportingbet4\app.py",
                                                    stdout=sys.stdout, stderr=sys.stderr)
                # p = Popen([r"python", r"D:\anderson.morais\Documents\dev\sportingbet4\app.py"], stdout=sys.stdout, stderr=sys.stderr, bufsize=1, universal_newlines=True, stdin=PIPE)
            
            print('esperando...')
            sleep(2 * 60)    
        except:
            print('tentando matar o processo anterior')
            try:
                Popen(f"taskkill /f /pid {proc.pid}")     
                chrome_process_id = le_de_arquivo('chrome_process_id.txt', 'int')
                #p = psutil.Process(chrome_process_id)
                Popen(f"taskkill /f /pid {chrome_process_id} /t")     
                # for p in p.children(recursive=True):
                #     print(p.pid)
                #     Popen(f'taskkill /f /pid {p.pid}')                           
            except Exception as e:
                print(e) 
asyncio.run(main())

