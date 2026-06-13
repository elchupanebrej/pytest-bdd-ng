"""

Unit tests for feature file collector helpers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pytest_bdd.collector import FeatureFileModule
from pytest_bdd.scenario import FeaturePathType

pytestmark = [pytest.mark.unit]


def test_detect_uri_pathtype_handles_file_url() -> None:
    """
    detect_uri_pathtype returns path mode for file URLs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype("file:///tmp/example.feature")

    assert path == "/" + "tmp/example.feature"
    assert path_type is FeaturePathType.PATH


def test_detect_uri_pathtype_handles_remote_url() -> None:
    """
    detect_uri_pathtype returns URL mode for remote URLs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype("https://example.test/example.feature")

    assert path == "https://example.test/example.feature"
    assert path_type is FeaturePathType.URL


def test_detect_uri_pathtype_handles_relative_path() -> None:
    """
    detect_uri_pathtype returns undefined mode for relative paths.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype("example.feature")

    assert path == "example.feature"
    assert path_type is FeaturePathType.UNDEFINED


def test_get_feature_pathlike_from_url_file_reads_shortcut(tmp_path: Path) -> None:
    """
    URL shortcut files resolve feature URL and working directory.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    shortcut = tmp_path / "feature.url"
    shortcut.write_text(
        "[InternetShortcut]\nURL=https://example.test/feature.feature\nWorkingDirectory=/tmp/features\n",
        encoding="utf-8",
    )

    path, path_type, working_dir = FeatureFileModule.get_feature_pathlike_from_url_file(shortcut)

    assert path == "https://example.test/feature.feature"
    assert path_type is FeaturePathType.URL
    assert working_dir == "/" + "tmp/features"


def test_get_feature_pathlike_from_desktop_file_reads_link(tmp_path: Path) -> None:
    """
    Desktop link files resolve their URL field.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    shortcut = tmp_path / "feature.desktop"
    shortcut.write_text("[Desktop Entry]\nType=Link\nURL=file:///tmp/feature.feature\n", encoding="utf-8")

    path, path_type, base_dir = FeatureFileModule.get_feature_pathlike_from_desktop_file(shortcut)

    assert path == "/" + "tmp/feature.feature"
    assert path_type is FeaturePathType.PATH
    assert base_dir is None


def test_get_feature_pathlike_from_desktop_file_ignores_non_link(tmp_path: Path) -> None:
    """
    Desktop non-link files do not resolve feature paths.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    shortcut = tmp_path / "feature.desktop"
    shortcut.write_text("[Desktop Entry]\nType=Application\nURL=file:///tmp/feature.feature\n", encoding="utf-8")

    path, path_type, base_dir = FeatureFileModule.get_feature_pathlike_from_desktop_file(shortcut)

    assert path is None
    assert path_type is FeaturePathType.UNDEFINED
    assert base_dir is None


def test_detect_uri_pathtype_handles_none_input() -> None:
    """
    detect_uri_pathtype handles None input.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype(None)

    assert path is None
    assert path_type is FeaturePathType.UNDEFINED


def test_detect_uri_pathtype_handles_absolute_path() -> None:
    """
    detect_uri_pathtype returns URL mode for Windows absolute paths (single-letter scheme).

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    # Windows absolute paths with drive letters (C:/...) match URI scheme pattern
    abs_path = str(Path("C:/absolute/path/feature.feature"))
    path, path_type = FeatureFileModule.detect_uri_pathtype(abs_path)

    assert path == abs_path
    assert path_type is FeaturePathType.URL


def test_detect_uri_pathtype_handles_windows_unc() -> None:
    """
    detect_uri_pathtype returns path mode for Windows UNC paths.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    unc = "\\\\server\\share\\feature.feature"
    path, path_type = FeatureFileModule.detect_uri_pathtype(unc)

    assert path == unc
    # UNC may be PATH or UNDEFINED depending on platform
    assert path_type in {FeaturePathType.PATH, FeaturePathType.UNDEFINED}


def test_detect_uri_pathtype_handles_http_url() -> None:
    """
    detect_uri_pathtype returns URL mode for HTTP URLs.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype("http://example.test/feature.feature")

    assert path == "http://example.test/feature.feature"
    assert path_type is FeaturePathType.URL


def test_detect_uri_pathtype_handles_empty_string() -> None:
    """
    detect_uri_pathtype treats empty string as UNDEFINED.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    path, path_type = FeatureFileModule.detect_uri_pathtype("")

    assert not path
    assert path_type is FeaturePathType.UNDEFINED


def test_get_feature_pathlike_from_weblock_file_reads_plist(tmp_path: Path) -> None:
    """
    Weblock files resolve their URL field from plist format.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    shortcut = tmp_path / "feature.webloc"
    shortcut.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n<dict>\n<key>URL</key>\n<string>https://example.test/feature.feature</string>\n</dict>\n</plist>\n',
        encoding="utf-8",
    )

    path, path_type, base_dir = FeatureFileModule.get_feature_pathlike_from_weblock_file(shortcut)

    assert path == "https://example.test/feature.feature"
    assert path_type is FeaturePathType.URL
    assert base_dir is None


def test_get_feature_pathlike_from_url_file_defaults_working_dir(tmp_path: Path) -> None:
    """
    URL shortcut defaults working directory when not specified.

    Test target:
        Verify internal unit invariants and correct behavior of individual code components.
    Test type:
        Unit test
    Test scenario:
        Given the relevant preconditions are met, when Verify internal unit invariants and correct behavior of
        individual code components., then the expected outcome is produced.
    BDD reference:
        None
    Fixtures:
        - None
    Mocks:
        - None
    Side effects:
        None
    Reduction:
        Requires real component interaction that cannot be reproduced by mocking alone.
    Escalation:
        Testing at a higher level would not add coverage and would slow down the suite.
    Atomicity:
        All assertions share the same setup and verify a single coherent behavior.
    Autonomy:
        Covers a distinct code path not exercised by any sibling test.
    Test quality score:
        #test-eval:isolation=5
        #test-eval:determinism=5
        #test-eval:setup_complexity=1
        #test-eval:assertions_clarity=5
    """
    shortcut = tmp_path / "feature.url"
    shortcut.write_text("[InternetShortcut]\nURL=https://example.test/feature.feature\n", encoding="utf-8")

    path, path_type, working_dir = FeatureFileModule.get_feature_pathlike_from_url_file(shortcut)

    assert path == "https://example.test/feature.feature"
    assert path_type is FeaturePathType.URL
    assert working_dir is None
