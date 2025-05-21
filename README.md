# Cozyup Static Calendar

This repository combines a Cozi calendar and an Outlook calendar and can generate a static page that can be hosted on GitHub Pages.

## Generating the site
1. Copy `settings.env` and provide your calendar URLs and a SHA‑256 hash of the password you want to protect the page with.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate a hash for your password:
   ```bash
   python hash_password.py "my secret" > pass.txt
   ```
   Copy the resulting hash into `settings.env` as `SITE_PASSWORD_HASH`.
4. Load the environment variables and run:
   ```bash
   export $(grep -v '^#' settings.env | xargs)
   python generate_site.py
   ```
The script creates `index.html` with the upcoming events (7 days by default).
Set `DAYS_AHEAD` in your environment to change the horizon.

You can then push `index.html` to the `gh-pages` branch or enable GitHub Pages from the `main` branch to make the page available.

## Password protection
The generated page uses a simple client‑side password check. Set the environment variable `SITE_PASSWORD_HASH` to a SHA‑256 hash of your chosen password. Only users with the password can view the page, but note that client‑side protection is not fully secure.
