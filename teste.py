import json

betslip = json.load( open('betslip_data_test.json'))

# print(betslip['betslip']['bets'])

datas = ['2025-01-14T12:30:00Z', '2025-01-15T12:30:00Z', '2025-01-14T13:30:00Z', '2025-01-14T16:30:00Z']

# print( list( sorted( datas ) ))

datas = []

print( sorted( map( lambda e: e['fixture']['date'], betslip['betslip']['bets'] ))[0] )

# for bet in betslip['betslip']['bets']:
#     print( bet['fixture']['date'] )
#     datas.append( bet['fixture']['date'] )