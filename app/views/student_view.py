import streamlit as st
import pandas as pd
import sqlite3
import json
import sys
import io
import os
import traceback
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.core.models import Quiz, Question, User, Submission, Answer
from code_editor import code_editor

def get_db():
    db = SessionLocal()
    try: return db
    finally: db.close()

# --- Helper for West Africa Time (WAT) ---
def get_wat_time():
    return datetime.utcnow() + timedelta(hours=1)

# --- DRACULA PRO IDE CSS & DASHBOARD CARDS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,600&display=swap');
    
    [data-testid="stToolbar"], [data-testid="stHeader"], [data-testid="stAppDeployButton"],
    .stAppDeployButton, header, footer { display: none !important; }
    
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 98% !important; 
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(15, 23, 42, 0.2) !important;
        border: 0.5px solid rgba(45, 212, 191, 0.15) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    /* Cool Welcome Text */
    .elegant-title {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-weight: 600;
        font-size: 1.45rem;
        color: #38BDF8;
        letter-spacing: 0.5px;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.3);
    }

    /* Mac Window Header */
    .mac-window {
        background: #282A36 !important;
        border: 1px solid #44475A !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0 0;
        margin-top: -10px;
    }
    .mac-header {
        background: #1E1F29 !important;
        padding: 6px 12px;
        display: flex;
        align-items: center;
        border-radius: 8px 8px 0 0;
    }
    .mac-dot { width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
    .mac-dot.red { background: #FF5555; }
    .mac-dot.yellow { background: #F1FA8C; }
    .mac-dot.green { background: #50FA7B; }
    .mac-title { color: #6272A4; font-size: 11px; margin-left: auto; margin-right: auto; font-family: monospace; }

    /* Terminal Outputs */
    .console-output {
        background-color: #282A36 !important;
        color: #F8F8F2;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #44475A !important;
        margin-top: 5px; 
        white-space: pre-wrap;
    }
    .console-label {
        color: #6272A4;
        font-size: 10px;
        text-transform: uppercase;
        margin-bottom: 2px;
        margin-top: 10px;
        font-weight: bold;
        letter-spacing: 0.5px;
    }
    .console-error-output {
        background-color: #282A36 !important;
        color: #FF5555;
        font-family: monospace;
        font-size: 13px;
        padding: 12px;
        border-radius: 6px;
        border: 1px solid #FF5555 !important;
        margin-top: 5px; 
    }

    .problem-box {
        background: rgba(15, 23, 42, 0.7);
        border-left: 4px solid #38BDF8;
        border-radius: 6px;
        padding: 12px 15px;
        margin-bottom: 10px;
        color: #F8FAFC;
        font-size: 0.95rem;
    }
    
    .result-banner-correct { background: rgba(80, 250, 123, 0.1); border: 1px solid #50FA7B; color: #50FA7B; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-weight: bold; text-align: center; }
    .result-banner-incorrect { background: rgba(255, 85, 85, 0.1); border: 1px solid #FF5555; color: #FF5555; padding: 10px; border-radius: 6px; margin-bottom: 10px; font-weight: bold; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- PROFESSIONAL DATA TOOLS ---

def generate_mermaid_erd(dataset_path):
    try:
        if dataset_path and (dataset_path.endswith('.db') or dataset_path.endswith('.sqlite')):
            conn = sqlite3.connect(dataset_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
            mermaid_code = "erDiagram\n"
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                cols = cursor.fetchall()
                mermaid_code += f"    {table} {{\n"
                for col in cols: mermaid_code += f"        {col[2]} {col[1]}\n"
                mermaid_code += "    }\n"
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                for fk in cursor.fetchall():
                    mermaid_code += f"    {table} ||--o{{ {fk[2]} : \"{fk[3]}\"\n"
            conn.close()
            return mermaid_code
        return ""
    except: return ""

def get_table_previews(dataset_path):
    previews = {}
    if not dataset_path or not os.path.exists(dataset_path): return previews
    try:
        if dataset_path.endswith('.db') or dataset_path.endswith('.sqlite'):
            conn = sqlite3.connect(dataset_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall() if t[0] != 'sqlite_sequence']
            for table in tables: previews[table] = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5", conn)
            conn.close()
        elif dataset_path.endswith('.csv'): previews['Dataset'] = pd.read_csv(dataset_path, nrows=5)
        elif dataset_path.endswith('.parquet'): previews['Dataset'] = pd.read_parquet(dataset_path).head(5)
        elif dataset_path.endswith('.xlsx'): previews['Dataset'] = pd.read_excel(dataset_path, nrows=5)
        elif dataset_path.endswith('.json'): previews['Dataset'] = pd.read_json(dataset_path).head(5)
    except: pass
    return previews

def execute_python(code, dataset_path=None):
    if not code or not str(code).strip(): return "", None
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    env = {}
    if dataset_path and os.path.exists(dataset_path): env['DATASET_PATH'] = dataset_path
    try:
        exec(code, env)
        return redirected_output.getvalue().strip(), None
    except Exception: return None, traceback.format_exc()
    finally: sys.stdout = old_stdout

def execute_sql(query, dataset_path=None):
    if not query or not str(query).strip(): return pd.DataFrame(), None
    conn = None
    try:
        if not dataset_path or not os.path.exists(dataset_path): conn = sqlite3.connect(':memory:')
        else: conn = sqlite3.connect(dataset_path)
        return pd.read_sql_query(query, conn), None
    except TypeError as e:
        if "'NoneType' object is not iterable" in str(e):
            return pd.DataFrame({"Terminal Status": ["Query executed successfully. No table data returned."]}), None
        return None, str(e)
    except Exception as e: 
        return None, str(e)
    finally:
        if conn: conn.close()

# --- MAIN ROUTING LOGIC ---
def student_portal():
    db = get_db()
    
    if 'active_quiz_id' not in st.session_state: st.session_state['active_quiz_id'] = None
    if 'confirm_submit' not in st.session_state: st.session_state['confirm_submit'] = False

    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 5px; margin-bottom: 15px;">
            <div style="font-size: 1.2rem; font-weight: 500; color: #E0E7FF;">
                Welcome, <span class="elegant-title">{st.session_state.get('user_name', 'Learner')}</span>
            </div>
            <div class="status-badge">Secure Session</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state['active_quiz_id'] is None:
        render_dashboard(db)
    else:
        render_workspace(db, st.session_state['active_quiz_id'])

# --- VIEW 1: THE DASHBOARD ---
def render_dashboard(db):
    st.markdown('<div class="section-header">Your Learning Modules</div>', unsafe_allow_html=True)
    
    quizzes = db.query(Quiz).filter(Quiz.active == True).all()
    if not quizzes:
        st.info("No active assessments assigned to you at this time.")
        return

    quizzes.sort(key=lambda q: q.due_date if q.due_date else datetime.max)

    for quiz in quizzes:
        existing_sub = db.query(Submission).filter(
            Submission.student_id == st.session_state['user_id'], 
            Submission.quiz_id == quiz.quiz_id
        ).first()
        
        wat_now = get_wat_time()
        is_past_deadline = quiz.due_date and wat_now > quiz.due_date
        
        if existing_sub and is_past_deadline:
            status_text = f"Graded - Score: {existing_sub.score}"
            status_color = "#50FA7B"
            btn_label = "Review Results"
        elif existing_sub and not is_past_deadline:
            status_text = "Draft Auto-Saved (Editable)"
            status_color = "#F1FA8C"
            btn_label = "Continue Assessment"
        elif not existing_sub and is_past_deadline:
            status_text = "Missed Deadline"
            status_color = "#FF5555"
            btn_label = "View Locked Assessment"
        else:
            status_text = "Pending"
            status_color = "#38BDF8"
            btn_label = "Start Assessment"

        deadline_str = quiz.due_date.strftime("%b %d, %Y - %I:%M %p WAT") if quiz.due_date else "No Deadline"

        with st.container(border=True):
            col_info, col_action = st.columns([3, 1], gap="small")
            
            with col_info:
                st.markdown(f"""
                <div style="margin-bottom: 4px;">
                    <span style="font-size: 1.15rem; font-weight: 600; color: #F8FAFC;">{quiz.title}</span>
                </div>
                <div style="font-size: 0.9rem; color: #94A3B8; margin-bottom: 10px;">{quiz.description}</div>
                <div style="font-size: 0.8rem; color: #64748B;">
                    <span style="margin-right: 15px;"><b>Deadline:</b> {deadline_str}</span>
                    <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with col_action:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                if st.button(btn_label, key=f"btn_{quiz.quiz_id}", use_container_width=True, type="primary" if "Start" in btn_label or "Continue" in btn_label else "secondary"):
                    st.session_state['active_quiz_id'] = quiz.quiz_id
                    st.rerun()
                    
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- VIEW 2: THE WORKSPACE & REVIEW MODE ---
def render_workspace(db, quiz_id):
    quiz = db.query(Quiz).filter(Quiz.quiz_id == quiz_id).first()
    questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
    
    existing_sub = db.query(Submission).filter(
        Submission.student_id == st.session_state['user_id'], 
        Submission.quiz_id == quiz.quiz_id
    ).first()
    
    wat_now = get_wat_time()
    is_past_deadline = quiz.due_date and wat_now > quiz.due_date
    is_review_mode = is_past_deadline and existing_sub

    if st.session_state['confirm_submit']:
        st.markdown("<br><br>", unsafe_allow_html=True)
        _, center_col, _ = st.columns([2.5, 5, 2.5])
        
        with center_col:
            with st.container(border=True):
                st.markdown("<div style='text-align:center; font-size:3rem; margin-bottom: -15px;'>🚨</div>", unsafe_allow_html=True)
                st.markdown("<h3 style='text-align:center; color:#F8FAFC;'>Confirm Submission</h3>", unsafe_allow_html=True)
                
                st.markdown("<p style='text-align:center; color:#94A3B8; margin-bottom: 25px;'>Your progress is auto-saved. Submitting will log your current score, but you can always return to update your answers before the deadline.</p>", unsafe_allow_html=True)
                
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state['confirm_submit'] = False
                        st.rerun()
                with conf_col2:
                    if st.button("Yes, Log Submission", type="primary", use_container_width=True):
                        submit_assessment(db, quiz, questions, existing_sub, is_final=True)
        return 

    # TOP NAVIGATION BAR
    nav_col1, nav_col2, nav_col3 = st.columns([1.5, 5, 2], gap="small")
    with nav_col1:
        if st.button("← Back", use_container_width=True):
            st.session_state['active_quiz_id'] = None
            st.rerun()
            
    with nav_col2:
        task_options = [f"Task {i+1}: {q.question_type.replace('_', ' ').title()} ({q.points}pts)" for i, q in enumerate(questions)]
        selected_task_label = st.selectbox("Navigate Tasks", task_options, label_visibility="collapsed")
        q_idx = task_options.index(selected_task_label)
        current_q = questions[q_idx]

    with nav_col3:
        if is_review_mode:
            max_points = sum(q.points for q in questions)
            st.markdown(f"<div style='text-align:right; font-size:1.1rem; color:#50FA7B; padding-top:5px;'><b>Final Score: {int(existing_sub.score)} / {max_points}</b></div>", unsafe_allow_html=True)
        elif is_past_deadline and not existing_sub:
            st.button("Assessment Closed", disabled=True, use_container_width=True)
        else:
            submit_label = "Submit Assessment" if not existing_sub else "Update Submission"
            if st.button(submit_label, type="primary", use_container_width=True):
                st.session_state['confirm_submit'] = True
                st.rerun()

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)

    if 'student_answers' not in st.session_state: 
        st.session_state['student_answers'] = {}
        if existing_sub:
            for pa in db.query(Answer).filter(Answer.submission_id == existing_sub.submission_id).all(): 
                st.session_state['student_answers'][pa.question_id] = pa.student_answer

    # --- 50/50 SPLIT ---
    left_pane, right_pane = st.columns(2, gap="large")

    # ==========================================================
    # LEFT PANE: Instructions, Side-by-Side Options, Schema Grid
    # ==========================================================
    with left_pane:
        
        if current_q.question_type in ["multiple_choice", "sql_mcq", "python_mcq"]:
            q_col, opt_col = st.columns([6, 4], gap="small")
            
            with q_col:
                st.markdown(f'<div class="problem-box" style="height: 100%;"><b>Instruction:</b><br>{current_q.question_text}</div>', unsafe_allow_html=True)
                
            with opt_col:
                st.markdown('<div class="console-label" style="margin-top:0px; margin-bottom:5px;">Select Answer:</div>', unsafe_allow_html=True)
                options = json.loads(current_q.options) if current_q.options else {}
                choices = [f"A) {options.get('A','')}", f"B) {options.get('B','')}", f"C) {options.get('C','')}", f"D) {options.get('D','')}"]
                prev_ans = st.session_state['student_answers'].get(current_q.question_id, choices[0])
                if prev_ans not in choices: prev_ans = choices[0]
                
                if not is_past_deadline:
                    st.session_state['student_answers'][current_q.question_id] = st.radio("Options:", choices, index=choices.index(prev_ans), label_visibility="collapsed")
                else:
                    st.info(f"Locked: **{prev_ans}**")
        else:
            st.markdown(f'<div class="problem-box"><b>Instruction:</b><br>{current_q.question_text}</div>', unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if current_q.dataset_path and os.path.exists(current_q.dataset_path):
            tab_erd, tab_data = st.tabs(["Database Schema", "Data Previews"])
            
            with tab_erd:
                mermaid_code = generate_mermaid_erd(current_q.dataset_path)
                if mermaid_code:
                    st.components.v1.html(f"""
                        <div class="mermaid" style="background: transparent;">{mermaid_code}</div>
                        <script type="module">
                            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                            mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
                        </script>
                    """, height=600, scrolling=False)
                else: 
                    st.info("No relational schema available.")
                    
            with tab_data:
                previews = get_table_previews(current_q.dataset_path)
                if previews:
                    table_names = list(previews.keys())
                    preview_tabs = st.tabs(table_names)
                    
                    for i, t_name in enumerate(table_names):
                        with preview_tabs[i]:
                            st.dataframe(previews[t_name], use_container_width=False, hide_index=True)

    # ==========================================================
    # RIGHT PANE: Unified Coding Editor & Outputs 
    # ==========================================================
    with right_pane:
        
        # --- EDITOR SETTINGS ---
        editor_options = {
            "enableBasicAutocompletion": True, 
            "enableLiveAutocompletion": True, 
            "enableSnippets": True,
            "showLineNumbers": True,
            "tabSize": 4,
            "fontSize": "13px"
        }

        if is_review_mode:
            student_ans_record = db.query(Answer).filter(Answer.submission_id == existing_sub.submission_id, Answer.question_id == current_q.question_id).first()
            if student_ans_record and student_ans_record.is_correct: st.markdown("<div class='result-banner-correct'>✓ Correct (+{} pts)</div>".format(current_q.points), unsafe_allow_html=True)
            else: st.markdown("<div class='result-banner-incorrect'>✗ Incorrect (0 pts)</div>", unsafe_allow_html=True)
                
            st.markdown('<div class="console-label">Your Submission</div>', unsafe_allow_html=True)
            if current_q.question_type in ["python", "sql"]:
                ans_val = student_ans_record.student_answer if student_ans_record else ""
                rev_options = editor_options.copy()
                rev_options["readOnly"] = True
                code_editor(ans_val, lang=current_q.question_type, theme="dracula", options=rev_options, key=f"rev_{current_q.question_id}")
            else: st.info(student_ans_record.student_answer if student_ans_record else "No answer submitted.")

            st.markdown('<div class="console-label">Expected Answer / Explanation</div>', unsafe_allow_html=True)
            if current_q.question_type in ["python", "sql"]:
                exp_options = editor_options.copy()
                exp_options["readOnly"] = True
                code_editor(current_q.expected_answer, lang=current_q.question_type, theme="dracula", options=exp_options, key=f"exp_{current_q.question_id}")
            elif current_q.question_type in ["multiple_choice", "sql_mcq", "python_mcq"]:
                opts = json.loads(current_q.options) if current_q.options else {}
                st.success(f"Correct Option: **{opts.get('Correct', '')}**\n\n{current_q.expected_answer if current_q.question_type == 'multiple_choice' else ''}")
                
                if current_q.question_type in ["sql_mcq", "python_mcq"] and current_q.expected_answer:
                    st.markdown("**Expected Code to arrive at this answer:**")
                    lang = "sql" if current_q.question_type == "sql_mcq" else "python"
                    exp_options = editor_options.copy()
                    exp_options["readOnly"] = True
                    code_editor(current_q.expected_answer, lang=lang, theme="dracula", options=exp_options, key=f"exp_code_{current_q.question_id}")
            else: st.success(current_q.expected_answer)
                
        else: # Active Workspace
            is_pure_code = current_q.question_type in ["sql", "python"]
            is_hybrid = current_q.question_type in ["sql_mcq", "python_mcq"]

            if is_pure_code or is_hybrid:
                
                default_idx = 0 if "sql" in current_q.question_type else 1
                
                st.markdown('<div class="console-label">Select Programming Environment</div>', unsafe_allow_html=True)
                tool_mode = st.radio(
                    "Environment:", 
                    ["SQL", "Python"], 
                    index=default_idx, 
                    horizontal=True, 
                    label_visibility="collapsed",
                    key=f"env_toggle_{current_q.question_id}"
                )
                
                lang = "sql" if tool_mode == "SQL" else "python"
                lang_label = "main.py" if lang == "python" else "main.sql"
                
                # --- COOL ITALICIZED EDITOR LABEL ---
                st.markdown(f'<div class="console-label" style="font-style: italic; color: #38BDF8; font-size: 12px; letter-spacing: 1px;">{tool_mode} Editor</div>', unsafe_allow_html=True)
                
                default_code = "-- Write your SQL query here\n" if lang == "sql" else "import pandas as pd\nimport sqlite3\n\nconn = sqlite3.connect(DATASET_PATH)\n# Write your pandas code here\n"
                
                ide_key = f"ide_code_{current_q.question_id}_{lang}"
                
                if is_pure_code:
                    prev_code = st.session_state['student_answers'].get(current_q.question_id, "")
                    if not prev_code: prev_code = default_code
                else:
                    if ide_key not in st.session_state: st.session_state[ide_key] = default_code
                    prev_code = st.session_state[ide_key]

                with st.container(border=True):
                    st.markdown(f'<div class="mac-window"><div class="mac-header"><div class="mac-dot red"></div><div class="mac-dot yellow"></div><div class="mac-dot green"></div><div class="mac-title">{lang_label}</div></div></div>', unsafe_allow_html=True)
                    
                    active_options = editor_options.copy()
                    
                    if is_past_deadline: 
                        active_options["readOnly"] = True
                        custom_btns = []
                    else:
                        # Re-instated the internal "Run Code" button that hovers inside the editor
                        custom_btns = [{
                            "name": "Run Code",
                            "feather": "Play",
                            "primary": True,
                            "hasText": True,
                            "showWithIcon": True,
                            "commands": ["submit"],
                            "style": {"bottom": "0.5rem", "right": "0.5rem"}
                        }]
                    
                    editor_response = code_editor(
                        prev_code, 
                        lang=lang, 
                        theme="dracula", 
                        options=active_options, 
                        buttons=custom_btns,
                        key=f"code_editor_{current_q.question_id}_{lang}" 
                    )
                    
                    if editor_response and isinstance(editor_response, dict):
                        if 'text' in editor_response and editor_response['text']:
                            user_code = editor_response['text']
                        elif editor_response.get('type') == "":
                            user_code = prev_code
                        else:
                            user_code = ""
                    else:
                        user_code = prev_code
                    
                    if not is_past_deadline:
                        if is_pure_code:
                            st.session_state['student_answers'][current_q.question_id] = user_code
                        else:
                            st.session_state[ide_key] = user_code

                # --- STATEFUL TERMINAL CACHING ---
                run_btn = editor_response.get("type") == "submit" if editor_response else False
                terminal_out_key = f"terminal_out_{current_q.question_id}_{lang}"

                if not is_past_deadline and run_btn:
                    if lang == "python":
                        output, error = execute_python(user_code, current_q.dataset_path)
                        st.session_state[terminal_out_key] = {"is_sql": False, "output": output, "error": error}
                    else:
                        df_out, error = execute_sql(user_code, current_q.dataset_path)
                        st.session_state[terminal_out_key] = {"is_sql": True, "output": df_out, "error": error}

                # Always render the cached terminal output if it exists so it doesn't clear
                if terminal_out_key in st.session_state:
                    st.markdown('<div class="console-label">Terminal Output</div>', unsafe_allow_html=True)
                    res = st.session_state[terminal_out_key]
                    
                    if not res["is_sql"]:
                        if res["error"]: 
                            st.markdown(f"<div class='console-error-output'>{res['error']}</div>", unsafe_allow_html=True)
                        else: 
                            out_text = res['output'] if res['output'] else 'Success (No output)'
                            st.markdown(f"<div class='console-output'>{out_text}</div>", unsafe_allow_html=True)
                    else:
                        if res["error"]: 
                            st.markdown(f"<div class='console-error-output'>{res['error']}</div>", unsafe_allow_html=True)
                        else: 
                            st.dataframe(res["output"], use_container_width=False, hide_index=True)

            elif current_q.question_type == "multiple_choice":
                st.info("👈 Please select your answer from the options provided on the left side.")
            
            else:
                st.markdown('<div class="console-label">Written Response</div>', unsafe_allow_html=True)
                prev_ans = st.session_state['student_answers'].get(current_q.question_id, "")
                if not is_past_deadline:
                    st.session_state['student_answers'][current_q.question_id] = st.text_area("Answer:", value=prev_ans, height=200, label_visibility="collapsed")
                else: st.info(prev_ans if prev_ans else "No answer submitted.")

    # --- SILENT AUTO-SAVE HOOK ---
    if not is_past_deadline and not st.session_state['confirm_submit']:
        submit_assessment(db, quiz, questions, existing_sub, is_final=False)

def submit_assessment(db, quiz, questions, existing_sub, is_final=True):
    total_points_earned = 0
    max_points = sum(q.points for q in questions)

    if existing_sub:
        db.query(Answer).filter(Answer.submission_id == existing_sub.submission_id).delete()
        target_sub = existing_sub
    else:
        target_sub = Submission(student_id=st.session_state['user_id'], quiz_id=quiz.quiz_id, total_questions=len(questions), score="0")
        db.add(target_sub)
        db.flush()

    for q in questions:
        ans_text = st.session_state['student_answers'].get(q.question_id, "")
        is_correct = False

        if is_final:
            if q.question_type in ["multiple_choice", "sql_mcq", "python_mcq"]:
                opts = json.loads(q.options) if q.options else {}
                if ans_text.startswith(opts.get('Correct', '')): is_correct = True
            elif q.question_type == "sql" and q.expected_answer:
                exp_df, _ = execute_sql(q.expected_answer, q.dataset_path)
                stu_df, _ = execute_sql(ans_text, q.dataset_path)
                if exp_df is not None and stu_df is not None and exp_df.equals(stu_df): is_correct = True
            elif q.question_type == "python" and q.expected_answer:
                exp_out, _ = execute_python(q.expected_answer, q.dataset_path)
                stu_out, _ = execute_python(ans_text, q.dataset_path)
                if exp_out == stu_out: is_correct = True
            
            if is_correct: total_points_earned += q.points
            
        db.add(Answer(submission_id=target_sub.submission_id, question_id=q.question_id, student_answer=ans_text, is_correct=is_correct))

    if is_final:
        target_sub.score = int(total_points_earned)
        
    target_sub.submitted_at = get_wat_time()
    db.commit()

    if is_final:
        st.session_state.pop('student_answers', None) 
        st.session_state['active_quiz_id'] = None
        st.session_state['confirm_submit'] = False
        st.toast("Assessment submitted and graded successfully!", icon="✅")
        st.rerun()