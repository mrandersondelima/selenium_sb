import pickle

matches_and_options = dict()
fixture_id_to_betslip = dict()

try: 
    with open('matches_and_options.pkl', 'rb') as fp:
        matches_and_options = pickle.load(fp)
    matches_and_options.clear()

    with open('fixture_id_to_betslip.pkl', 'rb') as fp:
        fixture_id_to_betslip = pickle.load(fp)
    fixture_id_to_betslip.clear()

    with open('matches_and_options.pkl', 'wb') as fp:
        pickle.dump(matches_and_options, fp)   

    with open('fixture_id_to_betslip.pkl', 'wb') as fp:
        pickle.dump(fixture_id_to_betslip, fp)  
except:
    print('erro ao ler arquivo')