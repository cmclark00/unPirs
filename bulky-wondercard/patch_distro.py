#!/usr/bin/env python3
"""
Put a Gen 4 Wonder Card (.pcd) into a dump of the "Deoxys 2008" Pokemon
distribution cartridge so that a DS running the patched ROM wirelessly hands
the card to Diamond / Pearl / Platinum / HeartGold / SoulSilver.

Usage:
    python3 patch_distro.py DEOXYS2008.nds bulky.pcd bulky_distro.nds
    python3 patch_distro.py DEOXYS2008.nds bulky.pcd out.nds --language french

You must supply your own dump of the distribution cart; none is included.
The offsets are the ones used by MicShadow's Wondercard Distribution Patcher
(WCDPatcher), which only supports this one ROM:
    MD5 cc30a203c5489440ea2315db3c791866
"""

import argparse
import hashlib
import struct
import sys

from make_bulky_card import PCD_SIZE, decrypt_pk4, describe_pcd, is_encrypted_pk4

DEOXYS_2008_MD5 = "cc30a203c5489440ea2315db3c791866"

CARD_OFFSET = 0x05DD50          # full 856-byte PCD
HEADER_OFFSETS = (0x05DC10, 0x05DD00)  # copies of PCD 0x104-0x153 (title, games, card ID)
RECEIVED_DATE_OFFSET = 0x05E0A4  # PCD 0x354 inside the ROM copy; must be zero
GGID_OFFSET = 0x168C00           # selects which language of game will listen
DATE_WINDOW_OFFSET = 0x16C600    # start (4 bytes) + end (4 bytes) of distribution period
HEADER_CRC_OFFSET = 0x15E

GGID = {
    "english": 0x00400318,
    "french": 0x008000CD,
    "german": 0x008000CE,
    "italian": 0x008000CF,
    "spanish": 0x008000D0,
    "japanese": 0x00000345,
    "korean": 0x00C00018,
}


def crc16(data):
    """CRC-16/MODBUS, as used for the NDS header checksum."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc


def card_species(card):
    raw = card[8:8 + 0xEC]
    pk = decrypt_pk4(raw) if is_encrypted_pk4(raw) else raw
    return struct.unpack_from("<H", pk, 8)[0]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("rom", help="clean dump of the Deoxys 2008 distribution cart (.nds)")
    parser.add_argument("pcd", help="Wonder Card to distribute (856-byte .pcd)")
    parser.add_argument("output", help="patched ROM to write")
    parser.add_argument("--language", choices=sorted(GGID), default="english",
                        help="language of the games that should receive the card (default: english)")
    parser.add_argument("--force", action="store_true",
                        help="patch even if the ROM's MD5 does not match the known Deoxys 2008 dump")
    args = parser.parse_args(argv)

    with open(args.rom, "rb") as f:
        rom = bytearray(f.read())
    with open(args.pcd, "rb") as f:
        card = f.read()

    if len(card) != PCD_SIZE:
        sys.exit(f"{args.pcd}: expected {PCD_SIZE} bytes, got {len(card)}")

    md5 = hashlib.md5(rom).hexdigest()
    if md5 != DEOXYS_2008_MD5:
        if not args.force:
            sys.exit(f"{args.rom}: MD5 {md5} is not the Deoxys 2008 distribution ROM "
                     f"({DEOXYS_2008_MD5}). The offsets only fit that ROM; use --force "
                     "only if you know this is a trimmed copy of it.")
        print(f"warning: MD5 {md5} does not match, patching anyway (--force)")
    if len(rom) < DATE_WINDOW_OFFSET + 8:
        sys.exit(f"{args.rom}: too small ({len(rom)} bytes) to be the distribution ROM")
    existing = bytes(rom[CARD_OFFSET:CARD_OFFSET + PCD_SIZE])
    if existing[0] != 1 or card_species(existing) != 386:
        print("warning: no Deoxys Wonder Card found at the expected offset")

    header_crc = struct.unpack_from("<H", rom, HEADER_CRC_OFFSET)[0]

    for offset in HEADER_OFFSETS:
        rom[offset:offset + 0x50] = card[0x104:0x154]
    rom[CARD_OFFSET:CARD_OFFSET + PCD_SIZE] = card
    rom[RECEIVED_DATE_OFFSET:RECEIVED_DATE_OFFSET + 2] = b"\0\0"
    struct.pack_into("<I", rom, GGID_OFFSET, GGID[args.language])
    struct.pack_into("<II", rom, DATE_WINDOW_OFFSET, 0x00000000, 0xFFFFFFFF)  # always active

    # Nothing above touches the cartridge header, so its CRC must still hold.
    assert crc16(rom[:0x15E]) == header_crc, "NDS header CRC mismatch"

    with open(args.output, "wb") as f:
        f.write(rom)

    print(f"Wrote {args.output} ({args.language} games)\n")
    print(describe_pcd(card))
    return 0


if __name__ == "__main__":
    sys.exit(main())
