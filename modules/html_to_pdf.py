import sys
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright


# Possible browser binary names to look up in PATH (Chromium-based only)
BROWSER_NAMES = (
    "chromium", "chromium-browser",
    "google-chrome", "google-chrome-stable",
    "chrome",
    "brave", "brave-browser",
    "opera",
    "vivaldi",
    "msedge",
)

# Standard install locations on Windows (browsers usually aren't in PATH there)
WINDOWS_CANDIDATES = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files\Opera\opera.exe",
    r"C:\Program Files (x86)\Opera\opera.exe",
    r"C:\Program Files\Vivaldi\Application\vivaldi.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
)

# Standard install locations on macOS
MACOS_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Opera.app/Contents/MacOS/Opera",
    "/Applications/Vivaldi.app/Contents/MacOS/Vivaldi",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
)


def find_browser() -> str | None:
    """Locate a Chromium-based browser in the system."""
    # 1. Try PATH (works on Linux/macOS, and Windows if added to PATH)
    for name in BROWSER_NAMES:
        path = shutil.which(name)
        if path:
            return path

    # 2. Platform-specific standard install locations
    if sys.platform == "win32":
        candidates = WINDOWS_CANDIDATES
    elif sys.platform == "darwin":
        candidates = MACOS_CANDIDATES
    else:
        candidates = ()

    for path in candidates:
        if Path(path).exists():
            return path

    return None


def html_to_pdf(html_path: str | Path, pdf_path: str | Path) -> bool:
    """
    Convert an HTML file to PDF using Playwright with a system-installed
    Chromium-based browser.

    Returns:
        True  — PDF generated successfully.
        False — No Chromium-based browser found.
    """

    chrome = find_browser()
    if chrome is None:
        return False

    abs_html = Path(html_path).resolve().as_uri()
    abs_pdf = str(Path(pdf_path).resolve())

    with sync_playwright() as p:  # type: ignore[possibly-unbound]
        browser = p.chromium.launch(executable_path=chrome)
        page = browser.new_page()
        page.goto(abs_html, wait_until="networkidle")
        page.pdf(
            path=abs_pdf,
            format="A4",
            print_background=True,                 # render background colors
            display_header_footer=False,           # no header/footer text on margins
            margin={"top": "0", "bottom": "0",     # Margins: None
                    "left": "0", "right": "0"},
            scale=1.08,                            # Scale: 108
        )
        browser.close()

    return True
