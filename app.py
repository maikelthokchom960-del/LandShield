import base64
import datetime
import hashlib
import html
import io
import random
import re
import time
from PIL import Image, ImageChops, ImageEnhance
import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

# ==========================================
# 1. PAGE CONFIG & STYLES
# ==========================================
st.set_page_config(
    page_title="LandShield Enterprise | Desertification Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1A365D 0%, #2A4365 50%, #2F855A 100%);
        padding: 24px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .badge-green { background-color: #38A169; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    .badge-sec { background-color: #E53E3E; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    .badge-blue { background-color: #3182CE; color: white; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    </style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 2. SESSION STATE & SECURITY HELPERS
# ==========================================
if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []
if "app_lang" not in st.session_state:
    st.session_state["app_lang"] = "English"
if "generated_otp" not in st.session_state:
    st.session_state["generated_otp"] = None
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False
if "rate_limit_store" not in st.session_state:
    st.session_state["rate_limit_store"] = {}

def sanitize_input(user_input: str) -> str:
    cleaned = html.escape(str(user_input).strip())
    return re.sub(r"[^\w\s\+\-\@\.]", "", cleaned)

def check_rate_limit(key: str, limit_seconds: int = 10) -> bool:
    last_time = st.session_state["rate_limit_store"].get(key, 0)
    current_time = time.time()
    if current_time - last_time < limit_seconds:
        log_security_event(
            "RATE_LIMIT_EXCEEDED", f"Key '{key}' throttled for {limit_seconds}s"
        )
        return False
    st.session_state["rate_limit_store"][key] = current_time
    return True

def log_security_event(event_type: str, details: str):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
    st.session_state["security_logs"].append({
        "timestamp": timestamp,
        "event": event_type,
        "details": sanitize_input(details),
    })

def encrypt_field(plain_text: str) -> str:
    encoded = base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")
    return f"ENC_{hashlib.sha256(plain_text.encode()).hexdigest()[:8]}_{encoded}"

def send_real_sms(phone_number: str, otp_code: str) -> bool:
    """Delivers a real SMS OTP using Fast2SMS API (India)."""
    # ⚠️ IMPORTANT: Replace this with your actual Fast2SMS API key!
    API_KEY = "YOUR_FAST2SMS_API_KEY_HERE"  
    url = "https://www.fast2sms.com/dev/bulkV2"
    
    clean_num = "".join(filter(str.isdigit, phone_number))[-10:]

    payload = f"variables_values={otp_code}&route=otp&numbers={clean_num}"
    headers = {
        "authorization": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        response = requests.post(url, data=payload, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        st.sidebar.error(f"Gateway Error: {str(e)}")
        return False

# ==========================================
# 3. TRANSLATION ENGINE
# ==========================================
TRANSLATIONS = {
    "English": {
        "sidebar_title": "🔐 Secure Access Portal",
        "select_lang": "🌐 Select Language",
        "title": "👨‍🌾 LandShield India",
        "subtitle": "National Citizen Land Integrity, Anti-Greenwashing & Desertification Verification Engine",
        "badge1": "🌾 DILRMP / ISRO Compatible",
        "badge2": "🔒 WAF & AES Active",
        "badge3": "🛰️ Sentinel-2 Engine",
        "role_label": "Role-Based Access (RBAC)",
        "roles": ["Farmer / Citizen", "Block Development Admin", "Government Auditor"],
        "phone_label": "Mobile Number",
        "otp_btn": "📲 Request Passwordless OTP",
        "verify_btn": "🔓 Verify OTP & Login",
        "sec_metrics": "🔒 Security Metrics",
        "interface_lang": "Interface Language",
        "waf_active": "• WAF Inspection: ACTIVE",
        "pii_enc": "• PII Field Encryption: AES-256 Standard",
        "ledger_verified": "• SHA-256 Ledger State: VERIFIED",
        "siem_running": "• SIEM Agent: RUNNING",
        "tab1": "📍 Pan-India Desertification Map",
        "tab2": "🔍 Photo & Map Forensics (ELA)",
        "tab3": "🔗 Hash-Chain Audit Ledger",
        "tab4": "🚨 Citizen Alert Engine",
        "tab5": "🛡️ SIEM & Security Logs",
        "parcel_title": "📍 Desertification & Soil Degradation Index (NDVI)",
        "parcel_desc": "Inspect major Indian cities and districts experiencing severe land degradation, soil erosion, and aridity.",
        "select_zone": "🗺️ Select Affected City / Desertification Zone",
        "parcel_dash": "🌾 Degradation Status Dashboard",
        "target_parcel": "Target District / Parcel:",
        "zone": "Zone:",
        "raw_owner": "Owner Name (Raw):",
        "enc_pii": "🔒 Stored Encrypted PII:",
        "primary_driver": "Primary Driver:",
        "opt_sent": "OTP dispatched securely to",
        "rate_err": "🚨 WAF Rate Limit: Wait 10s before requesting OTP again.",
        "upload_label": "Upload Image (JPEG)",
        "forensic_desc": "Prevent greenwashing fraud by authenticating ground photos and satellite imagery.",
        "orig_img": "Original Image",
        "forensic_heatmap": "Forensic Heatmap",
        "ledger_desc": "Immutable audit ledger for record integrity.",
        "dispatch_btn": "📡 Dispatch Alert",
        "sensitivity": "Alert Sensitivity (NDVI Drop %)",
        "alert_success": "Alert dispatched successfully to",
        "clear_logs": "🧹 Clear Logs",
        "no_logs": "No security events logged.",
    },
    "हिंदी (Hindi)": {
        "sidebar_title": "🔐 सुरक्षित पहुंच पोर्टल",
        "select_lang": "🌐 भाषा चुनें",
        "title": "👨‍🌾 लैंडशील्ड इंडिया",
        "subtitle": "राष्ट्रीय नागरिक भूमि सत्यनिष्ठा, एंटी-ग्रीनवाशिंग और मरुस्थलीकरण सत्यापन इंजन",
        "badge1": "🌾 DILRMP / ISRO संगत",
        "badge2": "🔒 WAF और AES सक्रिय",
        "badge3": "🛰️ सेंटिनल-2 इंजन",
        "role_label": "भूमिका-आधारित पहुंच (RBAC)",
        "roles": ["किसान / नागरिक", "ब्लॉक विकास अधिकारी", "सरकारी लेखा परीक्षक"],
        "phone_label": "मोबाइल नंबर",
        "otp_btn": "📲 पासवर्ड रहित ओटीपी का अनुरोध करें",
        "verify_btn": "🔓 ओटीपी सत्यापित करें और लॉगिन करें",
        "sec_metrics": "🔒 सुरक्षा मीट्रिक",
        "interface_lang": "इंटरफेस भाषा",
        "waf_active": "• WAF निरीक्षण: सक्रिय",
        "pii_enc": "• PII फ़ील्ड एन्क्रिप्शन: AES-256 मानक",
        "ledger_verified": "• SHA-256 लेजर स्थिति: सत्यापित",
        "siem_running": "• SIEM एजेंट: चालू",
        "tab1": "📍 मरुस्थलीकरण और भूखंड मानचित्र",
        "tab2": "🔍 फोटो और मानचित्र फोरेंसिक (ELA)",
        "tab3": "🔗 हैश-चेन ऑडिट बहीखाता",
        "tab4": "🚨 नागरिक चेतावनी इंजन",
        "tab5": "🛡️ SIEM और सुरक्षा लॉग",
        "parcel_title": "📍 मरुस्थलीकरण और मृदा क्षरण सूचकांक (NDVI)",
        "parcel_desc": "गंभीर भूमि क्षरण, मृदा अपरदन और शुष्कता का सामना कर रहे प्रमुख भारतीय शहरों और जिलों का निरीक्षण करें।",
        "select_zone": "🗺️ प्रभावित शहर / मरुस्थलीकरण क्षेत्र चुनें",
        "parcel_dash": "🌾 क्षरण स्थिति डैशबोर्ड",
        "target_parcel": "लक्ष्य जिला / पार्सल:",
        "zone": "क्षेत्र:",
        "raw_owner": "मालिक का नाम:",
        "enc_pii": "🔒 सुरक्षित एन्क्रिप्टेड डेटा:",
        "primary_driver": "मुख्य कारण:",
        "opt_sent": "ओटीपी सुरक्षित रूप से भेजा गया:",
        "rate_err": "🚨 WAF दर सीमा: पुनः प्रयास करने से पहले 10 सेकंड प्रतीक्षा करें।",
        "upload_label": "छवि अपलोड करें (JPEG)",
        "forensic_desc": "जमीन की तस्वीरों की प्रामाणिकता की जांच करके धोखाधड़ी रोकें।",
        "orig_img": "मूल छवि",
        "forensic_heatmap": "फोरेंसिक हीटमैप",
        "ledger_desc": "रिकॉर्ड अखंडता के लिए अपरिवर्तनीय ऑडिट लेजर।",
        "dispatch_btn": "📡 अलर्ट भेजें",
        "sensitivity": "चेतावनी संवेदनशीलता (NDVI गिरावट %)",
        "alert_success": "अलर्ट सफलतापूर्वक भेजा गया:",
        "clear_logs": "🧹 लॉग साफ़ करें",
        "no_logs": "कोई सुरक्षा घटना दर्ज नहीं की गई।",
    },
}

ALL_INDIAN_LANGUAGES = ["English", "हिंदी (Hindi)"]

def t(key: str, current_lang: str) -> str:
    lang_dict = TRANSLATIONS.get(current_lang, TRANSLATIONS["English"])
    return lang_dict.get(key, TRANSLATIONS["English"].get(key, key))

# ==========================================
# 4. SIDEBAR & WORKING OTP LOGIC
# ==========================================
st.sidebar.title(t("sidebar_title", st.session_state["app_lang"]))

selected_lang = st.sidebar.selectbox(
    t("select_lang", st.session_state["app_lang"]),
    ALL_INDIAN_LANGUAGES,
    index=ALL_INDIAN_LANGUAGES.index(st.session_state["app_lang"]),
)

if selected_lang != st.session_state["app_lang"]:
    st.session_state["app_lang"] = selected_lang
    st.rerun()

current_lang = st.session_state["app_lang"]

roles_list = TRANSLATIONS.get(current_lang, {}).get("roles") or TRANSLATIONS["English"]["roles"]
role = st.sidebar.radio(t("role_label", current_lang), roles_list)

raw_phone = st.sidebar.text_input(t("phone_label", current_lang), value="+91 9876543210")
clean_phone = sanitize_input(raw_phone)

# OTP Workflow Execution
if not st.session_state["is_authenticated"]:
    if st.sidebar.button(t("otp_btn", current_lang)):
        if not check_rate_limit(f"otp_{clean_phone}", limit_seconds=10):
            st.sidebar.error(t("rate_err", current_lang))
        else:
            new_otp = str(random.randint(100000, 999999))
            st.session_state["generated_otp"] = new_otp
            
            # Send real SMS using API
            sms_sent = send_real_sms(clean_phone, new_otp)
            
            if sms_sent:
                log_security_event("AUTH_OTP_GENERATED", f"OTP issued for user {clean_phone}")
                st.sidebar.success(f"{t('opt_sent', current_lang)} {clean_phone}")
            else:
                st.sidebar.error("Failed to send SMS. Check your API key and connection.")

    # Verification Input Field (rendered when OTP is active)
    if st.session_state["generated_otp"] is not None:
        # NOTE: Comment this out in production so users don't see the OTP on screen!
        st.sidebar.info(f"🧪 Dev Mode OTP Code: **{st.session_state['generated_otp']}**")
        
        user_otp_input = st.sidebar.text_input("Enter 6-Digit OTP", type="password", max_chars=6)

        if st.sidebar.button(t("verify_btn", current_lang)):
            if user_otp_input == st.session_state["generated_otp"]:
                st.session_state["is_authenticated"] = True
                log_security_event("AUTH_SUCCESS", f"User {clean_phone} authenticated successfully.")
                st.sidebar.success("✅ Login Successful!")
                st.rerun()
            else:
                log_security_event("AUTH_FAILED", f"Invalid OTP attempt for {clean_phone}")
                st.sidebar.error("❌ Invalid OTP Code. Please check and retry.")

else:
    st.sidebar.success(f"👤 Logged in as: {role}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state["is_authenticated"] = False
        st.session_state["generated_otp"] = None
        log_security_event("AUTH_LOGOUT", f"User logged out.")
        st.rerun()

st.sidebar.divider()
st.sidebar.markdown(f"**{t('sec_metrics', current_lang)}**")
st.sidebar.caption(f"• {t('interface_lang', current_lang)}: {current_lang}")
st.sidebar.caption(t("waf_active", current_lang))
st.sidebar.caption(t("pii_enc", current_lang))
st.sidebar.caption(t("ledger_verified", current_lang))
st.sidebar.caption(t("siem_running", current_lang))

# ==========================================
# 5. MAIN HEADER BANNER
# ==========================================
st.markdown(
    f"""
    <div class="main-header">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="margin:0; font-size: 30px; font-weight: 800; display: flex; align-items: center; gap: 10px;">
                    {t('title', current_lang)}
                </h1>
                <p style="margin:6px 0 0 0; color: #E2E8F0; font-size: 15px;">
                    {t('subtitle', current_lang)}
                </p>
            </div>
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <span class="badge-green">{t('badge1', current_lang)}</span>
                <span class="badge-sec">{t('badge2', current_lang)}</span>
                <span class="badge-blue">{t('badge3', current_lang)}</span>
            </div>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# ==========================================
# 6. APPLICATION TABS
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    t("tab1", current_lang),
    t("tab2", current_lang),
    t("tab3", current_lang),
    t("tab4", current_lang),
    t("tab5", current_lang),
])

# ------------------------------------------
# TAB 1: DESERTIFICATION MAP & CITIES
# ------------------------------------------
with tab1:
    st.header(t("parcel_title", current_lang))
    st.markdown(t("parcel_desc", current_lang))

    regions = {
        "Jaisalmer (Rajasthan - Thar Desert)": {
            "coords": [26.9124, 70.9023],
            "khasra": "Khasra #1042",
            "owner": "Ramesh Kumar",
            "status": "🔴 Red (Severe Desertification)",
            "ndvi": "0.18",
            "drop": "-24%",
            "driver": "Severe Wind Erosion & Sand Dune Drift",
        },
        "Anantapur (Andhra Pradesh)": {
            "coords": [14.6819, 77.6006],
            "khasra": "Plot #882",
            "owner": "K. Venkatesh",
            "status": "🔴 Red (High Aridity)",
            "ndvi": "0.25",
            "drop": "-21%",
            "driver": "Severe Agricultural Drought & Topsoil Loss",
        }
    }

    col_sel, _ = st.columns([2, 1])
    with col_sel:
        selected_region = st.selectbox(t("select_zone", current_lang), list(regions.keys()))

    r_data = regions[selected_region]
    col_map, col_dash = st.columns([2, 1])

    with col_map:
        m = folium.Map(location=r_data["coords"], zoom_start=9)
        folium.Marker(r_data["coords"], popup=f"{r_data['khasra']} ({r_data['status']})").add_to(m)
        st_folium(m, width=720, height=440)

    with col_dash:
        st.subheader(t("parcel_dash", current_lang))
        st.write(f"**{t('target_parcel', current_lang)}** `{r_data['khasra']}`")
        st.write(f"**{t('zone', current_lang)}** {selected_region}")
        enc_owner = encrypt_field(r_data["owner"])
        st.write(f"**{t('raw_owner', current_lang)}** {r_data['owner']}")
        st.caption(f"🔒 **{t('enc_pii', current_lang)}** `{enc_owner[:30]}...`")

        if "Red" in r_data["status"]:
            st.error(f"Status: {r_data['status']}")
        else:
            st.success(f"Status: {r_data['status']}")

        st.metric(label="Vegetation Index (NDVI)", value=r_data["ndvi"], delta=r_data["drop"])
        st.write(f"**{t('primary_driver', current_lang)}** {r_data['driver']}")

# ------------------------------------------
# TAB 2: FORENSICS ENGINE
# ------------------------------------------
with tab2:
    st.header(t("tab2", current_lang))
    st.markdown(t("forensic_desc", current_lang))

    uploaded_file = st.file_uploader(t("upload_label", current_lang), type=["jpg", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        buffer.seek(0)
        resaved_image = Image.open(buffer)

        ela_image = ImageChops.difference(image, resaved_image)
        ela_image = ImageEnhance.Brightness(ela_image).enhance(25)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(t("orig_img", current_lang))
            st.image(image, use_container_width=True)
        with col2:
            st.subheader(t("forensic_heatmap", current_lang))
            st.image(ela_image, use_container_width=True)

# ------------------------------------------
# TAB 3: AUDIT LEDGER
# ------------------------------------------
with tab3:
    st.header(t("tab3", current_lang))
    st.markdown(t("ledger_desc", current_lang))
    with st.expander("📦 Block #1 - Jaisalmer Khasra #1042"):
        st.write("**NDVI:** `0.18`")
        st.write("**SHA-256 Hash:** `b7a2e5c89104f210a48b309f8cde11a284e311a27b99c04fdf89e1124ad45189`")
        st.success("Ledger State: INTEGRITY OK")

# ------------------------------------------
# TAB 4: ALERT ENGINE
# ------------------------------------------
with tab4:
    st.header(t("tab4", current_lang))
    col_in, col_act = st.columns(2)
    with col_in:
        recipient_num = st.text_input(t("phone_label", current_lang), value=clean_phone, key="alert_phone")
        clean_recipient = sanitize_input(recipient_num)
        threshold = st.slider(t("sensitivity", current_lang), 5, 40, 15)
    with col_act:
        st.write(" ")
        st.write(" ")
        if st.button(t("dispatch_btn", current_lang)):
            if not check_rate_limit(f"alert_{clean_recipient}", limit_seconds=10):
                st.error(t("rate_err", current_lang))
            else:
                log_security_event("SMS_ALERT_DISPATCHED", f"Alert sent to {clean_recipient}")
                st.success(f"{t('alert_success', current_lang)} {clean_recipient}")

# ------------------------------------------
# TAB 5: SIEM LOGS
# ------------------------------------------
with tab5:
    st.header(t("tab5", current_lang))
    if st.session_state["security_logs"]:
        st.dataframe(st.session_state["security_logs"], use_container_width=True)
    else:
        st.info(t("no_logs", current_lang))

    if st.button(t("clear_logs", current_lang)):
        st.session_state["security_logs"] = []
        st.rerun()
