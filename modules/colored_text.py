import colorama


class Color:
    """
    A class for colored text output in the terminal.
    """

    def __init__(self):
        colorama.init(autoreset=True)

    @staticmethod
    def red(text: str) -> str:
        return f"{colorama.Fore.RED}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def green(text: str) -> str:
        return f"{colorama.Fore.GREEN}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def yellow(text: str) -> str:
        return f"{colorama.Fore.YELLOW}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def blue(text: str) -> str:
        return f"{colorama.Fore.BLUE}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def magenta(text: str) -> str:
        return f"{colorama.Fore.MAGENTA}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def cyan(text: str) -> str:
        return f"{colorama.Fore.CYAN}{text}{colorama.Style.RESET_ALL}"
    
    @staticmethod
    def white(text: str) -> str:
        return f"{colorama.Fore.WHITE}{text}{colorama.Style.RESET_ALL}"


class CType:
    
    @staticmethod
    def error(text: str) -> str:
        return Color.red(text)

    @staticmethod
    def success(text: str) -> str:
        return Color.green(text)

    @staticmethod
    def warning(text: str) -> str:
        return Color.yellow(text)

    @staticmethod
    def info(text: str) -> str:
        return Color.blue(text)

    @staticmethod
    def bullet(text: str) -> str:
        return Color.cyan(text)

    @staticmethod
    def header(text: str) -> str:
        return Color.magenta(text)
    

def bullet() -> str:
    return CType.bullet("•")


def print_colored(text: str, color: str) -> None:
    """
    Print text in the specified color.
    
    Args:
        text (str): The text to print.
        color (str): The color name (e.g., 'red', 'green', 'blue').
    """
    color_obj = Color()
    color_method = getattr(color_obj, color.lower(), None)
    
    if callable(color_method):
        print(color_method(text))
    else:
        print(text)  # Default to no color if the method doesn't exist


def print_typed(text: str, ctype: str) -> None:
    """
    Print text with a specific type (e.g., error, success, warning, info).
    
    Args:
        text (str): The text to print.
        ctype (str): The type of message (e.g., 'error', 'success', 'warning', 'info').
    """
    ctype_method = getattr(CType, ctype.lower(), None)
    
    if callable(ctype_method):
        print(ctype_method(text))
    else:
        print(text)  # Default to no color if the method doesn't exist


def print_error(text: str):
    """
    Print an error message in red.
    
    Args:
        text (str): The error message to print.
    """
    print_typed(text, 'error')


def print_success(text: str):
    """
    Print a success message in green.
    
    Args:
        text (str): The success message to print.
    """
    print_typed(text, 'success')


def print_warning(text: str):
    """
    Print a warning message in yellow.
    
    Args:
        text (str): The warning message to print.
    """
    print_typed(text, 'warning')


def print_info(text: str):
    """
    Print an informational message in blue.
    
    Args:
        text (str): The informational message to print.
    """
    print_typed(text, 'info')
