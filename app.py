# =============================
# ABA 2 - RELATÓRIO DETALHADO
# =============================
with abas[1]:
    st.header("🎯 Relatório Detalhado do Jogador")

    col1, col2 = st.columns(2)
    with col1:
        csv_rodadas = st.file_uploader("🎰 CSV de Rodadas", type=["csv"])
    with col2:
        csv_transacoes = st.file_uploader("💳 CSV de Transações", type=["csv"])

    if not csv_rodadas or not csv_transacoes:
        st.warning("⚠️ Envie os DOIS arquivos para gerar o relatório.")
        st.stop()

    try:
        df_r = carregar_csv(csv_rodadas)
        df_t = carregar_csv(csv_transacoes)

        player_id = df_r["Client"].iloc[0] if "Client" in df_r.columns else "N/A"

        # ---------- RODADAS ----------
        cols = detectar_colunas_rodadas(df_r)

        df_r[cols["bet"]] = df_r[cols["bet"]].apply(converter_numero)
        df_r[cols["payout"]] = df_r[cols["payout"]].apply(converter_numero)
        df_r[cols["data"]] = pd.to_datetime(df_r[cols["data"]], errors="coerce")

        primeira_jogada = df_r[cols["data"]].min()
        ultima_jogada = df_r[cols["data"]].max()

        # ---------- TRANSAÇÕES ----------
        col_valor, col_tipo = detectar_colunas_transacoes(df_t)
        col_status = next(
            (c for c in df_t.columns if "processing" in c.lower()),
            None
        )

        if not col_status:
            raise Exception("Coluna 'Processing Status' não encontrada no CSV de transações.")

        df_t[col_valor] = df_t[col_valor].apply(converter_numero)
        df_t[col_tipo] = df_t[col_tipo].astype(str).str.lower()
        df_t[col_status] = df_t[col_status].astype(str).str.upper()

        df_t["Categoria"] = df_t[col_tipo].apply(classificar_transacao)

        # COMPLETED
        trans_completas = df_t[
            (df_t[col_status] == "COMPLETED")
        ]

        depositos = trans_completas[
            trans_completas["Categoria"] == "deposito"
        ][col_valor].sum()

        saques = trans_completas[
            trans_completas["Categoria"] == "saque"
        ][col_valor].sum()

        # MANUAL APPROVE REQUIRED
        trans_pendentes = df_t[
            df_t[col_status] == "MANUAL_APPROVE_REQUIRED"
        ]

        dep_pendentes = trans_pendentes[
            trans_pendentes["Categoria"] == "deposito"
        ][col_valor].sum()

        saq_pendentes = trans_pendentes[
            trans_pendentes["Categoria"] == "saque"
        ][col_valor].sum()

        # ---------- RELATÓRIO ----------
        relatorio = f"""
🎯 RELATÓRIO DETALHADO DO JOGADOR
==================================================

🆔 ID DO JOGADOR: {player_id}

🕒 PERÍODO DE ATIVIDADE
--------------------------------------------------
🎰 Primeira jogada ....: {formatar_data_br(primeira_jogada)}
🎰 Última jogada ......: {formatar_data_br(ultima_jogada)}

💳 TRANSAÇÕES FINANCEIRAS (COMPLETAS)
--------------------------------------------------
💰 Depósitos ..........: {formatar_brl(depositos)}
🏧 Saques .............: {formatar_brl(saques)}

⚠️ TRANSAÇÕES PENDENTES (MANUAL APPROVE REQUIRED)
--------------------------------------------------
💰 Depósitos pendentes : {formatar_brl(dep_pendentes)}
🏧 Saques pendentes ..: {formatar_brl(saq_pendentes)}

🎮 RESUMO POR JOGO
==================================================
"""

        resumo = df_r.groupby(cols["jogo"]).agg(
            Rodadas=(cols["bet"], "count"),
            Apostado=(cols["bet"], "sum"),
            Payout=(cols["payout"], "sum")
        ).reset_index()

        for _, r in resumo.iterrows():
            resultado = r["Payout"] - r["Apostado"]

            relatorio += f"""
🎰 JOGO: {r[cols["jogo"]]}
--------------------------------------------------
🎲 Rodadas ..........: {int(r['Rodadas'])}
💰 Apostado .........: {formatar_brl(r['Apostado'])}
🏆 Payout ...........: {formatar_brl(r['Payout'])}
📊 Resultado ........: {formatar_brl(resultado)}
"""

        st.text_area("📋 Relatório Final (copiar e colar)", relatorio, height=800)

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")
