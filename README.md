# Cozyup Static Calendar

This repository combines a Cozi calendar and an Outlook calendar and can generate a static page that can be hosted on GitHub Pages.

## Generating the site
1. Copy `settings.env` and fill in your calendar URLs.
2. Create a password hash using `python hash_password.py <password>` and put the result in `SITE_PASSWORD_HASH` inside `settings.env`.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Load the environment variables and run:
   ```bash
   export $(grep -v '^#' settings.env | xargs)
   python generate_site.py
   ```
The script creates `index.html` showing upcoming events. Set `DAYS_AHEAD` in `settings.env` to control how many days are included (defaults to 7).

You can then push `index.html` to the `gh-pages` branch or enable GitHub Pages from the `main` branch to make the page available.

## Password protection
The generated page uses a simple client-side password check based on the hash in `SITE_PASSWORD_HASH`. This is meant only to keep casual visitors out.
