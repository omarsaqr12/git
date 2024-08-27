# Simple Git Implementation in Python

This project is a simplified implementation of some core Git functionalities using Python. It demonstrates how Git manages objects like blobs, trees, and commits under the hood by manually handling hashing, compression, and file storage.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
  - [Initialize Repository](#initialize-repository)
  - [Hash Object](#hash-object)
  - [Cat File](#cat-file)
  - [Write Tree](#write-tree)
  - [Commit Tree](#commit-tree)
  - [List Tree](#list-tree)
- [Author](#author)
- [License](#license)

## Features

- **Initialize Repository**: Create a new Git repository by setting up the necessary `.git` directory structure.
- **Hash Object**: Create a blob object from a file and store it in the `.git/objects` directory.
- **Cat File**: Retrieve and display the content of a Git object (blob, tree, commit) by its SHA-1 hash.
- **Write Tree**: Generate a tree object representing the current directory structure and store it in the `.git/objects` directory.
- **Commit Tree**: Create a commit object that references a tree object and optionally a parent commit.
- **List Tree**: Display the contents of a tree object in a human-readable format.

## Prerequisites

- Python 3.x installed on your system.
- Basic understanding of Git and its internal workings.
- Operating system with support for Python file operations (tested on Unix-like systems).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/simple-git-python.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd simple-git-python
   ```

3. **Ensure Dependencies are Met**

   This script uses standard Python libraries, so no additional packages are required.

## Usage

Run the script using the Python interpreter followed by the desired command and its arguments.

```bash
python git.py <command> [arguments]
```

### Initialize Repository

Sets up a new Git repository in the current directory by creating the necessary `.git` folders and files.

**Command**

```bash
python git.py init
```

**Output**

```
Initialized git directory
```

### Hash Object

Creates a blob object from a specified file and stores it in the `.git/objects` directory.

**Command**

```bash
python git.py hash-object -w <file_path>
```

**Parameters**

- `-w`: Write the object to the object database.
- `<file_path>`: Path to the file to be hashed.

**Example**

```bash
python git.py hash-object -w example.txt
```

**Output**

```
<sha1_hash_of_the_blob>
```

### Cat File

Displays the content of a Git object identified by its SHA-1 hash.

**Command**

```bash
python git.py cat-file -p <object_sha>
```

**Parameters**

- `-p`: Pretty-print the contents of the object.
- `<object_sha>`: SHA-1 hash of the object to display.

**Example**

```bash
python git.py cat-file -p e69de29bb2d1d6434b8b29ae775ad8c2e48c5391
```

**Output**

```
<content_of_the_object>
```

### Write Tree

Generates a tree object representing the current directory structure and stores it in the `.git/objects` directory.

**Command**

```bash
python git.py write-tree
```

**Output**

```
<sha1_hash_of_the_tree>
```

### Commit Tree

Creates a commit object that references a tree object and optionally a parent commit.

**Command**

```bash
python git.py commit-tree <tree_sha> -m "<commit_message>" [-p <parent_sha>]
```

**Parameters**

- `<tree_sha>`: SHA-1 hash of the tree object to commit.
- `-m`: Commit message.
- `-p`: (Optional) SHA-1 hash of the parent commit.

**Example**

```bash
python git.py commit-tree a1b2c3d4 -m "Initial commit"
```

**Output**

```
<sha1_hash_of_the_commit>
```

### List Tree

Displays the contents of a tree object in a human-readable format.

**Command**

```bash
python git.py ls-tree <tree_sha>
```

**Parameters**

- `<tree_sha>`: SHA-1 hash of the tree object to list.

**Example**

```bash
python git.py ls-tree d4c3b2a1
```

**Output**

```
<list_of_files_and_directories_in_the_tree>
```

## Author

**Omar Saqr**
- Email: [omar_saqr@example.com](mailto:omar_saqr@example.com)

## License

This project is licensed under the [MIT License](LICENSE).

---

**Note**: This implementation is for educational purposes and does not cover all features and edge cases of the actual Git version control system. Use it to understand the fundamentals of how Git works internally.
