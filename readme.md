# 🔐 CipherVault

> A secure cloud storage platform built with **React**, **FastAPI**, **Supabase PostgreSQL**, and **Google Drive API**, featuring AES-GCM encryption, password-protected downloads, and unique Access IDs.

![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/Database-Supabase_PostgreSQL-3ECF8E?logo=supabase)
![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python)
![License](https://img.shields.io/badge/License-Educational-green)

---

# 📖 Overview

CipherVault is a secure cloud storage platform that encrypts every uploaded file before storing it in Google Drive.

Unlike traditional cloud storage systems, files are never stored in plain form. Each uploaded file is encrypted using **AES-GCM**, protected using a user-defined password, assigned a unique **Access ID**, and securely stored in Google Drive.

The encrypted file metadata—including username, filename, password hash, and Drive File ID—is stored in **Supabase PostgreSQL**, enabling secure retrieval and user-specific file management.

---

# ✨ Features

- 🔒 AES-GCM File Encryption
- 🔑 Password-Protected Downloads
- 🆔 Unique Access ID Generation
- 👤 Username-Based File Dashboard
- ☁️ Google Drive Cloud Storage
- 🗄️ Supabase PostgreSQL Metadata Storage
- 🗑️ File Deletion
- 📱 Responsive React Interface
- ⚡ FastAPI REST APIs
- 🌐 Cloud Deployment (Vercel + Render)

---

# 🏗️ System Architecture

```text
                    User
                      │
                      ▼
          React Frontend (Vercel)
                      │
                REST API Calls
                      │
                      ▼
          FastAPI Backend (Render)
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
 AES-GCM Encryption         SQLAlchemy ORM
        │                           │
        ▼                           ▼
 Google Drive Storage      Supabase PostgreSQL
 (Encrypted Files)          (Metadata)
```

---

# 🛠️ Tech Stack

## Frontend

- React.js
- Axios
- CSS3

## Backend

- FastAPI
- Python
- SQLAlchemy ORM
- Passlib (bcrypt)

## Database

- Supabase PostgreSQL

## Security

- AES-GCM Encryption
- bcrypt Password Hashing

## Cloud Services

- Google Drive API
- Render
- Vercel

---

# 🚀 Upload Workflow

1. User enters a username.
2. User selects a file.
3. User sets a download password.
4. React sends the file to FastAPI.
5. Backend generates a unique Access ID.
6. Password is hashed using bcrypt.
7. File is encrypted using AES-GCM.
8. Encrypted file is uploaded to Google Drive.
9. Metadata is stored in Supabase PostgreSQL.
10. Access ID is returned to the user.

---

# 📥 Download Workflow

1. User enters Access ID.
2. User enters password.
3. FastAPI validates the Access ID.
4. Password hash is verified.
5. Encrypted file is downloaded from Google Drive.
6. File is decrypted.
7. Original file is returned to the user.

---

# 📡 REST API Endpoints

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/upload` | Upload encrypted file |
| POST | `/download` | Download & decrypt file |
| GET | `/user-files/{username}` | Retrieve files uploaded by a user |
| GET | `/files` | List stored metadata |
| DELETE | `/files/{id}` | Delete a file |

---

# 🔐 Security Features

## AES-GCM Encryption

Every uploaded file is encrypted before storage, providing:

- Confidentiality
- Integrity
- Authentication

---

## Password Protection

Passwords are never stored in plaintext.

They are securely hashed using **bcrypt** before being stored in PostgreSQL.

---

## Access ID

Every uploaded file receives a randomly generated Access ID that is required for downloading the file.

---

## Cloud Storage

Only encrypted files are stored in Google Drive.

Metadata is stored separately in Supabase PostgreSQL.

---

# 📸 Screenshots

## Upload Page

<img width="857" height="876" alt="Upload" src="https://github.com/user-attachments/assets/2a0f8a72-3873-40cc-8c25-87fe8e81a398" />

---

## Access ID Generation

<img width="887" height="300" alt="Access ID" src="https://github.com/user-attachments/assets/d83d523c-ba38-4b33-9671-c491b76caac7" />

---

## Download Page

<img width="855" height="331" alt="Download" src="https://github.com/user-attachments/assets/d93a3517-3ce9-4eed-afc4-3954cb3d1bd2" />

---

# ☁️ Deployment

## Frontend

- Vercel

## Backend

- Render

## Database

- Supabase PostgreSQL

## Storage

- Google Drive API

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/Anmol-Kapil/CipherVault.git

cd CipherVault
```

---

## Backend Setup

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```

Backend runs on:

```
http://127.0.0.1:8000
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

# 🔑 Environment Variables

Create a `.env` file inside the backend folder.

```env
DATABASE_URL=your_supabase_database_url

GOOGLE_FOLDER_ID=your_google_drive_folder

GOOGLE_TOKEN=your_google_token_json
```

Never commit these credentials to GitHub.

---

# 💡 Challenges Faced

## 1. Secure Cloud Storage

### Problem

Google Drive stores uploaded files as normal files.

### Solution

Implemented AES-GCM encryption before uploading and decrypted files only after successful authentication.

---

## 2. Cloud Deployment

### Problem

Managing Google Drive credentials securely on Render.

### Solution

Moved credentials into environment variables and securely configured the backend.

---

## 3. Database Migration

### Problem

Needed persistent metadata storage suitable for production.

### Solution

Migrated metadata storage to **Supabase PostgreSQL** using SQLAlchemy ORM without changing the application's business logic.

---

## 4. Frontend–Backend Communication

### Problem

API requests failed after deployment due to localhost URLs and CORS restrictions.

### Solution

Configured FastAPI CORS middleware and updated the frontend to use production API endpoints.

---

# 🚀 Future Improvements

- JWT Authentication
- Google OAuth Login
- Email Verification
- File Sharing
- Expiring Download Links
- One-Time Downloads
- Upload Progress Bar
- Drag & Drop Upload
- Folder Support
- Download Analytics

---

# ⭐ Key Highlights

- Full Stack React + FastAPI Application
- RESTful API Architecture
- AES-GCM Encryption
- Password Hashing with bcrypt
- Google Drive API Integration
- SQLAlchemy ORM
- Supabase PostgreSQL
- Cloud Deployment
- Production Environment Variables
- Responsive UI

---

# 👨‍💻 Author

## Anmol Kapil

**GitHub**

https://github.com/Anmol-Kapil

**LinkedIn**

https://linkedin.com/in/anmol-kapil-4b4339263

---

# 📜 License

This project is developed for educational, learning, and portfolio purposes.
