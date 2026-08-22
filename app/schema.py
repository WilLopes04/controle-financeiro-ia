def inicializar_banco(conexao):
    """
    Cria a estrutura necessária no banco selecionado.
    CREATE TABLE IF NOT EXISTS não apaga nem altera dados existentes.
    """

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo_conta TEXT NOT NULL,
            tipo_movimento TEXT NOT NULL,
            categoria TEXT NOT NULL,
            forma_pagamento TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            parcela_atual INTEGER DEFAULT 1,
            total_parcelas INTEGER DEFAULT 1,
            id_compra TEXT
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS cartoes (
            nome TEXT PRIMARY KEY,
            dia_vencimento INTEGER NOT NULL,
            dia_fechamento INTEGER NOT NULL
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS regras (
            padrao TEXT PRIMARY KEY,
            tipo_conta TEXT NOT NULL,
            categoria TEXT
        )
    """)
