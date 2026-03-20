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
from streamlit_ace import st_ace 

def get_db():
    db = SessionLocal()
    try: return db
    finally: db.close()

# --- Helper for West Africa Time (WAT) ---
def get_wat_time():
    # WAT is UTC + 1 hour
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
    except Exception as e: return None, str(e)
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

    # Sort quizzes: Closest deadline first. No deadline goes to the bottom.
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

    # -------------------------------------------------------------
    # NEW PROFESSIONAL CONFIRMATION DIALOG INTERCEPTOR
    # -------------------------------------------------------------
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

    left_pane, right_pane = st.columns([4, 6], gap="medium")

    with left_pane:
        st.markdown(f'<div class="problem-box"><b>Instruction:</b><br>{current_q.question_text}</div>', unsafe_allow_html=True)
        
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
                    """, height=350, scrolling=True)
                else: st.info("No relational schema available.")
                    
            with tab_data:
                previews = get_table_previews(current_q.dataset_path)
                if previews:
                    for table_name, df_preview in previews.items():
                        st.markdown(f"<span style='color:#38BDF8; font-size:13px; font-weight:600;'>Table: {table_name}</span>", unsafe_allow_html=True)
                        st.dataframe(df_preview, use_container_width=True, hide_index=True)

    with right_pane:
        if is_review_mode:
            student_ans_record = db.query(Answer).filter(Answer.submission_id == existing_sub.submission_id, Answer.question_id == current_q.question_id).first()
            if student_ans_record and student_ans_record.is_correct: st.markdown("<div class='result-banner-correct'>✓ Correct (+{} pts)</div>".format(current_q.points), unsafe_allow_html=True)
            else: st.markdown("<div class='result-banner-incorrect'>✗ Incorrect (0 pts)</div>", unsafe_allow_html=True)
                
            st.markdown('<div class="console-label">Your Submission</div>', unsafe_allow_html=True)
            if current_q.question_type in ["python", "sql"]:
                st_ace(value=student_ans_record.student_answer if student_ans_record else "", language=current_q.question_type, theme="dracula", readonly=True, height=150, key=f"rev_{current_q.question_id}")
            else: st.info(student_ans_record.student_answer if student_ans_record else "No answer submitted.")

            st.markdown('<div class="console-label">Expected Answer / Explanation</div>', unsafe_allow_html=True)
            if current_q.question_type in ["python", "sql"]:
                st_ace(value=current_q.expected_answer, language=current_q.question_type, theme="dracula", readonly=True, height=150, key=f"exp_{current_q.question_id}")
            elif current_q.question_type in ["multiple_choice", "sql_mcq", "python_mcq"]:
                opts = json.loads(current_q.options) if current_q.options else {}
                st.success(f"Correct Option: **{opts.get('Correct', '')}**\n\n{current_q.expected_answer if current_q.question_type == 'multiple_choice' else ''}")
                
                # Render the expected SQL or Python code for the hybrid questions
                if current_q.question_type in ["sql_mcq", "python_mcq"] and current_q.expected_answer:
                    st.markdown("**Expected Code to arrive at this answer:**")
                    lang = "sql" if current_q.question_type == "sql_mcq" else "python"
                    st_ace(value=current_q.expected_answer, language=lang, theme="dracula", readonly=True, height=120, key=f"exp_code_{current_q.question_id}")
            else: st.success(current_q.expected_answer)
                
        else:
            if current_q.question_type in ["python", "sql"]:
                default_idx = 0 if current_q.question_type == "sql" else 1
                tool_mode = st.radio("Environment:", ["SQL", "Python"], index=default_idx, horizontal=True, label_visibility="collapsed")
                prev_ans = st.session_state['student_answers'].get(current_q.question_id, "")
                lang_label = "main.py" if tool_mode == "Python" else "main.sql"
                
                with st.container(border=True):
                    st.markdown(f'<div class="mac-window"><div class="mac-header"><div class="mac-dot red"></div><div class="mac-dot yellow"></div><div class="mac-dot green"></div><div class="mac-title">{lang_label}</div></div></div>', unsafe_allow_html=True)
                    user_code = st_ace(
                        value=prev_ans, language="python" if tool_mode == "Python" else "sql", theme="dracula", height=220, 
                        key=f"ace_{current_q.question_id}", auto_update=True, readonly=is_past_deadline
                    )
                    
                    if not is_past_deadline:
                        _, col_btn = st.columns([7.5, 2.5]) 
                        with col_btn: run_btn = st.button("Execute Code", type="primary", use_container_width=True)
                        st.session_state['student_answers'][current_q.question_id] = user_code

                if not is_past_deadline and run_btn:
                    st.markdown('<div class="console-label">Terminal Output</div>', unsafe_allow_html=True)
                    if tool_mode == "Python":
                        output, error = execute_python(user_code, current_q.dataset_path)
                        if error: st.markdown(f"<div class='console-error-output'>{error}</div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div class='console-output'>{output if output else 'Success (No output)'}</div>", unsafe_allow_html=True)
                    else:
                        df_out, error = execute_sql(user_code, current_q.dataset_path)
                        if error: st.markdown(f"<div class='console-error-output'>{error}</div>", unsafe_allow_html=True)
                        else: st.dataframe(df_out, use_container_width=True, hide_index=True)

            # ==========================================================
            # NEW: HYBRID MCQ + SCRATCHPAD LOGIC (Supports SQL and Python)
            # ==========================================================
            elif current_q.question_type in ["sql_mcq", "python_mcq"]:
                st.markdown('<div class="console-label">Data Scratchpad (Investigate to find the answer)</div>', unsafe_allow_html=True)
                
                lang = "sql" if current_q.question_type == "sql_mcq" else "python"
                lang_label = "scratchpad.sql" if lang == "sql" else "scratchpad.py"
                
                scratch_key = f"scratch_{current_q.question_id}"
                if scratch_key not in st.session_state: 
                    st.session_state[scratch_key] = "SELECT * FROM dataset LIMIT 5;" if lang == "sql" else "import pandas as pd\ndf = pd.read_csv(DATASET_PATH)\nprint(df.head())"
                    
                with st.container(border=True):
                    st.markdown(f'<div class="mac-window"><div class="mac-header"><div class="mac-dot red"></div><div class="mac-dot yellow"></div><div class="mac-dot green"></div><div class="mac-title">{lang_label}</div></div></div>', unsafe_allow_html=True)
                    scratch_code = st_ace(value=st.session_state[scratch_key], language=lang, theme="dracula", height=150, key=f"ace_scratch_{current_q.question_id}", auto_update=True, readonly=is_past_deadline)
                    
                    if not is_past_deadline:
                        _, col_btn = st.columns([7.5, 2.5]) 
                        with col_btn: run_btn = st.button("Run Scratchpad", type="primary", use_container_width=True, key=f"run_{current_q.question_id}")
                        st.session_state[scratch_key] = scratch_code

                if not is_past_deadline and run_btn:
                    st.markdown('<div class="console-label">Scratchpad Output</div>', unsafe_allow_html=True)
                    if lang == "python":
                        output, error = execute_python(scratch_code, current_q.dataset_path)
                        if error: st.markdown(f"<div class='console-error-output'>{error}</div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div class='console-output'>{output if output else 'Success (No output)'}</div>", unsafe_allow_html=True)
                    else:
                        df_out, error = execute_sql(scratch_code, current_q.dataset_path)
                        if error: st.markdown(f"<div class='console-error-output'>{error}</div>", unsafe_allow_html=True)
                        else: st.dataframe(df_out, use_container_width=True, hide_index=True)

                st.markdown('<div class="console-label">Select Final Answer</div>', unsafe_allow_html=True)
                options = json.loads(current_q.options) if current_q.options else {}
                choices = [f"A) {options.get('A','')}", f"B) {options.get('B','')}", f"C) {options.get('C','')}", f"D) {options.get('D','')}"]
                prev_ans = st.session_state['student_answers'].get(current_q.question_id, choices[0])
                if prev_ans not in choices: prev_ans = choices[0]
                
                if not is_past_deadline:
                    st.session_state['student_answers'][current_q.question_id] = st.radio("Options:", choices, index=choices.index(prev_ans), label_visibility="collapsed")
                else: st.info(f"Your locked answer: {prev_ans}")
            # ==========================================================

            elif current_q.question_type == "multiple_choice":
                st.markdown('<div class="console-label">Select Response</div>', unsafe_allow_html=True)
                options = json.loads(current_q.options) if current_q.options else {}
                choices = [f"A) {options.get('A','')}", f"B) {options.get('B','')}", f"C) {options.get('C','')}", f"D) {options.get('D','')}"]
                prev_ans = st.session_state['student_answers'].get(current_q.question_id, choices[0])
                if prev_ans not in choices: prev_ans = choices[0]
                
                if not is_past_deadline:
                    st.session_state['student_answers'][current_q.question_id] = st.radio("Options:", choices, index=choices.index(prev_ans), label_visibility="collapsed")
                else: st.info(f"Your locked answer: {prev_ans}")
            
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

        # ONLY RUN HEAVY GRADING LOGIC IF THEY ARE OFFICIALLY SUBMITTING
        if is_final:
            # All 3 MCQ variations grade the same way: by checking if they chose the "Correct" option letter
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

    # Calculate final score only if final, otherwise leave as draft 0
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