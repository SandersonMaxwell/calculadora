import streamlit as st
import pandas as pd
import io
from datetime import datetime

# =============================
# CONFIGURAÇÃO
# =============================
st.set_page_config(page_title="Calculadora", page_icon="🧮", layout="wide")
st.title("💸 Calculadora de Cashback e Relatórios")

abas = st.tabs(["📊 Cashback", "🎯 Relatório Detalhado"])

# =============================
# FUNÇÕES AUXILIARES
# =============================
def converter_numero(valor):
    if pd.isna(valor):
        return 0
    v = str(valor).strip().replace(" ", "")
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

def formatar_data(data):
    if pd.isna(data):
        return "-"
    return data.strftime("%d-%m-%Y")

def mostrar_lucro(lucro):
    if lucro > 0:
        return f"💰 <span style='color:green;'>Lucro do jogador: {formatar_brl(lucro)}</span>"
    elif lucro < 0:
        return f"💸 <span style='color:red;'>Prejuízo do jogador: {formatar_brl(lucro)}</span>"
    else:
        return f"⚖️ <span style='color:gray;'>Sem lucro ou prejuízo</span>"

# =============================
# ABA 1 - CASHBACK (INALTERADA)
# =============================
with abas[0]:
    st.info("📊 Aba de Cashback mantida separada conforme solicitado.")

# =============================
# ABA 2 - RELATÓRIO DETALHADO
# =============================
with abas[1]:
    st.header("🎯 Relatório Detalhado do Jogador")

    col_a, col_b = st.columns(2)

    with col_a:
        file_rodadas = st.file_uploader("🎰 CSV de Rodadas", type=["csv"], key="rodadas")

    with col_b:
        file_transacoes = st.file_uploader("💳 CSV de Transações", type=["csv"], key="transacoes")

    if file_rodadas and file_transacoes:
        try:
            # =============================
            # LEITURA DOS CSVs
            # =============================
            raw_r = file_rodadas.read().decode("utf-8")
            sep_r = "," if raw_r.count(",") > raw_r.count(";") else ";"
            df_r = pd.read_csv(io.StringIO(raw_r), sep=sep_r)

            raw_t = file_transacoes.read().decode("utf-8")
            sep_t = "," if raw_t.count(",") > raw_t.count(";") else ";"
            df_t = pd.read_csv(io.StringIO(raw_t), sep=sep_t)

            # =============================
            # ID DO JOGADOR
            # =============================
            if "Client" in df_r.columns:
                player_id = df_r["Client"].iloc[0]
                st.markdown(f"## 🆔 Jogador: `{player_id}`")

            # =============================
            # MAPEAR COLUNAS RODADAS
            # =============================
            col_jogo = next(c for c in df_r.columns if "game" in c.lower() or "nome" in c.lower())
            col_bet = next(c for c in df_r.columns if "bet" in c.lower())
            col_payout = next(c for c in df_r.columns if "payout" in c.lower())
            col_data = next(c for c in df_r.columns if "date" in c.lower() or "creation" in c.lower())
            col_free = next((c for c in df_r.columns if "free" in c.lower()), None)

            df_r[col_bet] = df_r[col_bet].apply(converter_numero)
            df_r[col_payout] = df_r[col_payout].apply(converter_numero)
            df_r[col_data] = pd.to_datetime(df_r[col_data], errors="coerce")

            if col_free:
                df_r["Free Spin"] = df_r[col_free].astype(str).str.lower()
            else:
                df_r["Free Spin"] = "false"

            # =============================
            # MAPEAR COLUNAS TRANSAÇÕES
            # =============================
            col_valor = next(c for c in df_t.columns if "amount" in c.lower() or "valor" in c.lower())
            col_tipo = next(c for c in df_t.columns if "type" in c.lower() or "transaction" in c.lower())
            col_status = next(c for c in df_t.columns if "processing" in c.lower())
            col_data_t = next(c for c in df_t.columns if "date" in c.lower() or "creation" in c.lower())

            df_t[col_valor] = df_t[col_valor].apply(converter_numero)
            df_t[col_tipo] = df_t[col_tipo].astype(str).str.lower()
            df_t[col_status] = df_t[col_status].astype(str).str.upper()
            df_t[col_data_t] = pd.to_datetime(df_t[col_data_t], errors="coerce")

            # =============================
            # FILTRAR TRANSAÇÕES
            # =============================
            df_completas = df_t[df_t[col_status] == "COMPLETED"]
            df_manual = df_t[df_t[col_status] == "MANUAL_APPROVE_REQUIRED"]

            depositos = df_completas[df_completas[col_tipo].str.contains("deposit")][col_valor].sum()
            saques = df_completas[df_completas[col_tipo].str.contains("withdraw")][col_valor].sum()

            # =============================
            # VISÃO GERAL DE RODADAS
            # =============================
            st.divider()
            st.subheader("🎲 Visão Geral das Rodadas")

            total_reais = df_r[df_r["Free Spin"] == "false"]
            total_gratis = df_r[df_r["Free Spin"] == "true"]

            st.write(f"🎰 **Rodadas reais:** {len(total_reais)}")
            st.write(f"🎁 **Rodadas grátis:** {len(total_gratis)}")
            st.write(f"🎯 **Total geral:** {len(df_r)}")

            st.write(f"📅 **Primeira jogada:** {formatar_data(df_r[col_data].min())}")
            st.write(f"📅 **Última jogada:** {formatar_data(df_r[col_data].max())}")

            # =============================
            # RESUMO POR JOGO
            # =============================
            st.divider()
            st.subheader("🎮 Resumo por Jogo")

            resumo = df_r.groupby(col_jogo).agg(
                Rodadas=(col_bet, "count"),
                Apostado=(col_bet, "sum"),
                Payout=(col_payout, "sum")
            ).reset_index()

            for _, row in resumo.iterrows():
                lucro = row["Payout"] - row["Apostado"]
                st.markdown(f"### 🎰 {row[col_jogo]}")
                st.write(f"🎯 Rodadas: {int(row['Rodadas'])}")
                st.write(f"💸 Apostado: {formatar_brl(row['Apostado'])}")
                st.write(f"🏆 Payout: {formatar_brl(row['Payout'])}")
                st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
                st.divider()

            # =============================
            # RESUMO FINANCEIRO
            # =============================
            st.subheader("💳 Resumo Financeiro")

            st.write(f"💰 **Depósitos concluídos:** {formatar_brl(depositos)}")
            st.write(f"🏧 **Saques concluídos:** {formatar_brl(saques)}")

            if not df_manual.empty:
                st.warning(f"⏳ Existem **{len(df_manual)} transações pendentes de aprovação manual**.")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
