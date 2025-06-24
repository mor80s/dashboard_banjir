import streamlit as st
import pandas as pd

st.title("Halaman DataFrame")
st.write("Halaman ini menampilkan informasi sumber data serta data banjir yang telah melalui proses pembersihan (cleaning).")

st.markdown("""
Visualisasi ini menggunakan data yang bersumber dari [Satu Data Jakarta](https://satudata.jakarta.go.id), yaitu platform yang menyediakan berbagai jenis data publik, mulai dari open data, data sektoral, data statistik, hingga data spasial.  

Dataset yang digunakan berisi informasi mengenai kejadian banjir di wilayah Provinsi DKI Jakarta tahun 2024, yang mencakup lokasi terdampak, waktu kejadian, serta dampaknya terhadap masyarakat.  

🔗 [Tautan Sumber Dataset](https://satudata.jakarta.go.id/open-data/detail?kategori=dataset&page_url=data-kejadian-bencana-banjir&data_no=1)
""")

df = pd.read_csv("banjir.csv")

st.sidebar.header("🔎 Filter Data")

filter_columns = ['bulan', 'wilayah_adm', 'kecamatan', 'kelurahan']
filtered_df = df.copy()

for col in filter_columns:
    if col in df.columns:
        unique_values = df[col].dropna().unique()
        selected_values = st.sidebar.multiselect(f"Filter kolom '{col}'", sorted(unique_values), default=sorted(unique_values))
        filtered_df = filtered_df[filtered_df[col].isin(selected_values)]

st.dataframe(filtered_df, use_container_width=True)

@st.cache_data
def convert_df(data):
    return data.to_csv(index=False).encode('utf-8')

csv_data = convert_df(filtered_df)

st.download_button(
    label="📥 Download Dataset (Sesuai Filter)",
    data=csv_data,
    file_name='banjir_filtered.csv',
    mime='text/csv'
)