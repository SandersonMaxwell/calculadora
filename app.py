import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Calculadora", page_icon="🧮", layout="wide")
st.title("💸 Calculadora de Cashback e Análise de Jogadas de Cassino")

abas = st.tabs(["📊 Cashback", "🎯 Analise Cassino"])

# =============================
# FUNÇÕES AUXILIARES
# =============================
def calcular_percentual(qtd_rodadas):
    regras = [
        (25, 59, 0.05),
        (60, 94, 0.06),
        (95, 129, 0.07),
        (130, 164, 0.08),
        (165, 199, 0.09),
        (200, 234, 0.10),
        (235, 269, 0.11),
        (270, 304, 0.12),
        (305, 339, 0.13),
        (340, 374, 0.14),
        (375, 409, 0.15),
        (410, 444, 0.16),
    ]
    if qtd_rodadas >= 445:
        return 0.17
    for (min_r, max_r, perc) in regras:
        if min_r <= qtd_rodadas <= max_r:
            return perc
    return 0

def converter_numero(valor):
    if pd.isna(valor):
        return 0
    v = str(valor).strip().replace(' ', '')
    if ',' in v and '.' in v:
        v = v.replace('.', '').replace(',', '.')
    elif ',' in v:
        v = v.replace(',', '.')
    try:
        return float(v)
    except:
        return 0

def formatar_brl(valor):
    return f"R${valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def mostrar_lucro(lucro):
    if lucro > 0:
        return f"💰 <span style='color:green;'>Lucro do jogador: {formatar_brl(lucro)}</span>"
    elif lucro < 0:
        return f"💸 <span style='color:red;'>Prejuízo do jogador: {formatar_brl(lucro)}</span>"
    else:
        return f"⚖️ <span style='color:gray;'>Sem lucro ou prejuízo</span>"

# =============================
# ABA 1 - CASHBACK
# =============================
with abas[0]:
    st.header("📊 Cálculo de Cashback")

    uploaded_file = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="aba1")

    if uploaded_file:
        try:
            raw = uploaded_file.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            
            # -----------------------------
            # ID do jogador
            # -----------------------------
            if "Client" in df.columns:
                player_id = df["Client"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")


            coluna_bet = next((c for c in df.columns if 'bet' in c.lower()), None)
            coluna_payout = next((c for c in df.columns if 'payout' in c.lower()), None)
            coluna_free = next((c for c in df.columns if 'free' in c.lower()), None)
            coluna_jogo = next((c for c in df.columns if 'game' in c.lower() or 'nome' in c.lower()), None)

            if not coluna_bet or not coluna_payout:
                st.error("❌ Não foi possível identificar as colunas 'Bet' e 'Payout'. Verifique o CSV.")
                st.stop()

            df[coluna_bet] = df[coluna_bet].apply(converter_numero)
            df[coluna_payout] = df[coluna_payout].apply(converter_numero)

            
            df_reais = df.copy()

            # ⚠️ CÁLCULO DO CASHBACK (visão da casa)
            soma_b = df_reais[coluna_bet].sum()
            soma_c = df_reais[coluna_payout].sum()
            diferenca = soma_b - soma_c  # apostado - payout
            qtd_rodadas = len(df_reais)
            percentual = calcular_percentual(qtd_rodadas)
            resultado_final = diferenca * percentual

            # EXIBIÇÃO
            st.subheader("📈 Resultados Gerais")
            st.write(f"**Total apostado:** {formatar_brl(soma_b)}")
            st.write(f"**Total ganho (payout):** {formatar_brl(soma_c)}")

            # mostra lucro para a casa (sem inverter aqui)
            if diferenca > 0:
                st.markdown(f"🏦 <span style='color:green;'>Lucro da casa: {formatar_brl(diferenca)}</span>", unsafe_allow_html=True)
            elif diferenca < 0:
                st.markdown(f"💸 <span style='color:red;'>Prejuízo da casa: {formatar_brl(diferenca)}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"⚖️ <span style='color:gray;'>Sem lucro ou prejuízo</span>", unsafe_allow_html=True)

            st.write(f"**Número de rodadas:** {qtd_rodadas}")
            st.write(f"**Percentual aplicado:** {percentual * 100:.0f}%")
            st.write(f"**Valor de cashback:** {formatar_brl(resultado_final)}")

            # REGRAS DE ELEGIBILIDADE
            if qtd_rodadas < 25 or percentual < 0.05 or resultado_final < 10 or diferenca <= 0:
                st.warning("❌ O jogador **não tem direito a receber cashback**.")
                motivos = []
                if qtd_rodadas < 25:
                    motivos.append(f"rodadas insuficientes ({qtd_rodadas})")
                if percentual < 0.05:
                    motivos.append(f"percentual aplicado menor que 5% ({percentual*100:.0f}%)")
                if resultado_final < 10:
                    motivos.append(f"valor final menor que 10 ({formatar_brl(resultado_final)})")
                if diferenca <= 0:
                    motivos.append("jogador teve lucro (sem perdas para cashback)")
                st.info("Motivo(s): " + ", ".join(motivos))
            else:
                st.success(f"✅ O jogador deve receber **{formatar_brl(resultado_final)}** em cashback!")

            # RESUMO POR JOGO (aqui visão do jogador)
            if coluna_jogo:
                st.divider()
                st.subheader("🎮 Resumo por Jogo (Rodadas Reais)")
                resumo_jogos = df_reais.groupby(coluna_jogo).agg(
                    Total_Apostado=(coluna_bet, 'sum'),
                    Total_Payout=(coluna_payout, 'sum'),
                    Rodadas=(coluna_bet, 'count')
                ).reset_index()

                for _, linha in resumo_jogos.iterrows():
                    st.markdown(f"#### 🎯 {linha[coluna_jogo]}")
                    st.write(f"📊 Total de rodadas: {int(linha['Rodadas'])}")
                    st.write(f"💰 Total apostado: {formatar_brl(linha['Total_Apostado'])}")
                    st.write(f"🏆 Total ganho (payout): {formatar_brl(linha['Total_Payout'])}")
                    lucro = linha['Total_Payout'] - linha['Total_Apostado']  # visão do jogador
                    st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
                    st.divider()

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")

# =============================
# ABA 2 - RESUMO DETALHADO
# =============================
with abas[1]:
    st.header("🎯 Resumo Detalhado por Jogo")

    uploaded_file2 = st.file_uploader("Envie o arquivo CSV do jogador", type=["csv"], key="detalhado")

    if uploaded_file2:
        try:
            raw = uploaded_file2.read().decode("utf-8")
            sep = ',' if raw.count(',') > raw.count(';') else ';'
            df = pd.read_csv(io.StringIO(raw), sep=sep)

            # Normalizar colunas: remover espaços e BOM
            df.columns = df.columns.str.strip().str.replace('\ufeff','')

            if "Client" in df.columns:
                player_id = df["Client"].iloc[0]
                st.markdown(f"### 🆔 ID do Jogador: {player_id}")

            # localizar colunas
            coluna_jogo = next((c for c in df.columns if 'game' in c.lower() or 'nome' in c.lower()), None)
            coluna_bet = next((c for c in df.columns if 'bet' in c.lower()), None)
            coluna_payout = next((c for c in df.columns if 'payout' in c.lower()), None)
            coluna_data = next((c for c in df.columns if 'creation' in c.lower() or 'date' in c.lower()), None)
            coluna_free = next((c for c in df.columns if 'free' in c.lower()), None)

            if not all([coluna_jogo, coluna_bet, coluna_payout, coluna_data]):
                st.error("❌ O CSV precisa conter as colunas 'Game Name', 'Bet', 'Payout' e 'Creation Date'.")
                st.stop()

            # conversões
            df[coluna_bet] = df[coluna_bet].apply(converter_numero)
            df[coluna_payout] = df[coluna_payout].apply(converter_numero)
            df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')

            if coluna_free:
                df['Free Spin'] = df[coluna_free].astype(str).str.lower()
            else:
                df['Free Spin'] = 'false'

            # -----------------------------
            # FILTROS DE DATA E HORA
            # -----------------------------
            st.markdown("### 📅 Filtro por Data e Hora (intervalo)")

            data_min = df[coluna_data].min()
            data_max = df[coluna_data].max()

            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input(
                    "📆 Data inicial",
                    value=data_min.date(),
                    min_value=data_min.date(),
                    max_value=data_max.date()
                )
                hora_inicio = st.time_input("🕓 Hora inicial", value=data_min.time())
            with col2:
                data_fim = st.date_input(
                    "📆 Data final",
                    value=data_max.date(),
                    min_value=data_min.date(),
                    max_value=data_max.date()
                )
                hora_fim = st.time_input("🕕 Hora final", value=data_max.time())

            dt_inicio = datetime.combine(data_inicio, hora_inicio)
            dt_fim = datetime.combine(data_fim, hora_fim)

            # aplica filtro
            df = df[(df[coluna_data] >= dt_inicio) & (df[coluna_data] <= dt_fim)]

            # -----------------------------
            # EXIBIÇÃO POR JOGO
            # -----------------------------
            jogos = df[coluna_jogo].unique()

            for jogo in jogos:
                st.markdown(f"### 🎮 {jogo}")

                for status in ['false', 'true']:
                    tipo = "Rodadas Reais" if status == 'false' else "Rodadas Gratuitas"
                    subset = df[(df[coluna_jogo] == jogo) & (df['Free Spin'] == status)]

                    if not subset.empty:
                        total_rodadas = len(subset)
                        total_apostado = subset[coluna_bet].sum()
                        total_payout = subset[coluna_payout].sum()
                        lucro = total_payout - total_apostado

                        primeira_data = subset[coluna_data].min().strftime("%d/%m/%Y %H:%M")
                        ultima_data = subset[coluna_data].max().strftime("%d/%m/%Y %H:%M")

                        st.markdown(f"#### 🎯 {tipo}")
                        st.write(f"**Total de rodadas:** {total_rodadas}")
                        st.write(f"**Total apostado:** {formatar_brl(total_apostado)}")
                        st.write(f"**Total ganho (payout):** {formatar_brl(total_payout)}")
                        st.markdown(mostrar_lucro(lucro), unsafe_allow_html=True)
                        st.write(f"**Primeira rodada:** {primeira_data}")
                        st.write(f"**Última rodada:** {ultima_data}")
                        st.divider()

            # -----------------------------
            # CALCULAR LUCRO TOTAL DO JOGADOR
            # -----------------------------
            lucro_total = df[coluna_payout].sum() - df[coluna_bet].sum()
            st.markdown(f"## 💰 Lucro total do jogador: {formatar_brl(lucro_total)}", unsafe_allow_html=True)

            # -----------------------------
            # TOTAL DE RODADAS REAIS E GRÁTIS
            # -----------------------------
            total_reais = len(df[df['Free Spin'] == 'false'])
            total_gratis = len(df[df['Free Spin'] == 'true'])
            total_geral = total_reais + total_gratis

            st.markdown("## 🎲 Totais Gerais")
            st.write(f"🧮 **Total de rodadas reais:** {total_reais}")
            st.write(f"🎁 **Total de rodadas grátis:** {total_gratis}")
            st.write(f"🎯 **Total geral de rodadas:** {total_geral}")

            # -----------------------------
            # NOVA SEÇÃO: CSV DE TRANSAÇÕES
            # -----------------------------
            st.markdown("---")
            st.header("🏦 Resumo Financeiro (Depósitos e Saques)")

            uploaded_file3 = st.file_uploader(
                "Envie o arquivo CSV de transações (Operation, Amount, Processing Status, Created At)",
                type=["csv"],
                key="financeiro"
            )

            if uploaded_file3:
                try:
                    raw2 = uploaded_file3.read().decode("utf-8")
                    sep2 = ',' if raw2.count(',') > raw2.count(';') else ';'
                    df_fin = pd.read_csv(io.StringIO(raw2), sep=sep2)

                    # Normalizar colunas: remover espaços, BOM e minúsculas
                    df_fin.columns = df_fin.columns.str.strip().str.replace('\ufeff','').str.lower()

                    # localizar colunas
                    col_op = next((c for c in df_fin.columns if 'operation' in c), None)
                    col_val = next((c for c in df_fin.columns if 'amount' in c), None)
                    col_data2 = next((c for c in df_fin.columns if 'created at' in c), None)
                    col_status = next((c for c in df_fin.columns if 'status' in c), None)

                    if not all([col_op, col_val, col_data2, col_status]):
                        st.error("❌ O CSV precisa conter as colunas 'Operation', 'Amount', 'Processing Status' e 'Created At'.")
                        st.stop()

                    # conversões
                    df_fin[col_val] = df_fin[col_val].apply(converter_numero)
                    df_fin[col_data2] = pd.to_datetime(df_fin[col_data2], errors='coerce')

                    # manter apenas transações concluídas
                    df_fin = df_fin[df_fin[col_status].astype(str).str.upper() == "COMPLETED"]

                    # aplicar o mesmo filtro de data/hora
                    df_fin = df_fin[(df_fin[col_data2] >= dt_inicio) & (df_fin[col_data2] <= dt_fim)]

                    # identificar depósitos e saques
                    df_fin['Operation'] = df_fin[col_op].astype(str).str.lower()
                    depositos = df_fin[df_fin['Operation'].str.contains("deposit", case=False, na=False)]
                    saques = df_fin[df_fin['Operation'].str.contains("withdraw", case=False, na=False)]

                    total_deposito = depositos[col_val].sum()
                    total_saque = saques[col_val].sum()
                    lucro_mais_deposito = lucro_total + total_deposito

                    st.markdown("### 💵 Totais Financeiros (filtrados pelo intervalo de data/hora)")
                    st.write(f"💰 **Total depositado:** {formatar_brl(total_deposito)}")
                    st.write(f"📈 **Lucro + Depósito:** {formatar_brl(lucro_mais_deposito)}")
                    st.write(f"💸 **Total sacado:** {formatar_brl(total_saque)}")

                    if len(df_fin) == 0:
                        st.info("Nenhuma transação encontrada dentro do período selecionado.")

                except Exception as e:
                    st.error(f"Ocorreu um erro ao processar o CSV de transações: {e}")

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
