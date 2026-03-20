import os
import argparse

# =========================
# CONFIG
# =========================
FOLDER_ICON = "📁"
FILE_ICON = "📄"
ROOT_ICON = "📂"

IGNORE_FOLDERS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
IGNORE_FILES = {".DS_Store"}

# =========================
# GITIGNORE SUPPORT
# =========================
def load_gitignore(root_path):
    gitignore_path = os.path.join(root_path, ".gitignore")
    patterns = set()

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    return patterns

# =========================
# TREE GENERATOR
# =========================
def generate_tree(root_path, prefix="", depth=None, current_depth=0, gitignore=None):
    if gitignore is None:
        gitignore = set()

    if depth is not None and current_depth > depth:
        return []

    try:
        items = sorted(os.listdir(root_path))
    except PermissionError:
        return []

    filtered = []
    for item in items:
        if item in IGNORE_FILES:
            continue
        if item in gitignore:
            continue
        full_path = os.path.join(root_path, item)
        if os.path.isdir(full_path) and item in IGNORE_FOLDERS:
            continue
        filtered.append(item)

    tree_lines = []

    for i, item in enumerate(filtered):
        path = os.path.join(root_path, item)
        is_last = i == len(filtered) - 1

        connector = "└── " if is_last else "├── "

        if os.path.isdir(path):
            tree_lines.append(f"{prefix}{connector}{FOLDER_ICON} {item}/")
            extension = "    " if is_last else "│   "
            tree_lines.extend(
                generate_tree(
                    path,
                    prefix + extension,
                    depth,
                    current_depth + 1,
                    gitignore,
                )
            )
        else:
            try:
                size_kb = os.path.getsize(path) / 1024
                size_str = f" ({size_kb:.1f} KB)"
            except OSError:
                size_str = ""
            tree_lines.append(f"{prefix}{connector}{FILE_ICON} {item}{size_str}")

    return tree_lines

# =========================
# EXPORT TO README (CLEAN OVERWRITE WITH MARKERS)
# =========================
def export_to_readme(tree_lines, project_name):
    start_marker = "<!-- PROJECT_STRUCTURE_START -->"
    end_marker = "<!-- PROJECT_STRUCTURE_END -->"

    new_section = f"""{start_marker}
## 📂 Project Structure

```
{ROOT_ICON} Project Root: {project_name}/
"""
    new_section += "\n".join(tree_lines)
    new_section += f"\n```\n{end_marker}\n"

    readme_path = "README.md"

    # If README doesn't exist, create it
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_section)
        print("\n✅ README.md created with project structure")
        return

    # Read existing content
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace existing section if markers exist
    if start_marker in content and end_marker in content:
        before = content.split(start_marker)[0]
        after = content.split(end_marker)[1]
        updated_content = before + new_section + after
    else:
        # Append section if markers not found
        updated_content = content + "\n\n" + new_section

    # Write back
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("\n✅ Project structure section updated cleanly in README.md")

# =========================
# MAIN
# =========================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--depth", type=int, help="Limit folder depth")
    parser.add_argument("--export", action="store_true", help="Export to README.md")

    args = parser.parse_args()

    root = os.getcwd()
    project_name = os.path.basename(root)

    gitignore = load_gitignore(root)

    print(f"{ROOT_ICON} Project Root: {project_name}/")

    tree = generate_tree(root, depth=args.depth, gitignore=gitignore)

    for line in tree:
        print(line)

    if args.export:
        export_to_readme(tree, project_name)

# =========================
# TESTS
# =========================
def _run_tests():
    root = os.getcwd()
    tree = generate_tree(root)

    assert isinstance(tree, list)
    assert len(tree) > 0
    assert any(line.startswith("├──") or line.startswith("└──") for line in tree)

    print("All tests passed ✔")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    _run_tests()
    main()
