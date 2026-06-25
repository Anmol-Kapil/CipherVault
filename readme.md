# 🔐 CipherVault

CipherVault is a secure cloud storage platform that enables users to upload, store, and retrieve files securely using AES-GCM encryption, password-protected downloads, and unique Access IDs.

The application is built using React, FastAPI, SQLite, Google Drive API, and deployed using Vercel and Render.

---

## 🚀 Features

- Secure file upload and download
- AES-GCM encryption for file protection
- Password-protected file retrieval
- Unique Access ID generation for each file
- Google Drive cloud storage integration
- Metadata management using SQLite
- Responsive React frontend
- FastAPI backend with REST APIs
- Deployed on Vercel and Render

---

## 🏗️ System Architecture

```text
User
   │
   ▼
React Frontend (Vercel)
   │
   ▼
FastAPI Backend (Render)
   │
   ├── AES-GCM Encryption
   │
   ├── SQLite Metadata Database
   │
   ▼
Google Drive Storage
```

---

## ⚙️ Tech Stack

### Frontend

- React.js
- Axios
- CSS

### Backend

- FastAPI
- Python
- SQLAlchemy
- SQLite

### Security

- AES-GCM Encryption
- bcrypt Password Hashing

### Cloud Services

- Google Drive API
- Render
- Vercel

---

## 📂 Upload Workflow

1. User selects a file and enters a password.
2. Frontend sends file and password to FastAPI.
3. Backend generates a unique Access ID.
4. Password is hashed using bcrypt.
5. File is encrypted using AES-GCM.
6. Encrypted file is uploaded to Google Drive.
7. Metadata is stored in SQLite.
8. Access ID is returned to the user.

---

## 📥 Download Workflow

1. User enters Access ID and password.
2. Backend validates Access ID.
3. Password hash is verified using bcrypt.
4. Encrypted file is downloaded from Google Drive.
5. File is decrypted using AES-GCM.
6. Original file is returned to the user.

---

## 🔒 Security Features

### AES-GCM Encryption

Files are encrypted before storage using AES-GCM, which provides:

- Confidentiality
- Data integrity
- Authentication

### Password Protection

Passwords are never stored in plain text.

Passwords are securely hashed using bcrypt before being saved to the database.

### Access ID Retrieval

Each uploaded file receives a unique Access ID that is required during download.

---

## 📸 Screenshots

### Upload Page

Add screenshot here.

### Access ID Generation

Add screenshot here.

### Download Page

Add screenshot here.

---

## 🌐 Deployment

### Frontend

Deployed on:

- Vercel

### Backend

Deployed on:

- Render

### Storage

- Google Drive API

---

## 🛠️ Installation

### Clone Repository

```bash
git clone https://github.com/Anmol-Kapil/CipherVault.git
cd CipherVault
```

---

### Backend Setup

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend runs on:

```text
http://127.0.0.1:8000
```

---

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## 🔑 Environment Variables

Create a `.env` file:

```env
GOOGLE_FOLDER_ID=your_folder_id
```

For production deployment configure:

```env
GOOGLE_FOLDER_ID
GOOGLE_CREDENTIALS
GOOGLE_TOKEN
DATABASE_URL
```

inside Render Environment Variables.

---

## 🎯 Challenges Faced

### Secure File Retrieval

Initially files could be downloaded without sufficient access control.

**Solution:**

- Implemented unique Access IDs
- Added password-protected downloads
- Used bcrypt password hashing

---

### Cloud Deployment

Local Google Drive authentication files could not be exposed publicly.

**Solution:**

- Moved credentials to environment variables
- Configured secure deployment on Render

---

### Frontend-Backend Communication

After deployment API requests failed due to localhost URLs and CORS restrictions.

**Solution:**

- Updated production API endpoints
- Configured FastAPI CORS middleware

---

## 🔮 Future Improvements

- JWT Authentication
- Google OAuth Login
- File Expiration Links
- One-Time Downloads
- PostgreSQL Migration
- User Dashboards
- File Sharing with Expiry
- Download Analytics

---

## 👨‍💻 Author

**Anmol Kapil**

- GitHub: https://github.com/Anmol-Kapil
- LinkedIn: https://linkedin.com/in/anmol-kapil-4b4339263

---

## 📜 License

This project is developed for educational and portfolio purposes.
