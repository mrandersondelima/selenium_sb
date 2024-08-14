def calcula_dutching( array_odds, meta ):

    array_valores = [ 0.0 for x in array_odds ]

    if meta == 0:
        array_valores = [ 0.1 for x in array_odds ]
        return array_valores

    valor_gasto_na_aposta = 0.00

    algum_abaixo = True

    while algum_abaixo:
        algum_abaixo = False
        for i in range( len(array_odds) ):
            if array_valores[i] * array_odds[i] < meta + valor_gasto_na_aposta:
                algum_abaixo = True
                array_valores[i] += 0.01
                valor_gasto_na_aposta += 0.01

       # print( array_valores )
    
    array_valores = [ float( f'{x:.2f}' ) for x in array_valores]


    return array_valores


if __name__ == '__main__':
    array = calcula_dutching( [ 3.37, 7.48, 6.62 ], 5 )     
    print( array )
    print( sum( array ))
