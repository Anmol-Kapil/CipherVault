import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState("");
  const [downloadPassword, setDownloadPassword] = useState("");
  const [lastAccessId, setLastAccessId] = useState("");
  const [downloadId, setDownloadId] = useState("");

  useEffect(() => {
    if (!lastAccessId) {
      return;
    }

    const timer = setTimeout(() => {
      setLastAccessId("");
    }, 15000);

    return () => clearTimeout(timer);
  }, [lastAccessId]);

  const API = "https://ciphervault-backend.onrender.com";

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const response = await axios.get(`${API}/files`);
      setFiles(response.data);
    } catch (error) {
      console.error("Error loading files:", error);
    }
  };

  const deleteFile = async (fileId) => {
    const confirmDelete = window.confirm("Delete this file?");
    if (!confirmDelete) return;

    try {
      await axios.delete(`${API}/files/${fileId}`);
      alert("File Deleted Successfully");
      loadFiles();
    } catch (error) {
      console.error(error);
      alert("Delete Failed");
    }
  };

  const uploadFile = async () => {
    if (!file) {
      alert("Select a file");
      return;
    }

    try {
      setLoading(true);
      const formData = new FormData();

      formData.append("file", file);
      formData.append("password", password);

      const response = await axios.post(`${API}/upload`, formData);
      setLastAccessId(response.data.access_id);
      alert("File Uploaded Successfully");
      setFile(null);
      setPassword("");
      loadFiles();
    } catch (error) {
      console.error(error);
      alert("Upload Failed");
    } finally {
      setLoading(false);
    }
  };

  const downloadFile = async () => {
    if (!downloadId) {
      alert("Enter Access ID");
      return;
    }

    if (!downloadPassword) {
      alert("Enter Password");
      return;
    }

    try {
      const response = await axios.post(
  `${API}/download`,
  null,
  {
    params: {
      access_id: downloadId,
      password: downloadPassword
    },
    responseType: "blob"
  }
);

      let filename = "downloaded_file";

      const disposition = response.headers["content-disposition"];

      if (disposition) {
        const match = disposition.match(/filename="?([^"]+)"?/);

        if (match) {
          filename = match[1];
        }
      }

      const blob = new Blob([response.data], {
        type: response.headers["content-type"],
      });

      const url = window.URL.createObjectURL(blob);

      const link = document.createElement("a");

      link.href = url;

      link.download = filename;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);

      alert("Invalid Access ID or Password");
    }
  };

  return (
    <div className="container">
      <div className="card">
        <div className="header">
          <div className="logo-box">
            <div className="logo-icon">🔐</div>
            <div>
              <h1>Secure Cloud Storage</h1>
              <p className="subtitle">End-to-End Encrypted Cloud Storage</p>
            </div>
          </div>
        </div>

        {/* Upload Section */}
        <div className="upload-section">
          <h2>Upload File</h2>
          <div className="file-input-wrapper">
            <div className="file-input-group">
              <label className="file-input-label">
                Choose File
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files[0])}
                />
              </label>
            </div>

            {file && (
              <div
                style={{
                  background: "#f8fafc",
                  padding: "12px 18px",
                  borderRadius: "10px",
                  border: "1px solid #e2e8f0",
                  fontWeight: "600",
                  maxWidth: "350px",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                📄 {file.name}
              </div>
            )}

            <input
              type="password"
              placeholder="Set Download Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "12px",
                marginTop: "10px",
                marginBottom: "10px",
                border: "2px solid #333",
                borderRadius: "8px",
                fontSize: "16px",
              }}
            />

            <button
              className="btn-upload"
              onClick={uploadFile}
              disabled={loading}
            >
              {loading ? "Uploading..." : "Upload File"}
            </button>
          </div>
        </div>

        {/* Access ID Section */}
        {lastAccessId && (
          <div className="upload-section">
            <h2>Access ID</h2>

            <div
              style={{
                background: "#fff3cd",
                color: "#856404",
                padding: "12px",
                borderRadius: "10px",
                marginBottom: "15px",
                border: "1px solid #ffeeba",
                fontWeight: "600",
              }}
            >
              ⚠️ Save this Access ID now. It will automatically disappear after
              15 seconds.
            </div>

            <p
              style={{
                fontSize: "24px",
                fontWeight: "bold",
                letterSpacing: "2px",
              }}
            >
              {lastAccessId}
            </p>

            <button
              className="btn-upload"
              onClick={() => {
                navigator.clipboard.writeText(lastAccessId);

                alert("Access ID copied!");
              }}
            >
              Copy Access ID
            </button>
          </div>
        )}

        {/* Download Section */}
        <div className="upload-section">
          <h2>Download File</h2>

          <input
            type="text"
            placeholder="Enter Access ID"
            value={downloadId}
            onChange={(e) => setDownloadId(e.target.value)}
            style={{
              width: "100%",
              padding: "12px",
              marginTop: "10px",
              marginBottom: "10px",
              border: "2px solid #333",
              borderRadius: "8px",
              fontSize: "16px",
            }}
          />

          <input
            type="password"
            placeholder="Enter Password"
            value={downloadPassword}
            onChange={(e) => setDownloadPassword(e.target.value)}
            style={{
              width: "100%",
              padding: "12px",
              marginTop: "10px",
              marginBottom: "10px",
              border: "2px solid #333",
              borderRadius: "8px",
              fontSize: "16px",
            }}
          />

          <button className="btn-upload" onClick={downloadFile}>
            Download File
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;