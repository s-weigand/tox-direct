import os
import sys

import pytest
from tox.config import parseconfig
from tox_direct.hookimpls import has_direct_envs

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path


class TestArgs:
    def test_normal(self, newconfig):
        newconfig("")
        print(os.getcwd())
        config = parseconfig([])
        assert not config.option.direct
        assert not config.option.direct_yolo

    def test_direct(self, newconfig):
        newconfig("")
        config = parseconfig(["--direct"])
        assert config.option.direct
        assert not config.option.direct_yolo

    def test_direct_yolo(self, newconfig):
        newconfig("")
        config = parseconfig(["--direct-yolo"])
        assert not config.option.direct
        assert config.option.direct_yolo


@pytest.mark.parametrize(
    "envlist, expectation",
    (
        ([], False),
        (["direct"], True),
        (["directwhatever"], True),
        (["whateverdirect"], True),
        (["whatdirectever"], True),
        (["direct", "another-direct"], True),
        (["normal", "another-normal"], False),
    ),
)
def test_has_direct_envs(envlist, expectation):
    if isinstance(expectation, bool):
        assert has_direct_envs(envlist) == expectation
    else:
        with pytest.raises(expectation):
            has_direct_envs(envlist)


def test_config(newconfig):
    config = newconfig(
        """
        [tox]
        skip_install = True
        [testenv:direct]
        skip_install = True
        deps = a
        """
    )
    direct = config.envconfigs["direct"]
    assert direct.deps == []
    assert direct.skip_install is True
    assert direct.basepython == sys.executable
    assert direct.envpython == sys.executable
    assert direct.get_envbindir() == str(Path(sys.executable).parent)


def test_does_not_interfer_with_normal_operation(cmd, initproj):
    initproj(
        "does_not_interfer_with_normal_operation",
        filedefs={
            "tox.ini": """
                    [testenv:normal]
                    deps = decorator
                    commands = 
                        pip list
                        python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd()
    assert r.ret == 0
    assert not r.session.config.option.direct
    assert not r.session.config.option.direct_yolo
    assert "We need direct action" not in r.out
    assert "won't build a package" not in r.out
    assert "won't install dependencies" not in r.out
    assert "won't install project" not in r.out
    assert "decorator" in r.out
    assert "congratulations :)" in r.out
    assert sys.executable not in r.out


def test_direct_vertical(cmd, initproj):
    initproj(
        "direct_vertical",
        filedefs={
            "tox.ini": """
                    [testenv:direct]
                    deps = dontcare
                    commands = python -c 'import sys; print(sys.executable);'
            """
        },
    )
    r = cmd("tox", "-vv")
    assert r.ret == 0
    assert not r.session.config.option.direct
    assert not r.session.config.option.direct_yolo
    assert "won't build a package" in r.out
    assert "won't install dependencies" in r.out
    assert "won't install project" in r.out
    assert "creating no virtual environment" in r.out
    assert "congratulations :)" in r.out
    assert sys.executable in r.out


def test_direct_yolo_normal_vertical(cmd, initproj):
    initproj(
        "yolo_normal_vertical",
        filedefs={
            "tox.ini": """
                    [testenv:normal]
                    deps = decorator
                    commands = 
                        pip list
                        python -c 'import sys; print(sys.executable);'
                        
            """
        },
    )
    r = cmd("tox", "-vv", "--direct-yolo")
    r.out = "\n".join(r.outlines)
    assert "YOLO!1!!" in r.out
    assert "decorator" in r.out
    assert sys.executable in r.out
    package = list((Path(".tox") / "dist").glob("*"))[0]
    assert "yolo_normal_vertical-0.1.zip" in package.name