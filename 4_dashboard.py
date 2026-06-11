import streamlit as st
import paho.mqtt.client as mqtt
import json
import pandas as pd
import plotly.graph_objects as go
import time

# Sayfa Yapılandırması (Geniş Ekran)
st.set_page_config(page_title="Edge AI Kestirimci Bakım", layout="wide", page_icon="🏭")

# --- ARKA PLAN / MQTT BACKEND (DOKUNULMADI) ---
@st.cache_resource
def get_veri_kuyrugu():
    return []

veri_kuyrugu = get_veri_kuyrugu()

def on_message(client, userdata, msg):
    try:
        gelen_veri = json.loads(msg.payload.decode('utf-8'))
        veri_kuyrugu.append(gelen_veri)
        if len(veri_kuyrugu) > 30:
            veri_kuyrugu.pop(0)
    except:
        pass

@st.cache_resource
def mqtt_baslat():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("broker.emqx.io", 1883, 60)
    client.subscribe("mehmet_okur/fabrika/motor_1")
    client.loop_start()
    return client

mqtt_istemci = mqtt_baslat()
# ----------------------------------------------

# --- UI / FRONTEND TASARIMI (ENDÜSTRİ 4.0 SCADA EKRANI) ---

# Şaşalı Başlık
st.markdown("<h1 style='text-align: center; color: #00E5FF; text-shadow: 0px 0px 10px #00E5FF;'>🏭 Endüstri 4.0: AI Tabanlı Kestirimci Bakım Merkezi</h1>", unsafe_allow_html=True)
st.markdown("---")

# Yer tutucular
alarm_alani = st.empty()
metrik_alani = st.empty()
grafik_alani = st.empty()

if len(veri_kuyrugu) > 0:
    son_veri = veri_kuyrugu[-1]
    df = pd.DataFrame(veri_kuyrugu)
    
    durum_arizali = son_veri['durum'] == "ARIZALI"
    
    # 1. DİNAMİK ALARM SİSTEMİ (Devasa HTML Banner)
    with alarm_alani.container():
        if durum_arizali:
            # Arıza durumunda yanıp sönen (blink) kırmızı alarm
            st.markdown("""
            <div style="background-color:#ff4b4b; padding:20px; border-radius:10px; text-align:center; box-shadow: 0px 0px 20px #ff4b4b;">
                <h2 style="color:white; margin:0; font-weight:bold;">🚨 DİKKAT! KRİTİK MOTOR ARIZASI TESPİT EDİLDİ! ACİL MÜDAHALE GEREKLİ! 🚨</h2>
            </div>
            <br>
            """, unsafe_allow_html=True)
        else:
            # Sağlam durumunda güven veren yeşil bar
            st.markdown("""
            <div style="background-color:#00c853; padding:15px; border-radius:10px; text-align:center; box-shadow: 0px 0px 15px #00c853;">
                <h3 style="color:white; margin:0;">✅ Sistem Normal - Yapay Zeka Aktif İzlemede</h3>
            </div>
            <br>
            """, unsafe_allow_html=True)
            
    # 2. YAN YANA HAVALI METRİK KARTLARI
    with metrik_alani.container():
        c1, c2, c3 = st.columns(3)
        renk = "inverse" if durum_arizali else "normal"
        c1.metric("⚙️ Motor Durumu", son_veri['durum'], delta="Edge AI Aktif", delta_color=renk)
        c2.metric("📊 Titreşim (RMS)", f"{son_veri['rms']:.4f}")
        c3.metric("⚡ Frekans Şiddeti (FFT Max)", f"{son_veri['fft_max']:.2f}")

    st.write("") # Araya küçük bir boşluk

    # 3. GRAFİKLER (Akıllı Çizgi ve Devir Saati)
    with grafik_alani.container():
        # Ekranı 70'e 30 oranında ikiye bölüyoruz
        col_grafik, col_gauge = st.columns([7, 3]) 
        
        with col_grafik:
            # AKILLI ÇİZGİ RENGİ: Sağlamken Neon Mavi, Arıza anında Kırmızı
            cizgi_rengi = '#ff4b4b' if durum_arizali else '#00E5FF'
            
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(
                x=df['zaman'], 
                y=df['rms'], 
                mode='lines+markers', 
                name='RMS', 
                line=dict(color=cizgi_rengi, width=4),
                marker=dict(size=8, color='white', line=dict(width=2, color=cizgi_rengi))
            ))
            fig_line.update_layout(
                title="📈 Canlı Titreşim (RMS) Akışı", 
                xaxis_title="Zaman", 
                yaxis_title="RMS Değeri", 
                height=400,
                template="plotly_dark",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
        with col_gauge:
            # KALAN ÖMÜR (RUL) DEVİR SAATİ (GAUGE CHART)
            rul_degeri = son_veri['rul']
            
            # İbre Rengini RUL değerine göre dinamik belirleme
            if rul_degeri <= 20:
                bar_color = "#ff4b4b" # Kırmızı (Tehlike)
            elif rul_degeri <= 50:
                bar_color = "#ffa700" # Sarı (Uyarı)
            else:
                bar_color = "#00c853" # Yeşil (Güvenli)
                
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = rul_degeri,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "⏳ Kalan Faydalı Ömür (RUL) %", 'font': {'size': 20, 'color': 'white'}},
                number = {'font': {'size': 45, 'color': bar_color, 'fontweight': 'bold'}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "white"},
                    'bar': {'color': bar_color, 'thickness': 0.3},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 20], 'color': "rgba(255, 75, 75, 0.3)"},
                        {'range': [20, 50], 'color': "rgba(255, 167, 0, 0.3)"},
                        {'range': [50, 100], 'color': "rgba(0, 200, 83, 0.3)"}
                    ],
                }
            ))
            fig_gauge.update_layout(
                height=400, 
                template="plotly_dark",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

else:
    st.info("📡 Buluttan veri bekleniyor... Lütfen sanal sensörün (3_sanal_sensor.py) çalıştığına emin olun.")

# Ekranı saniyede bir yenile
time.sleep(1)
st.rerun()
