import shutil
import stat
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from git import Remote, Repo

from pytest_bdd.util.packaging import get_distribution_version

messages_distribution_version = get_distribution_version("cucumber_messages")


def main():
    schema_path = Path(__file__).parent.parent / "model" / "message_jsonschema"
    if schema_path.exists():
        schema_path.chmod(schema_path.stat().st_mode | stat.S_IWRITE)
    shutil.rmtree(str(schema_path), ignore_errors=True)
    schema_path.mkdir(parents=True)
    folder_in_repo = Path("jsonschema", "src")
    tag_name = f"v{messages_distribution_version}"

    with TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "messages"
        repo_path.mkdir(parents=True)
        repo = Repo.init(repo_path)
        repo.git.config("core.sparseCheckout", "true")
        repo.create_remote("origin", "https://github.com/cucumber/messages.git")

        sparse_checkout_file = repo_path / ".git" / "info" / "sparse-checkout"
        with sparse_checkout_file.open("w", encoding="utf-8") as f:
            f.write(f"{folder_in_repo.as_posix()}/**\n")

        cast(Remote, repo.remotes.origin).fetch(f"refs/tags/{tag_name}:refs/tags/{tag_name}")
        repo.git.checkout(tag_name)
        shutil.copytree(str(repo_path / folder_in_repo), str(schema_path), dirs_exist_ok=True)


if __name__ == "__main__":
    main()
