# A small Git loose-object implementation in Python

An educational implementation of selected Git plumbing commands, developed as a [CodeCrafters Build Your Own Git](https://codecrafters.io/challenges/git) exercise. The code builds and reads Git-compatible **SHA-1 loose objects** to make blob, tree, and commit storage understandable. It is not a Git replacement or a full version-control system.

The implementation lives in [`app/main.py`](app/main.py). The [`your_program.sh`](your_program.sh) launcher invokes that module; there is no `git.py` file. It uses only the Python standard library. The CodeCrafters runner configuration is in [`codecrafters.yml`](codecrafters.yml).

## Quickstart

Requires Python 3 and a Unix-like shell. Use an **empty, disposable working directory**: `init` creates `.git` where you run the command, not where the source code is stored. Substitute your actual checkout path for `REPO_DIR`.

```sh
REPO_DIR=/absolute/path/to/your/checkout/of/git
mkdir -p /tmp/git-exercise-demo
cd /tmp/git-exercise-demo
sh "$REPO_DIR/your_program.sh" init
printf 'hello Git\n' > hello.txt
sh "$REPO_DIR/your_program.sh" hash-object -w hello.txt
sh "$REPO_DIR/your_program.sh" write-tree
```

The last two commands print 40-character SHA-1 IDs. To inspect objects, copy the printed IDs into the commands below:

```sh
sh "$REPO_DIR/your_program.sh" cat-file -p <blob-sha>
sh "$REPO_DIR/your_program.sh" ls-tree --name-only <tree-sha>
```

Angle-bracket IDs above are placeholders, not literal shell arguments. To create a commit object, set your own identity and use the printed tree ID:

```sh
export GIT_AUTHOR_NAME='Your Name' GIT_AUTHOR_EMAIL='you@example.com'
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
sh "$REPO_DIR/your_program.sh" commit-tree <tree-sha> -m 'Initial snapshot'
```

`commit-tree` only writes an object: it does **not** advance `HEAD` or create a branch. Pass `-p <commit-sha>` to provide a parent. For reproducible hashes, you can set `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE` to Git's internal `<unix-seconds> +/-HHMM` format.

## Commands and implementation

| Command | What this implementation does |
| --- | --- |
| `init` | Creates `.git/objects`, `.git/refs/heads`, and a symbolic `HEAD` pointing to `main`; rerunning does not overwrite an existing `HEAD`. |
| `hash-object [-w] <path>` | Computes a blob SHA-1 from **raw bytes** and optionally writes the zlib-compressed loose object. |
| `cat-file -p <sha>` | Reads a loose blob, tree, or commit; checks its SHA-1 and declared size; writes blob bytes unchanged. |
| `write-tree` | Recursively snapshots the **working directory** (not Git's staging index), excluding `.git` and empty directories. |
| `ls-tree [--name-only] <tree-sha>` | Parses binary tree entries and lists names or modes, object types, IDs, and names. |
| `commit-tree <tree-sha> -m <message> [-p <parent-sha>]` | Creates a commit with explicit identity and optional parent object(s). |

Object records are encoded as `type + space + decimal byte length + NUL + raw content`, hashed with SHA-1, and stored in `.git/objects/aa/<remaining-38-hex-digits>` after zlib compression. Tree records contain an octal mode, raw filename bytes, NUL, and a 20-byte binary object ID. See [Git's loose-object format](https://git-scm.com/docs/gitformat-loose), [tree listing](https://git-scm.com/docs/git-ls-tree), and [commit-tree](https://git-scm.com/docs/git-commit-tree) for the reference behavior.

The implementation uses normal/executable modes and stores symlink targets as blobs on Unix-like systems. Files and directories are ordered using Git's directory-as-`name/` sort rule. Identity is supplied through `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, and optional committer counterparts; the project does not invent a developer's email in commit objects.

## Run the tests

From this repository's root, with Git installed:

```sh
python3 -m unittest discover -s tests -v
```

The tests run the shell launcher in temporary directories and compare generated blob, tree, and commit IDs and output with an independently installed Git executable. They also test corrupt objects, CLI errors, missing identity, empty directories, symlinks, binary data, and repeat writes. Tests were run locally with Python 3.13 and Git 2.47.3; CodeCrafters' private test suite was not run here.

## Scope and limitations

- Only a `.git` directory **in the current working directory** and SHA-1 **loose objects** are supported; there is no packed-object, SHA-256, tag creation, remote, index, checkout, diff, merge, or branch-management implementation.
- Unlike real [`git write-tree`](https://git-scm.com/docs/git-write-tree), this `write-tree` scans working-directory files directly. It includes otherwise untracked or ignored files and skips `.git` directories; do not run it on a sensitive or large working directory.
- Standard listing uses raw filename bytes rather than Git's exact quoting rules for unusual filenames. It is intended for typical local educational exercises, not untrusted repositories or arbitrary large objects.
- The demonstration writes objects but does not update references; use a disposable directory rather than an existing valuable repository.

This repository contains no standalone license file. No license grant is asserted by this README.
