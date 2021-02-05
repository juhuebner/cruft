import gc
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
from warnings import warn

import typer
from git import Repo

from . import utils
from .utils import example


def _pre_sweep(repo: Repo):
    """Invoke a DIY close() on the repo before repo.close().

    Possibly this helps. It's not clear if it's the cleansing done here, or simply a delay
    before the real call, which makes this work.

    Args:
        repo (Repo): git Repo instance.

    Returns:
        bool: success if true
    """
    repo.git.clear_cache()
    gc.collect()
    if not gc.garbage:
        return True

    warn("Could not collect {}".format(str(gc.garbage)), ResourceWarning)
    return False


@example()
def check(
    project_dir: Path = Path("."), checkout: Optional[str] = None, strict: bool = True
) -> bool:
    """Checks to see if there have been any updates to the Cookiecutter template
    used to generate this project."""
    cruft_file = utils.cruft.get_cruft_file(project_dir)
    cruft_state = json.loads(cruft_file.read_text())
    with TemporaryDirectory() as cookiecutter_template_dir:
        with utils.cookiecutter.get_cookiecutter_repo(
            cruft_state["template"], Path(cookiecutter_template_dir), checkout
        ) as repo:
            last_commit = repo.head.object.hexsha
            if utils.cruft.is_project_updated(repo, cruft_state["commit"], last_commit, strict):
                typer.secho(
                    "SUCCESS: Good work! Project's cruft is up to date and "
                    "as clean as possible :).",
                    fg=typer.colors.GREEN,
                )
                return True

            typer.secho(
                "FAILURE: Project's cruft is out of date! "
                "Run `cruft update` to clean this mess up.",
                fg=typer.colors.RED,
            )
            # DIY pre-close before closing the repo context.
            _pre_sweep(repo)
        # A TemporaryDirectory pre-cleanup()
        with os.scandir(cookiecutter_template_dir) as it:
            for entry in it:
                utils.generate._remove_single_path(Path(entry))  # pylint: disable=protected-access

        return False
