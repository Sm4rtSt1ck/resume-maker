# remaker

HTML resume generator based on Jinja2 templates. Quickly create tailored resumes for different job positions by swapping out data files.

## Features

- **Multiple data files** - keep separate JSON profiles for different roles or industries
- **Interactive TUI editor** - edit resume data right in the terminal with `remaker edit`
- **Multiple templates** - switch between `classic`, `nord`, and `swiss` designs
- **Auto-PDF conversion** - converts HTML to PDF using your installed Chromium browser
- **Multi-language** - resume content supports `en` and `ru` locales
- **Fully CLI-driven** - create, manage, search, and export resumes from the terminal


## Installation

### 1. Clone and set up the virtual environment

```bash
git clone https://github.com/Sm4rtSt1ck/resume-maker
cd resume-maker
python -m venv venv
```

```bash
# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

```bash
pip install -r requirements.txt
```

### 2. Set up the CLI shortcut

**Linux / macOS** - make the wrapper executable and symlink it:

```bash
chmod +x remaker
sudo ln -sf "$(pwd)/remaker" /usr/local/bin/remaker
```

**Windows** - add the project directory to your `PATH`:

1. Open **System Properties → Advanced → Environment Variables**
2. Under **User variables**, select `Path` → **Edit → New**
3. Paste the full project path (e.g. `C:\Projects\resume-maker`)
4. Click OK and restart any open terminals

### 3. PDF support (optional)

PDF conversion uses a system-installed Chromium-based browser (Chrome, Brave, Edge, Vivaldi, Chromium, Opera). The tool searches `PATH` first, then checks standard install locations.

**Windows:** Microsoft Edge is pre-installed on Windows 10/11 and is detected automatically - no extra steps needed.

**Linux:** If no compatible browser is installed:

```bash
# Debian/Ubuntu
sudo apt install chromium

# Arch
sudo pacman -S chromium
```

**macOS:** If no compatible browser is installed:

```bash
brew install --cask chromium
```

If no compatible browser is found, HTML generation still works normally.


## Quick start

```bash
# Create a new data file and fill it in
remaker new myprofile
remaker edit myprofile

# Generate a resume for a specific position
remaker make "Python Developer"

# List generated files
remaker list
```


## Data format

Data files are JSON stored in `data/`. Run `remaker new NAME` to create one from the built-in template.

```jsonc
{
    "lang": "en",              // "en" or "ru"

    "photo": "photo.png",      // filename inside data/
    "name": "Name Surname",
    "birth_date": "01.01.2000",

    "phone": "+12345678910",   // leave "" to hide
    "email": "email@example.com",
    "github": "https://github.com/YourUserName",
    "telegram": "your_tag_without_at",
    "city": "Moscow",

    "work_formats": ["office", "hybrid", "remote"],  // any subset or []

    "about": "Short summary about yourself.",
    "hobbies": ["Reading", "Cycling"],

    "education": [
        ["2020–2024", "University", "Computer Science", "Optional description"]
    ],

    "work_experience": [
        ["2022–2024", "Company", "Backend Developer", "What you did there."]
    ],

    "skills": {
        "Python": "high",      // high / mid / low
        "SQL":    "mid",
        "Docker": "low"
    }
}
```

**Notes:**
- `work_formats` accepts any combination of `office`, `hybrid`, `remote`, or an empty list
- Education and work experience entries: `[date_range, institution/company, role, description]` - description can be `""`
- Skill levels: `high`, `mid`, `low`
- `phone` can be `""` to omit it from the resume


## Commands

### Resume generation

| Command | Description |
|---|---|
| `make POSITION` | Generate HTML resume (+ PDF if enabled) |
| `make POSITION -d NAME` | Use a specific data file instead of the default |
| `convert` | Convert the last generated HTML to PDF |
| `convert -n NAME` | Convert by vacancy name or path to an HTML file |
| `convert -o PATH` | Write PDF to a custom output directory |
| `last` | Open the last generated resume in a browser |
| `search POSITION` | Find generated files matching a position name |
| `list` | List all generated HTML files |
| `list pdf` | List PDF files |
| `list all` | List all generated files |

### Data management

| Command | Description |
|---|---|
| `data` | Show available data files |
| `data NAME` | Set the default data file |
| `new NAME` | Create a new data file from the template |
| `new NAME -c SOURCE` | Create a new data file by copying an existing one |
| `edit [NAME]` | Edit a data file in the interactive TUI editor |
| `remove NAME` | Delete a data file (prompts for confirmation) |
| `rename OLD NEW` | Rename a data file |
| `show [NAME]` | Display the contents of a data file |
| `export PATH` | Export the default data file and its photo |
| `export PATH name1 name2` | Export specific data files |
| `export PATH /` | Export all data files |
| `import PATH` | Import a data file or a directory of data files |

### Configuration

| Command | Description |
|---|---|
| `output` | Show the current output directory |
| `output PATH` | Set the output directory |
| `output --reset` | Reset to default (`output/`) |
| `template` | List available templates |
| `template NAME` | Set the active template |
| `template --reset` | Reset to default (`classic`) |
| `browser` | Show auto-open state |
| `browser on\|off` | Toggle opening resumes in a browser after generation |
| `pdf` | Show auto-convert state |
| `pdf on\|off` | Toggle automatic PDF conversion after `make` |
| `config` | Show all settings as a table |


## Templates

Three templates are included:

| Name | Description |
|---|---|
| `classic` | Clean two-column layout, default |
| `nord` | Dark nord-themed design |
| `swiss` | Minimalist single-column style |

Switch with:

```bash
remaker template nord
```

Custom templates can be added by placing a `.html` Jinja2 file in `templates/`.


## Configuration

Settings are stored in `config.json` and managed through the CLI (`remaker config` to view).

| Key | Default | Description |
|---|---|---|
| `template` | `classic` | Active HTML template |
| `data_file` | - | Default data file name |
| `output_path` | `output/` | Directory for generated files |
| `auto_open` | `true` | Open resume in browser after `make` |
| `convert_to_pdf` | `true` | Auto-convert HTML to PDF after `make` |
| `last_file` | - | Path to the last generated file (set automatically) |


## Project structure

```
resume-maker/
├── remaker.py            # entry point
├── remaker               # Linux/macOS shell wrapper
├── remaker.bat           # Windows wrapper
├── template.json         # blank data file used by `new`
├── locales.yml           # UI strings (en/ru)
├── requirements.txt
├── modules/
│   ├── commands.py       # command implementations
│   ├── consts.py         # BASE_DIR, VERSION
│   ├── defaults.py       # config default values
│   ├── html_to_pdf.py    # PDF conversion via Playwright
│   ├── utils.py          # console helpers, config I/O
│   └── editor/           # interactive TUI data editor (Textual)
│       ├── app.py        # editor application, sidebar, exit dialog
│       ├── schema.py     # field specs inferred from template.json + data
│       └── widgets.py    # spec-driven rows, sections, skill columns
├── templates/
│   ├── classic.html      # default Jinja2 template
│   ├── nord.html
│   └── swiss.html
├── data/                 # your resume data files live here
│   ├── myprofile.json
│   └── photo.png
└── output/               # generated resumes
    ├── resume_python_developer.html
    └── resume_python_developer.pdf
```


## Dependencies

| Package | Purpose |
|---|---|
| `jinja2` | HTML template rendering |
| `click` | CLI framework |
| `rich` | Terminal output formatting |
| `rich-click` | Rich-formatted `--help` output |
| `playwright` | PDF generation via Chromium |


## License

Code is licensed under the MIT License. See [LICENSE](LICENSE) for details.
