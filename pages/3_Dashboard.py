import streamlit as st
import pandas as pd
import plotly.express as px
import json
import numpy as np

st.set_page_config(page_title="Dashboard Banjir 2024", layout="wide")

# =====================
# 📥 LOAD DATA
# =====================
df = pd.read_csv("banjir.csv")

# Load GeoJSON untuk wilayah dan kecamatan
with open("jakarta_geojson.json", "r", encoding="utf-8") as f:
    jakarta_geo = json.load(f)

with open("kecamatan_geojson.json", "r", encoding="utf-8") as f:
    geojson_kecamatan = json.load(f)

# =====================
# 🎛️ SIDEBAR FILTER
# =====================
st.sidebar.header("Filter Global")

# Wilayah
wilayah_opsi = ["Semua Wilayah"] + sorted(df["wilayah_adm"].dropna().unique())
selected_wilayah = st.sidebar.selectbox("Pilih Wilayah Administratif", wilayah_opsi)

# Bulan
bulan_order = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
               'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
bulan_opsi = ["Semua Bulan"] + bulan_order
selected_bulan = st.sidebar.selectbox("Pilih Bulan", bulan_opsi)

# Terapkan filter
df_filtered = df.copy()
if selected_wilayah != "Semua Wilayah":
    df_filtered = df_filtered[df_filtered["wilayah_adm"] == selected_wilayah]
if selected_bulan != "Semua Bulan":
    df_filtered = df_filtered[df_filtered["bulan"] == selected_bulan]

# =====================
# 📊 GRAFIK 1: BULAN & TRIWULAN
# =====================
st.subheader("📅 Kejadian Banjir per Bulan dan Triwulan Tahun 2024")

df_filtered['bulan'] = pd.Categorical(df_filtered['bulan'], categories=bulan_order, ordered=True)

# Bulanan
agg_bulan = df_filtered.groupby('bulan', observed=False)['jumlah_kejadian'].sum().reset_index()

# Tambahan: hover detail wilayah
wilayah_bulan = df_filtered.groupby(['bulan', 'wilayah_adm'], observed=False)['jumlah_kejadian'].sum().reset_index()
def format_hover(bulan):
    rows = wilayah_bulan[wilayah_bulan['bulan'] == bulan]
    total = agg_bulan[agg_bulan['bulan'] == bulan]['jumlah_kejadian'].values[0]
    teks = f"Bulan {bulan}: {total} kejadian"
    for _, row in rows.iterrows():
        teks += f"<br>{row['wilayah_adm']}: {int(row['jumlah_kejadian'])}"
    return teks

agg_bulan['custom_hover'] = agg_bulan['bulan'].apply(format_hover)

fig_bulan = px.line(agg_bulan, x='bulan', y='jumlah_kejadian', markers=True,
                    labels={'jumlah_kejadian': 'Jumlah Kejadian', 'bulan': 'Bulan'})
fig_bulan.update_traces(
    line=dict(color='teal', width=3),
    hovertemplate='%{customdata[0]}<extra></extra>',
    customdata=agg_bulan[['custom_hover']].values
)
fig_bulan.update_layout(title='Jumlah Kejadian Banjir per Bulan',
                        template='plotly_white', height=350,
                        xaxis_tickangle=-45)

# Triwulan
agg_triwulan = df_filtered.groupby('triwulan')['jumlah_kejadian'].sum().reset_index()
fig_triwulan = px.line(agg_triwulan, x='triwulan', y='jumlah_kejadian', markers=True,
                       labels={'jumlah_kejadian': 'Jumlah Kejadian', 'triwulan': 'Triwulan'})
fig_triwulan.update_traces(line=dict(color='steelblue', width=3))
fig_triwulan.update_layout(title='Jumlah Kejadian Banjir per Triwulan',
                           template='plotly_white', height=350)

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_bulan, use_container_width=True)
with col2:
    st.plotly_chart(fig_triwulan, use_container_width=True)

# =====================
# 🌍 GRAFIK 2: PETA PERSEBARAN
# =====================
st.subheader("🗺️ Peta Persebaran Kejadian Banjir di DKI Jakarta Tahun 2024")

# Peta Wilayah
with open("jakarta_geojson.json", "r", encoding="utf-8") as f:
    jakarta_geo = json.load(f)

# --- Peta Wilayah ---
agg_wilayah = df_filtered.groupby('wilayah_adm')['jumlah_kejadian'].sum().reset_index()
agg_wilayah['wilayah_adm'] = agg_wilayah['wilayah_adm'].str.title()

fig_wilayah = px.choropleth(
    agg_wilayah,
    geojson=jakarta_geo,
    locations='wilayah_adm',
    featureidkey='properties.province',
    color='jumlah_kejadian',
    color_continuous_scale="OrRd",
    labels={'jumlah_kejadian': 'Jumlah Kejadian'},
    height=350
)
fig_wilayah.update_geos(fitbounds="locations", visible=False)
fig_wilayah.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, title="Sebaran Kejadian Banjir per Wilayah")

# --- Peta Kecamatan ---
df_filtered['kecamatan'] = df_filtered['kecamatan'].str.upper()
agg_kecamatan_map = df_filtered.groupby('kecamatan')['jumlah_kejadian'].sum().reset_index()
agg_kecamatan_map.columns = ['name', 'jumlah_kejadian']

geo_kecamatan = [f['properties']['name'] for f in geojson_kecamatan['features']]
geo_df = pd.DataFrame({'name': geo_kecamatan})

full_data = geo_df.merge(agg_kecamatan_map, on='name', how='left')
full_data['jumlah_kejadian'] = full_data['jumlah_kejadian'].fillna(0)

fig_kecamatan = px.choropleth(
    full_data,
    geojson=geojson_kecamatan,
    locations='name',
    featureidkey='properties.name',
    color='jumlah_kejadian',
    color_continuous_scale='OrRd',
    labels={'jumlah_kejadian': 'Jumlah Kejadian'},
    height=350
)
fig_kecamatan.update_geos(fitbounds="locations", visible=False)
fig_kecamatan.update_layout(margin={"r":0,"t":30,"l":0,"b":0}, title="Sebaran Kejadian Banjir per Kecamatan")

# Tampilkan sejajar
col_map1, col_map2 = st.columns(2)
with col_map1:
    st.plotly_chart(fig_wilayah, use_container_width=True)
with col_map2:
    st.plotly_chart(fig_kecamatan, use_container_width=True)

# =====================
# 📍 GRAFIK 3: 10 KECAMATAN / KELURAHAN
# =====================
st.subheader("📍 10 Wilayah dengan Kejadian Banjir Terbanyak")

opsi = st.selectbox("Pilih Tingkat Wilayah", ["Kecamatan", "Kelurahan"])

if opsi == "Kecamatan":
    agg = df_filtered.groupby(['kecamatan', 'wilayah_adm'])['jumlah_kejadian'].sum().reset_index()
    agg['label'] = agg['kecamatan'] + ', ' + agg['wilayah_adm']
    top10 = agg.sort_values(by='jumlah_kejadian', ascending=False).head(10)
    fig_bar = px.bar(top10, x='jumlah_kejadian', y='kecamatan', orientation='h',
                     color='jumlah_kejadian', color_continuous_scale='Blues',
                     labels={'jumlah_kejadian': 'Jumlah Kejadian', 'kecamatan': 'Kecamatan'})
    fig_bar.update_layout(title='10 Kecamatan dengan Kejadian Banjir Terbanyak',
                          template='plotly_white', height=350,
                          yaxis={'categoryorder': 'total ascending'})
else:
    df_filtered['kelurahan'] = df_filtered['kelurahan'].str.title()
    agg = df_filtered.groupby(['kelurahan', 'kecamatan', 'wilayah_adm'])['jumlah_kejadian'].sum().reset_index()
    agg['label'] = agg['kelurahan'] + ', ' + agg['kecamatan'] + ', ' + agg['wilayah_adm']
    top10 = agg.sort_values(by='jumlah_kejadian', ascending=False).head(10)
    fig_bar = px.bar(top10, x='jumlah_kejadian', y='kelurahan', orientation='h',
                     color='jumlah_kejadian', color_continuous_scale='Blues',
                     labels={'jumlah_kejadian': 'Jumlah Kejadian', 'kelurahan': 'Kelurahan'})
    fig_bar.update_layout(title='10 Kelurahan dengan Kejadian Banjir Terbanyak',
                          template='plotly_white', height=350,
                          yaxis={'categoryorder': 'total ascending'})

st.plotly_chart(fig_bar, use_container_width=True)

# =====================
# 🌊 GRAFIK 4: Tinggi Air Rata-rata dan Maksimum
# =====================
import numpy as np  # pastikan numpy sudah di-import jika belum

st.subheader("🌊 10 Wilayah dengan Rata-Rata Tinggi Air Tertinggi")

# Pilih tingkat wilayah (gunakan key unik!)
opsi_tinggi = st.selectbox("Pilih Tingkat Wilayah", ["Kecamatan", "Kelurahan"], key="tinggi_air_opsi")

# Pembulatan khusus tinggi air
def pembulatan_tinggi(x):
    desimal = round(x, 1)
    desimal_digit = int(str(desimal).split('.')[-1][0])
    if 1 <= desimal_digit <= 5:
        return int(np.floor(desimal))
    elif 6 <= desimal_digit <= 9:
        return int(np.ceil(desimal))
    else:
        return int(desimal)

if opsi_tinggi == "Kecamatan":
    # Siapkan label gabungan
    df_filtered['kecamatan'] = df_filtered['kecamatan'].str.title()
    df_filtered['wilayah_adm'] = df_filtered['wilayah_adm'].str.title()
    df_filtered['kecamatan_wilayah'] = df_filtered['kecamatan'] + ', ' + df_filtered['wilayah_adm']

    # Agregasi
    agg_kec = df_filtered.groupby(['kecamatan', 'wilayah_adm', 'kecamatan_wilayah']).agg({
        'tinggi_air_avg': 'mean',
        'tinggi_air_max': 'mean'
    }).reset_index()

    # Bulatkan hasil
    agg_kec['tinggi_air_avg_bulat'] = agg_kec['tinggi_air_avg'].apply(pembulatan_tinggi)
    agg_kec['tinggi_air_max_bulat'] = agg_kec['tinggi_air_max'].apply(pembulatan_tinggi)

    # Ambil top 10
    top10 = agg_kec.sort_values(by='tinggi_air_avg_bulat', ascending=False).head(10)

    # Plot
    fig = px.bar(
        top10,
        x='tinggi_air_avg_bulat',
        y='kecamatan',
        orientation='h',
        labels={'tinggi_air_avg_bulat': 'Tinggi Air Rata-rata (cm)', 'kecamatan': 'Kecamatan'},
        color='tinggi_air_avg_bulat',
        color_continuous_scale='Reds',
        hover_name='kecamatan_wilayah',
        hover_data={'tinggi_air_max_bulat': True}
    )
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>'
                      'Tinggi Air Rata-rata (cm): %{x}<br>'
                      'Tinggi Air Maksimum (cm): %{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        title='10 Kecamatan dengan Rata-Rata Tinggi Air Tertinggi',
        yaxis={'categoryorder': 'total ascending'},
        height=350,
        template='plotly_white',
        xaxis_title='Tinggi Air Rata-rata (cm)',
        yaxis_title='Kecamatan'
    )

else:
    # Kelurahan
    df_filtered['kelurahan'] = df_filtered['kelurahan'].str.title()
    df_filtered['kecamatan'] = df_filtered['kecamatan'].str.title()
    df_filtered['wilayah_adm'] = df_filtered['wilayah_adm'].str.title()
    df_filtered['kelurahan_kecamatan_wilayah'] = (
        df_filtered['kelurahan'] + ', ' + df_filtered['kecamatan'] + ', ' + df_filtered['wilayah_adm']
    )

    agg_kel = df_filtered.groupby(['kelurahan', 'kecamatan', 'wilayah_adm', 'kelurahan_kecamatan_wilayah']).agg({
        'tinggi_air_avg': 'mean',
        'tinggi_air_max': 'mean'
    }).reset_index()

    agg_kel['tinggi_air_avg_bulat'] = agg_kel['tinggi_air_avg'].apply(pembulatan_tinggi)
    agg_kel['tinggi_air_max_bulat'] = agg_kel['tinggi_air_max'].apply(pembulatan_tinggi)
    top10 = agg_kel.sort_values(by='tinggi_air_avg_bulat', ascending=False).head(10)

    fig = px.bar(
        top10,
        x='tinggi_air_avg_bulat',
        y='kelurahan',
        orientation='h',
        labels={'tinggi_air_avg_bulat': 'Tinggi Air Rata-Rata (cm)', 'kelurahan': 'Kelurahan'},
        color='tinggi_air_avg_bulat',
        color_continuous_scale='Reds',
        hover_name='kelurahan_kecamatan_wilayah',
        hover_data={'tinggi_air_max_bulat': True}
    )
    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>'
                      'Tinggi Air Rata-rata (cm): %{x}<br>'
                      'Tinggi Air Maksimum (cm): %{customdata[0]}<extra></extra>'
    )
    fig.update_layout(
        title='10 Kelurahan dengan Rata-rata Tinggi Air Tertinggi',
        yaxis={'categoryorder': 'total ascending'},
        height=350,
        template='plotly_white',
        xaxis_title='Tinggi Air Rata-rata (cm)',
        yaxis_title='Kelurahan'
    )
st.plotly_chart(fig, use_container_width=True)

# =====================
# 🧭 GRAFIK 5: Jumlah Pengungsi per Wilayah (Pie Chart)
# =====================
st.subheader("🧭 Distribusi Jumlah Pengungsi per Wilayah")

# Pastikan data bersih dan terstruktur
df_filtered['wilayah_adm'] = df_filtered['wilayah_adm'].str.title()
df_filtered['bulan'] = df_filtered['bulan'].str.title()

bulan_order = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]
df_filtered['bulan'] = pd.Categorical(df_filtered['bulan'], categories=bulan_order, ordered=True)

# Total per wilayah
evakuasi_summary = (
    df_filtered
    .groupby('wilayah_adm')[['jumlah_pengungsi', 'jumlah_tempat_pengungsian']]
    .sum()
    .reset_index()
)

# Detail bulanan per wilayah
bulanan = (
    df_filtered
    .groupby(['wilayah_adm', 'bulan'], observed=True)[['jumlah_pengungsi', 'jumlah_tempat_pengungsian']]
    .sum()
    .reset_index()
)

# Hover info format
def format_hover(wilayah):
    total = evakuasi_summary[evakuasi_summary['wilayah_adm'] == wilayah].iloc[0]
    isi = f"Wilayah: {wilayah}<br>Jumlah Pengungsi: {int(total['jumlah_pengungsi'])}<br>Jumlah Tempat Pengungsian: {int(total['jumlah_tempat_pengungsian'])}"
    
    data_bulanan = bulanan[bulanan['wilayah_adm'] == wilayah]
    for _, row in data_bulanan.iterrows():
        if row['jumlah_pengungsi'] > 0 or row['jumlah_tempat_pengungsian'] > 0:
            isi += f"<br>{row['bulan']}:<br>Pengungsi: {int(row['jumlah_pengungsi'])}<br>Tempat: {int(row['jumlah_tempat_pengungsian'])}"
    return isi

evakuasi_summary['hover_text'] = evakuasi_summary['wilayah_adm'].apply(format_hover)
evakuasi_summary = evakuasi_summary.sort_values('jumlah_pengungsi', ascending=False)

# Pie chart
fig = px.pie(
    evakuasi_summary,
    names='wilayah_adm',
    values='jumlah_pengungsi',
    color_discrete_sequence=['#1f3b57', '#295173', '#3d6c8d', '#5486a8', '#6da1c3'],
    hover_data={'hover_text': True}
)
fig.update_traces(
    hovertemplate='%{customdata[0]}<extra></extra>',
    customdata=evakuasi_summary[['hover_text']].values,
    textinfo='percent+label'
)
fig.update_layout(
    height=350,
    template='plotly_white',
    showlegend=True
)
st.plotly_chart(fig, use_container_width=True)

# =====================
# 🧍‍♂️ GRAFIK 6: Top 10 Kecamatan/Kelurahan dengan Jumlah Pengungsi Tertinggi
# =====================
st.subheader("🧍‍♂️ 10 Wilayah dengan Jumlah Pengungsi Tertinggi")

# Dropdown untuk memilih tingkat wilayah
opsi_level = st.selectbox("Pilih Tingkat Wilayah", ["Kecamatan", "Kelurahan"], key="top_pengungsi_level")

# Preprocessing
df_filtered['kelurahan'] = df_filtered['kelurahan'].str.title()
df_filtered['kecamatan'] = df_filtered['kecamatan'].str.title()
df_filtered['wilayah_adm'] = df_filtered['wilayah_adm'].str.title()
df_filtered['bulan'] = df_filtered['bulan'].str.title()

bulan_order = [
    'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
    'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
]
df_filtered['bulan'] = pd.Categorical(df_filtered['bulan'], categories=bulan_order, ordered=True)

# ====== Kecamatan Mode ======
if opsi_level == "Kecamatan":
    total_kecamatan = (
        df_filtered
        .groupby(['kecamatan', 'wilayah_adm'], observed=True)['jumlah_pengungsi']
        .sum()
        .reset_index()
    )
    top10_kec = total_kecamatan.sort_values('jumlah_pengungsi', ascending=False).head(10)

    # Ambil baris kejadian dengan jumlah pengungsi tertinggi di tiap kecamatan
    kejadian_tertinggi = df_filtered[df_filtered['kecamatan'].isin(top10_kec['kecamatan'])]
    idx_max = kejadian_tertinggi.groupby('kecamatan')['jumlah_pengungsi'].idxmax()
    data_max = kejadian_tertinggi.loc[idx_max][[
        'kecamatan', 'wilayah_adm', 'bulan', 'jumlah_pengungsi', 'jumlah_tempat_pengungsian'
    ]].rename(columns={
        'bulan': 'bulan_kejadian_tertinggi',
        'jumlah_pengungsi': 'jumlah_pengungsi_tertinggi',
        'jumlah_tempat_pengungsian': 'jumlah_tempat_pengungsian_kejadian_tertinggi'
    })

    df_plot = top10_kec.merge(data_max, on=['kecamatan', 'wilayah_adm'], how='left')
    df_plot['hover_text'] = df_plot.apply(
        lambda row: f"{row['kecamatan']}, {row['wilayah_adm']}<br>"
                    f"Bulan Kejadian (Pengungsi Tertinggi): {row['bulan_kejadian_tertinggi']}<br>"
                    f"Jumlah Pengungsi Tertinggi: {int(row['jumlah_pengungsi_tertinggi'])}<br>"
                    f"Jumlah Tempat Pengungsian: {int(row['jumlah_tempat_pengungsian_kejadian_tertinggi'])}",
        axis=1
    )

    fig = px.bar(
        df_plot,
        x='kecamatan',
        y='jumlah_pengungsi',
        color='jumlah_pengungsi',
        color_continuous_scale='Greens',
        title='10 Kecamatan dengan Jumlah Pengungsi Tertinggi',
        labels={
            'kecamatan': 'Kecamatan',
            'jumlah_pengungsi': 'Total Jumlah Pengungsi'
        },
        hover_data={
            'hover_text': True,
            'jumlah_pengungsi': False,
            'kecamatan': False
        }
    )

# ====== Kelurahan Mode ======
else:
    total_kelurahan = (
        df_filtered
        .groupby(['kelurahan', 'kecamatan', 'wilayah_adm'], observed=True)['jumlah_pengungsi']
        .sum()
        .reset_index()
    )
    top10_kel = total_kelurahan.sort_values('jumlah_pengungsi', ascending=False).head(10)

    kejadian_tertinggi = df_filtered[df_filtered['kelurahan'].isin(top10_kel['kelurahan'])]
    idx_max = kejadian_tertinggi.groupby('kelurahan')['jumlah_pengungsi'].idxmax()
    data_max = kejadian_tertinggi.loc[idx_max][[
        'kelurahan', 'kecamatan', 'wilayah_adm', 'bulan', 'jumlah_pengungsi', 'jumlah_tempat_pengungsian'
    ]].rename(columns={
        'bulan': 'bulan_kejadian_tertinggi',
        'jumlah_pengungsi': 'jumlah_pengungsi_tertinggi',
        'jumlah_tempat_pengungsian': 'jumlah_tempat_pengungsian_kejadian_tertinggi'
    })

    df_plot = top10_kel.merge(data_max, on=['kelurahan', 'kecamatan', 'wilayah_adm'], how='left')
    df_plot['hover_text'] = df_plot.apply(
        lambda row: f"{row['kelurahan']}, {row['kecamatan']}, {row['wilayah_adm']}<br>"
                    f"Bulan Kejadian (Pengungsi Tertinggi): {row['bulan_kejadian_tertinggi']}<br>"
                    f"Jumlah Pengungsi Tertinggi: {int(row['jumlah_pengungsi_tertinggi'])}<br>"
                    f"Jumlah Tempat Pengungsian: {int(row['jumlah_tempat_pengungsian_kejadian_tertinggi'])}",
        axis=1
    )

    fig = px.bar(
        df_plot,
        x='kelurahan',
        y='jumlah_pengungsi',
        color='jumlah_pengungsi',
        color_continuous_scale='Greens',
        title='10 Kelurahan dengan Jumlah Pengungsi Tertinggi',
        labels={
            'kelurahan': 'Kelurahan',
            'jumlah_pengungsi': 'Total Jumlah Pengungsi'
        },
        hover_data={
            'hover_text': True,
            'jumlah_pengungsi': False,
            'kelurahan': False
        }
    )

# =====================
# Finalisasi Grafik
# =====================
fig.update_traces(
    hovertemplate='%{customdata[0]}<extra></extra>'
)
fig.update_layout(
    height=350,
    template='plotly_white',
    xaxis_tickangle=-30,
    xaxis_title='Wilayah',
    yaxis_title='Total Jumlah Pengungsi',
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Arial")
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("📌 Perbandingan Jumlah Tempat Pengungsian dengan Jumlah Pengungsi")

fig3 = px.scatter(
    df_filtered,  # gunakan df_filtered agar sesuai dengan filter global
    x='jumlah_tempat_pengungsian',
    y='jumlah_pengungsi',
    color='wilayah_adm',
    labels={
        'jumlah_tempat_pengungsian': 'Jumlah Tempat Pengungsian',
        'jumlah_pengungsi': 'Jumlah Pengungsi',
        'wilayah_adm': 'Wilayah'
    },
    hover_data=['kecamatan', 'kelurahan', 'bulan']  # tambahkan 'bulan' ke dalam hover_data
)

fig3.update_layout(
    template='plotly_white',
    height=350,  # ubah tinggi jadi 350
    font=dict(family='Arial', size=12),
    hoverlabel=dict(font_size=12, font_family='Arial'),
)
st.plotly_chart(fig3, use_container_width=True)