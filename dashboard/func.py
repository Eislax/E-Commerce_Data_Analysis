import folium
from folium.plugins import HeatMap
from streamlit_folium import folium_static  
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

class DataAnalyzer:
    def __init__(self, df):
        self.df = df

    def create_daily_orders_df(self):
        daily_orders_df = self.df.resample(rule='D', on='order_approved_at').agg({
            "order_id": "nunique",
            "payment_value": "sum"
        })
        daily_orders_df = daily_orders_df.reset_index()
        daily_orders_df.rename(columns={
            "order_id": "order_count",
            "payment_value": "revenue"
        }, inplace=True)
        
        return daily_orders_df
    
    def create_monthly_orders_df(self):
        monthly_orders_df = self.df.resample(rule='M', on='order_approved_at').agg({
            "order_id": "nunique",
        }).reset_index()
        
        monthly_orders_df.rename(columns={
            "order_id": "order_count",
        }, inplace=True)
        
        monthly_orders_df['month_year'] = monthly_orders_df['order_approved_at'].dt.strftime('%b %Y')
        monthly_orders_df = monthly_orders_df.sort_values('order_approved_at')
        
        return monthly_orders_df

    def create_sum_order_items_df(self):
        sum_order_items_df = self.df.groupby("product_category_name_english")["product_id"].count().reset_index()
        sum_order_items_df.rename(columns={
            "product_id": "products_count"
        }, inplace=True)
        sum_order_items_df = sum_order_items_df.sort_values(by='products_count', ascending=False)

        return sum_order_items_df

    def review_score_df(self):
        review_scores = self.df['review_score'].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        most_common_score = review_scores.idxmax()
        # colors = ["#B0C4DE", "#A0B6D8", "#8FA9D1", "#6E94C9", "#3A71B4"]
        return review_scores, most_common_score



    def create_byState_df(self):
        bystate_df = self.df.groupby(by="customer_state").customer_id.nunique().reset_index()
        bystate_df.rename(columns={
            "customer_id": "customer_count"
        }, inplace=True)
        most_common_state = bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']
        bystate_df = bystate_df.sort_values(by='customer_count', ascending=False)

        return bystate_df, most_common_state
    
    def create_byCity_df(self):
        bycity_df = self.df.groupby(by="customer_city").customer_id.nunique().reset_index()
        bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
        
        most_common_city = bycity_df.loc[bycity_df['customer_count'].idxmax(), 'customer_city']
        bycity_df = bycity_df.sort_values(by='customer_count', ascending=False).head(10)  # Ambil 10 kota dengan customer terbanyak

        return bycity_df, most_common_city

    def create_order_status(self):
        order_status_df = self.df["order_status"].value_counts().sort_values(ascending=False)
        most_common_status = order_status_df.idxmax()

        return order_status_df, most_common_status
    
    def compute_rfm(self):
        reference_date = self.df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
        rfm_df = self.df.groupby('customer_unique_id').agg({
            'order_purchase_timestamp': lambda x: (reference_date - x.max()).days,
            'order_id': 'count',
            'price': 'sum'
        }).rename(columns={
            'order_purchase_timestamp': 'Recency',
            'order_id': 'Frequency',
            'price': 'Monetary'
        })
        
        rfm_df['R_Score'] = pd.qcut(rfm_df['Recency'], q=5, labels=[5, 4, 3, 2, 1]).astype(int)
        rfm_df['F_Score'] = pd.qcut(rfm_df['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        rfm_df['M_Score'] = pd.qcut(rfm_df['Monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
        
        rfm_df['RFM_Score'] = rfm_df['R_Score'] + rfm_df['F_Score'] + rfm_df['M_Score']
        
        def segment_customer(rfm_score):
            if rfm_score >= 12:
                return 'Best Customer'
            elif 9 <= rfm_score < 12:
                return 'Loyal Customer'
            elif 7 <= rfm_score < 9:
                return 'Potential Loyalist'
            elif 5 <= rfm_score < 7:
                return 'At Risk'
            else:
                return 'Lost Customer'
        
        rfm_df['Customer_Segment'] = rfm_df['RFM_Score'].apply(segment_customer)
        
        return rfm_df
    
    
class HeatMapPlotter:
    def __init__(self, geolocation_df, customers_df, st):
        self.geolocation_df = geolocation_df
        self.customers_df = customers_df
        self.st = st

    def plot(self):
        gp_silver = self.geolocation_df.groupby(['geolocation_zip_code_prefix'])[['geolocation_lat', 'geolocation_lng']].median().reset_index()
        customers_silver = self.customers_df.merge(gp_silver, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='inner')
        heat_data = customers_silver[['geolocation_lat', 'geolocation_lng']].values.tolist()
        m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
        HeatMap(heat_data, radius=10).add_to(m)
        folium_static(m)
