import streamlit as st
import pandas as pd
import json
import os
import sqlite3
import uuid
from datetime import datetime
from app.core.database import SessionLocal
from app.core.models import Quiz, Question, User, Submission, Answer 

# --- AUTO-SCHEMA GENERATOR ---
def extract_sqlite_schema(db_path):
    """Automatically extracts tables and columns from an SQLite DB."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_md = "#### Database Schema / ERD\n"
        for table in tables:
            table_name = table[0]
            schema_md += f"**Table: `{table_name}`**\n"
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            for col in columns:
                schema_md += f"- `{col[1]}` *( {col[2]} )*\n"
            schema_md += "\n"
        conn.close()
        return schema_md
    except Exception as e:
        return f"*Could not parse schema: {e}*"

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# --- PREMIUM ADMIN CSS ---
def inject_admin_css():
    st.markdown("""
    <style>
        /* 1. AGGRESSIVELY NUKE ALL STREAMLIT ARTIFACTS */
        [data-testid="stToolbar"], 
        [data-testid="stHeader"], 
        [data-testid="stAppDeployButton"],
        .stAppDeployButton,
        header, 
        footer { 
            display: none !important; 
            width: 0 !important;
            height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        
        /* 2. Optimize Layout */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 2rem !important;
            max-width: 95% !important; 
        }

        /* 3. Sleek Translucent Forms (No Annoying Animations) */
        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            padding: 25px 30px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
        }
        
        /* Kill the glass shine specifically on admin forms so they stay clean */
        div[data-testid="stForm"]::before, 
        div[data-testid="stForm"]::after {
            display: none !important;
            content: none !important;
            animation: none !important;
        }

        /* 4. Custom Accents */
        .section-header {
            font-size: 0.85rem;
            font-weight: 600;
            color: #38BDF8;
            letter-spacing: 1.5px;
            margin-bottom: 15px;
            text-transform: uppercase;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
        }
        
        /* Custom Question List Styling */
        .question-row {
            padding: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            transition: background 0.2s;
        }
        .question-row:hover {
            background: rgba(255,255,255,0.05);
        }
    </style>
    """, unsafe_allow_html=True)


def admin_dashboard():
    inject_admin_css()
    
    # Initialize session state for isolated question viewing
    if 'editing_q_id' not in st.session_state:
        st.session_state.editing_q_id = None

    # Wrap the Dashboard in columns for a sleek, centered web-app feel
    _, center_dashboard, _ = st.columns([0.5, 8, 0.5])

    with center_dashboard:
        # Authenticated Dashboard Header
        admin_name = st.session_state.get('user_name', 'Instructor')
        st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 10px; margin-bottom: 25px; border-bottom: 1px solid rgba(45, 212, 191, 0.3);">
                <div style="font-size: 1.4rem; font-weight: 600; color: #F8FAFC;">
                    Instructor <span class="elegant-title" style="color:#2DD4BF;">Workspace</span>
                </div>
                <div class="status-badge admin" style="border: 1px solid #2DD4BF; color: #2DD4BF; background: rgba(45,212,191,0.1); padding: 4px 12px; border-radius: 20px; font-size: 0.75rem;">
                    ● {admin_name} Active
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        db = get_db()

        # Dynamic Tabs - Now separated Add Questions vs Question Bank
        tabs_list = [
            "Deploy Assessment", 
            "Add Questions", 
            "Question Bank",
            "User Access", 
            "Performance Analytics"
        ]
        
        if st.session_state.get('is_master'):
            tabs_list.append("Master: Instructors")

        tabs = st.tabs(tabs_list)

        # ----------------------------
        # TAB 1: DEPLOY ASSESSMENT
        # ----------------------------
        with tabs[0]:
            st.markdown('<div class="section-header">Configure New Module</div>', unsafe_allow_html=True)
            with st.form("deploy_form"):
                title = st.text_input("Assessment Title", placeholder="e.g., Module 1: Advanced SQL Joins")
                desc = st.text_area("Module Objectives", placeholder="Enter the goals and instructions for this assessment...")
                
                col1, col2 = st.columns(2)
                with col1: due_date = st.date_input("Submission Date Deadline")
                with col2: due_time = st.time_input("Submission Time Deadline")

                st.markdown("<br>", unsafe_allow_html=True)
                submit_btn = st.form_submit_button("Publish Assessment", type="primary")

                if submit_btn:
                    if title:
                        full_deadline = datetime.combine(due_date, due_time)
                        new_quiz = Quiz(title=title, description=desc, due_date=full_deadline)
                        db.add(new_quiz)
                        db.commit()
                        st.success(f"Module '{title}' published successfully! Deadline set for {full_deadline.strftime('%Y-%m-%d %H:%M')}")
                    else:
                        st.error("Please provide a module title.")

        # ----------------------------
        # TAB 2: ADD QUESTIONS
        # ----------------------------
        with tabs[1]:
            st.markdown('<div class="section-header">Add New Question</div>', unsafe_allow_html=True)
            quizzes = db.query(Quiz).all()
            
            if not quizzes:
                st.info("Please publish an assessment module first.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    selected_quiz = st.selectbox("Target Assessment:", [q.title for q in quizzes], key="add_q_quiz")
                    quiz_id = next(q.quiz_id for q in quizzes if q.title == selected_quiz)
                with col2:
                    question_type = st.selectbox("Question Format", ["sql", "python", "multiple_choice", "text"])

                with st.form("add_question_form", clear_on_submit=True):
                    q_col1, q_col2 = st.columns([1.2, 1], gap="large")
                    
                    with q_col1:
                        st.markdown("**Problem Setup**")
                        question_text = st.text_area("Problem Statement", placeholder="Enter the scenario or instructions...", height=150)
                        points_val = st.number_input("Points Awarded for Correct Answer", min_value=1, max_value=100, value=1, step=1)
                        
                        options_json = None
                        expected_answer = ""
                        dataset_path = None
                        schema_info = None

                    with q_col2:
                        if question_type in ["sql", "python"]:
                            st.markdown("**Dataset Attachment**")
                            uploaded_file = st.file_uploader(
                                "Supported: .db, .sqlite, .csv, .parquet, .xlsx, .json", 
                                type=["db", "sqlite", "csv", "parquet", "xlsx", "json"]
                            )
                            
                            if uploaded_file:
                                os.makedirs("datasets", exist_ok=True)
                                file_ext = uploaded_file.name.split('.')[-1]
                                safe_filename = f"{uuid.uuid4().hex}.{file_ext}"
                                dataset_path = os.path.join("datasets", safe_filename)
                                
                                with open(dataset_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())
                                    
                                if file_ext in ["db", "sqlite"]:
                                    schema_info = extract_sqlite_schema(dataset_path)
                                    st.success("✓ Relational Database connected.")
                                else:
                                    schema_info = f"**Dataset:** `{uploaded_file.name}` (Single Table)"
                                    st.success(f"✓ File `{uploaded_file.name}` uploaded.")

                        if question_type == "multiple_choice":
                            st.markdown("**Multiple Choice Options**")
                            opt_col1, opt_col2 = st.columns(2)
                            with opt_col1:
                                opt_a = st.text_input("Option A")
                                opt_c = st.text_input("Option C")
                            with opt_col2:
                                opt_b = st.text_input("Option B")
                                opt_d = st.text_input("Option D")
                            correct_ans = st.selectbox("Which option is correct?", ["A", "B", "C", "D"])
                            expected_answer = st.text_area("Explanation", placeholder="Explain why this answer is correct...")
                        else:
                            st.markdown(f"**{question_type.upper()} Solution**")
                            expected_answer = st.text_area("Expected Code / Answer", placeholder=f"Write the correct {question_type.upper()} solution here...", height=150)

                    st.markdown("<br>", unsafe_allow_html=True)
                    save_btn = st.form_submit_button("Save Question to Module", type="primary")

                    if save_btn and question_text:
                        if question_type == "multiple_choice":
                            options_dict = {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d, "Correct": correct_ans}
                            options_json = json.dumps(options_dict)
                        
                        new_q = Question(
                            quiz_id=quiz_id,
                            question_text=question_text,
                            question_type=question_type,
                            expected_answer=expected_answer,
                            options=options_json,
                            dataset_path=dataset_path,
                            schema_info=schema_info,
                            points=points_val
                        )
                        db.add(new_q)
                        db.commit()
                        st.success(f"Question appended successfully! ({points_val} points)")
                        st.rerun()

        # ----------------------------
        # TAB 3: QUESTION BANK (ISOLATED VIEW)
        # ----------------------------
        with tabs[2]:
            st.markdown('<div class="section-header">Question Repository</div>', unsafe_allow_html=True)
            quizzes = db.query(Quiz).all()
            
            if not quizzes:
                st.info("No assessments deployed.")
            else:
                # STATE 1: List View
                if st.session_state.editing_q_id is None:
                    selected_bank_quiz = st.selectbox("Select Assessment to View Questions:", [q.title for q in quizzes], key="bank_quiz_sel")
                    quiz_id = next(q.quiz_id for q in quizzes if q.title == selected_bank_quiz)
                    
                    existing_questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
                    
                    if not existing_questions:
                        st.info("No questions in this module yet.")
                    else:
                        st.markdown("<br>", unsafe_allow_html=True)
                        for i, q in enumerate(existing_questions, 1):
                            with st.container(border=True):
                                c1, c2 = st.columns([5, 1], vertical_alignment="center")
                                with c1:
                                    st.markdown(f"**Q{i} | {q.question_type.upper()} | {q.points} Pts**")
                                    st.caption(f"{q.question_text[:120]}...")
                                with c2:
                                    if st.button("View / Edit", key=f"open_q_{q.question_id}"):
                                        st.session_state.editing_q_id = q.question_id
                                        st.rerun()

                # STATE 2: Isolated Edit View
                else:
                    if st.button("⬅ Back to Question List"):
                        st.session_state.editing_q_id = None
                        st.rerun()
                    
                    q = db.query(Question).filter(Question.question_id == st.session_state.editing_q_id).first()
                    if q:
                        st.markdown(f"### Editing Question (Type: `{q.question_type.upper()}`)")
                        with st.form(f"edit_isolated_{q.question_id}"):
                            edit_text = st.text_area("Full Question Prompt", value=q.question_text, height=200)
                            edit_ans = st.text_area("Expected Answer/Code", value=q.expected_answer, height=200)
                            edit_pts = st.number_input("Points", value=q.points, min_value=1)
                            
                            st.markdown("<br>", unsafe_allow_html=True)
                            c1, c2 = st.columns([1, 1])
                            with c1:
                                update_q_btn = st.form_submit_button("Save Changes", type="primary")
                            with c2:
                                delete_q_btn = st.form_submit_button("Delete Entire Question")
                                
                            if update_q_btn:
                                q.question_text = edit_text
                                q.expected_answer = edit_ans
                                q.points = edit_pts
                                db.commit()
                                st.success("Question updated successfully!")
                                st.session_state.editing_q_id = None # Go back to list
                                st.rerun()
                                
                            if delete_q_btn:
                                db.delete(q)
                                db.commit()
                                st.warning("Question deleted.")
                                st.session_state.editing_q_id = None # Go back to list
                                st.rerun()

        # ----------------------------
        # TAB 4: UPLOAD STUDENTS
        # ----------------------------
        with tabs[3]:
            st.markdown('<div class="section-header">Manage Authorized Learners</div>', unsafe_allow_html=True)
            st.markdown("Upload a CSV file containing `email` and `name` columns. Their default password will be `student123`.")

            with st.container(border=True):
                uploaded_file = st.file_uploader("Upload Access Roster (CSV)", type="csv", key="csv_uploader")

                if uploaded_file is not None:
                    try:
                        df = pd.read_csv(uploaded_file)
                        if 'email' not in df.columns:
                            st.error("CSV must contain an 'email' column.")
                        else:
                            added_count = 0
                            for _, row in df.iterrows():
                                email = str(row['email']).strip()
                                name = str(row.get('name', '')).strip()
                                existing = db.query(User).filter(User.email == email).first()
                                if not existing:
                                    new_student = User(email=email, name=name, password="student123", role="student")
                                    db.add(new_student)
                                    added_count += 1
                            db.commit()
                            st.success(f"Successfully authorized {added_count} new learners!")
                    except Exception as e:
                        st.error(f"Error processing file: {e}")

        # ----------------------------
        # TAB 5: PERFORMANCE ANALYTICS
        # ----------------------------
        with tabs[4]:
            st.markdown('<div class="section-header">Submission Tracking & Analytics</div>', unsafe_allow_html=True)
            if not quizzes:
                st.info("No assessments deployed.")
            else:
                track_quiz = st.selectbox("Select Module to Analyze:", [q.title for q in quizzes], key="track_quiz")
                
                selected_quiz_obj = next(q for q in quizzes if q.title == track_quiz)
                submissions = db.query(Submission).filter(Submission.quiz_id == selected_quiz_obj.quiz_id).all()
                module_questions = db.query(Question).filter(Question.quiz_id == selected_quiz_obj.quiz_id).all()
                
                total_possible_points = sum(q.points for q in module_questions)
                
                if not submissions:
                    st.info("No students have submitted this assessment yet.")
                else:
                    # Calculate Detailed Metrics
                    scores = [sub.score for sub in submissions]
                    avg_score = sum(scores) / len(scores)
                    high_score = max(scores)
                    low_score = min(scores)
                    
                    pass_threshold = total_possible_points * 0.5 
                    passed_students = sum(1 for s in scores if s >= pass_threshold)
                    failed_students = len(scores) - passed_students
                    
                    pass_rate = (passed_students / len(scores)) * 100
                    fail_rate = (failed_students / len(scores)) * 100

                    # Display Metrics
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Submissions", len(submissions))
                    m2.metric("Average Score", f"{avg_score:.0f} / {total_possible_points}")
                    m3.metric("Pass Rate", f"{pass_rate:.1f}%", f"{passed_students} Passed", delta_color="normal")
                    m4.metric("Fail Rate", f"{fail_rate:.1f}%", f"-{failed_students} Failed", delta_color="inverse")
                    
                    st.markdown(f"**Score Extremes:** Highest: `{high_score}` | Lowest: `{low_score}`")
                    st.markdown("---")

                    # --- QUESTION-BY-QUESTION STATS ---
                    st.markdown('<div class="section-header">Question Difficulty Analysis</div>', unsafe_allow_html=True)
                    
                    q_stats_data = []
                    for i, q in enumerate(module_questions, 1):
                        answers = db.query(Answer).filter(Answer.question_id == q.question_id).all()
                        
                        if answers:
                            total_attempts = len(answers)
                            correct_count = sum(1 for a in answers if a.is_correct)
                            avg_pts_earned = sum(a.points_awarded for a in answers) / total_attempts if hasattr(answers[0], 'points_awarded') else 0
                            q_pass_rate = (correct_count / total_attempts) * 100
                            q_fail_rate = 100 - q_pass_rate
                        else:
                            total_attempts = 0
                            q_pass_rate = 0
                            q_fail_rate = 0
                            avg_pts_earned = 0
                            
                        q_stats_data.append({
                            "Q#": f"Q{i}",
                            "Question Preview": q.question_text[:45] + "...",
                            "Type": q.question_type.upper(),
                            "Max Pts": q.points,
                            "Avg Pts Earned": f"{avg_pts_earned:.1f}",
                            "Pass Rate (%)": f"{q_pass_rate:.1f}%",
                            "Fail Rate (%)": f"{q_fail_rate:.1f}%"
                        })
                        
                    df_q_stats = pd.DataFrame(q_stats_data)
                    st.dataframe(df_q_stats, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    
                    # Learner Roster Output
                    st.markdown('<div class="section-header">Individual Learner Results</div>', unsafe_allow_html=True)
                    results_data = []
                    for sub in submissions:
                        student = db.query(User).filter(User.id == sub.student_id).first()
                        sub_time = sub.submitted_at.strftime("%b %d, %Y - %H:%M") if sub.submitted_at else "N/A"
                        status = "✅ Pass" if sub.score >= pass_threshold else "❌ Fail"

                        results_data.append({
                            "Learner Name": student.name if student else "Unknown",
                            "Email": student.email if student else "Unknown",
                            "Final Score": str(int(float(sub.score))) if sub.score is not None else "0",
                            "Status": status,
                            "Submitted On": sub_time
                        })
                    
                    df_results = pd.DataFrame(results_data)
                    st.dataframe(df_results, use_container_width=True, hide_index=True)

        # ----------------------------
        # TAB 6: MASTER ADMIN ONLY
        # ----------------------------
        if st.session_state.get('is_master'):
            with tabs[5]:
                st.markdown('<div class="section-header">Allocate Instructor Access</div>', unsafe_allow_html=True)
                st.write("Grant access to co-instructors. They will log in using `admin123` and be prompted to change it.")
                
                with st.form("add_admin_form"):
                    new_admin_email = st.text_input("New Instructor Email")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Grant Access", type="primary"):
                        existing = db.query(User).filter(User.email == new_admin_email).first()
                        if existing:
                            st.error("This email already has an account on the platform.")
                        else:
                            new_admin = User(email=new_admin_email, name="Instructor", password="admin123", role="instructor", is_master=False)
                            db.add(new_admin)
                            db.commit()
                            st.success(f"Access granted to {new_admin_email}! They can now log in.")
                            st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-header">Current Instructors</div>', unsafe_allow_html=True)
                admins = db.query(User).filter(User.role == 'instructor').all()
                admin_data = [{"Email": a.email, "Master Privilege": a.is_master} for a in admins]
                st.dataframe(pd.DataFrame(admin_data), use_container_width=True, hide_index=True)