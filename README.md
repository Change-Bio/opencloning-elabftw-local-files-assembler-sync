# eLabFTW OpenCloning Sequence Sync

This script syncs GenBank/FASTA sequences and Assembly Syntax definitions from specified eLabFTW categories into an OpenCloning `static_content` folder.

It implements a **Sync and Prune** strategy:
- Looks up the eLabFTW internal IDs automatically using the category names you provide.
- Fetches the *newest* `.gb`, `.gbk`, or `.fasta` attachment for sequence resources.
- Fetches the *newest* `.json` attachment for syntax resources.
- Smartly re-downloads updated files when the sequence/syntax is modified in eLabFTW.
- Deletes local files that no longer exist or were removed from the tracked categories in eLabFTW.
- Automatically generates and updates OpenCloning's required `index.json`.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) (Python package manager)
- An eLabFTW instance
- OpenCloning instance with a mounted `static_content` volume

## Setup

1. **Clone the repository:**
   ```bash
   git clone <your_repo_url>
   cd elabftw-opencloning-sync
   ```

2. **Sync Dependencies using `uv`:**
   ```bash
   uv sync
   ```
   *This automatically creates a `.venv` folder and installs all required dependencies (`requests` and `python-dotenv`).*

3. **Configure the Environment:**
   Copy the example config and edit it:
   ```bash
   cp .env.example .env
   nano .env
   ```
   
   Ensure you provide:
   - `ELABFTW_TOKEN`: Get this from your eLabFTW User Panel -> API Keys.
   - `CATEGORY_NAMES`: Comma-separated list of the exact category names you want to sync for sequences (e.g., `"Plasmids, Primers"`).
   - `SYNTAX_CATEGORY_NAMES`: Comma-separated list of the exact category names for syntaxes (e.g., `"Assembly Syntaxes"`).
   - `STATIC_DIR`: The absolute path to your OpenCloning `static_content` folder (e.g., `/path/to/opencloning/static_content`).

## Manual Run

To test if the script works correctly:
```bash
uv run sync_sequences.py
```

## Setting up a Cron Job

To automatically sync sequences in the background, set up a cron job. This example runs the sync every 15 minutes.

1. Open your crontab editor:
   ```bash
   crontab -e
   ```

2. Add the following line (replace paths to match where you cloned this repo and where `uv` is installed):
   ```cron
   */15 * * * * cd /path/to/elabftw-opencloning-sync && /path/to/uv run sync_sequences.py >> sync.log 2>&1
   ```

*Note: You can find exactly where `uv` is installed by running `which uv`.*