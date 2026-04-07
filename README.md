# ================================
# 📧 EMAIL SPAM DETECTOR PROJECT
# ================================

# -------- README.md --------

# 📧 Email Spam Detector

A simple full-stack project that detects whether an email is **spam or legitimate (ham)** using machine learning + handcrafted features.

## 🚀 Features

- Detect spam from subject + body
- Shows:
  - Verdict (Spam / Ham)
  - Confidence score
  - Reasons (why flagged)
- Uses:
  - TF-IDF (text features)
  - Custom features (caps, links, spam words)
- Flask backend + simple frontend
- Fallback client model if backend fails

---

## 🧠 How it works

1. Combine subject + body
2. Convert to numbers using TF-IDF
3. Extract extra features (caps, links, etc.)
4. Pass to Logistic Regression model
5. Return prediction + confidence + reasons

---

## 🗂️ Structure

      project/
      ├── app.py
      ├── model/
      │   ├── trainer.py
      │   ├── predictor.py
      │   ├── features.py
      │   └── spam_model.pkl
      ├── data/
      │   └── sample_data.py
      ├── frontend/
      │   ├── index.html
      │   ├── app.js
      │   └── style.css

---

## ⚙️ Setup

Install dependencies:
pip install flask flask-cors scikit-learn numpy scipy

---

## ▶️ Run Backend

python app.py

Runs at:
http://127.0.0.1:5000

---

## 🌐 Run Frontend

Open:
frontend/index.html

---

## 🔌 API

POST /api/detect  
GET /api/stats  
POST /api/retrain  
GET /api/health  

---

## ⚠️ Notes

- Uses small dataset → not production-ready
- Falls back to client model if backend fails

---

## 💡 Future Improvements

- Bigger dataset
- Better models
- Deployment

---

## 🧑‍💻 Author

Learning project (ML + full-stack)
EOF


# ================================
# 🚀 INSTALL DEPENDENCIES
# ================================
pip install flask flask-cors scikit-learn numpy scipy


# ================================
# ▶️ RUN BACKEND
# ================================
python app.py


# ================================
# 🌐 OPEN FRONTEND
# ================================
# Just open this file in browser:
# frontend/index.html


# ================================
# 🧪 TEST API (optional)
# ================================
curl -X POST http://127.0.0.1:5000/api/detect \
-H "Content-Type: application/json" \
-d '{"subject":"Win money now","body":"Click here to claim prize"}'
