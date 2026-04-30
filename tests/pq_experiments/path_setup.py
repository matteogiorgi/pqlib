"""Import-path helpers for source-tree Python experiments."""

import pathlib
import sys


def add_repo_root_to_path() -> None:
    """Allow importing the in-place pqlib extension from tests."""

    repo_root = pathlib.Path(__file__).resolve().parents[2]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
