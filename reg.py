import re

#qualquer palavra sub que pode ter um hífen ou não, seguido de um ou mais números

teste = 'R$ 4,23'

# print( re.sub(r"\d", '', teste ) )

numeros = re.findall( r"\d+", teste )

print( f'{numeros[0]}.{numeros[1]}' )

#print( re.findall(r"sub-*\d+|reserv.*|femin.*|u-*\d+|women", "feminio".lower()) )

#print( re.findall(r"sub-*\d+", "Sub-23".lower()) )