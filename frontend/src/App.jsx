import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "./App.css";

function Icon({ name, size = 20 }) {
  const paths = {
    shield: (
      <>
        <path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z" />
        <path d="m8 12 3 3 5-6" />
      </>
    ),
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    upload: <path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5" />,
    download: <path d="M12 3v13m-5-5 5 5 5-5M4 17v4h16v-4" />,
    file: (
      <>
        <path d="M14 2H5v20h14V7zM14 2v6h5M8 13h8M8 17h6" />
      </>
    ),
    lock: (
      <>
        <rect x="5" y="10" width="14" height="11" rx="3" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
      </>
    ),
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 6 6" />
      </>
    ),
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    copy: (
      <>
        <rect x="8" y="8" width="12" height="13" rx="2" />
        <path d="M15 8V3H3v13h5" />
      </>
    ),
    trash: <path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7M14 10v7" />,
    check: <path d="m5 12 4 4L19 6" />,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    refresh: <path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5" />,
    disk: (
      <>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.file}
    </svg>
  );
}
function trapModalFocus(event) {
  if (event.key !== "Tab") return;
  const controls = [
    ...event.currentTarget.querySelectorAll(
      "button:not(:disabled), input, select, a[href]",
    ),
  ];
  const first = controls[0],
    last = controls[controls.length - 1];
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last?.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first?.focus();
  }
}

const bytes = (value) =>
  value >= 1048576
    ? `${(value / 1048576).toFixed(1)} MB`
    : value >= 1024
      ? `${(value / 1024).toFixed(1)} KB`
      : `${value} B`;
const navItems = [
  ["overview", "grid", "Overview"],
  ["upload", "upload", "Upload file"],
  ["files", "file", "My files"],
  ["download", "download", "Retrieve file"],
];

export default function App() {
  const [page, setPage] = useState("overview");
  const [files, setFiles] = useState([]);
  const [status, setStatus] = useState("connecting");
  const [storage, setStorage] = useState(null);
  const [checkingDrive, setCheckingDrive] = useState(false);
  const [lastStorage, setLastStorage] = useState("drive");
  const [notice, setNotice] = useState(null);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [accessId, setAccessId] = useState("");
  const [downloadId, setDownloadId] = useState("");
  const [downloadPassword, setDownloadPassword] = useState("");
  const [query, setQuery] = useState("");
  const [owner, setOwner] = useState("");
  const [deleting, setDeleting] = useState(null);
  const [deletePassword, setDeletePassword] = useState("");
  const fileInput = useRef(null);

  async function refresh() {
    try {
      const [response, health] = await Promise.all([
        axios.get("/api/files"),
        axios.get("/api/"),
      ]);
      setFiles(response.data);
      setStorage(health.data.storage);
      setStatus("online");
    } catch {
      setStatus("offline");
      setNotice({
        error: true,
        text: "Cannot reach the local backend. Start it on port 8000, then reconnect.",
      });
    }
  }
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      axios.get("/api/files", { signal: controller.signal }),
      axios.get("/api/", { signal: controller.signal }),
    ])
      .then(([response, health]) => {
        setFiles(response.data);
        setStorage(health.data.storage);
        setStatus("online");
      })
      .catch((error) => {
        if (!axios.isCancel(error)) setStatus("offline");
      });
    return () => controller.abort();
  }, []);
  async function checkDrive() {
    setCheckingDrive(true);
    setNotice(null);
    try {
      const { data } = await axios.post("/api/storage/check");
      setStorage(data);
    } catch (error) {
      await errorNotice(error);
    } finally {
      setCheckingDrive(false);
    }
  }
  const offlineDemo = storage?.backend === "local";
  const destination = offlineDemo
    ? "this device (offline demo)"
    : "your Google Drive";
  async function errorNotice(error) {
    let detail = error.response?.data;
    if (detail instanceof Blob) {
      try {
        detail = JSON.parse(await detail.text());
      } catch {
        detail = null;
      }
    }
    setNotice({
      error: true,
      text:
        typeof detail?.detail === "string"
          ? detail.detail
          : "Something went wrong. Check your inputs and local server, then try again.",
    });
  }
  function chooseFile(file) {
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
      setNotice({ error: true, text: "Choose a file of 25 MB or smaller." });
      return;
    }
    setSelected(file);
    setNotice(null);
  }
  async function upload(event) {
    event.preventDefault();
    if (!selected) {
      setNotice({ error: true, text: "Choose a file first." });
      return;
    }
    setBusy(true);
    setNotice(null);
    try {
      const form = new FormData();
      form.append("file", selected);
      form.append("username", username);
      form.append("password", password);
      const { data } = await axios.post("/api/upload", form);
      setLastStorage(data.storage_backend);
      setAccessId(data.access_id);
      setDownloadId(data.access_id);
      setSelected(null);
      setPassword("");
      if (fileInput.current) fileInput.current.value = "";
      await refresh();
    } catch (error) {
      await errorNotice(error);
    } finally {
      setBusy(false);
    }
  }
  async function download(event) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    try {
      const response = await axios.post(
        "/api/download",
        { access_id: downloadId, password: downloadPassword },
        { responseType: "blob" },
      );
      const name =
        response.headers["content-disposition"]?.split("filename*=UTF-8''")[1];
      const url = URL.createObjectURL(response.data);
      const link = document.createElement("a");
      link.href = url;
      link.download = name ? decodeURIComponent(name) : "download";
      document.body.appendChild(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setDownloadPassword("");
      setNotice({
        text: "File decrypted successfully. Your download is ready.",
      });
    } catch (error) {
      await errorNotice(error);
    } finally {
      setBusy(false);
    }
  }
  async function remove(event) {
    event.preventDefault();
    setBusy(true);
    try {
      await axios.delete(`/api/files/${deleting.id}`, {
        data: { password: deletePassword },
      });
      setDeleting(null);
      setDeletePassword("");
      await refresh();
      setNotice({ text: "File permanently deleted from its storage." });
    } catch (error) {
      await errorNotice(error);
    } finally {
      setBusy(false);
    }
  }
  function navigate(next) {
    setPage(next);
    setNotice(null);
  }
  const visible = files.filter(
    (file) =>
      file.filename.toLowerCase().includes(query.toLowerCase()) &&
      (!owner || file.username === owner),
  );
  const total = files.reduce((sum, file) => sum + file.size, 0);
  const title = {
    overview: "Your files. Your space.",
    upload: "A little more peace of mind.",
    files: "Everything in its place.",
    download: "Only you hold the details.",
  }[page];

  function fileTable(items) {
    return items.length ? (
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>File name</th>
              <th>Owner</th>
              <th>Size</th>
              <th>Date added</th>
              <th>
                <span className="sr-only">Actions</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {items.map((file) => (
              <tr key={file.id}>
                <td>
                  <div className="file-cell">
                    <span
                      className={`file-icon ${file.mime_type.startsWith("image/") ? "image" : ""}`}
                    >
                      <Icon name="file" />
                    </span>
                    <div>
                      <strong>{file.filename}</strong>
                      <small>
                        {file.filename.includes(".")
                          ? file.filename.split(".").pop().toUpperCase()
                          : "FILE"}{" "}
                        <span>
                          ·{" "}
                          {file.storage_backend === "drive" ? "Drive" : "Local"}{" "}
                          · Encrypted
                        </span>
                      </small>
                    </div>
                  </div>
                </td>
                <td>{file.username}</td>
                <td>{bytes(file.size)}</td>
                <td>
                  {new Date(file.upload_date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </td>
                <td>
                  <button
                    className="icon-button danger"
                    aria-label={`Delete ${file.filename}`}
                    onClick={() => {
                      setDeleting(file);
                      setNotice(null);
                    }}
                  >
                    <Icon name="trash" size={17} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <div className="empty">
        <Icon name="file" size={34} />
        <h3>{files.length ? "No matching files" : "Your vault starts here"}</h3>
        <p>
          {files.length
            ? "Try a different filename or owner."
            : "Upload your first file and keep it encrypted in your own storage."}
        </p>
        {!files.length && (
          <button
            className="button secondary"
            onClick={() => navigate("upload")}
          >
            Upload a file <Icon name="arrow" size={16} />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" inert={Boolean(accessId || deleting)}>
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            navigate("overview");
          }}
        >
          <span className="brand-mark">
            <Icon name="shield" size={26} />
          </span>
          CipherVault<span className="brand-dot">.</span>
        </a>
        <div className="workspace-label">PERSONAL WORKSPACE</div>
        <nav aria-label="Main navigation">
          {navItems.map(([key, icon, label]) => (
            <button
              key={key}
              className={`nav-item ${page === key ? "active" : ""}`}
              onClick={() => navigate(key)}
            >
              <Icon name={icon} />
              {label}
              {key === "files" && (
                <span className="nav-count">{files.length}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="privacy-note">
            <Icon name="shield" size={23} />
            <strong>Private by design.</strong>
            <p>
              Encrypted files. Your storage.
              <br />A space that stays yours.
            </p>
            <span>
              AES-256-GCM <Icon name="check" size={13} />
            </span>
          </div>
          <div className="local-profile">
            <span className="avatar">G</span>
            <div>
              <strong>
                {offlineDemo ? "Offline demo" : "Your Google Drive"}
              </strong>
              <small>
                {offlineDemo ? "Local test storage" : "Your own account"}
              </small>
            </div>
            <Icon name="lock" size={16} />
          </div>
        </div>
      </aside>
      <div className="main-shell" inert={Boolean(accessId || deleting)}>
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span>{" "}
            <strong>{navItems.find((item) => item[0] === page)[2]}</strong>
          </div>
          <span className={`connection ${status}`}>
            <i />
            {status === "online"
              ? offlineDemo
                ? "Offline demo"
                : storage?.verified
                  ? "Drive connected"
                  : storage?.configured
                    ? "Drive configured"
                    : "Drive setup needed"
              : status === "offline"
                ? "Backend offline"
                : "Connecting to vault"}
          </span>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                YOUR FILES. YOUR GOOGLE DRIVE. YOUR PEACE OF MIND.
              </div>
              <h1>{title}</h1>
              <p>
                {page === "overview"
                  ? "A calmer, safer home for the things you want to keep."
                  : page === "upload"
                    ? "Encrypt a file and make yourself at home."
                    : page === "files"
                      ? "Browse, find, and manage your encrypted files."
                      : "Retrieve an original file with its access ID and password."}
              </p>
            </div>
            {page === "overview" && (
              <button
                className="button primary"
                onClick={() => navigate("upload")}
              >
                <Icon name="upload" size={17} /> Upload file
              </button>
            )}
          </div>
          {status === "offline" && (
            <div className="notice error" role="alert">
              Your backend is offline. Run the local server, then{" "}
              <button onClick={refresh}>reconnect</button>.
            </div>
          )}
          {status === "online" && storage?.backend === "drive" && (
            <div
              className={`storage-banner ${storage.verified ? "verified" : ""}`}
              aria-label="Storage connection"
            >
              <Icon name="shield" size={22} />
              <div>
                <strong>
                  {storage.verified
                    ? "Your Google Drive is connected"
                    : storage.configured
                      ? "Your Google Drive credentials are configured"
                      : "Connect your own Google Drive"}
                </strong>
                <p>
                  {storage.message} Metadata and your encryption key stay on
                  this computer.
                </p>
                {!storage.configured && (
                  <a
                    href="https://github.com/Anmol-Kapil/CipherVault#2-connect-your-own-google-drive"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open the Google Drive setup guide{" "}
                    <Icon name="arrow" size={13} />
                  </a>
                )}
              </div>
              <button
                className="button secondary"
                onClick={checkDrive}
                disabled={checkingDrive || !storage.configured}
              >
                {checkingDrive ? "Checking…" : "Check Drive connection"}
              </button>
            </div>
          )}
          {status === "online" && offlineDemo && (
            <div className="demo-banner">
              Offline demo mode · Files stay on this device. Google Drive is the
              default for normal use.
            </div>
          )}
          {notice && (
            <div
              className={`notice ${notice.error ? "error" : ""}`}
              role={notice.error ? "alert" : "status"}
            >
              <Icon name={notice.error ? "shield" : "check"} size={18} />
              {notice.text}
              <button
                className="icon-button"
                aria-label="Dismiss notification"
                onClick={() => setNotice(null)}
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          )}
          {page === "overview" && (
            <>
              <section className="hero">
                <div className="hero-copy">
                  <span className="pill">
                    <span /> ENCRYPT FIRST. STORE IN YOUR DRIVE.
                  </span>
                  <h2>
                    Keep it close.
                    <br />
                    Keep it <em>yours.</em>
                  </h2>
                  <p>
                    Your important files, encrypted before they leave the app.
                    <br />
                    {offlineDemo
                      ? "Offline demo storage on this device."
                      : "Your own Google account. Your own private vault."}
                  </p>
                  <button
                    className="text-button"
                    onClick={() => navigate("upload")}
                  >
                    Add something worth keeping <Icon name="arrow" size={18} />
                  </button>
                </div>
                <div className="vault-art" aria-hidden="true">
                  <div className="orbit orbit-one" />
                  <div className="orbit orbit-two" />
                  <span className="art-star star-one">+</span>
                  <span className="art-star star-two">+</span>
                  <div className="vault-shadow" />
                  <div className="vault-box">
                    <div className="vault-face">
                      <div className="vault-dial">
                        <span />
                        <span />
                        <span />
                        <span />
                        <div>
                          <Icon name="lock" size={33} />
                        </div>
                      </div>
                      <i className="hinge top" />
                      <i className="hinge bottom" />
                    </div>
                  </div>
                  <span className="art-tag">
                    <Icon name="shield" size={14} /> Encrypted before upload
                  </span>
                </div>
              </section>
              <section className="stats" aria-label="Vault statistics">
                <div className="stat">
                  <span className="stat-symbol">
                    <Icon name="file" />
                  </span>
                  <div>
                    <p>Files in your vault</p>
                    <strong>{files.length.toString().padStart(2, "0")}</strong>
                  </div>
                  <span className="stat-label">ALL ENCRYPTED</span>
                </div>
                <div className="stat">
                  <span className="stat-symbol peach">
                    <Icon name="disk" />
                  </span>
                  <div>
                    <p>Original file size</p>
                    <strong>{bytes(total)}</strong>
                  </div>
                  <span className="stat-label">ORIGINAL BYTES</span>
                </div>
                <div className="stat">
                  <span className="stat-symbol green">
                    <Icon name="shield" />
                  </span>
                  <div>
                    <p>Encryption standard</p>
                    <strong className="encryption-stat">
                      AES-256 <span>GCM</span>
                    </strong>
                  </div>
                  <span className="stat-label">AT REST</span>
                </div>
              </section>
              <section className="panel">
                <div className="section-heading">
                  <div>
                    <h2>
                      Recently tucked away <span>{files.length}</span>
                    </h2>
                    <p>A little order for your important things.</p>
                  </div>
                  <button
                    className="text-button"
                    onClick={() => navigate("files")}
                  >
                    View all files <Icon name="arrow" size={16} />
                  </button>
                </div>
                {fileTable(files.slice(0, 4))}
              </section>
              <div className="bottom-note">
                <Icon name="lock" size={14} /> Files encrypted in {destination}.
                Your key stays on this computer.
              </div>
            </>
          )}
          {page === "upload" && (
            <div className="form-layout">
              <section className="panel form-panel">
                <div className="section-heading">
                  <div>
                    <h2>Make room for something important</h2>
                    <p>One file, one password, one private place.</p>
                  </div>
                  <span className="step-tag">01 / ENCRYPT & SAVE</span>
                </div>
                <form onSubmit={upload}>
                  <label
                    className={`dropzone ${dragging ? "dragging" : ""}`}
                    onDragOver={(event) => {
                      event.preventDefault();
                      setDragging(true);
                    }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={(event) => {
                      event.preventDefault();
                      setDragging(false);
                      chooseFile(event.dataTransfer.files[0]);
                    }}
                  >
                    <input
                      ref={fileInput}
                      type="file"
                      aria-label="Choose a file"
                      onChange={(event) => chooseFile(event.target.files[0])}
                    />
                    <span className="drop-icon">
                      <Icon name={selected ? "file" : "upload"} size={28} />
                    </span>
                    <strong>
                      {selected
                        ? selected.name
                        : "Drop a file. We’ll keep it safe."}
                    </strong>
                    <span>
                      {selected ? (
                        `${bytes(selected.size)} · Click to choose another file`
                      ) : (
                        <>
                          or <b>browse your device</b>
                        </>
                      )}
                    </span>
                    <small>
                      Any file type · Up to 25 MB · One file at a time
                    </small>
                  </label>
                  <div className="form-grid">
                    <label>
                      Owner name
                      <input
                        required
                        maxLength={80}
                        value={username}
                        onChange={(event) => setUsername(event.target.value)}
                        placeholder="e.g. anmol"
                        autoComplete="username"
                      />
                      <small>A label to help you find your files later.</small>
                    </label>
                    <label>
                      File password
                      <input
                        required
                        type="password"
                        minLength={8}
                        maxLength={72}
                        value={password}
                        onChange={(event) => setPassword(event.target.value)}
                        placeholder="At least 8 characters"
                        autoComplete="new-password"
                      />
                      <small>
                        Keep this safe. Passwords cannot be recovered.
                      </small>
                    </label>
                  </div>
                  <button
                    className="button primary wide"
                    disabled={
                      busy || status !== "online" || !storage?.configured
                    }
                  >
                    <Icon name="lock" size={17} />
                    {busy ? "Encrypting & saving…" : "Encrypt & save file"}
                    <Icon name="arrow" size={17} />
                  </button>
                </form>
              </section>
              <aside className="info-card">
                <span className="info-icon">
                  <Icon name="shield" size={26} />
                </span>
                <h2>
                  A small ritual.
                  <br />A safer file.
                </h2>
                <ol>
                  <li>
                    <strong>Choose your file</strong>
                    <p>Documents, images, archives — bring what matters.</p>
                  </li>
                  <li>
                    <strong>Make it private</strong>
                    <p>
                      AES-256-GCM encrypts your file before it reaches{" "}
                      {destination}.
                    </p>
                  </li>
                  <li>
                    <strong>Keep your access ID</strong>
                    <p>
                      You’ll need it, along with your password, to retrieve the
                      original.
                    </p>
                  </li>
                </ol>
                <div className="info-foot">
                  <Icon name="lock" size={15} /> Only encrypted file content
                  reaches your storage.
                </div>
              </aside>
            </div>
          )}
          {page === "files" && (
            <section className="panel">
              <div className="section-heading">
                <div>
                  <h2>
                    Your file collection <span>{files.length}</span>
                  </h2>
                  <p>Encrypted in your storage. Easy to find here.</p>
                </div>
                <button className="button secondary" onClick={refresh}>
                  <Icon name="refresh" size={16} />
                  Refresh
                </button>
              </div>
              <div className="filters">
                <label className="search-field">
                  <Icon name="search" size={18} />
                  <input
                    aria-label="Search filenames"
                    placeholder="Find a file by name…"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </label>
                <label className="owner-filter">
                  Owner
                  <select
                    aria-label="Filter by owner"
                    value={owner}
                    onChange={(event) => setOwner(event.target.value)}
                  >
                    <option value="">All owners</option>
                    {[...new Set(files.map((file) => file.username))].map(
                      (name) => (
                        <option key={name}>{name}</option>
                      ),
                    )}
                  </select>
                </label>
              </div>
              {fileTable(visible)}
              <div className="table-footer">
                {visible.length} {visible.length === 1 ? "file" : "files"}{" "}
                <span>Metadata is visible within this local workspace.</span>
              </div>
            </section>
          )}
          {page === "download" && (
            <div className="form-layout">
              <section className="panel form-panel">
                <div className="section-heading">
                  <div>
                    <h2>Welcome your file back</h2>
                    <p>Two details unlock what’s yours.</p>
                  </div>
                  <span className="step-tag">02 / UNLOCK & RETRIEVE</span>
                </div>
                <div className="retrieve-symbol">
                  <Icon name="download" size={33} />
                </div>
                <form onSubmit={download} className="retrieve-form">
                  <label>
                    Access ID
                    <input
                      required
                      value={downloadId}
                      onChange={(event) => setDownloadId(event.target.value)}
                      placeholder="Paste the ID from your upload"
                      autoComplete="off"
                      spellCheck="false"
                    />
                  </label>
                  <label>
                    File password
                    <input
                      required
                      type="password"
                      value={downloadPassword}
                      onChange={(event) =>
                        setDownloadPassword(event.target.value)
                      }
                      placeholder="Enter this file’s password"
                      autoComplete="off"
                    />
                  </label>
                  <button
                    className="button primary wide"
                    disabled={busy || status !== "online"}
                  >
                    <Icon name="download" size={17} />
                    {busy ? "Decrypting…" : "Decrypt & download"}
                    <Icon name="arrow" size={17} />
                  </button>
                </form>
                <div className="form-foot">
                  <Icon name="shield" size={15} /> Integrity verified before
                  every download.
                </div>
              </section>
              <aside className="info-card">
                <span className="info-icon">
                  <Icon name="lock" size={26} />
                </span>
                <h2>
                  A key only
                  <br />
                  you can keep.
                </h2>
                <p>
                  Your access ID finds the file. Your password authorizes the
                  download. You need both.
                </p>
                <div className="tip">
                  <strong>Lost your details?</strong>
                  <p>
                    Access IDs are shown after upload. Save them somewhere safe
                    — there’s no password reset or recovery service.
                  </p>
                </div>
                <div className="info-foot">
                  Your original filename is preserved.
                </div>
              </aside>
            </div>
          )}
          <footer>
            <span>
              CipherVault <span className="footer-dot">/</span> A little privacy
              goes a long way.
            </span>
            <span>YOUR ACCOUNT. YOUR DRIVE. YOUR FILES.</span>
          </footer>
        </main>
      </div>
      {accessId && (
        <div className="modal-backdrop">
          <section
            className="modal"
            onKeyDown={trapModalFocus}
            role="dialog"
            aria-modal="true"
            aria-labelledby="saved-title"
          >
            <span className="success-symbol">
              <Icon name="check" size={30} />
            </span>
            <div className="eyebrow">SAFELY TUCKED AWAY</div>
            <h2 id="saved-title">One less thing to worry about.</h2>
            <p>
              Your file is encrypted and saved in{" "}
              {lastStorage === "local"
                ? "offline demo storage"
                : "your Google Drive"}
              .
              <br />
              Keep this access ID and your password somewhere safe.
            </p>
            <div className="access-code">
              <small>YOUR ACCESS ID</small>
              <code>{accessId}</code>
            </div>
            <button
              autoFocus
              className="button primary wide"
              onClick={async () => {
                try {
                  await navigator.clipboard.writeText(accessId);
                  setNotice({ text: "Access ID copied to clipboard." });
                } catch {
                  setNotice({
                    error: true,
                    text: "Clipboard unavailable. Select and copy the access ID manually.",
                  });
                }
              }}
            >
              <Icon name="copy" size={17} />
              Copy access ID
            </button>
            {notice && (
              <p role="status" className="copy-status">
                {notice.text}
              </p>
            )}
            <button
              className="text-button modal-done"
              onClick={() => {
                setAccessId("");
                navigate("files");
              }}
            >
              I’ve saved my ID. View my files <Icon name="arrow" size={16} />
            </button>
            <small>This ID stays visible until you close this message.</small>
          </section>
        </div>
      )}
      {deleting && (
        <div className="modal-backdrop">
          <section
            className="modal delete-modal"
            onKeyDown={trapModalFocus}
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-title"
          >
            <span className="success-symbol red">
              <Icon name="trash" size={27} />
            </span>
            <h2 id="delete-title">Let this file go?</h2>
            <p>
              <strong>{deleting.filename}</strong> will be permanently deleted
              from{" "}
              {deleting.storage_backend === "drive"
                ? "Google Drive"
                : "this device"}
              . This cannot be undone.
            </p>
            <form onSubmit={remove}>
              <label>
                File password
                <input
                  autoFocus
                  required
                  type="password"
                  value={deletePassword}
                  onChange={(event) => setDeletePassword(event.target.value)}
                  placeholder="Confirm with this file’s password"
                />
              </label>
              {notice?.error && (
                <p className="inline-error" role="alert">
                  {notice.text}
                </p>
              )}
              <div className="modal-actions">
                <button
                  type="button"
                  className="button secondary"
                  disabled={busy}
                  onClick={() => {
                    setDeleting(null);
                    setDeletePassword("");
                  }}
                >
                  Keep file
                </button>
                <button className="button destructive" disabled={busy}>
                  {busy ? "Deleting…" : "Delete permanently"}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </div>
  );
}
