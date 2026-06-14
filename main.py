from pathlib import Path


def build_tree_listing(base_folder: str):
    docs_dir = Path(f"docs/{base_folder}")

    tree = {}

    for file in sorted(docs_dir.rglob("*.md")):
        relative = file.relative_to(docs_dir)

        node = tree

        for folder in relative.parts[:-1]:
            node = node.setdefault(folder, {})

        node.setdefault("__files__", []).append(relative)

    def render(node, level=0):
        lines = []

        for folder in sorted(k for k in node if k != "__files__"):
            indent = "    " * level

            lines.append(
                f"{indent}- {folder.replace('-', ' ').replace('_', ' ').title()}"
            )

            lines.extend(render(node[folder], level + 1))

        for file in node.get("__files__", []):
            indent = "    " * level

            name = file.stem.replace("-", " ").replace("_", " ").title()
            link = f"{base_folder}/{file.as_posix()}"

            lines.append(f"{indent}- [{name}]({link})")

        return lines

    return "\n".join(render(tree))


def define_env(env):

    @env.macro
    def list_dictionary():
        return build_tree_listing("dictionary")

    @env.macro
    def list_entregables():
        return build_tree_listing("entregables")
