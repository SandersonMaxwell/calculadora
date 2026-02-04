import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Calculadora", page_icon="🧮", layout="wide")
st.title("💸 Calculadora de Cashback e Relatórios")

abas = st.tabs(["📊 Cashback", "🎯 Relatório Detalhado"])

# =============================
# FUNÇÕES AUXILIARES
# =============================
def calcular_percentual(qtd_rodadas):
    regras = [
        (25, 59, 0.05), (60, 94, 0.06), (95, 129, 0.07),
        (130, 164, 0.08), (165, 199, 0.09), (200, 234, 0.10),
        (235, 269, 0.11), (270, 304, 0.12), (305, 339, 0.13),
        (340, 374, 0.14), (375, 409, 0.15), (410, 444, 0.16)
    ]
    if qtd_rodadas >= 445:
        return 0.17
    for mn, mx, p in regras:
        if mn <= qtd_rodadas <= mx:
            return p
    return 0

def converter_numero(valor):
    if pd.isna(valor):
        return 0
    v = str(valor).replace(" ", "")
    if "," in v and "." in v:
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")
    try:
        return float(v)
    except:
        return 0

def formatar_brl(valor):
    return f"R${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def carregar_csv(uploaded_file):
    raw = uploaded_file.read().decode("utf-8")
    sep = "," if raw.count(",") > raw.count(";") else ";"
    return pd.read_csv(io.StringIO(raw), sep=sep)

def detectar_colunas(df):
    return {
        "jogo": next((c for c in df.columns if "game" in c.lower() or "nome" in c.lower()), None),
        "bet": next((c for c in df.columns if "bet" in c.lower()), None),
        "payout": next((c for c in df.columns if "payout" in c.lower()), None),
        "data": next((c for c in df.columns if "date" in c.lower() or "creation" in c.lower()), None),
        "free": next((c for c in df.columns if "free" in c.lower()), None),
    }

# =============================
# ABA 1 - CASHBACK (INALTERADA)
# =============================
with abas[0]:
    st.header("📊 Cálculo de Cashback")

    uploaded_file = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="aba1")

    if uploaded_file:
        try:
            df = carregar_csv(uploaded_file)

            if "Client" in df.columns:
                st.markdown(f"### 🆔 ID do Jogador: {df['Client'].iloc[0]}")

            col_bet = next(c for c in df.columns if "bet" in c.lower())
            col_payout = next(c for c in df.columns if "payout" in c.lower())
            col_free = next((c for c in df.columns if "free" in c.lower()), None)

            df[col_bet] = df[col_bet].apply(converter_numero)
            df[col_payout] = df[col_payout].apply(converter_numero)

            if col_free:
                df = df[df[col_free].astype(str).str.lower() == "false"]

            soma_b = df[col_bet].sum()
            soma_p = df[col_payout].sum()
            diff = soma_b - soma_p
            qtd = len(df)
            perc = calcular_percentual(qtd)
            cashback = diff * perc

            st.write(f"Total apostado: {formatar_brl(soma_b)}")
            st.write(f"Total payout: {formatar_brl(soma_p)}")
            st.write(f"Rodadas: {qtd}")
            st.write(f"Percentual: {perc*100:.0f}%")
            st.write(f"Cashback: {formatar_brl(cashback)}")

        except Exception as e:
            st.error(e)

# =============================
# ABA 2 - RELATÓRIO DETALHADO
# =============================
with abas[1]:
    st.header("🎯 Relatório Completo do Jogador")

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

        if "Client" in df_r.columns:
            player_id = df_r["Client"].iloc[0]
        else:
            player_id = "N/A"

        cols = detectar_colunas(df_r)

        df_r[cols["bet"]] = df_r[cols["bet"]].apply(converter_numero)
        df_r[cols["payout"]] = df_r[cols["payout"]].apply(converter_numero)
        df_r[cols["data"]] = pd.to_datetime(df_r[cols["data"]], errors="coerce")

        if cols["free"]:
            df_r["Free Spin"] = df_r[cols["free"]].astype(str).str.lower()
        else:
            df_r["Free Spin"] = "false"

        # -----------------------------
        # TRANSAÇÕES
        # -----------------------------
        col_valor = next(c for c in df_t.columns if "amount" in c.lower() or "valor" in c.lower())
        col_tipo = next(c for c in df_t.columns if "type" in c.lower() or "transaction" in c.lower())
        
        df_t[col_valor] = df_t[col_valor].apply(converter_numero)
        df_t[col_tipo] = df_t[col_tipo].astype(str).str.lower()
        
        depositos = df_t[df_t[col_tipo].str.contains("deposit")][col_valor].sum()
        saques = df_t[df_t[col_tipo].str.contains("withdraw")][col_valor].sum()
        bonus = df_t[df_t[col_tipo].str.contains("bonus")][col_valor].sum()


        # -----------------------------
        # RELATÓRIO
        # -----------------------------
        total_ap = df_r[cols["bet"]].sum()
        total_pay = df_r[cols["payout"]].sum()
        lucro = total_pay - total_ap

        relatorio = f"""
RELATÓRIO DETALHADO DO JOGADOR
=============================

ID DO JOGADOR: {player_id}

1. VISÃO GERAL
-----------------------------
Total de rodadas: {len(df_r)}
Total apostado: {formatar_brl(total_ap)}
Total payout: {formatar_brl(total_pay)}
Resultado do jogador: {formatar_brl(lucro)}

2. RODADAS
-----------------------------
Rodadas reais: {len(df_r[df_r["Free Spin"] == "false"])}
Rodadas grátis: {len(df_r[df_r["Free Spin"] == "true"])}

3. TRANSAÇÕES
-----------------------------
Depósitos: {formatar_brl(depositos)}
Saques: {formatar_brl(saques)}
Bônus: {formatar_brl(bonus)}

4. RESUMO POR JOGO
-----------------------------
"""

        resumo = df_r.groupby(cols["jogo"]).agg(
            Rodadas=(cols["bet"], "count"),
            Apostado=(cols["bet"], "sum"),
            Payout=(cols["payout"], "sum")
        ).reset_index()

        for _, r in resumo.iterrows():
            relatorio += f"""
Jogo: {r[cols["jogo"]]}
- Rodadas: {int(r['Rodadas'])}
- Apostado: {formatar_brl(r['Apostado'])}
- Payout: {formatar_brl(r['Payout'])}
- Resultado: {formatar_brl(r['Payout'] - r['Apostado'])}
"""

        st.text_area("📋 Relatório Final (copiar e colar)", relatorio, height=700)

    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")

