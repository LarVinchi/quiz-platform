# 📝 Streamlit Quiz Platform (Local Prototype)

A **role-based quiz application** built with **Streamlit and Python**. This platform allows **instructors to create quizzes and manage students**, while **students can log in and take assessments** through an interactive interface.

The project is currently in the **local prototyping phase**, using **SQLite** as the database engine.

---

# ✨ Current Features

### 🔐 Role-Based Access

* Separate portals for **Instructor** and **Student**
* Smooth routing between dashboards

### 👨‍🏫 Instructor Dashboard

* Create quizzes with **custom titles and descriptions**
* Add **multiple-choice questions**
* Assign **dynamic point values**
* Upload **authorized students via CSV**

  * Required columns: `email`, `name`

### 🎓 Student Portal

* Secure login using **authorized email validation**
* Interactive quiz interface
* **Auto-grading system**
* Student responses and scores are securely stored in the database

---

# 🛠️ Tech Stack

| Layer               | Technology                  |
| ------------------- | --------------------------- |
| **Frontend**        | Streamlit, Custom CSS       |
| **Backend**         | Python                      |
| **Database**        | SQLite (via SQLAlchemy ORM) |
| **Data Processing** | Pandas                      |

---

# 🚀 How to Run Locally

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

---

## 2️⃣ Set Up a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Run the Application

```bash
streamlit run app.py
```

Once the app starts, Streamlit will open it in your browser.

---

# 🧪 How to Test the Application

### Instructor Steps

1. Click **"I am an Instructor"**.
2. **Create a dummy quiz**.
3. Add several **questions**.
4. Upload a `.csv` file containing authorized student emails.

Example CSV format:

```csv
email,name
student@email.com,John Doe
```

Include **your own email** so you can test student login.

### Student Steps

1. Log out from instructor view.
2. Click **"I am a Student"**.
3. Log in using your authorized email.
4. Take the quiz and submit it.

The system will:

* Automatically grade the quiz
* Store scores and answers in the database

---

# 📂 Project Structure (Typical)

```
quiz-platform/
│
├── .streamlit/
│   └── config.toml
├── assets/
│   └── style.css
├── database.py
├── models.py
├── admin.py
├── student.py
├── app.py
└── requirements.txt
```

---

# 🗺️ Roadmap (Next Steps)

* [ ] **Migrate database to Cloud PostgreSQL** (Neon / Supabase)
* [ ] **Automated email notifications** using SendGrid
* [ ] **Instructor analytics dashboard** for class performance
* [ ] **Cloud deployment** on Streamlit Community Cloud

---

# 💡 Project Status

🚧 **Prototype Stage**

This version focuses on validating:

* role-based quiz workflows
* student authorization
* automated grading

Future versions will add **scalability, analytics, and cloud deployment**.

---

# 📜 License

This project is intended for **educational and prototyping purposes**.


<!-- PROJECT_STRUCTURE_START -->
## 📂 Project Structure

```
📂 Project Root: quiz-platform/
├── 📄 .gitignore (0.1 KB)
├── 📁 .streamlit/
│   └── 📄 config.toml (0.4 KB)
├── 📄 README.md (3.5 KB)
├── 📄 admin.py (24.5 KB)
├── 📄 app.py (17.3 KB)
├── 📁 assets/
│   └── 📄 style.css (7.2 KB)
├── 📁 data/
│   ├── 📄 content_catalog.parquet (3.5 KB)
│   ├── 📄 daily_watch_logs.csv (0.2 KB)
│   ├── 📄 retail_sample.db (20.0 KB)
│   └── 📄 streaming_users.db (12.0 KB)
├── 📄 database.py (0.6 KB)
├── 📁 datasets/
│   ├── 📄 17d48aef84fe4ccdaf6097f1d790882c.db (20.0 KB)
│   ├── 📄 a8259b1571b54267a3c077091fc72e9d.db (20.0 KB)
│   └── 📄 aa5cbcb1b1624099935aadb0f83cc935.db (20.0 KB)
├── 📄 generate_tree.py (4.9 KB)
├── 📄 models.py (3.2 KB)
├── 📄 requirements.txt (0.1 KB)
└── 📄 student.py (24.1 KB)
```
<!-- PROJECT_STRUCTURE_END -->
