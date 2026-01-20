import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_transactions_df, update_transaction_category, get_categories, add_transaction
from datetime import datetime
import os

# Page Config
st.set_page_config(page_title="Balance Automático", page_icon="💰", layout="wide")

# Title
st.title("💰 Control de Gastos & Balance (Google Sheets)")
st.caption("Conectado a: BalanceAutomaticoDB")

def get_df():
    return get_transactions_df()

def add_tx(date, amount, desc, source, cat, status):
    add_transaction(date, amount, desc, source, cat, status)

def update_tx(tx_id, cat):
    update_transaction_category(tx_id, cat)


# Sidebar: Actions
st.sidebar.header("Acciones Rápidas")
if st.sidebar.button("🔄 Recargar Datos"):
    st.rerun()

st.sidebar.divider()

# Manually add transaction (Fallback)
st.sidebar.subheader("📝 Agregar Manual")
with st.sidebar.form("manual_add"):
    m_desc = st.text_input("Descripción")
    m_amount = st.number_input("Monto (S/)", min_value=0.0, step=0.5)
    m_source = st.selectbox("Origen", ["Efectivo", "Yape", "BCP", "Otro"])
    m_cat = st.selectbox("Categoría", get_categories())
    m_date = st.date_input("Fecha", datetime.now())
    
    submitted = st.form_submit_button("Guardar Gasto")
    if submitted:
        add_tx(
            m_date.strftime('%Y-%m-%d %H:%M:%S'), 
            m_amount, 
            m_desc, 
            m_source, 
            m_cat, 
            status='verified'
        )
        st.success("Gasto guardado!")
        st.rerun()

# --- Main Content ---

# 1. KPIs
df = get_df()
if not df.empty:
    # Ensure columns exist (for GSheets empty case)
    if 'amount' not in df.columns: df['amount'] = 0
    if 'status' not in df.columns: df['status'] = 'pending_classification'
    
    total_spent = df['amount'].sum()
    pending_tx = df[df['status'] == 'pending_classification'].shape[0]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Gasto Total (Histórico)", f"S/ {total_spent:,.2f}")
    col2.metric("Pendientes de Clasificar", f"{pending_tx}", delta_color="inverse")
    col3.metric("Transacciones", len(df))

    st.divider()

    # 2. Editable Data Table
    st.subheader("📋 Movimientos Recientes")
    st.info("Edita la categoría o descripción directamente en la tabla.")
    
    # Prepare dataframe for editor
    # We allow editing: description, category, status
    # We hide ID but keep it for index
    
    valid_categories = get_categories()
    
    edited_df = st.data_editor(
        df,
        column_config={
            "category": st.column_config.SelectboxColumn(
                "Categoría",
                help="Clasifícalo",
                width="medium",
                options=valid_categories,
                required=True,
            ),
            "amount": st.column_config.NumberColumn(
                "Monto",
                format="S/ %.2f"
            ),
            "status": st.column_config.SelectboxColumn(
                "Estado",
                options=["verified", "pending_classification"],
                disabled=True # Status updates automatically when you change category ideally, but keeping it visible
            )
        },
        disabled=["id", "date", "source"], # Prevent editing generic fields
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="editor"
    )

    # Detect changes
    # Streamlit data_editor returns the state. We need to check if categories changed.
    # This acts as a 'bulk update' when the user is done editing.
    # Note: st.data_editor updates state instantly but we need to persist to DB.
    # A simple button to "Save Changes" is often safer for SQL consistency than auto-save on every cell
    
    if st.button("💾 Guardar Cambios en Tabla"):
        # Iterate and update DB
        # This is a naive implementation comparing the edited_df with DB relies on ID
        pass 
        # Actually, st.data_editor lets us see simple diffs if we used experimental features, 
        # but for now let's just use the sidebar or rely on the visual aspect. 
        # A true sync requires comparing rows.
        
        # Let's try an 'Auto-Save' approach on the backend? 
        # For simplicity in this v1: We iterate the edited_df and update the DB for *all* rows 
        # (or just check diffs if performance matters, but for personal finance < 10k rows is fine)
        
        progress_text = "Actualizando base de datos..."
        my_bar = st.progress(0, text=progress_text)
        
        for index, row in edited_df.iterrows():
            # Update each row
            # We assume ID is present and correct
            if 'id' in row:
                update_tx(row['id'], row['category'])
            
        my_bar.progress(100, text="Actualizado completo!")
        st.success("Datos sincronizados.")
        st.rerun()

    st.divider()

    # 3. Analytics
    st.subheader("📊 Análisis de Gastos")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Por Categoría**")
        cat_sum = df.groupby("category")["amount"].sum().reset_index()
        fig_pie = px.pie(cat_sum, values='amount', names='category', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.markdown("**Evolución Diaria**")
        # Convert date to datetime just in case
        df['date_dt'] = pd.to_datetime(df['date'])
        daily_sum = df.groupby(df['date_dt'].dt.date)["amount"].sum().reset_index()
        fig_bar = px.bar(daily_sum, x='date_dt', y='amount', title="Gastos por Día")
        st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.warning("No hay datos aún. Usa el formulario de la izquierda o espera a que lleguen correos.")
