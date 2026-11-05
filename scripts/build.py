"""Build Elmo addon ZIPs from repository sources using Python's standard library."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
INTERFACES = {"classic": 11509, "forever": 16001}
# Optional data loaders support existing installations; they are not bundled.
LEGACY_DEPENDENCIES = {
    "ElmoLeveling": {
        "classic": ["ClassicLeveling", "ClassicXPTracker"],
        "forever": ["ClassicLevelingForever", "ForeverLeveling"],
    },
    "ElmoPlater": {"classic": ["ClassicPlater", "ClassicTarget"]},
    "ElmoSpellTracker": {"classic": ["ClassicSpellsTracker", "ClassicCooldownTracker"]},
}


def build(source, client):
    name = source.name
    stage = ROOT / ".build" / client / name
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(source, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    toc = stage / (name + ".toc")
    text = toc.read_text()
    version = re.search(r"^## Version:\s*(\S+)", text, re.MULTILINE).group(1)
    text = re.sub(r"^## Interface:.*$", f"## Interface: {INTERFACES[client]}", text, flags=re.MULTILINE)
    dependencies = []
    for line in re.findall(r"^## OptionalDeps:\s*(.*)$", text, re.MULTILINE):
        dependencies.extend(value.strip() for value in line.split(",") if value.strip())
    dependencies.extend(LEGACY_DEPENDENCIES.get(name, {}).get(client, []))
    text = re.sub(r"^## OptionalDeps:.*\n", "", text, flags=re.MULTILINE)
    if dependencies:
        text = "## OptionalDeps: " + ", ".join(dict.fromkeys(dependencies)) + "\n" + text
    toc.write_text(text)
    if name == "ElmoDungeonLoot" and client == "forever":
        for filename in ("Catalog.lua", "QuestCatalog.lua"):
            shutil.copyfile(source / (filename[:-4] + "Forever.lua"), stage / filename)
    if name == "ElmoDungeonLoot":
        # The package contains only its client's factual catalogues.
        for filename in ("CatalogForever.lua", "QuestCatalogForever.lua"):
            (stage / filename).unlink()
    if name == "ElmoLeveling":
        (stage / "Client.lua").write_text(f'local _, A = ...\nA.flavor = "{client}"\n')
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):
            if not (stage / line.replace("\\", "/")).is_file():
                raise FileNotFoundError(f"{name}: missing TOC resource {line}")
    archive = ROOT / "dist" / f"{name}-{version}-{client}.zip"
    archive.parent.mkdir(exist_ok=True)
    roots = [stage]
    if name == "ElmoLFG":
        # Replacing the old manifests with data-only loaders preserves saved
        # settings without starting the old recruitment UI alongside ElmoLFG.
        for legacy in ("ClassicQuestLFG", "QuestLFG"):
            loader = stage.parent / legacy
            if loader.exists():
                shutil.rmtree(loader)
            shutil.copytree(ROOT / "compat" / legacy, loader)
            manifest = loader / (legacy + ".toc")
            manifest.write_text(re.sub(r"^## Interface:.*$", f"## Interface: {INTERFACES[client]}",
                manifest.read_text(), flags=re.MULTILINE))
            roots.append(loader)
    files = sorted(file for folder in roots for file in folder.rglob("*") if file.is_file())
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as package:
        for file in files:
            package.write(file, file.relative_to(stage.parent).as_posix())
    with zipfile.ZipFile(archive) as package:
        for file in files:
            if package.read(file.relative_to(stage.parent).as_posix()) != file.read_bytes():
                raise RuntimeError(f"Archive verification failed: {file}")
    print(f"{name} {version} {client}")
    return {
        "addon": name, "version": version, "client": client,
        "archive": archive.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    }


def main():
    reports = []
    for source in sorted(ROOT.glob("Elmo*")):
        if not source.is_dir() or not (source / (source.name + ".toc")).is_file():
            continue
        clients = ["classic", "forever"]
        reports.extend(build(source, client) for client in clients)
    (ROOT / ".build-report.json").write_text(json.dumps({"packages": reports}, indent=2) + "\n")


if __name__ == "__main__":
    main()
