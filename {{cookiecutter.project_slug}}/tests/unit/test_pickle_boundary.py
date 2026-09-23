"""The deployed agent must unpickle without the packages deploy.py does not ship.

deploy.py ships only `agent` and `prompts` to Agent Engine. cloudpickle stores
`root_agent` by value but its tool functions by reference, so the container imports
`agent/__init__.py` and `agent/tools/*`, never `agent/agent.py`. That is why
`agent/agent.py` may import `deployment.config` and nothing else under `agent/` may.

Breaking that rule still deploys green: the pickle builds and uploads fine, and the
`ModuleNotFoundError` only appears when the container serves its first request. These
tests reproduce the container's import closure locally, so it fails here instead.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

import cloudpickle
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Top-level packages in this repository that deploy.py does not put in extra_packages.
UNSHIPPED_PACKAGES = ("deployment", "tests")

# Run as `python -c SCRIPT <pickle file> <unshipped package>...`.
UNPICKLE_WITHOUT_UNSHIPPED = textwrap.dedent(
    """
    import sys

    import cloudpickle

    pickle_path, unshipped = sys.argv[1], set(sys.argv[2:])


    class BlockUnshipped:
        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in unshipped:
                raise ModuleNotFoundError(name + " is not shipped to Agent Engine")
            return None


    sys.meta_path.insert(0, BlockUnshipped())
    with open(pickle_path, "rb") as handle:
        cloudpickle.load(handle)
    """
)


def unpickle_in_container_closure(obj: object, tmp_path: Path) -> None:
    """Unpickle `obj` in a fresh interpreter that cannot import unshipped packages."""
    pickled = tmp_path / "agent.pkl"
    pickled.write_bytes(cloudpickle.dumps(obj))
    subprocess.run(
        [
            sys.executable,
            "-c",
            UNPICKLE_WITHOUT_UNSHIPPED,
            str(pickled),
            *UNSHIPPED_PACKAGES,
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def test_root_agent_unpickles_without_unshipped_packages(tmp_path):
    from agent.agent import root_agent

    try:
        unpickle_in_container_closure(root_agent, tmp_path)
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            "root_agent needs a package that is not shipped to Agent Engine. Keep "
            "`deployment` and `tests` imports out of agent/__init__.py and agent/tools/.\n"
            + exc.stderr
        )


def test_the_check_rejects_a_reference_into_deployment(tmp_path):
    """Negative control: without it, the test above could stop blocking anything and
    still pass."""
    from deployment.config import resolve_model

    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        unpickle_in_container_closure(resolve_model, tmp_path)

    assert "deployment is not shipped to Agent Engine" in excinfo.value.stderr
