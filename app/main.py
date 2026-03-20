import streamlit as st
import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.views import admin_view, student_view
from app.views import admin_view, student_view
from app.core.database import engine, SessionLocal
from app.core.models import Base, User          

# Keep the wide layout and collapsed sidebar
st.set_page_config(page_title="Course Assessment Portal", layout="wide", initial_sidebar_state="collapsed")

def get_db():
    db = SessionLocal()
    try: return db
    finally: db.close()

# --- BULLETPROOF INLINE CSS FOR ANIMATIONS & GLASSMORPHISM ---
st.markdown("""
<style>
    /* 1. AGGRESSIVELY NUKE ALL STREAMLIT ARTIFACTS GLOBALLY */
    [data-testid="stToolbar"], 
    [data-testid="stHeader"], 
    [data-testid="stAppDeployButton"],
    .stAppDeployButton,
    #MainMenu, 
    header, 
    footer { 
        display: none !important; 
        visibility: hidden !important; 
        opacity: 0 !important;
        pointer-events: none !important;
        height: 0 !important;
        width: 0 !important;
        position: absolute !important;
        z-index: -9999 !important;
    }

    /* 2. Base Container Styling */
    .block-container {
        padding-top: 1rem !important; 
        padding-bottom: 0rem !important;
        max-width: 95% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }

    /* 3. Hide Streamlit Anchor/Chain Links on text */
    .stMarkdown a.header-anchor,
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* --- PERMANENT DATA ENGINEERING WATERMARK --- */
    [data-testid="stApp"]::after {
        content: "";
        position: fixed;
        bottom: -5%;
        right: -5%;
        width: 800px;
        height: 800px;
        background-image: url("data:image/svg+xml,%3Csvg width='800' height='800' viewBox='0 0 24 24' fill='none' stroke='%232DD4BF' stroke-width='0.4' stroke-linecap='round' stroke-linejoin='round' xmlns='http://www.w3.org/2000/svg'%3E%3Cellipse cx='12' cy='5' rx='9' ry='3'%3E%3C/ellipse%3E%3Cpath d='M21 12c0 1.66-4 3-9 3s-9-1.34-9-3'%3E%3C/path%3E%3Cpath d='M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5'%3E%3C/path%3E%3Ccircle cx='12' cy='12' r='1.5'%3E%3C/circle%3E%3Cpath d='M12 13.5v4'%3E%3C/path%3E%3Ccircle cx='12' cy='19' r='1.5'%3E%3C/circle%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-size: contain;
        opacity: 0.04;
        z-index: 0;
        pointer-events: none;
    }
    
    /* --- AMBIENT NON-DISTRACTING BACKGROUND --- */
    .aurora-bg::before {
        content: "";
        position: fixed;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: 
            radial-gradient(circle at 40% 50%, rgba(45, 212, 191, 0.04) 0%, transparent 40%),
            radial-gradient(circle at 70% 30%, rgba(79, 70, 229, 0.03) 0%, transparent 50%);
        z-index: -3;
        pointer-events: none;
        animation: slowDrift 25s ease-in-out infinite alternate;
    }
    @keyframes slowDrift {
        0% { transform: rotate(0deg) scale(1) translate(0, 0); }
        100% { transform: rotate(2deg) scale(1.02) translate(-1%, 1%); }
    }
    
    /* --- THE GLOWING LOGO & RINGS --- */
    .glowing-logo-wrapper {
        position: relative;
        width: 300px;
        height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 20px auto;
    }
    
    .glowing-core {
        font-size: 4.5rem;
        color: #2DD4BF;
        background: rgba(15, 23, 42, 0.5);
        border: 2px solid rgba(45, 212, 191, 0.8);
        border-radius: 50%;
        width: 120px;
        height: 120px;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
        box-shadow: 0 0 30px rgba(45, 212, 191, 0.5), inset 0 0 20px rgba(45, 212, 191, 0.3);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        animation: floatLogo 4s ease-in-out infinite;
    }
    
    .ring {
        position: absolute;
        border-radius: 50%;
        border: 1px solid rgba(45, 212, 191, 0.6);
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: pulseRing 3s infinite linear;
        box-shadow: 0 0 15px rgba(45, 212, 191, 0.2);
    }
    
    .ring1 { animation-delay: 0s; }
    .ring2 { animation-delay: 1s; }
    .ring3 { animation-delay: 2s; }
    
    @keyframes pulseRing {
        0% { width: 120px; height: 120px; opacity: 1; }
        100% { width: 350px; height: 350px; opacity: 0; }
    }
    
    @keyframes floatLogo {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }

    /* --- GLASSMORPHISM LOGIN CARD --- */
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(40px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    [data-testid="stForm"] {
        position: relative;
        overflow: hidden; 
        background: rgba(15, 23, 42, 0.5) !important;
        border: 1px solid rgba(45, 212, 191, 0.2) !important;
        border-radius: 16px !important;
        padding: 25px 30px !important; 
        box-shadow: 0 15px 50px 0 rgba(0, 0, 0, 0.6), inset 0 0 20px rgba(255,255,255,0.03) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        animation: slideUpFade 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
    }
    
    .welcome-text {
        text-align: center;
        color: #F8FAFC;
        margin-top: 0px;
        margin-bottom: 5px;
        font-weight: 600;
        font-size: 2rem;
        letter-spacing: 0.5px;
    }
    .welcome-sub {
        text-align: center;
        color: #94A3B8;
        font-size: 1rem;
        margin-bottom: 25px; 
    }
    .accent-text { color: #2DD4BF; }
</style>
""", unsafe_allow_html=True)

# Inject the Data Engineering Watermark and Aurora BG globally
st.markdown('<div class="aurora-bg"></div><div class="data-watermark"></div>', unsafe_allow_html=True)

# --- CREATE TABLES IF THEY DON'T EXIST ---
Base.metadata.create_all(bind=engine)

# --- INITIALIZE MASTER ADMIN ---
def init_master_admin():
    db = get_db()
    master = db.query(User).filter(User.email == "larryvander580@gmail.com").first()
    if not master:
        master_user = User(email="larryvander580@gmail.com", name="Master Admin", password="admin123", role="instructor", is_master=True)
        if hasattr(master_user, 'needs_password_change'):
            master_user.needs_password_change = False 
        db.add(master_user)
        db.commit()

init_master_admin()

# --- INITIALIZE SESSION STATE ---
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = None
if 'show_login' not in st.session_state: st.session_state['show_login'] = False
if 'show_forgot_password' not in st.session_state: st.session_state['show_forgot_password'] = False

# =====================================================================
# DYNAMIC CENTERING CSS (Only triggers when logged out)
# =====================================================================
if st.session_state['user_id'] is None:
    st.markdown("""
    <style>
        /* Hide scrollbars completely for the login/landing screens */
        ::-webkit-scrollbar { display: none; }
        html, body, [data-testid="stAppViewContainer"] { 
            overflow: hidden !important; 
        }
        /* Force absolute vertical and horizontal centering */
        .block-container {
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            width: 100% !important;
            padding-top: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- GLOBAL TOP NAVIGATION ---
if st.session_state['user_id'] is not None:
    nav1, nav2, nav3 = st.columns([1, 6, 2.5])
    
    with nav1:
        if st.button("⌂ Home", use_container_width=True):
            # ROUTING FIX: Wipe all sub-states so admin/student modules reset to their default views
            keys_to_keep = ['user_id', 'user_role', 'user_name', 'is_master', 'view_mode', 'needs_password_change']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            
            st.session_state['view_mode'] = st.session_state.get('user_role')
            st.rerun()
            
    with nav3:
        sub_col1, sub_col2 = st.columns(2)
        if st.session_state.get('user_role') == 'instructor':
            with sub_col1:
                toggle_btn = "👤 Learner View" if st.session_state['view_mode'] == 'instructor' else "⚙️ Admin View"
                if st.button(toggle_btn, use_container_width=True):
                    st.session_state['view_mode'] = 'student' if st.session_state['view_mode'] == 'instructor' else 'instructor'
                    st.rerun()
        with sub_col2:
            if st.button("Log Out ⎋", use_container_width=True):
                st.session_state.clear() 
                st.rerun()
                
    st.markdown("<div style='margin-top:-10px; margin-bottom: 20px; border-bottom: 1px solid #374151;'></div>", unsafe_allow_html=True)

# --- PASSWORD CHANGE INTERCEPTOR ---
def show_password_change_screen():
    _, pw_col, _ = st.columns([1, 1.5, 1])
    
    with pw_col:
        st.markdown("<div style='text-align:center; font-size:3rem; margin-bottom: -15px;'>🔒</div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center; color:#F8FAFC; margin-top:0px;'>Security Action Required</h2>", unsafe_allow_html=True)
        
        st.markdown("<div style='text-align:center; color:#94A3B8; margin-bottom: 20px;'>You are using a default assigned password. Please set a new secure password to proceed.</div>", unsafe_allow_html=True)
        
        with st.form("change_pwd_form", border=False):
            new_pwd = st.text_input("New Password", type="password")
            confirm_pwd = st.text_input("Confirm New Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)
            
            if submitted:
                if len(new_pwd) < 6: 
                    st.error("Password must be at least 6 characters.")
                elif new_pwd != confirm_pwd: 
                    st.error("Passwords do not match. Please try again.")
                else:
                    db = get_db()
                    user = db.query(User).filter(User.id == st.session_state['user_id']).first()
                    user.password = new_pwd
                    
                    if hasattr(user, 'needs_password_change'):
                        user.needs_password_change = False
                        
                    db.commit()
                    st.session_state['needs_password_change'] = False
                    st.success("Password updated securely! Redirecting...")
                    time.sleep(1)
                    st.rerun()

# =====================================================================
# MAIN ROUTING LOGIC
# =====================================================================

if st.session_state['user_id'] is None:

    if not st.session_state['show_login']:
        st.markdown("""
        <div class="glowing-logo-wrapper">
            <div class="ring ring1"></div>
            <div class="ring ring2"></div>
            <div class="ring ring3"></div>
            <div class="glowing-core">❖</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <h1 style='text-align:center; font-size: 3.5rem; font-weight: 800; line-height: 1.15; margin-top: 0px; color: #F8FAFC;'>
            Data Knowledge <span class='accent-text'>Assessment</span>
        </h1>
        <p style='text-align:center; color:#94A3B8; font-size:1.1rem; max-width:600px; margin: 15px auto 30px auto;'>
            A secure, interactive workspace to validate your SQL and Python skills through real-world scenarios.
        </p>
        """, unsafe_allow_html=True)

        _, btn_col, _ = st.columns([1.5, 1, 1.5])
        with btn_col:
            if st.button("Enter Workspace ➔", type="primary", use_container_width=True):
                st.session_state['show_login'] = True
                st.rerun()

    else:
        _, auth_col, _ = st.columns([1.5, 1.2, 1.5]) 
        
        with auth_col:
            
            if not st.session_state['show_forgot_password']:
                
                st.markdown("""
                <div style='text-align:center; margin-bottom: -15px; position:relative; z-index:20;'>
                    <div style='display:inline-block; font-size: 3rem; color: #2DD4BF; text-shadow: 0 0 20px rgba(45,212,191,0.6);'>❖</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.form("unified_login_form"):
                    st.markdown("<p class='welcome-text'>Welcome Back</p>", unsafe_allow_html=True)
                    st.markdown("<p class='welcome-sub'>Sign in to continue to your workspace</p>", unsafe_allow_html=True)
                    
                    email_input = st.text_input("Email Address", placeholder="user@domain.com", autocomplete="email")
                    password_input = st.text_input("Password", type="password", placeholder="••••••••")
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    submitted = st.form_submit_button("Secure Login", type="primary", use_container_width=True)
                    
                    if submitted:
                        if not email_input or not password_input:
                            st.error("Please enter both email and password.")
                        else:
                            db = get_db()
                            user = db.query(User).filter(User.email == email_input).first()
                            
                            if user and user.password == password_input:
                                st.session_state['user_id'] = user.id
                                st.session_state['user_role'] = user.role
                                st.session_state['user_name'] = user.name or user.email.split("@")[0]
                                st.session_state['is_master'] = user.is_master
                                st.session_state['view_mode'] = user.role 
                                
                                if hasattr(user, 'needs_password_change'):
                                    st.session_state['needs_password_change'] = user.needs_password_change
                                elif password_input in ["admin123", "student123"]:
                                    st.session_state['needs_password_change'] = True
                                else:
                                    st.session_state['needs_password_change'] = False
                                    
                                st.rerun()
                            else:
                                st.error("Invalid credentials. Access denied.")
                
                sub_col1, sub_col2 = st.columns(2)
                with sub_col1:
                    if st.button("← Back Home", use_container_width=True):
                        st.session_state['show_login'] = False
                        st.rerun()
                with sub_col2:
                    if st.button("Forgot Password?", type="tertiary", use_container_width=True):
                        st.session_state['show_forgot_password'] = True
                        st.rerun()
                
            else:
                st.markdown("<div style='text-align:center; font-size:3rem; margin-bottom: -5px; color:#94A3B8;'>⟳</div>", unsafe_allow_html=True)
                st.markdown("<h3 style='text-align:center; margin-top: 0px; margin-bottom: 15px; color:#F8FAFC;'>Account Recovery</h3>", unsafe_allow_html=True)
                
                with st.container(border=True):
                    st.info("To regain access, please request a password reset from the course administrator.")
                    st.markdown("**Admin Contact:** `larryvander580@gmail.com`")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Return to Login", use_container_width=True):
                    st.session_state['show_forgot_password'] = False
                    st.rerun()

# -----------------------------------------------------------------
# POST-LOGIN ROUTING
# -----------------------------------------------------------------
elif st.session_state.get('needs_password_change'):
    show_password_change_screen()

else:
    current_view = st.session_state.get('view_mode')
    if current_view == 'instructor':
        admin_view.admin_dashboard()
    elif current_view == 'student':
        student_view.student_portal()