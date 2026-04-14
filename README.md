# Resume maker

HTML resume generator based on Jinja2 templates. Quickly make tailored resumes for different job positions by swapping out data files.

## Project Structure

```
remaker/
├── main.py           # entry point
├── template.html     # Jinja2 resume template
├── style.css         # styles
├── locales.json      # translations (ru/en)
├── config.json       # settings
├── data.json         # default resume data
├── requirements.txt
└── output/           # generated resumes
```

## Installation

1. Clone the repository
```bash
git clone https://github.com/Sm4rtSt1ck/resume-maker
cd resume-maker
```

# Install the dependencies
```bash
python -m venv venv
```

```bash
# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

## Configuration

**`config.json`:**

```json
{
    "output_path": "output/",
    "style_path": "style.css",
    "data_path": "data/data.json",
    "lang": "en"
}
```

| Field | Description |
|---|---|
| `output_path` | folder for generated resumes |
| `style_path` | path to the stylesheet |
| `data_path` | path to resume data |
| `lang` | resume language (`ru` / `en`) |

## Resume Data

Resume data is stored in a JSON file. `data.json` is used by default.

```json
{
    "name": "John Doe",
    "email": "john@mail.com",
    "phone": "+12345678910",
    "city": "Moscow",
    "birth_date": "01.01.2000",
    "work_formats": ["office", "hybrid", "remote"],
    "github": "https://github.com/username",
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

## Usage

#### Make a resume

```bash
python remaker.py make "Python Developer"
```

With a custom data file:

```bash
python remaker.py make "Python Developer" -dp data_yandex.json
```

Output is saved to `output/resume_python_developer.html`.

#### Change language

```bash
# show current language
python remaker.py lang

# set language
python remaker.py lang en
```

#### Help

```bash
python main.py --help
python main.py make --help
```

## Dependencies

| Package | Purpose |
|---|---|
| `jinja2` | template engine |


## License

Code is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.