import sys
import os
import zlib
import hashlib 
import re
from pathlib import Path
from datetime import datetime, timezone
def create_commit(tree_sha, parent_sha, message):
    # Author and committer details
    name = "Omar Saqr"
    email = "omar_saqr@example.com"
    
    # Current timestamp in seconds since epoch
    timestamp = int(datetime.now(tz=timezone.utc).timestamp())
    timezone_offset = "+0000"  # UTC timezone

    # Prepare the commit content
    commit_content = [
        f"tree {tree_sha}",
    ]

    # Add parent SHA if present
    if parent_sha:
        commit_content.append(f"parent {parent_sha}")
    
    # Add author and committer details
    author_info = f"{name} <{email}> {timestamp} {timezone_offset}"
    commit_content.append(f"author {author_info}")
    commit_content.append(f"committer {author_info}")
    
    # Add commit message
    commit_content.append("")
    commit_content.append(message)

    # Join all parts of the commit content
    commit_content_str = "\n".join(commit_content)
    
    # Compute the header
    header = f"commit {len(commit_content_str)}\0"
    content = header + commit_content_str+"\n"

    # Compute the SHA1 hash of the commit
    commit_sha = hashlib.sha1(content.encode('utf-8')).hexdigest()

    # Write the commit object to the .git/objects directory
    dir_name = commit_sha[:2]
    file_name = commit_sha[2:]
    object_path = Path(f".git/objects/{dir_name}/{file_name}")

    if not object_path.exists():
        os.makedirs(object_path.parent, exist_ok=True)
        with open(object_path, 'wb') as f:
            f.write(zlib.compress(content.encode('utf-8')))

    return commit_sha




def create_blob(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
    header = f"blob {len(data)}\0"
    content = header + data
    sha = hashlib.sha1(content.encode('utf-8')).hexdigest()

    dir_name = sha[:2]
    file_name = sha[2:]
    object_path = Path(f".git/objects/{dir_name}/{file_name}")

    if not object_path.exists():
        os.makedirs(object_path.parent, exist_ok=True)
        with open(object_path, 'wb') as f:
            f.write(zlib.compress(content.encode('utf-8')))
    
    return sha

def create_tree(directory):
    entries = []

    for item in sorted(directory.iterdir()):
        if item.name == ".git":
            continue
        mode = "40000" if item.is_dir() else "100644"
        name = item.name.encode('utf-8')
        if item.is_dir():
            sha = create_tree(item)
        else:
            sha = create_blob(item)
        entries.append((mode, name, sha))

    tree_content = b"".join(
        mode.encode('utf-8') + b" " + name + b"\0" + bytes.fromhex(sha)
        for mode, name, sha in entries
    )

    header = f"tree {len(tree_content)}\0".encode('utf-8')
    content = header + tree_content
    tree_sha = hashlib.sha1(content).hexdigest()

    dir_name = tree_sha[:2]
    file_name = tree_sha[2:]
    object_path = Path(f".git/objects/{dir_name}/{file_name}")

    if not object_path.exists():
        os.makedirs(object_path.parent, exist_ok=True)
        with open(object_path, 'wb') as f:
            f.write(zlib.compress(content))
    
    return tree_sha

def extract_chars_until_number(byte_obj):
    # This will hold the collected bytes in reverse order
    collected_bytes = []

    # Iterate from the end of the byte object
    for byte in reversed(byte_obj):
        if 48 <= byte <= 57:  # ASCII values for '0' to '9'
            break
        collected_bytes.append(byte)

    # Reverse the collected bytes to restore original order
    collected_bytes.reverse()

    # Decode the collected bytes to a string using a fallback encoding
    try:
        result = bytes(collected_bytes).decode('utf-8', errors='ignore')
    except UnicodeDecodeError:
        result = bytes(collected_bytes).decode('iso-8859-1', errors='ignore')

    return result

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!")

    # Uncomment this block to pass the first stage
    #
    command = sys.argv[1]
    ha=''
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command=='cat-file':
        with open(f'.git/objects/{sys.argv[3][-40:-38]}/{sys.argv[3][-38:]}', 'rb') as file:
            data = file.read()
            data=zlib.decompress(data)
            print(data.decode('utf-8').split('\x00')[-1],end='')
    elif command=='hash-object':
        with open(f'{sys.argv[3]}', 'r') as file:
            data=file.read()
            name = (f"blob {len(data)}\0" + data)
            x=name
            name=name.encode('utf-8')
            name=hashlib.sha1(name).hexdigest()
            print(name)
            name1=name[0:2]
            name2=name[2:]
            os.mkdir(f".git/objects/{name1}")
            with open(f'.git/objects/{name1}/{name2}', 'wb') as file:
                file.write(zlib.compress(x.encode("utf-8")))
    elif command=="write-tree":
        root_dir = Path(os.curdir)  # Convert the string to a Path object
        tree_sha = create_tree(root_dir)
        ha=tree_sha
        print(tree_sha)
    elif command == "commit-tree":
        tree_sha = sys.argv[2]
        parent_sha = None
        message = ""

        for i in range(3, len(sys.argv)):
            if sys.argv[i] == "-p":
                parent_sha = sys.argv[i + 1]
            elif sys.argv[i] == "-m":
                message = sys.argv[i + 1]

        commit_sha = create_commit(tree_sha, parent_sha, message)
        print(commit_sha)


    elif command=='ls-tree':
        with open(f'.git/objects/{sys.argv[3][-40:-38]}/{sys.argv[3][-38:]}', 'rb') as file:
            data = file.read()
            data=zlib.decompress(data)  
            words = data.split(b'\x00')
            # print(words)
            # print(data)
            # Extract words before each \x00
            words_before_null=[]
            words=words[1:-1]
            for word in words:
                words_before_null.append(extract_chars_until_number(word))
            # Flatten the list of words and filter out empty strings
            # print(words)
            # print(words_before_null)
            # flattened_words = [word for sublist in words_before_null for word in sublist if word]
            wor=""
            for word in words_before_null:
                wor+=word.replace(' ','')+"\n"
            print(wor,end='')

            # for word in flattened_words:
            #     print(word)





    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
