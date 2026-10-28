"""Check the live fixture contract without rebuilding Lean or modifying committed samples."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from homalg.index import index_repository
from homalg.sitedata import write_site_data


def main() -> int:
    """Generate into an isolated directory and compare JSON bytes except manifest.generator."""
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="homalg-fixture-") as temporary:
        shadow = Path(temporary) / "input"
        shadow.mkdir()
        subprocess.run(["git", "init", "-q", str(shadow)], check=True)
        for directory in ("schema", "taxonomy"):
            shutil.copytree(root / directory, shadow / directory)
        for directory in ("HomAlg", "literature"):
            for key in ("Fixture2000", "Fixture2001"):
                shutil.copytree(root / directory / key, shadow / directory / key)
        for filename in ("lake-manifest.json", "lean-toolchain"):
            shutil.copyfile(root / filename, shadow / filename)
        (shadow / "build").mkdir()
        shutil.copyfile(
            root / "tools/tests/golden/fixture-export.json", shadow / "build/lean-export.json"
        )
        index = index_repository(
            shadow,
            ("Fixture2000", "Fixture2001"),
            commit="fixture",
            repo_url="https://github.com/example/homalg-db",
        )
        out = Path(temporary) / "output"
        write_site_data(root, index, out)
        expected = root / "site/fixtures/data"
        actual_files = {path.relative_to(out) for path in out.rglob("*") if path.is_file()}
        expected_files = {
            path.relative_to(expected) for path in expected.rglob("*") if path.is_file()
        }
        failures = [str(path) for path in actual_files ^ expected_files]
        for path in sorted(actual_files & expected_files):
            before, after = (expected / path).read_bytes(), (out / path).read_bytes()
            if path.as_posix() == "manifest.json":
                left, right = json.loads(before), json.loads(after)
                left.pop("generator", None)
                right.pop("generator", None)
                same = left == right
            else:
                same = before == after
            if not same:
                failures.append(str(path))
        if failures:
            print("Fixture site data is stale; run make fixture-site:")
            print("\n".join(sorted(set(failures))))
            return 1
    print("Fixture site data is current.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
