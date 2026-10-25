import streamlit as st
import pandas as pd
import pyproj


# ==============================================================================
# 1. UGANDA COORDINATE BATCH CONVERTER CLASS
# ==============================================================================
class UgandaCoordinateBatchConverter:
    # Full registry of supported Ugandan and global geodetic systems
    SYSTEM_REGISTRY = {
        1: {"name": "Arc 1960 / UTM Zone 35N", "epsg": 21095},
        2: {"name": "Arc 1960 / UTM Zone 36N", "epsg": 21096},
        3: {"name": "WGS 84 / Geographic (Lat/Lon)", "epsg": 4326},
        4: {"name": "WGS 84 / UTM Zone 35N", "epsg": 32635},
        5: {"name": "WGS 84 / UTM Zone 36N", "epsg": 32636},
        6: {"name": "ITRF2014 Frame", "epsg": 7912}
    }

    def __init__(self, source_epsg, target_epsg):
        self.source_crs = pyproj.CRS.from_user_input(source_epsg)
        self.target_crs = pyproj.CRS.from_user_input(target_epsg)

        # crucial: always_xy=True prevents X and Y from getting flipped
        self.transformer = pyproj.Transformer.from_crs(
            self.source_crs,
            self.target_crs,
            always_xy=True
        )

    def convert_dataframe(self, df: pd.DataFrame, x_column: str, y_column: str) -> pd.DataFrame:
        """Transforms coordinates in a pandas DataFrame and appends converted columns."""
        df_clean = df.copy()

        # Convert coordinate columns to numeric
        df_clean[x_column] = pd.to_numeric(df_clean[x_column], errors='coerce')
        df_clean[y_column] = pd.to_numeric(df_clean[y_column], errors='coerce')

        # Remove invalid rows
        df_clean = df_clean.dropna(subset=[x_column, y_column])

        # Perform transformation
        x_conv, y_conv = self.transformer.transform(
            df_clean[x_column].values,
            df_clean[y_column].values
        )

        # Append converted results
        df_clean["Converted_X_Easting"] = x_conv
        df_clean["Converted_Y_Northing"] = y_conv

        return df_clean


# ==============================================================================
# 2. STREAMLIT WEB INTERFACE
# ==============================================================================
def main():
    st.set_page_config(page_title="Uganda Coordinate Converter", page_icon="🌐", layout="wide")

    st.title("🌐 Uganda Batch Coordinate Converter")
    st.markdown(
        "Transform coordinate datasets across **Arc 1960**, **WGS 84**, and **ITRF2014** geodetic systems seamlessly.")

    # Sidebar: System Selections
    st.sidebar.header("⚙️ Geodetic Settings")

    systems_dict = {f"{data['name']} (EPSG:{data['epsg']})": data['epsg']
                    for data in UgandaCoordinateBatchConverter.SYSTEM_REGISTRY.values()}
    system_names = list(systems_dict.keys())

    source_choice = st.sidebar.selectbox("Source Coordinate System", system_names,
                                         index=1)  # Default: Arc 1960 Zone 36N
    target_choice = st.sidebar.selectbox("Target Coordinate System", system_names, index=4)  # Default: WGS 84 Zone 36N

    source_epsg = systems_dict[source_choice]
    target_epsg = systems_dict[target_choice]

    # File Upload Area
    st.subheader("1. Upload Dataset")
    uploaded_file = st.file_uploader("Upload your survey file (CSV or Excel)", type=["csv", "xlsx", "xls"])

    if uploaded_file is not None:
        try:
            # Read file based on extension
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Clean header whitespace
            df.columns = df.columns.astype(str).str.strip()

            st.write("📋 **Dataset Preview:**")
            st.dataframe(df.head(10), use_container_width=True)

            # Column Selection Area
            st.subheader("2. Map Coordinate Columns")
            col1, col2 = st.columns(2)

            # Auto-detect default columns if Easting/Northing or X/Y exist
            default_x_idx = 0
            default_y_idx = min(1, len(df.columns) - 1)

            for i, col in enumerate(df.columns):
                if col.lower() in ['easting', 'x', 'east', 'longitude', 'lon']:
                    default_x_idx = i
                elif col.lower() in ['northing', 'y', 'north', 'latitude', 'lat']:
                    default_y_idx = i

            with col1:
                x_col = st.selectbox("Select Easting (X) Column:", df.columns, index=default_x_idx)
            with col2:
                y_col = st.selectbox("Select Northing (Y) Column:", df.columns, index=default_y_idx)

            # Convert Action Button
            st.subheader("3. Execute Conversion")
            if st.button("🚀 Run Batch Transformation", type="primary"):
                with st.spinner("Transforming coordinates..."):
                    converter = UgandaCoordinateBatchConverter(source_epsg, target_epsg)
                    result_df = converter.convert_dataframe(df, x_col, y_col)

                    st.success(f"Successfully transformed {len(result_df)} points!")
                    st.write("📊 **Converted Output Preview:**")
                    st.dataframe(result_df.head(10), use_container_width=True)

                    # Export to CSV
                    csv_bytes = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Converted CSV",
                        data=csv_bytes,
                        file_name=f"converted_{uploaded_file.name}.csv",
                        mime="text/csv"
                    )

        except Exception as e:
            st.error(f"Error processing file: {e}")


if __name__ == "__main__":
    main()