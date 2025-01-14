import pickle
import json

def save_array_on_disk(nome_arquivo, array):        
    with open(nome_arquivo, "w") as fp:
        json.dump(array, fp)

def escreve_em_arquivo(nome_arquivo, valor, tipo_escrita):
    with open(nome_arquivo, tipo_escrita) as f:
        f.write(valor)

try: 
    with open('times_favoritos.json', 'wb') as fp:
        save_array_on_disk('times_favoritos.json', [])

    escreve_em_arquivo('perda_acumulada.txt','0.0', 'w')

    escreve_em_arquivo('qt_apostas_feitas_txt.txt', '0', 'w')

    escreve_em_arquivo('saldo.txt', '0', 'w')

    escreve_em_arquivo('event_url.txt', '', 'w')

    escreve_em_arquivo('maior_saldo.txt', '0', 'w')

    escreve_em_arquivo('maior_meta_ganho.txt', '0', 'w')

    escreve_em_arquivo('bet_slip_number.txt', '', 'w')

    escreve_em_arquivo('qt_true_bets_made.txt', '0', 'w')

    with open('jogos_inseridos.json', 'wb') as fp:
        save_array_on_disk('jogos_inseridos.json', [])

    with open('available_indexes.json', 'wb') as fp:
        save_array_on_disk('available_indexes.json', [0,1,2,3,4,5,6,7,8,9])

    with open('apostas_paralelas.json', 'wb') as fp:
        save_array_on_disk('apostas_paralelas.json', [5,5,5,5,5,5,5,5,5,5])

    escreve_em_arquivo('gastos.txt', '0.0', 'w')

    escreve_em_arquivo('maior_lucro_pool.txt', '0.0', 'w')

    pool_data = [{"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0, "qt_apostas_feitas": 0}, 
    {"perda_acumulada": 0.0, "qt_apostas_feitas": 0}]

    with open('pool_data.json', 'wb') as fp:
        save_array_on_disk('pool_data.json', pool_data )

    with open('matches_and_options.pkl', 'wb') as fp:
        pickle.dump({}, fp)   

    with open('fixture_id_to_betslip.pkl', 'wb') as fp:
        pickle.dump({}, fp)  

    with open('match_of_interest.pkl', 'wb') as fp:
        pickle.dump({}, fp)

    with open('bets_made.pkl', 'wb') as fp:
        pickle.dump({}, fp)
except:
    print('erro ao ler arquivo')