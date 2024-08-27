import pickle

matches_and_options = dict()

try: 
    with open('matches_and_options.pkl', 'rb') as fp:
        matches_and_options = pickle.load(fp)
    matches_and_options.clear()

    with open('matches_and_options.pkl', 'wb') as fp:
        pickle.dump(matches_and_options, fp)   
except:
    print('erro ao ler arquivo')