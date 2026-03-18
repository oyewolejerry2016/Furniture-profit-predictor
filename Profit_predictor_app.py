# app.py
import streamlit as st
import pandas as pd
import numpy as np
import joblib

# ── Page Config ─────────────────────────────────────────────────────
st.set_page_config(
    page_title='Profit Predictor',
    page_icon='📊',
    layout='wide'
)

# ── Load Model and Encoder ──────────────────────────────────────────
@st.cache_resource
def load_model():
    model = joblib.load('profit_prediction_model.pkl')
    le = joblib.load('label_encoder.pkl')
    return model, le

model, le = load_model()

# ── Feature Engineering ─────────────────────────────────────────────
def engineer_features(df):
    df = df.copy()
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    df['Ship_Date'] = pd.to_datetime(df['Ship_Date'])
    df['Order_Year'] = df['Order_Date'].dt.year
    df['Order_Month'] = df['Order_Date'].dt.month
    df['Order_DayOfWeek'] = df['Order_Date'].dt.dayofweek
    df['Quarter'] = df['Order_Month'].apply(lambda x: (x-1)//3 + 1)
    df['Shipping_Days'] = (df['Ship_Date'] - df['Order_Date']).dt.days
    df['Revenue_Per_Unit'] = df['Sales'] / df['Quantity']
    df['Discount_Amount'] = df['Sales'] * df['Discount']
    df['Sales_Per_Shipping_Day'] = df['Sales'] / (df['Shipping_Days'] + 1)
    df['Is_Discounted'] = (df['Discount'] > 0).astype(int)
    df = df.drop(columns=['Order_Date', 'Ship_Date'])
    return df

# ── Encoding ────────────────────────────────────────────────────────
def encode_features(df):
    df = df.copy()
    cat_cols = ['Ship_Mode', 'Segment', 'State', 'Region', 'Category', 'Sub_Category']
    for col in cat_cols:
        df[col] = le.fit_transform(df[col])
    return df

# ── Drop Unused ──────────────────────────────────────────────────────
def drop_unused(df):
    cols_to_drop = [
        'Row_ID', 'Order_ID', 'Customer_ID', 'Customer_Name',
        'Product_ID', 'Product_Name', 'Country', 'City', 'Postal_Code',
        'Category', 'Segment', 'Quarter', 'Order_Year',
        'Order_DayOfWeek', 'Ship_Mode', 'State'
    ]
    cols_to_drop = [c for c in cols_to_drop if c in df.columns]
    return df.drop(columns=cols_to_drop)

# ── Predict ──────────────────────────────────────────────────────────
def predict_profit(order):
    df = pd.DataFrame([order])
    df = engineer_features(df)
    df = encode_features(df)
    df = drop_unused(df)
    predicted_profit = model.predict(df)[0]
    margin = (predicted_profit / order['Sales']) * 100
    if predicted_profit > 0:
        status = 'Profitable'
        color = 'green'
    else:
        status = 'Loss Making'
        color = 'red'
    return round(float(predicted_profit), 2), round(float(margin), 2), status, color

# ── UI ───────────────────────────────────────────────────────────────
st.title('📊 Furniture Profit Predictor')
st.markdown('Predict whether a new order will be **profitable or loss making** before it is processed.')
st.divider()

# Two columns layout
col1, col2 = st.columns(2)

with col1:
    st.subheader('📦 Order Details')
    
    order_date = st.date_input('Order Date')
    ship_date = st.date_input('Ship Date')
    ship_mode = st.selectbox('Ship Mode', ['Standard Class', 'Second Class', 'First Class', 'Same Day'])
    segment = st.selectbox('Segment', ['Consumer', 'Corporate', 'Home Office'])
    region = st.selectbox('Region', ['West', 'East', 'Central', 'South'])

with col2:
    st.subheader('🪑 Product Details')
    
    state = st.selectbox('State', sorted([
        'Alabama', 'Arizona', 'Arkansas', 'California', 'Colorado',
        'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Idaho',
        'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky',
        'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan',
        'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska',
        'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
        'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
        'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
        'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia',
        'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'
    ]))
    sub_category = st.selectbox('Sub Category', ['Chairs', 'Tables', 'Bookcases', 'Furnishings'])
    sales = st.number_input('Sales Amount ($)', min_value=0.0, value=250.0, step=10.0)
    quantity = st.number_input('Quantity', min_value=1, value=1, step=1)
    discount = st.slider('Discount', min_value=0.0, max_value=0.8, value=0.0, step=0.01,
                         format='%.2f')

st.divider()

# Predict button
if st.button('🔍 Predict Profit', use_container_width=True):
    
    order = {
        'Order_Date': str(order_date),
        'Ship_Date': str(ship_date),
        'Ship_Mode': ship_mode,
        'Segment': segment,
        'State': state,
        'Region': region,
        'Category': 'Furniture',
        'Sub_Category': sub_category,
        'Sales': sales,
        'Quantity': quantity,
        'Discount': discount
    }

    predicted_profit, margin, status, color = predict_profit(order)

    st.divider()
    st.subheader('📈 Prediction Results')

    # Metrics row
    m1, m2, m3 = st.columns(3)
    m1.metric('Predicted Profit', f'${predicted_profit:,.2f}')
    m2.metric('Profit Margin', f'{margin:.2f}%')
    m3.metric('Status', status)

    # Color coded result
    if color == 'green':
        st.success(f'✅ This order is predicted to be **profitable** with a margin of {margin:.2f}%')
    else:
        st.error(f'🚨 This order is predicted to be **loss making** with a margin of {margin:.2f}%. Consider reducing the discount or reviewing the pricing.')