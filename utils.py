class AoAtingirMeta():
    FECHAR_APLICATIVO = 1
    DESLIGAR_COMPUTADOR = 2
    CONTINUAR_APOSTANDO = 3

class TipoValorAposta():
    PORCENTAGEM = 1
    VALOR_ABSOLUTO = 2

class TipoMeta():
    PORCENTAGEM = 1
    VALOR_ABSOLUTO = 2
    SALDO_MAIS_META = 3
    SALDO_MAIS_VALOR = 4
    NUMERO_VITORIAS = 5

class EstiloJogo(): 
    FAVORITO_COM_ODD_MAIOR_IGUAL_2 = 1
    ZEBRA_COM_ODD_MAIOR_IGUAL_2 = 2
    ALEATORIO_COM_ODD_MAIOR_IGUAL_2 = 3
    FAVORITO_COM_ODD_MENOR_1_E_MEIO = 4
    FAVORITO_EMPATE_COM_ODD_MAIOR_IGUAL_2 = 5
    RANDOMICO_ENTRE_JOGO_2_E_5 = 6
    TOTAL_GOLS = 7
    DOIS_GOLS_OU_ABAIXO_1_E_MEIO = 8
    JOGO_UNICO_ODD_ABAIXO_2_MEIO = 9
    JOGO_UNICO_ODD_ACIMA_2_MEIO = 10
    TRES_JOGOS_MAIS_1_5 = 11
    TRES_JOGOS_MAIS_2_5 = 12
    TRES_JOGOS_MENOS_2_5 = 13
    TRES_JOGOS_MAIS_2_5_ANALISE_PARTIDA = 14
    TRES_JOGOS_MENOS_2_5_ANALISE_PARTIDA = 15
    REVEZAMENTO_ENTRE_12_13 = 16
    DOIS_JOGOS_DOIS_OU_TRES_GOLS = 17
    ACIMA_DOIS_MEIO_E_DOIS_GOLS = 18

            
def escreve_em_arquivo(nome_arquivo, valor, tipo_escrita):
    with open(nome_arquivo, tipo_escrita) as f:
        f.write(valor)


def le_de_arquivo(nome_arquivo, tipo):
    with open(nome_arquivo, 'r') as f:
        if tipo == 'int':
            return int( f.read() )
        elif tipo == 'float':
            return float( f.read() )
        elif tipo == 'boolean':
            valor = f.read()
            return True if valor == 'True' else False
        elif tipo == 'string':
            return f.read()
         
