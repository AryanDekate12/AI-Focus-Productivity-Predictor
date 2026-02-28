import streamlit as st
import numpy as np
import joblib
import requests
import os
import tempfile

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENWEATHER_API_KEY")

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="Focus & Productivity Predictor", layout="wide")

# --------------------------------------------------
# PREMIUM UI STYLING
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

[data-testid="stMetricValue"] {
    font-size: 50px;
    font-weight: bold;
}

.stButton>button {
    border-radius: 8px;
}

hr {
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------
rf_model = joblib.load("model/random_forest_model_compressed.pkl")
scaler = joblib.load("model/scaler.pkl")

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🧠 Focus & Productivity Level Checker")
st.write("See how weather and lifestyle factors affect your daily performance.")

st.markdown("---")

# --------------------------------------------------
# WEATHER & AQI SECTION
# --------------------------------------------------
st.subheader("🌍 Automatic Weather & Air Quality")

city = st.text_input("Enter City Name")

temperature = 30
humidity = 60
pressure = 1010
wind_speed = 3
aqi = 150


if city and api_key:
    weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    weather_response = requests.get(weather_url)
    weather_data = weather_response.json()

    if weather_response.status_code == 200:
        temperature = weather_data["main"]["temp"]
        humidity = weather_data["main"]["humidity"]
        pressure = weather_data["main"]["pressure"]
        wind_speed = weather_data["wind"]["speed"]

        lat = weather_data["coord"]["lat"]
        lon = weather_data["coord"]["lon"]

        aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        aqi_data = requests.get(aqi_url).json()

        aqi = aqi_data["list"][0]["main"]["aqi"] * 100
        st.success(f"Weather & AQI loaded for {city}")
    else:
        st.error("Unable to fetch weather data.")

st.markdown("---")

# --------------------------------------------------
# INPUT SECTION
# --------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌡 Environment")
    temperature = st.slider("Temperature (°C)", 5, 45, int(temperature))
    humidity = st.slider("Humidity (%)", 20, 95, int(humidity))
    aqi = st.slider("Air Quality Index", 20, 400, int(aqi))
    pressure = st.slider("Pressure (hPa)", 980, 1035, int(pressure))
    wind_speed = st.slider("Wind Speed (m/s)", 0.0, 15.0, float(wind_speed))

with col2:
    st.subheader("🛌 Lifestyle")
    sleep_hours = st.slider("Sleep Hours", 3.0, 9.0, 7.0)
    hydration_level = st.slider("Hydration Level (1–5)", 1, 5, 3)
    caffeine_intake = st.slider("Caffeine Intake", 0, 6, 2)
    noise_level = st.slider("Noise Level (dB)", 30, 90, 55)
    screen_time = st.slider("Screen Time Before Task (hrs)", 0.0, 8.0, 3.0)

environment = st.radio("Environment", ["Indoor", "Outdoor"])
indoor_outdoor = 0 if environment == "Indoor" else 1

# --------------------------------------------------
# PREDICTION
# --------------------------------------------------
input_data = np.array([[temperature, humidity, aqi, pressure, wind_speed,
                        sleep_hours, hydration_level, caffeine_intake,
                        noise_level, screen_time, indoor_outdoor]])

input_scaled = scaler.transform(input_data)
rf_pred = rf_model.predict(input_scaled)[0]

st.markdown("---")

# --------------------------------------------------
# RESULT CARD
# --------------------------------------------------
st.subheader("📊 Your Performance Status")

st.metric("Performance Impact", f"{rf_pred:.1f}%")

if rf_pred < 12:
    status = "Excellent"
    st.success("🟢 Excellent — Conditions support strong focus and productivity.")
elif rf_pred < 20:
    status = "Fair"
    st.info("🟡 Fair — Minor factors may slightly reduce focus.")
elif rf_pred < 28:
    status = "Poor"
    st.warning("🟠 Poor — Productivity may be affected.")
else:
    status = "Very Poor"
    st.error("🔴 Very Poor — Performance is significantly impacted.")

st.markdown(f"### Overall Condition: **{status}**")

st.markdown("---")

# --------------------------------------------------
# PDF REPORT
# --------------------------------------------------
def generate_pdf(city_name, score, status_text):
    file_path = tempfile.NamedTemporaryFile(delete=False).name
    doc = SimpleDocTemplate(file_path)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Focus & Productivity Report - {city_name}", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(f"Performance Impact: {score:.1f}%", styles["Normal"]))
    elements.append(Paragraph(f"Overall Condition: {status_text}", styles["Normal"]))

    doc.build(elements)
    return file_path

pdf_path = generate_pdf(city if city else "Selected Location", rf_pred, status)

with open(pdf_path, "rb") as f:
    st.download_button(
        label="📄 Download Performance Report",
        data=f,
        file_name="focus_productivity_report.pdf",
        mime="application/pdf"
    )

st.markdown("---")

# --------------------------------------------------
# CITY COMPARISON
# --------------------------------------------------
st.subheader("🌆 Compare With Another City")

city2 = st.text_input("Enter Second City")

if city2 and api_key:
    url2 = f"https://api.openweathermap.org/data/2.5/weather?q={city2}&appid={api_key}&units=metric"
    res2 = requests.get(url2)
    data2 = res2.json()

    if res2.status_code == 200:
        temp2 = data2["main"]["temp"]
        hum2 = data2["main"]["humidity"]
        pres2 = data2["main"]["pressure"]
        wind2 = data2["wind"]["speed"]

        lat2 = data2["coord"]["lat"]
        lon2 = data2["coord"]["lon"]

        aqi_url2 = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat2}&lon={lon2}&appid={api_key}"
        aqi2 = requests.get(aqi_url2).json()["list"][0]["main"]["aqi"] * 100

        input2 = np.array([[temp2, hum2, aqi2, pres2, wind2,
                            sleep_hours, hydration_level, caffeine_intake,
                            noise_level, screen_time, indoor_outdoor]])

        input2_scaled = scaler.transform(input2)
        rf_pred2 = rf_model.predict(input2_scaled)[0]

        st.metric(f"{city2} Impact", f"{rf_pred2:.1f}%")

st.markdown("---")

st.caption("⚠ Educational ML simulation. Not medical advice.")
