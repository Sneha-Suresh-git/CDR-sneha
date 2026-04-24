import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime, timedelta
import PyPDF2
import io
import re
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="CDR Analysis Pro",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern professional styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
        background-attachment: fixed;
    }
    
    .stApp {
        background: transparent;
    }
    
    .block-container {
        padding: 2rem 3rem;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        margin: 1.5rem auto;
    }
    
    h1 {
        color: #1a202c;
        font-weight: 700;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 600;
        font-size: 1.75rem !important;
        margin-top: 1.5rem;
    }
    
    h3 {
        color: #4a5568;
        font-weight: 600;
        font-size: 1.25rem !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.65rem 1.75rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
    }
    
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1.5px solid #e2e8f0;
        padding: 0.65rem 0.85rem;
        transition: all 0.2s ease;
        background: #ffffff;
    }
    
    .stTextInput>div>div>input:focus, .stNumberInput>div>div>input:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        outline: none;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        margin: 1rem 0;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    
    .stAlert {
        border-radius: 10px;
        border-left: 4px solid #3b82f6;
        background: #eff6ff;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid #334155;
    }
    
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        background: rgba(255, 255, 255, 0.05);
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        transition: all 0.2s ease;
    }
    
    [data-testid="stSidebar"] .stRadio > label:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .uploadedFile {
        border-radius: 10px;
        border: 2px dashed #3b82f6;
        background: #f8fafc;
    }
    
    .stSuccess {
        background: #ecfdf5;
        color: #065f46;
        border-left: 4px solid #10b981;
        border-radius: 8px;
    }
    
    .stWarning {
        background: #fffbeb;
        color: #92400e;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
    }
    
    .stInfo {
        background: #eff6ff;
        color: #1e40af;
        border-left: 4px solid #3b82f6;
        border-radius: 8px;
    }
    
    .stError {
        background: #fef2f2;
        color: #991b1b;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
    }
    
    /* Dataframe styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: #f8fafc;
        border-radius: 10px;
        padding: 1.5rem;
        border: 2px dashed #cbd5e1;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #3b82f6;
        background: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

def get_tower_location(mcc, mnc, lac_tac, cell_id, api_key):
    """Get tower location from Unwired Labs API with enhanced error handling"""
    try:
        url = "https://us1.unwiredlabs.com/v2/process.php"
        
        payload = {
            "token": api_key,
            "radio": "gsm",
            "mcc": int(mcc),
            "mnc": int(mnc),
            "cells": [{
                "lac": int(lac_tac),
                "cid": int(cell_id)
            }],
            "address": 1
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok':
                lat = data.get('lat')
                lon = data.get('lon')
                accuracy = data.get('accuracy', 1000)
                address = data.get('address', 'Address not available')
                
                # Validate coordinates
                if lat is None or lon is None:
                    return {'error': 'Invalid coordinates received from API'}
                
                return {
                    'success': True,
                    'lat': float(lat),
                    'lon': float(lon),
                    'accuracy': int(accuracy),
                    'address': address
                }
            else:
                error_msg = data.get('message', 'Unknown error from API')
                return {'error': f'API Error: {error_msg}'}
        else:
            return {'error': f'HTTP Error {response.status_code}: {response.text[:200]}'}
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout. Please try again.'}
    except requests.exceptions.ConnectionError:
        return {'error': 'Connection error. Please check your internet connection.'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def create_map(lat, lon, accuracy, address):
    """Create an interactive map with tower location and enhanced visuals"""
    try:
        # Create map centered on tower location
        m = folium.Map(
            location=[lat, lon],
            zoom_start=16,
            tiles='OpenStreetMap',
            control_scale=True
        )
        
        # Add multiple tile layers for better visualization
        folium.TileLayer('CartoDB positron', name='Light Map').add_to(m)
        folium.TileLayer('CartoDB dark_matter', name='Dark Map').add_to(m)
        
        # Add main marker for tower location
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(
                f"""
                <div style="font-family: Arial; width: 200px;">
                    <h4 style="margin: 0; color: #3b82f6;">📡 Cell Tower</h4>
                    <hr style="margin: 5px 0;">
                    <p style="margin: 5px 0;"><b>Latitude:</b> {lat}</p>
                    <p style="margin: 5px 0;"><b>Longitude:</b> {lon}</p>
                    <p style="margin: 5px 0;"><b>Accuracy:</b> ±{accuracy}m</p>
                    <p style="margin: 5px 0;"><b>Address:</b><br>{address}</p>
                </div>
                """,
                max_width=250
            ),
            tooltip=f"📡 Tower Location (±{accuracy}m)",
            icon=folium.Icon(color='red', icon='tower-cell', prefix='fa')
        ).add_to(m)
        
        # Add accuracy circle
        folium.Circle(
            [lat, lon],
            radius=accuracy,
            color='#3b82f6',
            fill=True,
            fillColor='#3b82f6',
            fillOpacity=0.15,
            weight=2,
            popup=f'Accuracy radius: ±{accuracy} meters'
        ).add_to(m)
        
        # Add a smaller center point
        folium.CircleMarker(
            [lat, lon],
            radius=8,
            color='#ef4444',
            fill=True,
            fillColor='#ef4444',
            fillOpacity=0.9,
            weight=2,
            popup='Exact tower coordinates'
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Add coordinates display
        folium.LatLngPopup().add_to(m)
        
        return m
    except Exception as e:
        st.error(f"Map creation error: {str(e)}")
        return None

def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"PDF extraction error: {str(e)}")
        return None

def parse_call_records_advanced(text):
    """
    Advanced parsing specifically optimized for Jio bills and similar formats
    """
    records = []
    lines = text.split('\n')
    
    for line in lines:
        # Skip empty or header lines
        if len(line.strip()) < 15:
            continue
        
        # Skip lines that are clearly headers or totals
        if any(keyword in line.upper() for keyword in ['SUBTOTAL', 'TOTAL', 'USAGE IN INDIA', 'VOICE LOCAL', 'VOICE STD', 'REGULAR']):
            continue
        
        # Pattern for Jio format: Date, Time, Phone Number, Duration (in seconds)
        # Example: "22-APR-26 18:16:22 916364002405 8 0 0 0 0.00"
        
        # Find all phone numbers (10-12 digits)
        phone_pattern = r'\b(9\d{9}|[6-9]\d{11})\b'
        phones = re.findall(phone_pattern, line)
        
        if not phones:
            continue
        
        # Find date (DD-MMM-YY or DD/MM/YYYY format)
        date_pattern = r'\b(\d{1,2}[-/][A-Z]{3}[-/]\d{2,4}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'
        dates = re.findall(date_pattern, line, re.IGNORECASE)
        
        # Find time (HH:MM:SS or HH:MM format)
        time_pattern = r'\b(\d{1,2}:\d{2}(?::\d{2})?)\b'
        times = re.findall(time_pattern, line)
        
        # Find duration in seconds - look for standalone numbers that represent seconds
        # In Jio bills, after phone number, there are columns: Used Usage, Billed Usage, Free Usage, Chargeable Usage
        # The "Used Usage" column contains the actual duration in seconds
        
        # Split line by whitespace to get columns
        parts = line.split()
        
        duration_seconds = 0
        
        # Try to find duration after the phone number
        for i, part in enumerate(parts):
            if part in phones:
                # Look at the next few parts for a number that could be duration
                for j in range(i+1, min(i+5, len(parts))):
                    try:
                        potential_duration = int(parts[j])
                        # Duration should be reasonable (1 second to 1 hour = 3600 seconds)
                        if 1 <= potential_duration <= 3600:
                            duration_seconds = potential_duration
                            break
                    except ValueError:
                        continue
                if duration_seconds > 0:
                    break
        
        # Format duration as MM:SS
        if duration_seconds > 0:
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "00:00"
        
        # Only add if we have phone, date/time, and valid duration
        if phones and (dates or times) and duration_seconds > 0:
            record = {
                'phone': phones[0],
                'date': dates[0] if dates else 'N/A',
                'time': times[0] if times else 'N/A',
                'duration': duration_str,
                'duration_seconds': duration_seconds,
                'raw_line': line.strip()
            }
            records.append(record)
    
    return records

def analyze_call_records_v2(records):
    """
    Improved analysis with better validation and statistics
    """
    if not records:
        return None
    
    df = pd.DataFrame(records)
    
    # Validation: Remove records with 0 duration or unrealistic durations
    # Max call duration: 4 hours (14400 seconds)
    df_valid = df[(df['duration_seconds'] > 0) & (df['duration_seconds'] <= 14400)].copy()
    
    if len(df_valid) == 0:
        return {
            'error': 'no_valid_records',
            'total_parsed': len(df),
            'message': 'No valid call records found with reasonable durations'
        }
    
    # Statistics
    total_calls = len(df_valid)
    total_duration_seconds = df_valid['duration_seconds'].sum()
    avg_duration_seconds = df_valid['duration_seconds'].mean()
    median_duration_seconds = df_valid['duration_seconds'].median()
    longest_call_seconds = df_valid['duration_seconds'].max()
    shortest_call_seconds = df_valid['duration_seconds'].min()
    
    # Phone-wise analysis
    phone_stats = df_valid.groupby('phone').agg({
        'duration_seconds': ['sum', 'count', 'mean', 'median', 'max', 'min']
    }).round(2)
    
    phone_stats.columns = ['Total Duration (s)', 'Call Count', 'Avg Duration (s)', 
                           'Median Duration (s)', 'Longest Call (s)', 'Shortest Call (s)']
    phone_stats = phone_stats.sort_values('Total Duration (s)', ascending=False)
    
    # Most contacted
    most_contacted = df_valid['phone'].value_counts()
    
    # Date analysis if available
    date_stats = None
    if df_valid['date'].notna().any() and (df_valid['date'] != 'N/A').any():
        date_counts = df_valid[df_valid['date'] != 'N/A']['date'].value_counts()
        date_stats = {
            'unique_dates': len(date_counts),
            'calls_per_day': date_counts.to_dict()
        }
    
    return {
        'success': True,
        'df': df_valid,
        'total_calls': total_calls,
        'total_duration': total_duration_seconds,
        'avg_duration': avg_duration_seconds,
        'median_duration': median_duration_seconds,
        'longest_call': longest_call_seconds,
        'shortest_call': shortest_call_seconds,
        'phone_stats': phone_stats,
        'most_contacted': most_contacted.index[0] if len(most_contacted) > 0 else 'N/A',
        'most_contacted_count': most_contacted.values[0] if len(most_contacted) > 0 else 0,
        'date_stats': date_stats,
        'filtered_count': len(df) - len(df_valid),
        'total_parsed': len(df)
    }

def format_duration(seconds):
    """Format seconds into readable duration"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"

# Main App
def main():
    # Header
    st.markdown("<h1 style='text-align: center;'>📡 CDR Analysis Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 1.2rem;'>Professional Call Data Record Analysis & Tower Location Tracking</p>", unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        page = st.radio("Navigation Menu", ["🗼 Tower Location", "📊 Bill Analysis"], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        
        # API Key input
        api_key_input = st.text_input(
            "Unwired Labs API Key",
            type="password",
            value=st.session_state.api_key,
            help="Enter your Unwired Labs API key"
        )
        
        if api_key_input:
            st.session_state.api_key = api_key_input
            st.success("✅ API Key saved!")
        
        st.markdown("---")
        st.markdown("### 📖 About")
        st.markdown("Built with ❤️ for CDR analysis professionals")
        st.markdown("Version 1.0.0")
    
    # Page routing
    if page == "🗼 Tower Location":
        tower_location_page()
    else:
        bill_analysis_page()

def tower_location_page():
    st.markdown("## 🗼 Cell Tower Location Tracker")
    st.markdown("Get precise cell tower locations with pinpoint accuracy using MCC, MNC, LAC/TAC, and Cell ID")
    
    # Check if API key is set
    if not st.session_state.api_key:
        st.warning("⚠️ Please enter your Unwired Labs API key in the sidebar to use this feature.")
        st.info("💡 Get your free API key at: https://unwiredlabs.com/")
        
        with st.expander("📖 How to get your API key"):
            st.markdown("""
            1. Visit [Unwired Labs](https://unwiredlabs.com/)
            2. Sign up for a free account
            3. Get your API token from the dashboard
            4. Paste it in the sidebar
            5. Free tier includes 100 requests/day
            """)
        return
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📱 Device Type")
        device_type = st.selectbox("Select Device", ["Android", "iPhone"], help="Select your device type")
        
        st.markdown("### 📍 Network Parameters")
        mcc = st.number_input("MCC (Mobile Country Code)", min_value=0, max_value=999, value=404, help="e.g., 404 for India, 310 for USA")
        mnc = st.number_input("MNC (Mobile Network Code)", min_value=0, max_value=999, value=45, help="e.g., 45 for Airtel, 11 for Jio")
    
    with col2:
        st.markdown("### 🔢 Cell Information")
        if device_type == "iPhone":
            lac_tac = st.number_input("TAC (Tracking Area Code)", min_value=0, value=1234, help="For iPhone devices (LTE/5G)")
        else:
            lac_tac = st.number_input("LAC (Location Area Code)", min_value=0, value=1234, help="For Android devices")
        
        cell_id = st.number_input("Cell ID", min_value=0, value=12345, help="Cell tower identifier (CID)")
    
    st.markdown("---")
    
    # Info box with examples
    with st.expander("ℹ️ Common MCC/MNC Codes for India"):
        st.markdown("""
        **Jio (Reliance Jio):**
        - MCC: 404 or 405
        - MNC: 11, 27, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98
        
        **Airtel:**
        - MCC: 404 or 405
        - MNC: 10, 40, 45, 49, 70, 90, 92, 93, 94, 95, 96, 97
        
        **Vi (Vodafone Idea):**
        - MCC: 404 or 405
        - MNC: 01, 05, 11, 13, 15, 20, 27, 30, 46, 60, 86, 87
        
        **BSNL:**
        - MCC: 404 or 405
        - MNC: 34, 38, 53, 54, 55, 57, 58, 59, 71, 72, 73, 74, 75, 76, 77, 80
        """)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        locate_button = st.button("🔍 Locate Tower", use_container_width=True, type="primary")
    
    if locate_button:
        with st.spinner("🔄 Fetching tower location from satellite database..."):
            result = get_tower_location(mcc, mnc, lac_tac, cell_id, st.session_state.api_key)
            
            if 'error' in result:
                st.error(f"❌ Error: {result['error']}")
                st.info("💡 **Troubleshooting Tips:**\n- Verify your API key is correct\n- Check if MCC, MNC, LAC, and Cell ID values are accurate\n- Ensure you have API credits remaining\n- Try different cell tower parameters")
            elif 'success' in result and result['success']:
                st.success("✅ Tower location found successfully!")
                
                # Display metrics in cards
                st.markdown("### 📊 Location Details")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: white; margin: 0; font-size: 0.95rem;">📍 Latitude</h3>
                        <p style="font-size: 1.8rem; margin: 0.5rem 0 0 0; font-weight: 700;">{result['lat']:.6f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: white; margin: 0; font-size: 0.95rem;">📍 Longitude</h3>
                        <p style="font-size: 1.8rem; margin: 0.5rem 0 0 0; font-weight: 700;">{result['lon']:.6f}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: white; margin: 0; font-size: 0.95rem;">🎯 Accuracy</h3>
                        <p style="font-size: 1.8rem; margin: 0.5rem 0 0 0; font-weight: 700;">±{result['accuracy']}m</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Display address
                st.markdown("### 📍 Tower Address")
                st.info(f"📌 {result['address']}")
                
                # Google Maps link
                google_maps_url = f"https://www.google.com/maps?q={result['lat']},{result['lon']}"
                st.markdown(f"[🗺️ Open in Google Maps]({google_maps_url})")
                
                st.markdown("---")
                
                # Display interactive map
                st.markdown("### 🗺️ Interactive Tower Location Map")
                st.caption("🔍 Zoom in/out • 🖱️ Click markers for details • 📍 Red dot = Tower location")
                
                tower_map = create_map(result['lat'], result['lon'], result['accuracy'], result['address'])
                
                if tower_map:
                    st_folium(tower_map, width=None, height=600, returned_objects=[])
                else:
                    st.error("Failed to create map visualization")
                
                # Additional info
                st.markdown("---")
                st.markdown("### 📋 Technical Details")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **Network Information:**
                    - MCC: {mcc}
                    - MNC: {mnc}
                    - LAC/TAC: {lac_tac}
                    - Cell ID: {cell_id}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Coordinates:**
                    - Latitude: {result['lat']:.6f}°
                    - Longitude: {result['lon']:.6f}°
                    - Accuracy: ±{result['accuracy']} meters
                    - Device Type: {device_type}
                    """)
            else:
                st.error("❌ Unexpected response format from API")

def bill_analysis_page():
    st.markdown("## 📊 Call Bill Analysis")
    st.markdown("Upload your call bill PDF for comprehensive and accurate analysis")
    
    uploaded_file = st.file_uploader(
        "📄 Upload Call Bill (PDF)",
        type=['pdf'],
        help="Upload your call bill in PDF format"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            analyze_button = st.button("🔍 Analyze Bill", use_container_width=True)
        
        if analyze_button:
            with st.spinner("🔄 Analyzing your bill..."):
                # Extract text from PDF
                text = extract_text_from_pdf(uploaded_file)
                
                if text is None:
                    st.error("❌ Failed to extract text from PDF. Please ensure the file is not corrupted.")
                    return
                
                # Parse call records with advanced method
                records = parse_call_records_advanced(text)
                
                if not records:
                    st.warning("⚠️ No call records found in the PDF.")
                    with st.expander("📄 View Extracted Text (First 3000 chars)"):
                        st.text(text[:3000])
                    return
                
                st.info(f"📋 Found {len(records)} potential call records")
                
                # Analyze records
                analysis = analyze_call_records_v2(records)
                
                if analysis is None or 'error' in analysis:
                    st.error("❌ Failed to analyze call records.")
                    if analysis and 'message' in analysis:
                        st.warning(analysis['message'])
                        st.info(f"Total records parsed: {analysis.get('total_parsed', 0)}")
                    
                    with st.expander("🔍 View Sample Raw Data"):
                        sample_df = pd.DataFrame(records[:20])
                        st.dataframe(sample_df, use_container_width=True)
                    return
                
                # Success!
                st.success(f"✅ Successfully analyzed {analysis['total_calls']} valid call records!")
                
                if analysis['filtered_count'] > 0:
                    st.info(f"ℹ️ Filtered out {analysis['filtered_count']} records with invalid/missing durations")
                
                # Debug section
                with st.expander("🔍 View Sample Parsed Records (First 15)"):
                    st.markdown("**Parsed Call Data:**")
                    sample_df = analysis['df'][['phone', 'date', 'time', 'duration', 'duration_seconds']].head(15)
                    st.dataframe(sample_df, use_container_width=True)
                    
                    st.markdown("**Sample Raw Lines:**")
                    for idx, row in analysis['df'].head(5).iterrows():
                        st.code(row['raw_line'], language=None)
                
                st.markdown("---")
                
                # Display overall statistics
                st.markdown("### 📈 Overall Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: white; margin: 0; font-size: 0.9rem;">📞 Total Calls</h4>
                        <p style="font-size: 2.2rem; margin: 0.5rem 0 0 0; font-weight: 700;">{analysis['total_calls']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    total_dur_str = format_duration(analysis['total_duration'])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: white; margin: 0; font-size: 0.9rem;">⏱️ Total Duration</h4>
                        <p style="font-size: 2.2rem; margin: 0.5rem 0 0 0; font-weight: 700;">{total_dur_str}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    avg_dur_str = format_duration(analysis['avg_duration'])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: white; margin: 0; font-size: 0.9rem;">📊 Avg Duration</h4>
                        <p style="font-size: 2.2rem; margin: 0.5rem 0 0 0; font-weight: 700;">{avg_dur_str}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    longest_dur_str = format_duration(analysis['longest_call'])
                    st.markdown(f"""
                    <div class="metric-card">
                        <h4 style="color: white; margin: 0; font-size: 0.9rem;">🏆 Longest Call</h4>
                        <p style="font-size: 2.2rem; margin: 0.5rem 0 0 0; font-weight: 700;">{longest_dur_str}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Additional metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    median_dur_str = format_duration(analysis['median_duration'])
                    st.metric("📊 Median Duration", median_dur_str)
                
                with col2:
                    shortest_dur_str = format_duration(analysis['shortest_call'])
                    st.metric("⚡ Shortest Call", shortest_dur_str)
                
                with col3:
                    if analysis['date_stats']:
                        st.metric("📅 Unique Days", analysis['date_stats']['unique_dates'])
                    else:
                        st.metric("📅 Date Info", "Not Available")
                
                # Most contacted number
                st.markdown("### 👤 Most Contacted Number")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.info(f"📱 **{analysis['most_contacted']}**")
                with col2:
                    st.metric("Total Calls", analysis['most_contacted_count'])
                
                # Phone-wise statistics
                st.markdown("### 📱 Contact-wise Detailed Analysis")
                
                # Prepare display dataframe
                display_stats = analysis['phone_stats'].copy()
                display_stats['Total Duration'] = display_stats['Total Duration (s)'].apply(format_duration)
                display_stats['Avg Duration'] = display_stats['Avg Duration (s)'].apply(format_duration)
                display_stats['Median Duration'] = display_stats['Median Duration (s)'].apply(format_duration)
                display_stats['Longest Call'] = display_stats['Longest Call (s)'].apply(format_duration)
                display_stats['Shortest Call'] = display_stats['Shortest Call (s)'].apply(format_duration)
                
                st.dataframe(
                    display_stats[['Call Count', 'Total Duration', 'Avg Duration', 'Median Duration', 'Longest Call', 'Shortest Call']],
                    use_container_width=True,
                    height=400
                )
                
                # Visualizations
                st.markdown("### 📊 Visual Analytics")
                
                tab1, tab2, tab3 = st.tabs(["📞 Call Distribution", "⏱️ Duration Analysis", "📈 Trends"])
                
                with tab1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top 10 contacts by call count
                        top_contacts = analysis['phone_stats'].head(10)
                        fig1 = px.bar(
                            x=top_contacts.index,
                            y=top_contacts['Call Count'],
                            title="Top 10 Contacts by Call Count",
                            labels={'x': 'Phone Number', 'y': 'Number of Calls'},
                            color=top_contacts['Call Count'],
                            color_continuous_scale='Blues',
                            text=top_contacts['Call Count']
                        )
                        fig1.update_traces(textposition='outside')
                        fig1.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        # Pie chart for call distribution
                        fig2 = px.pie(
                            values=top_contacts['Call Count'],
                            names=top_contacts.index,
                            title="Call Distribution (Top 10)",
                            hole=0.4
                        )
                        fig2.update_layout(height=400)
                        st.plotly_chart(fig2, use_container_width=True)
                
                with tab2:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Top 10 by total duration
                        fig3 = px.bar(
                            x=top_contacts.index,
                            y=top_contacts['Total Duration (s)'] / 60,
                            title="Top 10 Contacts by Total Duration",
                            labels={'x': 'Phone Number', 'y': 'Duration (minutes)'},
                            color=top_contacts['Total Duration (s)'],
                            color_continuous_scale='Viridis',
                            text=(top_contacts['Total Duration (s)'] / 60).round(1)
                        )
                        fig3.update_traces(textposition='outside')
                        fig3.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig3, use_container_width=True)
                    
                    with col2:
                        # Average duration comparison
                        fig4 = px.bar(
                            x=top_contacts.index,
                            y=top_contacts['Avg Duration (s)'] / 60,
                            title="Average Call Duration (Top 10)",
                            labels={'x': 'Phone Number', 'y': 'Avg Duration (minutes)'},
                            color=top_contacts['Avg Duration (s)'],
                            color_continuous_scale='Plasma',
                            text=(top_contacts['Avg Duration (s)'] / 60).round(1)
                        )
                        fig4.update_traces(textposition='outside')
                        fig4.update_layout(showlegend=False, height=400)
                        st.plotly_chart(fig4, use_container_width=True)
                
                with tab3:
                    # Duration distribution histogram
                    fig5 = px.histogram(
                        analysis['df'],
                        x='duration_seconds',
                        nbins=30,
                        title="Call Duration Distribution",
                        labels={'duration_seconds': 'Duration (seconds)', 'count': 'Number of Calls'},
                        color_discrete_sequence=['#3b82f6']
                    )
                    fig5.update_layout(height=400)
                    st.plotly_chart(fig5, use_container_width=True)
                    
                    # Box plot for duration by top contacts
                    top_5_phones = analysis['phone_stats'].head(5).index.tolist()
                    df_top5 = analysis['df'][analysis['df']['phone'].isin(top_5_phones)]
                    
                    fig6 = px.box(
                        df_top5,
                        x='phone',
                        y='duration_seconds',
                        title="Call Duration Distribution (Top 5 Contacts)",
                        labels={'phone': 'Phone Number', 'duration_seconds': 'Duration (seconds)'},
                        color='phone'
                    )
                    fig6.update_layout(height=400, showlegend=False)
                    st.plotly_chart(fig6, use_container_width=True)
                
                # Download options
                st.markdown("### 💾 Export Data")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export detailed records
                    csv_detailed = analysis['df'].to_csv(index=False)
                    st.download_button(
                        label="📥 Download Detailed Records (CSV)",
                        data=csv_detailed,
                        file_name=f"call_records_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Export summary statistics
                    csv_summary = display_stats.to_csv()
                    st.download_button(
                        label="📥 Download Summary Statistics (CSV)",
                        data=csv_summary,
                        file_name=f"call_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()
