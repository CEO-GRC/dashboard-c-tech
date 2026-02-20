import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="Fintech Analytics | SLA & Excel", layout="wide")

st.title("🏗️ Dashboard de Recaudación: SLA & Collections")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("Sube tu reporte de Aging (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = [str(c).strip() for c in df.columns]

    def limpiar_dinero(serie):
        return pd.to_numeric(
            serie.astype(str).str.replace('$', '').str.replace(',', '').str.strip(), 
            errors='coerce'
        ).fillna(0)

    col_total = next((c for c in df.columns if "Total AR" in c), None)
    col_customer = 'Customer'
    col_terms = 'Terms'
    col_current = 'Current'

    if col_total and col_current:
        try:
            df[col_total] = limpiar_dinero(df[col_total])
            df[col_current] = limpiar_dinero(df[col_current])
            df['Past_Due_Total'] = df[col_total] - df[col_current]

            total_cartera = df[col_total].sum()
            total_corriente = df[col_current].sum()
            total_vencido = total_cartera - total_corriente
            
            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Cartera (AR)", f"${total_cartera:,.2f}")
            c2.metric("Total Corriente", f"${total_corriente:,.2f}")
            c3.metric("Total Vencido (Past Due)", f"${total_vencido:,.2f}")

            st.markdown("---")

            # --- SECCIÓN DE SLA CON BOTÓN DE EXCEL ---
            st.header("🎯 Priority Action List (SLA - 100% Touch Goal)")
            
            # Filtramos solo cuentas con deuda real
            df_sla = df[df['Past_Due_Total'] > 0.01].copy()
            df_sla = df_sla.sort_values(by='Past_Due_Total', ascending=False)
            
            # Seleccionamos las columnas para el reporte del agente
            reporte_agente = df_sla[[col_customer, 'Past_Due_Total', col_terms, col_total]]

            # --- LÓGICA PARA DESCARGAR EN EXCEL ---
            def to_excel(df):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Lista_de_Cobro')
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel(reporte_agente)

            # Botón de descarga
            st.download_button(
                label="📥 Descargar Lista de Cobro (Excel)",
                data=excel_data,
                file_name=f'SLA_Cobros_{pd.Timestamp.now().strftime("%Y-%m-%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )

            st.dataframe(reporte_agente, use_container_width=True, hide_index=True)
            st.info(f"💡 Tienes {len(df_sla)} cuentas para gestionar esta semana.")
            
            # --- GRÁFICO ---
            st.markdown("---")
            st.subheader("Distribución de Mora por Tiempo")
            # ... (tu código de buckets que ya funcionaba) ...
            buckets_map = {'1-30 Days': next((c for c in df.columns if "1-30" in c), None), '31-60 Days': next((c for c in df.columns if "31-60" in c), None), '61-90 Days': next((c for c in df.columns if "61-90" in c), None), '91-120 Days': next((c for c in df.columns if "91-120" in c), None), '121+ Days': [c for c in df.columns if any(x in c for x in ["121", "181", "> 365"])]}
            data_buckets = []
            for nombre, col in buckets_map.items():
                if isinstance(col, list): valor = sum([limpiar_dinero(df[c]).sum() for c in col])
                elif col: valor = limpiar_dinero(df[col]).sum()
                else: valor = 0
                data_buckets.append({'Rango': nombre, 'Monto': valor})
            
            fig = px.bar(pd.DataFrame(data_buckets), x='Rango', y='Monto', color='Rango')
            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("No se encontraron columnas necesarias.")
else:
    st.info("Favor subir el archivo Excel para procesar los datos.")