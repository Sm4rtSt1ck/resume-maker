# Resume maker

HTML resume generator based on Jinja2 templates. Quickly make tailored resumes for different job positions by swapping out data files.

## Project Structure

```
remaker/
├── remaker.py        # entry point
├── remaker           # Linux/macOS wrapper script
├── remaker.bat       # Windows wrapper script
├── modules/
├── template.html     # Jinja2 resume template
├── style.css         # styles
├── locales.json      # translations (ru/en)
├── config.json       # settings
├── requirements.txt
├── output/           # generated resumes
└── data/
    ├── data.json     # default resume data
    └── photo.png     # default photo
```

## Installation

1. Clone the repository
```bash
git clone https://github.com/Sm4rtSt1ck/resume-maker
cd resume-maker
```

2. Create a virtual environment and install dependencies
```bash
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

### Setting up the CLI

#### Linux / macOS

Make the wrapper script executable and create a symlink:

```bash
chmod +x remaker
sudo ln -sf "$(pwd)/remaker" /usr/local/bin/remaker
```

#### Windows

Add the project directory to your `PATH` so that `remaker.bat` is available system-wide:

1. Open **System Properties → Advanced → Environment Variables**
2. Under **User variables**, select `Path` and click **Edit**
3. Click **New** and paste the full path to the project directory (e.g. `C:\Projects\resume-maker`)
4. Click **OK** and restart any open terminals

Now you can run the tool from anywhere:

```bash
remaker new data
remaker make "Python Developer"
```


## Resume Data

Resume data and photo are stored in a JSON file in directory `data/`. `data.json` and `photo.png` are used by default.

```json
{
    "name": "John Doe",
    "email": "john@mail.com",
    "phone": "+12345678910",
    "city": "Moscow",
    "birth_date": "01.01.2000",
    "work_formats": ["office", "hybrid", "remote"],
    "github": "https://github.com/username",
    "telegram": "your_tag_without_at",
    "photo": "photo.png",
    "hobbies": ["Computer games", "Swimming", "Sleeping"],
    "about": "I'm good boy, meow meow...",
    "education": [
        ["2020–2024", "University", "Specialty", "Description (may be empty)"]
    ],
    "work_experience": [
        ["2023–2024", "Company", "Position", "Description of responsibilities (may be empty)"]
    ],
    "skills": {
        "Python": "high",
        "SQL": "low",
        "Git": "mid"
    }
}
```

Skill levels: `high`, `mid`, `low`\
Work formats: `office`, `hybrid`, `remote`, this list can be empty\
The phone number may not be specified; for this, the quotes must be blank


## Configuration

**`config.json`:**

```json
{
    "output_path": "output/",
    "template": "classic",
    "data_file": "data",
    "last_file": "test.html",
    "auto_open": true
}
```

You can use commands for configuration.

| Command | Field | Description |
|---|---|---|
| output | `output_path` | folder for generated resumes |
| data | `data_file` | path to resume data |
| lang | `lang` | resume language (`ru` / `en`) |


## Usage

#### Make a resume

```bash
remaker make "Python Developer"
```

With a custom data file:

```bash
remaker make "Python Developer" -dp your_data_file_name
```

Data is stored in `data/FILE_NAME.json`.

#### Change language

```bash
# show current language
remaker lang

# set language
remaker lang en
```

#### Change output path

```bash
# show current output path
remaker output

# set output path
remaker output "Path/to/output/dir"

# reset output path
remaker output --reset
```

#### Help

```bash
remaker --help
remaker make --help
```

## Dependencies

| Package | Purpose |
|---|---|
| `jinja2` | template engine |


## License

Code is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.
