import streamlit as st

st.title("🧪 Test de Déploiement")
st.write("Si vous voyez ce message, l'application de base fonctionne!")

try:
    import pandas as pd
    st.success("✅ pandas importé")
except Exception as e:
    st.error(f"❌ pandas: {e}")

try:
    import plotly.express as px
    st.success("✅ plotly importé")
except Exception as e:
    st.error(f"❌ plotly: {e}")

try:
    import export_utils
    st.success("✅ export_utils importé")
except Exception as e:
    st.error(f"❌ export_utils: {e}")

try:
    import pdf_generators
    st.success("✅ pdf_generators importé")
except Exception as e:
    st.error(f"❌ pdf_generators: {e}")

st.write("Tous les tests d'import sont terminés!")
