"""
Utilitaires geographiques : etats bresiliens, geojson, construction de cartes.
"""
import streamlit as st
import plotly.express as px

BR_STATES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
}

BRAZIL_GEOJSON_URL = "https://raw.githubusercontent.com/codeforgermany/click_that_hood/main/public/data/brazil-states.geojson"


@st.cache_data(show_spinner=False)
def load_brazil_geojson():
    try:
        import requests
        resp = requests.get(BRAZIL_GEOJSON_URL, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def build_choropleth(data, geojson, color_col, color_scale, style, labels, hover_data):
    kwargs = dict(
        data_frame=data, geojson=geojson, locations="customer_state",
        featureidkey="properties.name", color=color_col,
        color_continuous_scale=color_scale, zoom=2.6,
        center={"lat": -14.2, "lon": -51.9}, opacity=0.85,
        labels=labels, hover_data=hover_data,
    )
    if hasattr(px, "choropleth_map"):
        kwargs["map_style"] = style
        return px.choropleth_map(**kwargs)
    kwargs["mapbox_style"] = style
    return px.choropleth_mapbox(**kwargs)


def build_scatter_map(data, lat_c, lon_c, color_col, color_scale, style):
    kwargs = dict(
        data_frame=data, lat=lat_c, lon=lon_c, zoom=2.6,
        center={"lat": -14.2, "lon": -51.9}, opacity=0.55,
    )
    if color_col:
        kwargs["color"] = color_col
        kwargs["color_continuous_scale"] = color_scale
    if hasattr(px, "scatter_map"):
        kwargs["map_style"] = style
        return px.scatter_map(**kwargs)
    kwargs["mapbox_style"] = style
    return px.scatter_mapbox(**kwargs)


def find_latlon_cols(df):
    candidates = [
        ("customer_lat", "customer_lng"),
        ("customer_lat", "customer_lon"),
        ("customer_latitude", "customer_longitude"),
        ("geolocation_lat", "geolocation_lng"),
        ("lat", "lng"),
        ("lat", "lon"),
        ("latitude", "longitude"),
    ]
    for lat_c, lon_c in candidates:
        if lat_c in df.columns and lon_c in df.columns:
            return lat_c, lon_c
    return None
