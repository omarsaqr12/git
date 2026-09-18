"""Black-box tests against installed Git, not the exercise's own helper functions."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "your_program.sh"


@unittest.skipUnless(shutil.which("git"), "Git is required for interoperability tests")
class GitExerciseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.cwd = Path(self.temp_dir.name)
        self.env = os.environ.copy()
        self.env.update({
            "GIT_AUTHOR_NAME": "Test Author", "GIT_AUTHOR_EMAIL": "author@example.test",
            "GIT_COMMITTER_NAME": "Test Committer", "GIT_COMMITTER_EMAIL": "committer@example.test",
            "GIT_AUTHOR_DATE": "@1700000000 +0000", "GIT_COMMITTER_DATE": "@1700000001 +0000",
            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        })

    def ours(self, *args, check=True, env=None):
        return subprocess.run(["sh", str(LAUNCHER), *args], cwd=self.cwd,
                              env=env or self.env, capture_output=True, check=check)

    def git(self, *args, check=True):
        return subprocess.run(["git", *args], cwd=self.cwd, env=self.env,
                              capture_output=True, check=check)

    def init(self):
        self.assertEqual(self.ours("init").stdout, b"Initialized git directory\n")

    def test_writing_requires_init(self):
        (self.cwd / "example.txt").write_text("hello")
        for command in (("hash-object", "-w", "example.txt"), ("write-tree",)):
            with self.subTest(command=command):
                result = self.ours(*command, check=False)
                self.assertEqual(result.returncode, 1)
                self.assertIn(b"run init", result.stderr)
        self.assertFalse((self.cwd / ".git").exists())

    def test_init_and_empty_tree_match_git(self):
        self.init()
        self.assertEqual((self.cwd / ".git" / "HEAD").read_text(), "ref: refs/heads/main\n")
        sha = self.ours("write-tree").stdout.strip()
        self.assertEqual(sha, b"4b825dc642cb6eb9a060e54bf8d69288fbee4904")
        self.assertEqual(self.git("cat-file", "-t", sha.decode()).stdout, b"tree\n")
        self.assertEqual(self.ours("init").returncode, 0)

    def test_binary_blob_sha_readback_and_repeat_write(self):
        self.init()
        data = b"\x00\xff\x80\r\n\x00binary\n"
        (self.cwd / "binary.dat").write_bytes(data)
        reference_sha = self.git("hash-object", "binary.dat").stdout.strip()
        self.assertEqual(self.ours("hash-object", "binary.dat").stdout.strip(), reference_sha)
        self.assertFalse((self.cwd / ".git" / "objects" / reference_sha[:2].decode() / reference_sha[2:].decode()).exists())
        self.assertEqual(self.ours("hash-object", "-w", "binary.dat").stdout.strip(), reference_sha)
        self.assertEqual(self.ours("hash-object", "-w", "binary.dat").stdout.strip(), reference_sha)
        self.assertEqual(self.git("cat-file", "blob", reference_sha.decode()).stdout, data)
        self.assertEqual(self.ours("cat-file", "-p", reference_sha.decode()).stdout, data)

    def test_tree_matches_git_index_for_modes_names_nested_and_symlinks(self):
        self.init()
        (self.cwd / "a9 data.txt").write_bytes(b"plain\n")
        (self.cwd / "nested").mkdir()
        (self.cwd / "nested" / "run.sh").write_bytes(b"#!/bin/sh\nexit 0\n")
        (self.cwd / "nested" / "run.sh").chmod(0o755)
        (self.cwd / "nested" / "digit7-file8").write_bytes(b"\xff\x00")
        (self.cwd / "nested" / "empty").mkdir()
        (self.cwd / "link").symlink_to("a9 data.txt")
        tree = self.ours("write-tree").stdout.strip().decode()
        self.git("add", "-A")
        expected = self.git("write-tree").stdout.strip().decode()
        self.assertEqual(tree, expected)
        self.assertEqual(self.ours("ls-tree", tree).stdout, self.git("ls-tree", tree).stdout)
        self.assertEqual(self.ours("ls-tree", "--name-only", tree).stdout,
                         self.git("ls-tree", "--name-only", tree).stdout)
        self.assertEqual(self.ours("cat-file", "-p", tree).stdout, self.git("cat-file", "-p", tree).stdout)

    def test_directory_sorting_git_rule(self):
        self.init()
        (self.cwd / "name.ext").write_text("file")
        (self.cwd / "name").mkdir()
        (self.cwd / "name" / "x").write_text("nested")
        tree = self.ours("write-tree").stdout.strip().decode()
        self.git("add", "-A")
        self.assertEqual(tree, self.git("write-tree").stdout.strip().decode())

    def test_commit_matches_git_and_parent_relationship(self):
        self.init()
        (self.cwd / "file.txt").write_text("test\n")
        tree = self.ours("write-tree").stdout.strip().decode()
        commit = self.ours("commit-tree", tree, "-m", "First commit").stdout.strip().decode()
        expected = self.git("commit-tree", tree, "-m", "First commit").stdout.strip().decode()
        self.assertEqual(commit, expected)
        self.assertEqual(self.git("cat-file", "-t", commit).stdout, b"commit\n")
        descendant = self.ours("commit-tree", tree, "-p", commit, "-m", "Second").stdout.strip().decode()
        expected_descendant = self.git("commit-tree", tree, "-p", commit, "-m", "Second").stdout.strip().decode()
        self.assertEqual(descendant, expected_descendant)
        self.assertIn(f"parent {commit}\n".encode(), self.ours("cat-file", "-p", descendant).stdout)

    def test_errors_are_controlled(self):
        self.init()
        for command in [("cat-file", "-p", "not-an-id"), ("cat-file", "-p", "a" * 40),
                        ("commit-tree", "a" * 40, "-m", "message"), ("no-command",),
                        ("ls-tree", "--name-only")]:
            with self.subTest(command=command):
                result = self.ours(*command, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr)
        self.assertNotIn(b"Traceback", result.stderr)

    def test_corrupt_object_is_rejected(self):
        self.init()
        sha = self.ours("hash-object", "-w", str(LAUNCHER)).stdout.strip().decode()
        obj = self.cwd / ".git" / "objects" / sha[:2] / sha[2:]
        obj.write_bytes(b"corrupt")
        result = self.ours("cat-file", "-p", sha, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"git exercise:", result.stderr)

    def test_identity_is_required_not_fake(self):
        self.init()
        tree = self.ours("write-tree").stdout.strip().decode()
        env = self.env.copy()
        env.pop("GIT_AUTHOR_NAME")
        result = self.ours("commit-tree", tree, "-m", "message", env=env, check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn(b"GIT_AUTHOR_NAME", result.stderr)


if __name__ == "__main__":
    unittest.main()
