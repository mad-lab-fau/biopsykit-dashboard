import ast
import os
from _ast import ImportFrom
from tqdm import tqdm
from setuptools import glob

OWN_NAME = "combine_all_files.py"
RESULTING_FILENAME = "dashboard.py"
MAIN_FILE = "main.py"
IGNORE_FOLDERS = [
    "build",
    "dist",
    "pyodide",
    "pyscript",
]
class_file_dict = {}
function_file_dict = {}
files_added = []
functions_dict = {}
changed_imports = (
    "  const env_spec = ['https://cdn.holoviz.org/panel/1.2.3/dist/wheels/bokeh-3.2.2-py3-none-any.whl', "
    "'https://cdn.holoviz.org/panel/1.2.3/dist/wheels/panel-1.2.3-py3-none-any.whl', "
    "'pyodide-http==0.2.1', "
    "'https://raw.githubusercontent.com/shMeske/WheelFiles/master/docopt-0.6.2-py2.py3-none-any.whl', "
    "'https://raw.githubusercontent.com/shMeske/WheelFiles/master/littleutils-0.2.2-py3-none-any.whl', "
    "'https://files.pythonhosted.org/packages/63/ea/ace1b9df189c149e7c1272c0159c17117096d889b0ccf2130358d52ee881/fau_colors-1.1.0-py3-none-any.whl',"
    "'seaborn == 0.11.2', 'biopsykit', 'matplotlib', 'nilspodlib', 'numpy', 'packaging', "
    "'pandas', 'param', 'plotly', 'pytz',  'typing_extensions']\n"
)


def is_ignored(filename) -> bool:
    return (
        filename == OWN_NAME
        or filename == MAIN_FILE
        or "__init__" in filename
        or any(ignore in filename for ignore in IGNORE_FOLDERS)
    )


def read_python_files() -> dict:
    files_dict = {}
    for filename in glob.iglob("src/**/*.py", recursive=True):
        if is_ignored(filename):
            continue
        package_name = filename.replace("/", ".")
        package_name = package_name.replace(".py", "")
        with open(filename) as file:
            files_dict[package_name] = file.read()
    return files_dict


def get_combined_files_string(python_file_dict: dict) -> str:
    out_file_text = ""
    for key, value in tqdm(python_file_dict.items()):
        if key in files_added:
            continue
        if len(out_file_text) == 0:
            out_file_text += value
            out_file_text += "\n\n"
        else:
            out_file_text += "\n\n"
            out_file_text += value
        out_file_text = replace_all_imports(out_file_text, python_file_dict)
    return out_file_text


def replace_all_imports(out_file_text: str, python_file_dict: dict) -> str:
    node = ast.parse(out_file_text)
    imports = [
        n
        for n in node.body
        if isinstance(n, ast.ImportFrom) and n.module.startswith("src")
    ]
    while len(imports) > 0:
        out_file_text = add_subpart(imports[0], out_file_text, python_file_dict)
        node = ast.parse(out_file_text)
        imports = [
            n
            for n in node.body
            if isinstance(n, ast.ImportFrom) and n.module.startswith("src")
        ]
    return out_file_text


def add_subpart(
    import_from: ImportFrom, out_file_text: str, python_file_dict: dict
) -> str:
    text_to_add = []
    if import_from.module not in files_added:
        text_to_add = python_file_dict[import_from.module].splitlines(keepends=True)
    out_file_text_array = out_file_text.splitlines(keepends=True)
    out_file_text_array = (
        out_file_text_array[: import_from.lineno - 1]
        + text_to_add
        + out_file_text_array[import_from.end_lineno :]
    )
    out_file_text = "".join(out_file_text_array)
    files_added.append(import_from.module)
    return out_file_text


def combine_all_files():
    print("Reading python files")
    files_dict = read_python_files()
    print("Combining files:")
    out_file_text = get_combined_files_string(files_dict)
    out_file_text = 'import os \nos.environ["OUTDATED_IGNORE"] = "1"\n' + out_file_text
    with open(MAIN_FILE, "r") as file:
        main_file_text = file.read()
        out_file_text += "\n\n"
        out_file_text += main_file_text
    out_file_text = replace_all_imports(out_file_text, files_dict)
    with open(RESULTING_FILENAME, "w") as outfile:
        outfile.write(out_file_text)
    print("Everything combined")


def change_imports():
    print("Changing imports of pyodide File")
    with open("pyodide/dashboard.js", "r") as file:
        text = file.read()
        text = substring_replace(text)
    with open("pyodide/dashboard.js", "w") as file:
        file.write(text)
    print("Imports changed")


def substring_replace(string_file: str) -> str:
    result = []
    for line in string_file.splitlines():
        if line.startswith("  const env_spec = ["):
            line = changed_imports
        result.append(line)
    return "\n".join(result)


if __name__ == "__main__":
    combine_all_files()
    exit_code = os.system(
        "panel convert dashboard.py --to pyodide-worker --out pyodide"
    )
    if exit_code != 0:
        print("Error while converting to pyodide")
        exit(1)
    change_imports()
    print("Done")
