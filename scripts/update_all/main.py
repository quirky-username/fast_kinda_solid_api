#!/usr/bin/env python

import argparse
import ast
import glob


def extract_public_members(module_path):
    with open(module_path, "r") as file:
        tree = ast.parse(file.read(), filename=module_path)

    public_members = sorted(
        node.name
        for node in tree.body
        if isinstance(node, (ast.ClassDef, ast.FunctionDef))
        or (
            isinstance(node, ast.Assign)
            and all(isinstance(target, ast.Name) and target.id.isupper() for target in node.targets)
        )
    )
    return public_members


def update_all(module_path):
    public_members = extract_public_members(module_path)

    if not public_members:
        return

    all_def = "__all__ = [\n"
    for member in sorted(public_members):
        all_def += f'    "{member}",\n'

    all_def = "\n\n" + all_def + "]\n"

    with open(module_path, "r") as file:
        lines = file.readlines()

    with open(module_path, "w") as file:
        found_all = False
        for line in lines:
            if line.startswith("__all__"):
                file.write(all_def)
                found_all = True
            else:
                file.write(line)

        if not found_all:
            file.write(all_def)


def update_all_with_glob(pattern):
    for module_path in glob.glob(pattern, recursive=True):
        update_all(module_path)


def main():
    parser = argparse.ArgumentParser(description="Update __all__ in Python modules.")
    parser.add_argument("pattern", type=str, help="Glob pattern to match Python files")
    args = parser.parse_args()

    update_all_with_glob(args.pattern)


if __name__ == "__main__":
    main()


__all__ = [
    "extract_public_members",
    "main",
    "update_all",
    "update_all_with_glob",
]
