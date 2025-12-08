# Publications Auto-Update Setup

## Overview
Publications are automatically fetched from Google Scholar (primary) or ORCID (fallback) and updated during GitLab CI/CD builds.

## Setup Instructions

### 1. Update Configuration
Edit `scripts/fetch_publications.py`:

**For Google Scholar (Recommended - Most Up-to-Date):**
```python
GOOGLE_SCHOLAR_ID = "YOUR_SCHOLAR_ID"  # From your Google Scholar profile URL
USE_GOOGLE_SCHOLAR = True
```

To find your Google Scholar ID:
1. Go to your Google Scholar profile
2. Look at the URL: `https://scholar.google.com/citations?user=XXXXX`
3. Copy the `XXXXX` part (your Scholar ID)

**For ORCID (Fallback):**
```python
ORCID_ID = "0000-0002-1234-5678"  # Your actual ORCID ID
```

### 2. Install Dependencies Locally
```bash
# Install both requests and scholarly
pip install requests scholarly
```

### 3. Test Locally
```bash
# Run the script
python scripts/fetch_publications.py

# Check the output
cat src/data/publications.json
```

### 4. Configure GitLab Scheduled Pipeline
1. Go to your GitLab project → **CI/CD → Schedules**
2. Click **New schedule**
3. Set:
   - **Description**: "Update publications weekly"
   - **Interval Pattern**: `0 2 * * 1` (Every Monday at 2 AM)
   - **Target Branch**: `main`
4. Save

### 4. Manual Trigger
You can also manually trigger updates by:
- Pushing to `main` branch
- Running the scheduled pipeline manually in GitLab

## How It Works

1. **Scheduled Pipeline** runs (or on push to main)
2. **Python script** fetches publications:
   - **Primary**: Google Scholar (most up-to-date, includes citations)
   - **Fallback**: ORCID API (if Scholar fails)
3. **JSON file** is updated with new data
4. **Astro builds** the site with updated publications
5. **Site deploys** with latest publications

## Data Sources

### Google Scholar (Recommended)
- ✅ Most up-to-date publications
- ✅ Includes citation counts
- ✅ Complete author lists
- ⚠️ May be rate-limited by Google

### ORCID (Fallback)
- ✅ Reliable API
- ✅ No rate limits
- ⚠️ Sometimes incomplete author lists
- ⚠️ May have delays in updates

## Data Format

```json
{
  "last_updated": "2024-12-08T10:30:00.000Z",
  "count": 25,
  "publications": [
    {
      "title": "Paper Title",
      "authors": "Author1, Author2, Author3",
      "journal": "Journal Name",
      "year": 2024,
      "doi": "10.1234/example",
      "url": "https://...",
      "type": "Research Article",
      "citations": 15
    }
  ]
}
```

## Troubleshooting

### Publications not updating?
1. Check GitLab CI/CD logs for errors
2. Verify ORCID ID is correct and public
3. Ensure `requests` package is installed in CI

### Want more control?
You can edit `src/data/publications.json` manually and commit changes.
The script won't overwrite if it fails, so manual edits are preserved.

## Alternative: Google Scholar
If you prefer Google Scholar, install `scholarly`:
```bash
pip install scholarly
```
And modify the script to use it (note: may be blocked by Google).
