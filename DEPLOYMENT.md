# NativeFrames - XAMPP + Cloud Deployment

This version is designed to run in two environments without changing `app.py`.

## 1. Local XAMPP

Keep MySQL running in XAMPP on port **3307**.

Default connection:

- Host: `localhost`
- Port: `3307`
- User: `root`
- Password: empty (change it if your XAMPP MySQL has a password)
- Database: `nativeframes`

Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app can create the `nativeframes` database automatically when the host is localhost.

## 2. Public cloud deployment

A cloud server cannot normally connect to `localhost:3307` on your own PC. `localhost` in the cloud means the cloud server itself, not your XAMPP computer.

For a public deployment:

1. Create a **cloud MySQL database**.
2. Create/use a database named `nativeframes`.
3. Deploy this project to your Streamlit-compatible hosting service.
4. Add either `NATIVEFRAMES_DATABASE_URL` or the individual DB settings as cloud secrets/environment variables.
5. Set `NATIVEFRAMES_DB_AUTO_CREATE=false` for managed cloud MySQL.
6. Set the admin credentials as secrets rather than relying on the demo defaults.

Example:

```text
NATIVEFRAMES_DATABASE_URL=mysql://USER:PASSWORD@CLOUD_HOST:3306/nativeframes
NATIVEFRAMES_DB_AUTO_CREATE=false
NATIVEFRAMES_ADMIN_USERNAME=nativeframes
NATIVEFRAMES_ADMIN_PASSWORD=YOUR_SECURE_PASSWORD
```

The application supports both environment variables and Streamlit Secrets.

## 3. Important: uploaded photos/videos

The database is cloud-ready, but uploaded media is stored on the server filesystem.

- XAMPP: files stay in `static/uploads/`.
- Cloud host with a persistent disk: set `NATIVEFRAMES_UPLOAD_DIR` to the persistent disk path.
- Ephemeral hosts (including many free serverless-style deployments): uploaded files can disappear after a restart/redeploy.

For a serious public NativeFrames gallery, use either a host with persistent storage or add object storage (for example Cloudinary/S3) later.

## 4. Do not expose XAMPP directly

Do not simply open port 3307 on your home PC and publish your XAMPP MySQL server to the internet. Use a managed cloud database for the public version.

## 5. GitHub

Do not upload `.env` or real Streamlit secrets. The example files contain placeholders only.
