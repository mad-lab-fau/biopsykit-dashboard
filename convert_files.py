import ast
import os
import sys
from _ast import ImportFrom
from typing import List

from tqdm import tqdm
from setuptools import glob

POSSIBLE_PIPELINES = ["physiological", "sleep", "questionnaire", "saliva"]
OWN_NAME = "combine_all_files.py"
RESULTING_FILENAME = "index"
RESULTING_SINGLE_PIPELINE_FILENAME = "single_dashboard"
MAIN_FILE = "main.py"
IGNORE_FOLDERS = ["build", "dist", "pyodide", "pyscript", "Miscellaneous"]
files_added = []


changed_imports = (
    "  const env_spec = ['https://cdn.holoviz.org/panel/1.2.3/dist/wheels/bokeh-3.2.2-py3-none-any.whl', "
    "'https://cdn.holoviz.org/panel/1.2.3/dist/wheels/panel-1.2.3-py3-none-any.whl', "
    "'pyodide-http==0.2.1', "
    "'https://raw.githubusercontent.com/shMeske/WheelFiles/master/docopt-0.6.2-py2.py3-none-any.whl', "
    "'https://raw.githubusercontent.com/shMeske/WheelFiles/master/littleutils-0.2.2-py3-none-any.whl', "
    # "'https://files.pythonhosted.org/packages/63/ea/ace1b9df189c149e7c1272c0159c17117096d889b0ccf2130358d52ee881/fau_colors-1.1.0-py3-none-any.whl',"
    "'fau_colors==1.5.3',"
    "'https://raw.githubusercontent.com/shMeske/WheelFiles/master/pingouin-0.5.4-py3-none-any.whl', "
    "'biopsykit',"
    "'seaborn', "
    "'matplotlib', 'nilspodlib', 'numpy', 'packaging', "
    "'pandas', 'param', 'plotly', 'pytz',  'typing_extensions','holoviews', 'mne']\n"
)

# == 0.11.2


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
    out_file_text = (
        'import os \nos.environ["OUTDATED_IGNORE"] = "1"\npn.extension(notifications=True)\n'
        + out_file_text
    )
    with open(MAIN_FILE, "r") as file:
        main_file_text = file.read()
        out_file_text += "\n\n"
        out_file_text += main_file_text
    out_file_text = replace_all_imports(out_file_text, files_dict)
    with open(RESULTING_FILENAME + ".py", "w") as outfile:
        outfile.write(out_file_text)
    print("Everything combined")


def change_imports(combined_file: str):
    print("Changing imports of pyodide File")
    with open(f"{RESULTING_FILENAME}/{combined_file}.js", "r") as file:
        text = file.read()
        text = substring_replace(text)
    with open(f"{RESULTING_FILENAME}/{combined_file}.js", "w") as file:
        file.write(text)


def substring_replace(string_file: str) -> str:
    result = []
    for line in string_file.splitlines():
        if line.startswith("  const env_spec = ["):
            line = changed_imports
        result.append(line)
    return "\n".join(result)


def build_single_pipeline_app(pipeline_type: str):
    files_dict = read_python_files()
    pipeline_type = pipeline_type.lower() + "_pipeline"
    pipeline_class_names = [
        name for name in files_dict.keys() if pipeline_type in name.lower()
    ]

    if len(pipeline_class_names) != 1:
        print("Wrong pipeline")
        exit(1)

    with open("single_pipeline.py", "r") as file:
        main_file_text = file.read()

    pipeline_file_key = pipeline_class_names[0]
    pipeline_class_names = get_pipeline_class_names(files_dict[pipeline_file_key])

    if len(pipeline_class_names) != 1:
        print("Wrong pipeline")
        exit(1)

    pipeline_class_name = pipeline_class_names[0]
    result = []
    splitted_text = main_file_text.splitlines()

    pipeline_index = find_pipeline_index(splitted_text)

    if pipeline_index == -1:
        print(
            "Could not find the right place to insert the pipeline at the file: single_pipeline.py"
        )
        exit(1)

    for line in splitted_text:
        if line.startswith("pipeline = None"):
            line = (
                f"{files_dict[pipeline_file_key]}\n\npipeline = {pipeline_class_name}()"
            )
        result.append(line)

    result_text = "\n".join(result)
    out_file_text = replace_all_imports(result_text, files_dict)

    output_filename = pipeline_type + ".py"
    with open(output_filename, "w") as outfile:
        outfile.write(out_file_text)

    print("Everything combined")


def get_pipeline_class_names(file_contents: str) -> List[str]:
    return [
        name
        for name in get_class_names_from_file(file_contents)
        if "pipeline" in name.lower()
    ]


def find_pipeline_index(lines: List[str]) -> int:
    try:
        return lines.index("pipeline = None")
    except ValueError:
        return -1


def get_class_names_from_file(file_text: str) -> list:
    node = ast.parse(file_text)
    classes = [n.name for n in node.body if isinstance(n, ast.ClassDef)]
    return classes


def set_pipeline(pipeline_type: str, files_dict: dict):
    print("Setting pipeline")
    out_file_text = files_dict[pipeline_type]
    out_file_text = 'import os \nos.environ["OUTDATED_IGNORE"] = "1"\n' + out_file_text
    with open(RESULTING_SINGLE_PIPELINE_FILENAME + ".py", "w") as outfile:
        outfile.write(out_file_text)
    print("Pipeline set")


def remove_redundant_imports(pipeline_type: str):
    if pipeline_type != RESULTING_FILENAME:
        pipeline_type = f"{pipeline_type.lower()}_pipeline.py"
    else:
        pipeline_type = f"{pipeline_type}.py"
    if not os.path.exists(pipeline_type):
        print("Pipeline does not exist")
        exit(1)

    with open(pipeline_type, "r") as file:
        pipeline_code = file.read()

    nodes = ast.parse(pipeline_code)
    imports = [
        f"import {i.name}\n" if i.asname is None else f"import {i.name} as {i.asname}\n"
        for n in nodes.body
        if isinstance(n, ast.Import)
        for i in n.names
    ]
    imports = list(dict.fromkeys(imports))
    existing_imports = []
    with open(pipeline_type, "r") as input_file:
        for line in input_file:
            if "from main import app" in line:
                continue
            if "from" in line or "import" not in line:
                line = line.replace("pn.state.notifications", "app.notifications")
                existing_imports.append(line)

    with open(pipeline_type, "w") as output:
        output.writelines(imports + existing_imports)


def convert_to_pyodide(selected_pipeline: str):
    combined_file = selected_pipeline
    if selected_pipeline != RESULTING_FILENAME:
        combined_file += "_pipeline"
    print("Converting to pyodide")
    exit_code = os.system(
        f"panel convert {combined_file}.py --to pyodide-worker --out {RESULTING_FILENAME} --pwa"
    )
    if exit_code != 0:
        print("Error while converting to pyodide")
        exit(1)
    change_imports(combined_file)


def get_pipeline_name(pipeline_input: str) -> str:
    pipeline_input = pipeline_input.lower()
    if pipeline_input in POSSIBLE_PIPELINES:
        return pipeline
    l = [p for p in POSSIBLE_PIPELINES if p.startswith(pipeline_input)]
    if len(l) != 1:
        print("Wrong pipeline")
        exit(1)
    return l[0]


def build_one_pipeline(pipeline_input: str):
    build_single_pipeline_app(pipeline_input)
    remove_redundant_imports(pipeline_input)
    convert_to_pyodide(pipeline_input)


def build_all_pipelines():
    for single_pipeline in POSSIBLE_PIPELINES:
        files_added.clear()
        print(f"Building: {single_pipeline}\n")
        build_one_pipeline(single_pipeline)


def build_all_pipelines_into_one():
    combine_all_files()
    remove_redundant_imports(RESULTING_FILENAME)
    convert_to_pyodide(RESULTING_FILENAME)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build-all":
        build_all_pipelines_into_one()
        exit(0)
    print("Starting")
    combine_all_files_input = input(
        "Do you want to combine all pipelines into one large file? (y/n)\n"
    )
    if combine_all_files_input == "y":
        build_all_pipelines_into_one()
    else:
        build_every_pipeline_input = input(
            "Do you want to build every pipeline (each into one extra file)? (y/n)\n"
        )
        if build_every_pipeline_input == "y":
            build_all_pipelines()
        else:
            pipeline = input(
                "Which pipeline do you want to build? (physiological, sleep, questionnaire, saliva)\n"
            )
            pipeline = get_pipeline_name(pipeline)
            print(f"{pipeline} selected\n")
            build_one_pipeline(pipeline)
    print("Finished")
