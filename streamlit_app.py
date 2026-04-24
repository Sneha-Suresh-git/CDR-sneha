import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import PyPDF2
import re
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# MUST BE FIRST
st.set_page_config(
    page_title="CDR Analysis Pro",
    page_icon="📡",
    layout="wide"
)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# Custom CSS
st.markdown("""
<style>
    .main { background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%); }
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border-radius: 10px;
        padding: 0.65rem 1.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def get_tower_location(mcc, mnc, lac, cid, api_key):
    """Get tower location"""
    try:
        url = "https://us1.unwiredlabs.com/v2/process.php"
        payload = {
            "token": api_key,
            "radio": "gsm",
            "mcc": int(mcc),
            "mnc": int(mnc),
            "cells": [{"lac": int(lac), "cid": int(cid)}],
            "address": 1
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                return {
                    'lat': data.get('lat'),
                    'lon': data.get('lon'),
                    'accuracy': data.get('accuracy', 1000),
                    'address': data.get('address', 'N/A')
                }
        return {'error': 'Failed to get location'}
    except Exception as e:
        return {'error': str(e)}

def create_map(lat, lon, accuracy, address):
    """Create map"""
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat, lon], popup=address, tooltip="Tower").add_to(m)
    folium.Circle([lat, lon], radius=accuracy, color='blue', fill=True, fillOpacity=0.2).add_to(m)
    return m

def parse_call_records(text):
    """Parse Jio bill"""
    records = []
    lines = text.split('\n')
    
    for line in lines:
        if len(line.strip()) < 15:
            continue
        
        phones = re.findall(r'\b(9\d{9}|[6-9]\d{11})\b', line)
        if not phones:
            continue
            
        dates = re.findall(r'\b(\d{1,2}[-/][A-Z]{3}[-/]\d{2,4})\b', line, re.IGNORECASE)
        times = re.findall(r'\b(\d{1,2}:\d{2}(?::\d{2})?)\b', line)
        
        parts = line.split()
        duration_seconds = 0
        
        for i, part in enumerate(parts):
            if part in phones:
                for j in range(i+1, min(i+5, len(parts))):
                    try:
                        potential_duration = int(parts[j])
                        if 1 <= potential_duration <= 3600:
                            duration_seconds = potential_duration
                            break
                    except:
                        continue
                if duration_seconds > 0:
                    break
        
        if phones and duration_seconds > 0:
            records.append({
                'phone': phones[0],
                'date': dates[0] if dates else 'N/A',
                'time': times[0] if times else 'N/A',
                'duration_seconds': duration_seconds
            })
    
    return records

def analyze_records(records):
    """Analyze call records"""
    if not records:
        return None
    
    df = pd.DataFrame(records)
    df = df[df['duration_seconds'] > 0]
    
    if len(df) == 0:
        return None
    
    phone_stats = df.groupby('phone').agg({
        'duration_seconds': ['sum', 'count', 'mean', 'max']
    }).round(2)
    
    phone_stats.columns = ['Total (s)', 'Count', 'Avg (s)', 'Max (s)']
    phone_stats = phone_stats.sort_values('Total (s)', ascending=False)
    
    most_contacted = df['phone'].value_counts()
    
    return {
        'df': df,
        'total_calls': len(df),
        'total_duration': df['duration_seconds'].sum(),
        'avg_duration': df['duration_seconds'].mean(),
        'longest_call': df['duration_seconds'].max(),
        'phone_stats': phone_stats,
        'most_contacted': most_contacted.index[0] if len(most_contacted) > 0 else 'N/A',
        'most_contacted_count': most_contacted.values[0] if len(most_contacted) > 0 else 0
    }

# Main App
st.title("📡 CDR Analysis Pro")
st.markdown("Professional Call Data Record Analysis & Tower Location Tracking")

# Sidebar
with st.sidebar:
    st.header("🎯 Navigation")
    page = st.radio("Select", ["🗼 Tower Location", "📊 Bill Analysis"], label_visibility="collapsed")
    
    st.markdown("---")
    st.header("⚙️ Settings")
    api_key = st.text_input("Unwired Labs API Key", type="password", value=st.session_state.api_key)
    if api_key:
        st.session_state.api_key = api_key

# Tower Location Page
if page == "🗼 Tower Location":
    st.header("🗼 Cell Tower Location Tracker")
    
    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your API key in the sidebar")
        st.info("Get your free API key at: https://unwiredlabs.com/")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            mcc = st.number_input("MCC", min_value=0, value=404)
            mnc = st.number_input("MNC", min_value=0, value=11)
        
        with col2:
            lac = st.number_input("LAC/TAC", min_value=0, value=1234)
            cid = st.number_input("Cell ID", min_value=0, value=12345)
        
        if st.button("🔍 Locate Tower", type="primary"):
            with st.spinner("Locating..."):
                result = get_tower_location(mcc, mnc, lac, cid, st.session_state.api_key)
                
                if 'error' in result:
                    st.error(f"Error: {result['error']}")
                else:
                    st.success("✅ Tower found!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Latitude", f"{result['lat']:.6f}")
                    col2.metric("Longitude", f"{result['lon']:.6f}")
                    col3.metric("Accuracy", f"±{result['accuracy']}m")
                    
                    st.info(f"📍 {result['address']}")
                    
                    tower_map = create_map(result['lat'], result['lon'], result['accuracy'], result['address'])
                    st_folium(tower_map, width=None, height=500)

# Bill Analysis Page
else:
    st.header("📊 Call Bill Analysis")
    
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'])
    
    if uploaded_file and st.button("🔍 Analyze", type="primary"):
        with st.spinner("Analyzing..."):
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                records = parse_call_records(text)
                
                if not records:
                    st.warning("No call records found")
                else:
                    analysis = analyze_records(records)
                    
                    if analysis:
                        st.success(f"✅ Analyzed {analysis['total_calls']} calls!")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("Total Calls", analysis['total_calls'])
                        col2.metric("Total Duration", f"{analysis['total_duration']//60}m")
                        col3.metric("Avg Duration", f"{analysis['avg_duration']//60}m {int(analysis['avg_duration']%60)}s")
                        col4.metric("Longest Call", f"{analysis['longest_call']//60}m")
                        
                        st.info(f"📱 Most Contacted: {analysis['most_contacted']} ({analysis['most_contacted_count']} calls)")
                        
                        st.subheader("📱 Contact Statistics")
                        st.dataframe(analysis['phone_stats'], use_container_width=True)
                        
                        # Chart
                        top10 = analysis['phone_stats'].head(10)
                        fig = px.bar(x=top10.index, y=top10['Count'], title="Top 10 Contacts")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Download
                        csv = analysis['df'].to_csv(index=False)
                        st.download_button("📥 Download CSV", csv, "call_records.csv", "text/csv")
                    else:
                        st.error("Failed to analyze records")
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.caption("CDR Analysis Pro v1.0 | Built with Streamlit")
