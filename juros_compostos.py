numero_dias = 300
greens_ao_dia = 15
porcentagem = 0.0267
banca_inicial = 9.36
banca_final = banca_inicial
qt_greens = 0

valor_final = 0.0

for i in range(numero_dias):
    for j in range(greens_ao_dia):
        qt_greens += 1
        ganho = banca_final * porcentagem
        print('green ', qt_greens)
        print('Ganho: ', ganho)
        banca_final += ganho
        print('banca ', banca_final)

        input()

        if banca_final >= banca_inicial * 2:
            print(banca_final)
            print(qt_greens)
            exit()

print(banca_final)
print('Lucro: ', banca_final - banca_inicial)