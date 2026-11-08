"""Read a Figshare ZIP by HTTP range requests.

The RDD2022 archive is about 12 GB. Figshare signs each download URL for only
a few seconds, so this client refreshes the URL and reads just the ranges it
needs (the ZIP central directory, then individual members).
"""

from __future__ import annotations

import io
import struct
import time
import zlib
from dataclasses import dataclass

import requests

FIGSHARE_FILE = "https://ndownloader.figshare.com/files/38030910"
ARCHIVE_SIZE = 13_264_172_619


@dataclass
class Member:
    name: str
    method: int
    comp_size: int
    uncomp_size: int
    local_offset: int


class RemoteZip:
    def __init__(self, redirect_url: str = FIGSHARE_FILE, size: int = ARCHIVE_SIZE):
        self.redirect_url = redirect_url
        self.size = size
        self.session = requests.Session()
        self._signed_url = ""
        self._signed_at = 0.0
        self.members: list[Member] = []

    def _signed(self) -> str:
        if not self._signed_url or (time.time() - self._signed_at) > 6:
            response = self.session.get(self.redirect_url, allow_redirects=False, timeout=60)
            response.raise_for_status()
            self._signed_url = response.headers["Location"]
            self._signed_at = time.time()
        return self._signed_url

    def read_at(self, start: int, length: int) -> bytes:
        if length <= 0:
            return b""
        end = min(start + length, self.size) - 1
        last_error: Exception | None = None
        for _ in range(4):
            try:
                response = self.session.get(
                    self._signed(),
                    headers={"Range": f"bytes={start}-{end}"},
                    timeout=120,
                )
                if response.status_code == 403:
                    self._signed_url = ""
                    continue
                response.raise_for_status()
                data = response.content
                if len(data) < (end - start + 1):
                    raise IOError(f"short read at {start}: got {len(data)}")
                return data
            except Exception as exc:  # noqa: BLE001 — retry signed-URL expiry
                last_error = exc
                self._signed_url = ""
                time.sleep(0.4)
        raise RuntimeError(f"failed to read {start}:{length}") from last_error

    def load_index(self) -> None:
        tail = self.read_at(self.size - 70_000, 70_000)
        eocd = tail.rfind(b"PK\x05\x06")
        if eocd < 0:
            raise RuntimeError("ZIP end-of-central-directory record not found")
        cd_size, cd_offset = struct.unpack_from("<II", tail, eocd + 12)
        if cd_offset == 0xFFFFFFFF or cd_size == 0xFFFFFFFF:
            locator = tail.rfind(b"PK\x06\x07", 0, eocd)
            if locator < 0:
                raise RuntimeError("ZIP64 locator not found")
            zip64_offset = struct.unpack_from("<Q", tail, locator + 8)[0]
            record = self.read_at(zip64_offset, 80)
            if record[:4] != b"PK\x06\x06":
                raise RuntimeError("ZIP64 end record missing")
            cd_size, cd_offset = struct.unpack_from("<QQ", record, 40)
        directory = self.read_at(cd_offset, cd_size)
        self.members = list(_parse_central_directory(directory))

    def read_member(self, member: Member) -> bytes:
        header = self.read_at(member.local_offset, 30)
        if header[:4] != b"PK\x03\x04":
            raise RuntimeError(f"bad local header for {member.name}")
        name_len, extra_len = struct.unpack_from("<HH", header, 26)
        data_start = member.local_offset + 30 + name_len + extra_len
        compressed = self.read_at(data_start, member.comp_size)
        if member.method == 0:
            return compressed
        if member.method == 8:
            return zlib.decompress(compressed, -15)
        raise RuntimeError(f"unsupported compression method {member.method} for {member.name}")


def _parse_central_directory(directory: bytes):
    pos = 0
    end = len(directory)
    while pos + 46 <= end:
        if directory[pos : pos + 4] != b"PK\x01\x02":
            break
        method = struct.unpack_from("<H", directory, pos + 10)[0]
        comp_size, uncomp_size = struct.unpack_from("<II", directory, pos + 20)
        name_len, extra_len, comment_len = struct.unpack_from("<HHH", directory, pos + 28)
        local_offset = struct.unpack_from("<I", directory, pos + 42)[0]
        name_start = pos + 46
        name = directory[name_start : name_start + name_len].decode("utf-8", "replace")
        extra = directory[name_start + name_len : name_start + name_len + extra_len]
        if uncomp_size == 0xFFFFFFFF or comp_size == 0xFFFFFFFF or local_offset == 0xFFFFFFFF:
            uncomp_size, comp_size, local_offset = _zip64_extra(
                extra, uncomp_size, comp_size, local_offset
            )
        yield Member(name, method, comp_size, uncomp_size, local_offset)
        pos = name_start + name_len + extra_len + comment_len


def _zip64_extra(extra: bytes, uncomp: int, comp: int, offset: int):
    cursor = 0
    while cursor + 4 <= len(extra):
        header_id, size = struct.unpack_from("<HH", extra, cursor)
        payload = extra[cursor + 4 : cursor + 4 + size]
        cursor += 4 + size
        if header_id != 0x0001:
            continue
        view = io.BytesIO(payload)
        if uncomp == 0xFFFFFFFF:
            uncomp = struct.unpack("<Q", view.read(8))[0]
        if comp == 0xFFFFFFFF:
            comp = struct.unpack("<Q", view.read(8))[0]
        if offset == 0xFFFFFFFF:
            offset = struct.unpack("<Q", view.read(8))[0]
        return uncomp, comp, offset
    raise RuntimeError("ZIP64 extra field missing")

