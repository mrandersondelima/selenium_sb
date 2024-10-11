import pickle
import json

matches_and_options = dict()
fixture_id_to_betslip = dict()
times_favoritos = []

def save_array_on_disk(nome_arquivo, array):        
    with open(nome_arquivo, "w") as fp:
        json.dump(array, fp)

try: 
    with open('times_favoritos.json', 'wb') as fp:
        save_array_on_disk('times_favoritos.json', times_favoritos)

    with open('matches_and_options.pkl', 'wb') as fp:
        pickle.dump(matches_and_options, fp)   

    with open('fixture_id_to_betslip.pkl', 'wb') as fp:
        pickle.dump(fixture_id_to_betslip, fp)  
except:
    print('erro ao ler arquivo')