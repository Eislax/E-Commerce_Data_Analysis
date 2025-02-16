import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import seaborn as sns
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static
import urllib
from func import DataAnalyzer, HeatMapPlotter
from babel.numbers import format_currency

# Dataset
datetime_cols = ["order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date", "order_purchase_timestamp", "shipping_limit_date"]
all_df = pd.read_csv("../data/all_data.csv")
all_df.sort_values(by="order_approved_at", inplace=True)
all_df.reset_index(inplace=True)

# Geolocation Dataset
geolocation = pd.read_csv('../data/geolocation.csv')
data = geolocation.drop_duplicates(subset='customer_unique_id')

for col in datetime_cols:
    all_df[col] = pd.to_datetime(all_df[col])

# Sidebar
with st.sidebar:
    st.title("Muhammad Rafi Ilham")
    st.image("e-commerce.jpeg")

# Main
function = DataAnalyzer(all_df)
map_plot = HeatMapPlotter(geolocation, all_df, st)

daily_orders_df = function.create_daily_orders_df()
monthly_orders_df = function.create_monthly_orders_df()
sum_order_items_df = function.create_sum_order_items_df()
review_score, common_score = function.review_score_df()
state, most_common_state = function.create_byState_df()
city, most_common_city = function.create_byCity_df()
order_status, common_status = function.create_order_status()
rfm_df = function.compute_rfm()

st.header("E-Commerce Dashboard :convenience_store:")

# Monthly Orders
st.subheader("Monthly Orders")

col1, col2 = st.columns(2)

with col1:
    total_monthly_order = monthly_orders_df["order_count"].sum()
    st.markdown(f"Total Monthly Orders: **{total_monthly_order}**")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    monthly_orders_df["month_year"], 
    monthly_orders_df["order_count"], 
    marker='o', 
    linewidth=2, 
    color="#068DA9"
)

for i, txt in enumerate(monthly_orders_df["order_count"]):
    ax.annotate(txt, (monthly_orders_df["month_year"][i], monthly_orders_df["order_count"][i]), 
                textcoords="offset points", xytext=(0,5), ha='center', fontsize=10)

ax.set_title("Jumlah Pemesanan per Bulan", fontsize=16)
ax.set_xlabel("Bulan", fontsize=12)
ax.set_ylabel("Jumlah Pemesanan", fontsize=12)
ax.tick_params(axis="x", rotation=45, labelsize=10)
ax.tick_params(axis="y", labelsize=10)
ax.grid(axis='y', linestyle='--', alpha=0.7)

st.pyplot(fig)


# Daily Orders
st.subheader("Daily Orders")

col1, col2 = st.columns(2)

with col1:
    total_order = daily_orders_df["order_count"].sum()
    st.markdown(f"Total Order: **{total_order}**")

with col2:
    total_revenue = format_currency(daily_orders_df["revenue"].sum(), "IDR", locale="id_ID")
    st.markdown(f"Total Revenue: **{total_revenue}**")

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    daily_orders_df["order_approved_at"],
    daily_orders_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
st.pyplot(fig)


# Order Items
st.subheader("Order Items")

top_colors = sns.color_palette("Greens_r", 5)
bottom_colors = sns.color_palette("Reds_r", 5)

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

# Barplot untuk produk paling banyak terjual
sns.barplot(x="products_count", y="product_category_name_english", 
            data=sum_order_items_df.head(5), palette=top_colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Jumlah Produk Terjual")
ax[0].set_title("Produk Paling Banyak Terjual", loc="center", fontsize=18)
ax[0].tick_params(axis='y', labelsize=15)

# Menambahkan angka di atas bar (produk paling banyak terjual)
for p in ax[0].patches:
    ax[0].annotate(f'{p.get_width():,.0f}', 
                (p.get_width(), p.get_y() + p.get_height()/2), 
                ha='left', va='center', fontsize=12)

# Barplot untuk produk paling sedikit terjual
sns.barplot(x="products_count", y="product_category_name_english", 
            data=sum_order_items_df.sort_values(by="products_count", ascending=True).head(5), 
            palette=bottom_colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Jumlah Produk Terjual")
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Produk Paling Sedikit Terjual", loc="center", fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

# Menambahkan angka di atas bar (produk paling sedikit terjual)
for p in ax[1].patches:
    ax[1].annotate(f'{p.get_width():,.0f}', 
                (p.get_width(), p.get_y() + p.get_height()/2), 
                ha='right', va='center', fontsize=12)

plt.suptitle("Total Penjualan Kategori Produk", fontsize=25)
st.pyplot(fig)

# Review Score
st.subheader("Review Score")
col1,col2 = st.columns(2)

with col1:
    avg_review_score = review_score.mean()
    st.markdown(f"Average Review Score: **{avg_review_score:.2f}**")

with col2:
    review_score, most_common_score = function.review_score_df()
    st.markdown(f"Most Common Review Score: **{most_common_score}**")


# Gradasi warna sesuai skala rating
colors = ["#B0C4DE", "#A0B6D8", "#8FA9D1", "#6E94C9", "#3A71B4"]

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(
    x=review_score.index, 
    y=review_score.values, 
    order=[1, 2, 3, 4, 5],
    palette=colors
)

# Menampilkan jumlah review di atas setiap bar
for i, v in enumerate(review_score.values):
    ax.text(i, v + 50, str(v), ha='center', fontsize=12)

plt.title("Distribusi Rating Customer untuk Pelayanan E-Commerce", fontsize=15)
plt.xlabel("Rating", fontsize=12)
plt.ylabel("Jumlah Customer", fontsize=12)
plt.xticks(fontsize=12)
plt.grid(axis='y', linestyle='--', alpha=0.7)

st.pyplot(fig)

# RFM Analysis
st.subheader("Customer Segmentation (RFM Analysis)")

fig, ax = plt.subplots(figsize=(10, 6))
order = ['Best Customer', 'Loyal Customer', 'Potential Loyalist', 'At Risk', 'Lost Customer']
colors = ["#2ECC71", "#1ABC9C", "#F1C40F", "#E67E22", "#E74C3C"]

sns.barplot(
    x=rfm_df['Customer_Segment'].value_counts()[order].index,
    y=rfm_df['Customer_Segment'].value_counts()[order].values,
    palette=colors,
    ax=ax
)

ax.set_title("Distribusi Segmen Pelanggan Berdasarkan RFM Analysis", fontsize=14, fontweight='bold')
ax.set_xlabel("Customer Segment", fontsize=12)
ax.set_ylabel("Number of Customers", fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=20, ha="right")

for p in ax.patches:
    ax.annotate(f'{p.get_height():,.0f}', 
                (p.get_x() + p.get_width() / 2., p.get_height()), 
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='black')

st.pyplot(fig)


# Customer Demographic
st.subheader("Customer Demographic")
tab1, tab2, tab3, tab4 = st.tabs(["State", "City", "Order Status", "Geolocation"])

with tab1:
    most_common_state = state.customer_state.value_counts().index[0]
    st.markdown(f"Most Common State: **{most_common_state}**")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=state['customer_state'], 
                y=state['customer_count'], 
                data=state, 
                palette="Blues_r")
    
    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=10, color='black')
    
    plt.title("Number of Customers from Each State", fontsize=15)
    plt.xlabel("State")
    plt.ylabel("Number of Customers")
    plt.xticks(fontsize=10)
    st.pyplot(fig)

with tab2:  # Pastikan City ada di tab2
    st.markdown(f"Most Common City: **{most_common_city}**")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(x=city['customer_city'], 
                y=city['customer_count'], 
                data=city, 
                palette="Oranges_r")

    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=10, color='black')

    ax.set_title("Number of Customers from Each City", fontsize=15)
    ax.set_xlabel("City", fontsize=12)
    ax.set_ylabel("Number of Customers", fontsize=12)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, fontsize=10)

    st.pyplot(fig)


with tab3:
    common_status_ = order_status.value_counts().index[0]
    st.markdown(f"Most Common Order Status: **{common_status_}**")

    fig, ax = plt.subplots(figsize=(8, 6))
    ax = order_status.plot(kind='bar', color='green')

    for p in ax.patches:
        ax.annotate(f'{int(p.get_height())}', 
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=10, color='black')
    
    plt.title("Order Status", fontsize=15)
    plt.xlabel("Status")
    plt.ylabel("Number of Orders")
    st.pyplot(fig)

with tab4:
    map_plot.plot()

    with st.expander("See Explanation"):
        st.write('Sesuai dengan grafik yang sudah dibuat, Bisa dilihat pesebaran cukup meluas atau banyak di daerah timur hingga tenggara dari keseluruhan peta amerika selatan, terkhusus untuk brazil berarti pesebaran banyak di daerah selatan hingga tenggara. Dengan penyebaran pusatnya berada di sao paulo.')

st.caption('Copyright (C) M Rafi Ilham 2025')
