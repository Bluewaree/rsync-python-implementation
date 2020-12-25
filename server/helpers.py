import hashlib
import zlib
import os
import shutil

from .constants import BLOCK_SIZE


def delete_file(c, absolute_file_path):
    try:
        os.remove(absolute_file_path)
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))


def create_folder(c, absolute_path):
    try:
        os.makedirs(absolute_path)
    except FileExistsError:
        print ("Folder exists.")


def delete_folder(c, absolute_path):
    try:
        shutil.rmtree(absolute_path)
    except OSError as e:
        print ("Error: %s - %s." % (e.filename, e.strerror))


def md5_chunk(chunk):
    m = hashlib.md5()
    m.update(chunk)
    return m.hexdigest()


def adler32_chunk(chunk):
    return zlib.adler32(chunk)

def checksums_file(file):
    chunks = {}
    if os.path.exists(file):
        with open(file, "rb") as f:
            count = 0
            while True:
                chunk = f.read(BLOCK_SIZE)
                if not chunk:
                    break

                adler32=adler32_chunk(chunk)
                md5=md5_chunk(chunk)
                chunks[adler32] = {md5: count}
                count +=1
    return chunks


def write_blocks_to_file(blocks, absolute_file_path, tmp_file):
    if os.path.exists(absolute_file_path):
        with open(absolute_file_path, "rb") as ft:
            with open(tmp_file, "wb") as f:
                for block in blocks:
                    if isinstance(block, int):
                        ft.seek(block * BLOCK_SIZE)
                        content = ft.read(BLOCK_SIZE)
                        f.write(content)
                    else:
                        f.write(block)

                f.close()
                os.remove(absolute_file_path)
                os.rename(tmp_file, absolute_file_path)
            ft.close()
    else:
        with open(absolute_file_path, "wb") as f:
            for block in blocks:
                f.write(block)


