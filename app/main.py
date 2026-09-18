"""Small SHA-1 loose-object Git implementation for the CodeCrafters exercise.

This is intentionally not a full Git client: the working directory is walked
without an index, and only loose objects in the current directory are read.
"""

import argparse
import hashlib
import os
from pathlib import Path
import re
import stat
import sys
import time
import zlib

GIT_DIR = Path(".git")
OBJECT_ID = re.compile(r"[0-9a-fA-F]{40}\Z")
INTERNAL_DATE = re.compile(r"@?([0-9]+) ([+-][0-9]{4})\Z")


def object_bytes(kind, data):
    return kind.encode("ascii") + b" " + str(len(data)).encode("ascii") + b"\0" + data


def object_id(kind, data):
    return hashlib.sha1(object_bytes(kind, data)).hexdigest()


def store_object(kind, data):
    if not (GIT_DIR / "HEAD").is_file() or not (GIT_DIR / "objects").is_dir():
        raise ValueError("run init in this directory before writing Git objects")
    raw = object_bytes(kind, data)
    sha = hashlib.sha1(raw).hexdigest()
    path = GIT_DIR / "objects" / sha[:2] / sha[2:]
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(zlib.compress(raw))
    except FileExistsError:
        pass
    return sha


def load_object(sha, expected_type=None):
    if not OBJECT_ID.fullmatch(sha):
        raise ValueError("expected a full 40-character SHA-1 object ID")
    sha = sha.lower()
    path = GIT_DIR / "objects" / sha[:2] / sha[2:]
    raw = zlib.decompress(path.read_bytes())
    if hashlib.sha1(raw).hexdigest() != sha:
        raise ValueError("object hash does not match its file name")
    header, separator, data = raw.partition(b"\0")
    kind, delimiter, length = header.partition(b" ")
    if not separator or not delimiter or not length.isdigit() or int(length) != len(data):
        raise ValueError("invalid loose-object header or size")
    if kind not in (b"blob", b"tree", b"commit", b"tag"):
        raise ValueError("unrecognized Git object type")
    kind_str = kind.decode("ascii")
    if expected_type is not None and kind_str != expected_type:
        raise ValueError(f"expected {expected_type} object, got {kind_str}")
    return kind_str, data


def tree_entries(data):
    """Parse the binary Git tree format without confusing SHA bytes and names."""
    cursor = 0
    while cursor < len(data):
        space = data.find(b" ", cursor)
        nul = data.find(b"\0", space + 1)
        if space <= cursor or nul <= space + 1 or nul + 21 > len(data):
            raise ValueError("malformed tree entry")
        mode = data[cursor:space]
        name = data[space + 1:nul]
        if not mode or not all(48 <= byte <= 55 for byte in mode):
            raise ValueError("invalid tree entry mode")
        if b"/" in name:
            raise ValueError("invalid tree entry name")
        oid = data[nul + 1:nul + 21].hex()
        yield mode, name, oid
        cursor = nul + 21


def write_tree(directory, root=True):
    entries = []
    for path in directory.iterdir():
        if path.name == ".git":
            continue
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            mode = b"40000"
            sha = write_tree(path, root=False)
            if sha is None:
                continue  # Git does not store empty directories.
        elif stat.S_ISLNK(info.st_mode):
            mode = b"120000"
            sha = store_object("blob", os.fsencode(os.readlink(path)))
        elif stat.S_ISREG(info.st_mode):
            mode = b"100755" if info.st_mode & 0o111 else b"100644"
            sha = store_object("blob", path.read_bytes())
        else:
            raise ValueError(f"unsupported file type: {path}")
        name = os.fsencode(path.name)
        entries.append((name + (b"/" if mode == b"40000" else b""), mode, name, sha))
    if not entries and not root:
        return None
    entries.sort(key=lambda item: item[0])
    data = b"".join(mode + b" " + name + b"\0" + bytes.fromhex(sha)
                    for _, mode, name, sha in entries)
    return store_object("tree", data)


def identity(prefix):
    name = os.getenv(f"GIT_{prefix}_NAME")
    email = os.getenv(f"GIT_{prefix}_EMAIL")
    if prefix == "COMMITTER":
        name = name or os.getenv("GIT_AUTHOR_NAME")
        email = email or os.getenv("GIT_AUTHOR_EMAIL")
    if not name or not email:
        raise ValueError(f"set GIT_{prefix}_NAME and GIT_{prefix}_EMAIL before commit-tree")
    if any(char in name + email for char in "\r\n<>"):
        raise ValueError("Git author/committer identity contains invalid characters")
    raw_date = os.getenv(f"GIT_{prefix}_DATE")
    if raw_date is None:
        date = f"{int(time.time())} +0000"
    else:
        match = INTERNAL_DATE.fullmatch(raw_date)
        if match is None or int(match.group(2)[1:3]) > 23 or int(match.group(2)[3:]) > 59:
            raise ValueError(f"GIT_{prefix}_DATE must be '<unix-seconds> +/-HHMM'")
        date = f"{match.group(1)} {match.group(2)}"
    return f"{name} <{email}> {date}".encode("utf-8")


def commit_tree(tree_sha, message, parents):
    load_object(tree_sha, "tree")
    for parent in parents:
        load_object(parent, "commit")
    lines = [b"tree " + tree_sha.lower().encode("ascii")]
    lines.extend(b"parent " + p.lower().encode("ascii") for p in parents)
    lines.extend([b"author " + identity("AUTHOR"), b"committer " + identity("COMMITTER")])
    content = b"\n".join(lines) + b"\n\n" + message.encode("utf-8").rstrip(b"\n") + b"\n"
    return store_object("commit", content)


def show_tree(data, names_only=False):
    output = sys.stdout.buffer
    for mode, name, sha in tree_entries(data):
        if names_only:
            output.write(name + b"\n")
        else:
            kind = b"tree" if mode == b"40000" else b"blob"
            output.write(mode.rjust(6, b"0") + b" " + kind + b" " + sha.encode("ascii") + b"\t" + name + b"\n")


def argument_parser():
    parser = argparse.ArgumentParser(description="Educational Git loose-object commands (SHA-1 only)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init", help="initialize .git in the current directory")
    cat = sub.add_parser("cat-file", help="pretty-print an object")
    cat.add_argument("-p", action="store_true", required=True)
    cat.add_argument("sha")
    hash_command = sub.add_parser("hash-object", help="hash a file as a blob")
    hash_command.add_argument("-w", action="store_true", help="store the object")
    hash_command.add_argument("path")
    sub.add_parser("write-tree", help="snapshot the current directory, not the Git index")
    ls = sub.add_parser("ls-tree", help="list a tree object")
    ls.add_argument("--name-only", action="store_true")
    ls.add_argument("sha")
    commit = sub.add_parser("commit-tree", help="create an object without updating HEAD")
    commit.add_argument("tree_sha")
    commit.add_argument("-p", dest="parents", action="append", default=[])
    commit.add_argument("-m", dest="message", required=True)
    return parser


def main(argv=None):
    parser = argument_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            (GIT_DIR / "objects").mkdir(parents=True, exist_ok=True)
            (GIT_DIR / "refs" / "heads").mkdir(parents=True, exist_ok=True)
            head = GIT_DIR / "HEAD"
            if not head.exists():
                head.write_text("ref: refs/heads/main\n", encoding="ascii")
            print("Initialized git directory")
        elif args.command == "hash-object":
            data = Path(args.path).read_bytes()
            print(store_object("blob", data) if args.w else object_id("blob", data))
        elif args.command == "cat-file":
            kind, data = load_object(args.sha)
            if kind == "tree":
                show_tree(data)
            else:
                sys.stdout.buffer.write(data)
        elif args.command == "write-tree":
            print(write_tree(Path.cwd()))
        elif args.command == "ls-tree":
            _, data = load_object(args.sha, "tree")
            show_tree(data, args.name_only)
        elif args.command == "commit-tree":
            print(commit_tree(args.tree_sha, args.message, args.parents))
    except (OSError, ValueError, zlib.error) as exc:
        print(f"git exercise: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
