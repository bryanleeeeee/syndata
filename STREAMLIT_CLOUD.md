# Publish datasynthetic.streamlit.app

The repository is ready for a Streamlit Community Cloud deployment.

| Setting | Value |
|---|---|
| Repository | `bryanleeeeee/syndata` |
| Branch | `codex/field-studio` |
| Main file path | `streamlit_app.py` |
| App URL / custom subdomain | `datasynthetic` |
| Python version (Advanced settings) | `3.12` |
| Secrets | None |

1. Sign in at https://share.streamlit.io/ with the account that can access the repository.
2. Select **Create app**, then **Yup, I have an app**.
3. Enter the settings above. Use `streamlit_app.py`, not `launch_app.py`: Community Cloud starts Streamlit itself.
4. Open **Advanced settings**, choose Python 3.12, and save. No API keys or secrets are required.
5. Click **Deploy**. If the requested subdomain is available, the URL will be https://datasynthetic.streamlit.app/.
6. Wait for the build, then generate a 10-customer dataset, prepare a ZIP, and verify the download. Check the deployment logs if the app fails to boot.

The requested subdomain has not been reserved or verified as available. The host must accept it during deployment. Deployment also requires the account holder to complete sign-in and any required terms or repository-access approval.

## Public profile

The `streamlit_app.py` entrypoint sets `BANKSYNTH_DEPLOYMENT=community` and loads the same field studio. It retains the full 500-field catalog, selection, schema validation, explorer and exports, with:

- Simulator-only generation; no reference file uploads or SDV training.
- Up to 2,000 customers, 100,000 worst-case backing transactions and 2,000,000 working cells per run.
- No secrets, external APIs, persistent database or native system packages.
- Session-local generated data and run history; no persistence across server restarts.

These limits reduce per-run memory demand; they do not guarantee capacity for arbitrary concurrent traffic. Community Cloud controls hosting resources and app hibernation. Reference-trained generation remains available through `app.py` in a private/local or Cloudera deployment with the optional SDV dependencies installed.

## Deployment files

- `streamlit_app.py`: Community Cloud entrypoint.
- `requirements.txt`: automatically installed Python dependencies.
- `.streamlit/config.toml`: theme, upload limit and disabled usage telemetry.
- `app_pages/`, `banksynth/`, `logo.svg`: application sources and assets.

Do not upload `.venv`, `.env`, real customer data or local secrets. They are not needed and are excluded from Git.

## Updating

Push commits to `codex/field-studio`; Community Cloud redeploys from the configured branch. The existing Cloudera launcher and Docker entrypoint remain unchanged.

See [Streamlit deployment instructions](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) and [dependency guidance](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).
