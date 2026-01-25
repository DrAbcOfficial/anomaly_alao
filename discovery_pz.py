"""
This finds mod folders and their Lua scripts.

Handles the standard MO2 structure:
  <path>/gamedata/scripts/*.lua
  <path>/gamedata/scripts/*.script
"""

from pathlib import Path
from typing import Dict, List


def discover_mods(root_path: Path) -> Dict[str, List[Path]]:
    """
    Discover all mods and their script files.

    Returns dict mapping mod name -> list of script file paths
    """
    mods = {}
    root_path = Path(root_path)
    # scan for Project Zomboid mod structure: mod.info files
    # and look for media/lua folders
    for mod_info_path in root_path.rglob("mod.info"):
        # get the submod directory (parent of mod.info)
        submod_dir = mod_info_path.parent
        
        # check for media/lua directory
        lua_dir = submod_dir / "media" / "lua"
        if lua_dir.exists():
            scripts = find_scripts(lua_dir)
            if scripts:
                # generate mod name from path
                relative_path = submod_dir.relative_to(root_path)
                mod_name = str(relative_path)
                mods[mod_name] = scripts

    return mods


def find_scripts(scripts_dir: Path) -> List[Path]:
    """Find all Lua script files in a directory."""
    scripts = set()

    # .lua and .script are both used - glob root level first
    for ext in ("*.lua", "*.script"):
        scripts.update(scripts_dir.glob(ext))

    # also check subdirectories (some mods organize scripts in folders)
    for ext in ("**/*.lua", "**/*.script"):
        scripts.update(scripts_dir.glob(ext))

    return sorted(scripts)


def get_mod_info(mod_path: Path) -> dict:
    """
    Try to extract mod info from common metadata files.
    Returns dict with name, version, author if found.
    """
    info = {"name": mod_path.name}

    # check for mod.info (Project Zomboid)
    mod_info = mod_path / "mod.info"
    if mod_info.exists():
        try:
            content = mod_info.read_text(encoding='utf-8', errors='ignore')
            for line in content.splitlines():
                line = line.strip()
                if line.startswith("name="):
                    # handle quoted values
                    name_value = line.split("=", 1)[1].strip()
                    # remove quotes if present
                    if (name_value.startswith('\'') and name_value.endswith('\'')) or \
                       (name_value.startswith('"') and name_value.endswith('"')):
                        name_value = name_value[1:-1]
                    info["name"] = name_value
                elif line.startswith("id="):
                    info["id"] = line.split("=", 1)[1].strip()
                elif line.startswith("require="):
                    info["require"] = line.split("=", 1)[1].strip()
                elif line.startswith("modVersion="):
                    info["version"] = line.split("=", 1)[1].strip()
                elif line.startswith("description="):
                    desc_value = line.split("=", 1)[1].strip()
                elif line.startswith("author="):
                    info["author"] = line.split("=", 1)[1].strip()
                    # remove quotes if present
                    if (desc_value.startswith('\'') and desc_value.endswith('\'')) or \
                       (desc_value.startswith('"') and desc_value.endswith('"')):
                        desc_value = desc_value[1:-1]
                    info["description"] = desc_value
        except (OSError, IOError):
            pass

    # check for meta.ini (MO2 style)
    meta_ini = mod_path / "meta.ini"
    if meta_ini.exists():
        try:
            content = meta_ini.read_text(encoding='utf-8', errors='ignore')
            for line in content.splitlines():
                if line.startswith("name="):
                    info["name"] = line.split("=", 1)[1].strip()
                elif line.startswith("version="):
                    info["version"] = line.split("=", 1)[1].strip()
                elif line.startswith("author="):
                    info["author"] = line.split("=", 1)[1].strip()
        except (OSError, IOError):
            pass

    # check for modinfo.txt
    modinfo = mod_path / "modinfo.txt"
    if modinfo.exists():
        try:
            content = modinfo.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            if lines:
                info["name"] = lines[0].strip()
        except (OSError, IOError):
            pass

    return info


def discover_direct(path: Path) -> Dict[str, List[Path]]:
    """
    Discover scripts directly without gamedata/scripts structure.
    
    - If path is a .script/.lua file, return just that file
    - If path is a directory, find all scripts in it (recursively)
    
    Returns dict mapping mod name -> list of script file paths
    """
    path = Path(path)
    mods = {}
    
    # single file
    if path.is_file():
        if path.suffix in ('.script', '.lua'):
            mods["(direct)"] = [path]
        return mods
    
    # directory - find all scripts using set
    if path.is_dir():
        scripts = set()
        for ext in ("*.lua", "*.script"):
            scripts.update(path.glob(ext))
        for ext in ("**/*.lua", "**/*.script"):
            scripts.update(path.glob(ext))
        
        if scripts:
            mods["(direct)"] = sorted(scripts)
    
    return mods
