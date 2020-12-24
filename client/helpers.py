import hashlib
import zlib

BLOCK_SIZE = 8192

def md5_chunk(chunk):
    m = hashlib.md5()
    m.update(chunk)
    return m.hexdigest()

def adler32_chunk(chunk):
    return zlib.adler32(chunk)

def _get_block_list(file, checksums):
    blocks = []
    offset = 0
    with open(file, "rb") as f:
        while True:
            chunk = f.read(BLOCK_SIZE)
            if not chunk:
                break
            chunk_number = None
            adler32 = checksums.get(str(adler32_chunk(chunk)))
            if adler32:
                chunk_number = adler32.get(md5_chunk(chunk))

            if chunk_number is not None:
                offset += BLOCK_SIZE
                blocks.append(chunk_number)
                continue
            else:
                offset += 1
                blocks.append(chunk[0:1])
                f.seek(offset)
                continue
    return blocks

