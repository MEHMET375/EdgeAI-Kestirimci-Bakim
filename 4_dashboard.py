import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Kestirimci Bakım", layout="wide")

# 1. ÇÖZÜM: Global Veri Kutusu (Kuyruk) Oluşturma
# Bu sayede arka plandaki radyo sinyali (thread) ekranı çökertmeden buraya veri atabilecek.
@st.cache_resource
def get_veri_kuyrugu():
    return []

veri_kuyrugu = get_veri_kuyrugu()

# 2. MQTT Mesaj Geldiğinde Çalışacak Fonksiyon
def on_message(client, userdata, msg):
    try:
        gelen_veri = json.loads(msg.payload.decode('utf-8'))
        veri_kuyrugu.append(gelen_veri)
        
        # Ekranda sadece son 30 saniyeyi tutalım
        if len(veri_kuyrugu) > 30:
            veri_kuyrugu.pop(0)
    except:
        pass

# 3. MQTT Bağlantısını Sadece 1 Kere Başlatma
@st.cache_resource
def mqtt_baslat():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883, 60)
    client.subscribe("mehmet_okur/fabrika/motor_1")
    client.loop_start()
    return client

mqtt_istemci = mqtt_baslat()

# --- ARAYÜZ (DASHBOARD) TASARIMI ---
st.title("🏭 Edge AI Kestirimci Bakım İzleme Paneli")
st.markdown("Sensörden gelen veriler **Bulut MQTT** üzerinden canlı dinlenmektedir.")

metrik_alani = st.empty()
grafik_alani = st.empty()

# Eğer kutunun içinde veri varsa ekranı çiz
if len(veri_kuyrugu) > 0:
    son_veri = veri_kuyrugu[-1]
    df = pd.DataFrame(veri_kuyrugu)
    
    with metrik_alani.container():
        c1, c2, c3, c4 = st.columns(4)
        
        # Duruma göre renk değiştirme
        renk = "normal" if son_veri['durum'] == "SAĞLAM" else "inverse"
        
        c1.metric("Motor Durumu", son_veri['durum'], delta="Aktif Yayın", delta_color=renk)
        c2.metric("Titreşim (RMS)", son_veri['rms'])
        c3.metric("Frekans Şiddeti (FFT Max)", son_veri['fft_max'])
        c4.metric("Kalan Ömür", f"% {son_veri['rul']}")

    with grafik_alani.container():
        fig = go.Figure()
        
        # Grafiği Çizme
        fig.add_trace(go.Scatter(
            x=df['zaman'], 
            y=df['rms'], 
            mode='lines+markers', 
            name='RMS', 
            line=dict(color='#00E5FF', width=3)
        ))
        
        fig.update_layout(
            title="Canlı Titreşim (RMS) Akışı", 
            xaxis_title="Zaman", 
            yaxis_title="RMS Değeri", 
            height=400,
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Buluttan veri bekleniyor... Lütfen 1. Terminalde '3_sanal_sensor.py' dosyasının çalıştığına emin olun.")

# Ekranı saniyede bir otomatik yenile (Kutuya yeni veri gelmiş mi diye bak)
time.sleep(1)
st.rerun()