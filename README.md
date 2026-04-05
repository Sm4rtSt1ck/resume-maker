# Resume maker

HTML resume generator based on Jinja2 templates. Quickly create tailored resumes for different job positions by swapping out data files.

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
    "city": "Moscow",
    "birth_date": "01.01.2000",
    "github": "https://github.com/username",
    "photo": "photo.png",
    "education": [
        ["2020–2024", "University", "Specialty"]
    ],
    "work_experience": [
        ["2023–2024", "Company", "Position", "Description of responsibilities"]
    ],
    "skills": {
        "Python": "high",
        "SQL": "mid",
        "Git": "high"
    }
}
```

Skill levels: `high`, `mid`, `low`.

## Usage

#### Create a resume

```bash
python remaker.py create "Python Developer"
```

With a custom data file:

```bash
python remaker.py create "Python Developer" -dp data_yandex.json
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
python main.py create --help
```

## Dependencies

| Package | Purpose |
|---|---|
| `jinja2` | template engine |


## License

Code is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.