
jogos_aptos = [{ 'tempo': 1, 'cronometro': 33.444, 'odd': 1 }, 
                { 'tempo': 2, 'cronometro': 33.444, 'odd': 2 }]


jogos_aptos_ordenado = sorted(jogos_aptos, key=lambda el: ( -el['tempo'], el['cronometro'], el['odd']  ) )

print(jogos_aptos_ordenado)