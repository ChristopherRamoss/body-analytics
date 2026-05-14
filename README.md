diff --git a/README.md b/README.md
index 65ea5427958893dfc87bf90105d19c04d1330764..27d45b06fe056742f7aaf0f7aaf23b2e21de72b3 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,35 @@
-# body-analytics
\ No newline at end of file
+# body-analytics
+
+## Run locally
+
+```bash
+pip install -r requirements.txt
+streamlit run main.py
+```
+
+## Persistence backends
+
+By default the app uses SQLite (`body_analytics.db`).
+
+To use Google Sheets (recommended for Streamlit Cloud), set `.streamlit/secrets.toml`:
+
+```toml
+DATA_BACKEND = "gsheets"
+GOOGLE_SHEETS_KEY = "your_google_sheet_key"
+
+[gcp_service_account]
+type = "service_account"
+project_id = "..."
+private_key_id = "..."
+private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
+client_email = "..."
+client_id = "..."
+auth_uri = "https://accounts.google.com/o/oauth2/auth"
+token_uri = "https://oauth2.googleapis.com/token"
+auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
+client_x509_cert_url = "..."
+universe_domain = "googleapis.com"
+```
+
+Create a Google Sheet and share it with the `client_email` in service account credentials.
+The app will auto-create these tabs: `profile`, `weights`, `goals`.
