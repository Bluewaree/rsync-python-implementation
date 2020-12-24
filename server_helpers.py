import hashlib
import zlib
import os

BLOCK_SIZE = 8192

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

