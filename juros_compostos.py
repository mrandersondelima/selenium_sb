numero_dias = 30
greens_ao_dia = 15
porcentagem = 0.0081
banca_inicial = 141.79
banca_final = banca_inicial
qt_greens = 0

valor_final = 0.0

for i in range(numero_dias):
    for j in range(greens_ao_dia):
        qt_greens += 1
        ganho = banca_final * porcentagem
        print(f'dia {i+1}')
        print('green ', qt_greens)
        print(f'Ganho: {ganho:.2f}')
        banca_final += ganho
        print(f'banca {banca_final:.2f}')

        input()

        if banca_final >= banca_inicial * 2:
            print('----------------------')
            


print(banca_final)
print('Lucro: ', banca_final - banca_inicial)