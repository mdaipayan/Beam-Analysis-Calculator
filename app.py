import streamlit as st
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beam_calculator import BeamAnalyzer
import pandas as pd

st.set_page_config(page_title="Beam Analysis Calculator", layout="wide")

st.title("🔧 Beam Analysis Calculator")
st.markdown("Calculate Shear Force Diagrams (SFD) and Bending Moment Diagrams (BMD) for any beam configuration")

# Sidebar for inputs
with st.sidebar:
    st.header("Beam Configuration")
    
    # Beam type selection
    beam_type = st.selectbox(
        "Beam Type",
        ["simply_supported", "cantilever", "fixed_fixed", "overhang"],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Beam dimensions
    L = st.number_input("Beam Length (m)", min_value=0.1, value=6.0, step=0.1)
    
    # Load inputs
    st.header("Load Configuration")
    load_type = st.selectbox("Add Load Type", ["Point Load", "UDL", "Concentrated Moment"])
    
    if load_type == "Point Load":
        col1, col2 = st.columns(2)
        with col1:
            pos = st.number_input("Position (m)", 0.0, L, L/2, 0.1)
            mag = st.number_input("Magnitude (kN)", 0.0, 1000.0, 10.0, 1.0)
        with col2:
            direction = st.selectbox("Direction", ["Down", "Up"])
        
        if st.button("Add Point Load"):
            if 'loads' not in st.session_state:
                st.session_state.loads = []
            st.session_state.loads.append({
                'type': 'point', 'pos': pos, 'mag': mag, 
                'direction': direction.lower()
            })
            st.success(f"Added {mag}kN point load at {pos}m")
    
    elif load_type == "UDL":
        col1, col2 = st.columns(2)
        with col1:
            start = st.number_input("Start Position (m)", 0.0, L, 0.0, 0.1)
            end = st.number_input("End Position (m)", start, L, L, 0.1)
            intensity = st.number_input("Intensity (kN/m)", 0.0, 100.0, 5.0, 0.5)
        with col2:
            direction = st.selectbox("Direction", ["Down", "Up"])
        
        if st.button("Add UDL"):
            if 'loads' not in st.session_state:
                st.session_state.loads = []
            st.session_state.loads.append({
                'type': 'udl', 'start': start, 'end': end, 
                'intensity': intensity, 'direction': direction.lower()
            })
            st.success(f"Added UDL from {start}m to {end}m")
    
    elif load_type == "Concentrated Moment":
        col1, col2 = st.columns(2)
        with col1:
            pos = st.number_input("Position (m)", 0.0, L, L/2, 0.1)
            mag = st.number_input("Magnitude (kNm)", -1000.0, 1000.0, 10.0, 1.0)
        with col2:
            direction = st.selectbox("Direction", ["Clockwise", "Counter-clockwise"])
        
        if st.button("Add Moment"):
            if 'loads' not in st.session_state:
                st.session_state.loads = []
            st.session_state.loads.append({
                'type': 'moment', 'pos': pos, 'mag': mag,
                'direction': direction.lower()
            })
            st.success(f"Added moment at {pos}m")

    # Clear loads button
    if st.button("Clear All Loads"):
        st.session_state.loads = []
        st.success("All loads cleared!")

# Initialize session state
if 'loads' not in st.session_state:
    st.session_state.loads = []

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Analysis Results")
    
    if st.button("Run Analysis", type="primary"):
        # Create beam analyzer
        beam = BeamAnalyzer(L, beam_type)
        
        # Add all loads
        for load in st.session_state.loads:
            if load['type'] == 'point':
                beam.add_point_load(load['pos'], load['mag'], load['direction'])
            elif load['type'] == 'udl':
                beam.add_udl(load['start'], load['end'], load['intensity'], load['direction'])
            elif load['type'] == 'moment':
                beam.add_moment(load['pos'], load['mag'], load['direction'])
        
        # Calculate
        V, M = beam.analyze()
        
        # Display plots
        fig = beam.plot_diagrams()
        st.pyplot(fig)
        
        # Store for export
        st.session_state.results = {
            'x': beam.x, 'V': V, 'M': M,
            'max_vals': beam.get_max_values()
        }

with col2:
    st.subheader("Current Loads")
    if not st.session_state.loads:
        st.info("No loads added yet. Use the sidebar to add loads.")
    else:
        for i, load in enumerate(st.session_state.loads):
            with st.expander(f"Load {i+1}: {load['type'].title()}"):
                st.json(load)
                if st.button(f"Remove Load {i+1}", key=f"remove_{i}"):
                    st.session_state.loads.pop(i)
                    st.rerun()

    if 'results' in st.session_state:
        st.subheader("Key Results")
        max_vals = st.session_state.results['max_vals']
        st.metric("Max Shear Force", f"{max_vals['max_shear']:.2f} kN")
        st.metric("Max Bending Moment", f"{max_vals['max_moment']:.2f} kNm")
        st.metric("Max Shear at", f"{max_vals['max_shear_pos']:.2f} m")
        st.metric("Max Moment at", f"{max_vals['max_moment_pos']:.2f} m")
        
        # Export data
        if st.button("Download Results CSV"):
            df = pd.DataFrame({
                'Position (m)': st.session_state.results['x'],
                'Shear Force (kN)': st.session_state.results['V'],
                'Bending Moment (kNm)': st.session_state.results['M']
            })
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="beam_analysis.csv",
                mime="text/csv"
            )

# Instructions
with st.expander("How to use this app"):
    st.markdown("""
    1. **Select Beam Type**: Choose from Simply Supported, Cantilever, etc.
    2. **Set Dimensions**: Enter the beam length
    3. **Add Loads**: Use the sidebar to add:
       - Point loads (concentrated forces)
       - UDL (Uniformly Distributed Loads)
       - Concentrated moments
    4. **Analyze**: Click 'Run Analysis' to generate SFD and BMD
    5. **Export**: Download results as CSV for further analysis
    
    **Note**: This app uses numerical integration for generality. For educational purposes, 
    symbolic solutions are recommended for simple cases.
    """)
