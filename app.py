import streamlit as st
import pandas as pd

st.title("💼 Sistema de Conciliación de Facturas")

TOLERANCIA = 1.0

archivo = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if archivo is not None:
    st.success("Archivo cargado correctamente")

    facturas = pd.read_excel(archivo, sheet_name='Facturas')
    depositos = pd.read_excel(archivo, sheet_name='Depositos')

    facturas.columns = facturas.columns.str.strip()
    depositos.columns = depositos.columns.str.strip()

    facturas['Fecha factura'] = pd.to_datetime(facturas['Fecha factura'])
    depositos['Fecha depósito'] = pd.to_datetime(depositos['Fecha depósito'])

    facturas['Importe'] = pd.to_numeric(facturas['Importe'], errors='coerce')
    depositos['Importe'] = pd.to_numeric(depositos['Importe'], errors='coerce')

    facturas['Mes'] = facturas['Fecha factura'].dt.to_period('M')
    depositos['Mes'] = depositos['Fecha depósito'].dt.to_period('M')

    facturas['Fecha de Pago'] = 'Pendiente'
    facturas_pagadas = set()

    if st.button("🚀 Conciliar"):
        resumen = []

        for mes in facturas['Mes'].unique():
            dep_mes = depositos[depositos['Mes'] == mes].sort_values('Fecha depósito')

            for _, deposito in dep_mes.iterrows():
                monto = deposito['Importe']
                fecha = deposito['Fecha depósito']

                facs = facturas[
                    (facturas['Mes'] == mes) &
                    (~facturas.index.isin(facturas_pagadas)) &
                    (facturas['Fecha factura'] <= fecha)
                ].sort_values('Fecha factura')

                suma = 0
                usados = []

                for idx, row in facs.iterrows():
                    suma += row['Importe']
                    usados.append(idx)

                    if suma >= monto - TOLERANCIA:
                        break

                if usados:
                    for idx in usados:
                        facturas.at[idx, 'Fecha de Pago'] = fecha.strftime('%d/%m/%Y')
                        facturas_pagadas.add(idx)

                    resumen.append([fecha, monto, suma, "OK"])
                else:
                    resumen.append([fecha, monto, 0, "SIN MATCH"])

        st.success("✅ Conciliación completada")
        st.dataframe(facturas)

        output = "resultado.xlsx"
        facturas.to_excel(output, index=False)

        with open(output, "rb") as f:
            st.download_button("⬇️ Descargar resultado", f, file_name=output)
