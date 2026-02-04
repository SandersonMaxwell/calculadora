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

def formatar_data_br(dt):
    if pd.isna(dt):
        return "-"
    return dt.strftime("%d/%m/%Y %H:%M")

def carregar_csv(uploaded_file):
    raw = uploaded_file.read().decode("utf-8")
    sep = "," if raw.count(",") > raw.count(";") else ";"
    return pd.read_csv(io.StringIO(raw), sep=sep)

def detectar_colunas_rodadas(df):
    return {
        "jogo": next((c for c in df.columns if any(x in c.lower() for x in ["game", "nome"])), None),
        "bet": next((c for c in df.columns if "bet" in c.lower()), None),
        "payout": next((c for c in df.columns if "payout" in c.lower()), None),
        "data": next((c for c in df.columns if any(x in c.lower() for x in ["date", "creation"])), None),
        "free": next((c for c in df.columns if "free" in c.lower()), None),
    }

def detectar_colunas_transacoes(df):
    col_valor = next((c for c in df.columns if any(x in c.lower() for x in ["amount", "valor", "value", "delta"])), None)
    col_tipo = next((c for c in df.columns if any(x in c.lower() for x in ["type", "operation", "action", "transaction"])), None)
    return col_valor, col_tipo

def classificar_transacao(tipo):
    if any(x in tipo for x in ["deposit", "cash in", "add"]):
        return "deposito"
    if any(x in tipo for x in ["withdraw", "cash out"]):
        return "saque"
    return "outros"

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

            st.write(f"💰 Total apostado: {formatar_brl(soma_b)}")
            st.write(f"🏆 Total payout: {formatar_brl(soma_p)}")
            st.write(f"🎲 Rodadas: {qtd}")
            st.write(f"📈 Percentual: {perc*100:.0f}%")
            st.write(f"💸 Cashback: {formatar_brl(cashback)}")

        except Exception as e:
            st.error(e)

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

        df_r["Free Spin"] = (
            df_r[cols["free"]].astype(str).str.lower()
            if cols["free"] else "false"
        )

        primeira_jogada = df_r[cols["data"]].min()
        ultima_jogada = df_r[cols["data"]].max()

        # ---------- TRANSAÇÕES ----------
        col_valor, col_tipo = detectar_colunas_transacoes(df_t)

        df_t[col_valor] = df_t[col_valor].apply(converter_numero)
        df_t[col_tipo] = df_t[col_tipo].astype(str).str.lower()
        df_t["Categoria"] = df_t[col_tipo].apply(classificar_transacao)

        depositos = df_t[df_t["Categoria"] == "deposito"][col_valor].sum()
        saques = df_t[df_t["Categoria"] == "saque"][col_valor].sum()

        # ---------- RELATÓRIO ----------
        relatorio = f"""
🎯 RELATÓRIO DETALHADO DO JOGADOR
==================================================

🆔 ID DO JOGADOR: {player_id}

🕒 PERÍODO DE ATIVIDADE
--------------------------------------------------
🎰 Primeira jogada ....: {formatar_data_br(primeira_jogada)}
🎰 Última jogada ......: {formatar_data_br(ultima_jogada)}

💳 TRANSAÇÕES FINANCEIRAS
--------------------------------------------------
💰 Depósitos ..........: {formatar_brl(depositos)}
🏧 Saques .............: {formatar_brl(saques)}

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
