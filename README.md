# NativeFrames 🌿

A Streamlit + MySQL NativeFrames project with reliable embedded logo loading and working Nature, Midnight, and Minimal themes.

## Features

- NativeFrames circular logo presentation
- Viewer sign-in with Name + Mobile Number
- Admin sign-in
- Admin dashboard
- Photo, video and text uploads
- Text/story displayed beside media
- Favorites
- Trash / Restore / Permanent Delete
- Viewer count and login count
- Viewer login history in MySQL
- My Profile
- Theme settings
- Leaf animation
- Viewer gallery
- MySQL on `localhost:3307`

## Default Admin Login

Username:
`nativeframes`

Password:
`nativeframes@24`

For a real deployment, change these using environment variables:

- `NATIVEFRAMES_ADMIN_USERNAME`
- `NATIVEFRAMES_ADMIN_PASSWORD`

## MySQL

Default connection:

- Host: `localhost`
- Port: `3307`
- User: `root`
- Password: empty
- Database: `nativeframes`

If your MySQL root password is not empty, set:

Windows PowerShell:
```powershell
$env:NATIVEFRAMES_DB_PASSWORD="your_password"
```

## Run

1. Install Python.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Make sure MySQL is running on port 3307.
4. Start:

```bash
streamlit run app.py
```

The application creates the `nativeframes` database and required tables automatically.

## Important

This is a functional starter implementation. For public production use, add stronger authentication, CSRF protection where applicable, upload size/type validation, rate limiting, secure secret management, and HTTPS.


## Theme / Logo Fixes in this version

- The logo is embedded as a Base64 data URI, so it does not depend on Streamlit's static URL handling.
- Theme colors are injected directly by Python as CSS variables, so theme switching works reliably after Streamlit reruns.
- Nature, Midnight and Minimal themes now change the full app background, cards, sidebar, forms, text and buttons.


## NativeFrames V2 changes

- Default theme is now **Midnight**.
- Viewer/Audience login now asks for **Name only**; Mobile Number was removed.
- Added themes: **Camera Studio**, **Golden Cinema**, **Forest**, and **Aurora Gallery**.
- Existing Nature and Minimal themes remain.
- Existing MySQL databases are compatible because the viewer `mobile` field is nullable.

## XAMPP + Cloud support

This version supports local XAMPP and public cloud MySQL through environment variables or Streamlit Secrets. See `DEPLOYMENT.md` and `.streamlit/secrets.toml.example`.

**Important:** a public cloud deployment cannot use your PC's `localhost:3307` XAMPP database. Use a cloud MySQL database for the public version. Uploaded media should be placed on persistent cloud storage/disk for production.
