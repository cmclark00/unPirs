#!/usr/bin/env python3
"""
Build a Generation 4 Wonder Card (.pcd) that gives "BULKY", the Play2Win Games
mascot, to Pokemon Diamond / Pearl (and optionally Platinum / HeartGold /
SoulSilver) through Mystery Gift.

Gen 4 games can only receive species that already exist in the game, so Bulky
is a nicknamed Pokemon with a custom Original Trainer, held item, moves and
ribbon -- see README.md for the reasoning and the distribution steps.

Usage:
    python3 make_bulky_card.py                  # writes bulky.pcd
    python3 make_bulky_card.py -o other.pcd
    python3 make_bulky_card.py --info bulky.pcd # dump any Gen 4 .pcd

Only the Python 3 standard library is needed.  Layouts follow PKHeX
(PCD.cs, PGT.cs, PK4.cs, PokeCrypto.cs) and were checked against the 247
official Gen 4 Pokemon Wonder Cards in PKHeX's event database.
"""

import argparse
import struct
import sys

# ---------------------------------------------------------------------------
# Edit this block to change the gift.
# ---------------------------------------------------------------------------

CONFIG = {
    # The Pokemon
    "species": "mareep",          # key into SPECIES below
    "nickname": "BULKY",          # max 10 characters
    "level": 10,                  # 10 keeps him obedient for badge-less players
    "nature": "Relaxed",          # chill goat in sunglasses
    "gender": "male",             # male / female / genderless
    "shiny": True,                # pink wool and sparkles when he's sent out
    "held_item": 240,             # 240 = BlackGlasses (Bulky's shades)
    "ball": 16,                   # 16 = Cherish Ball (the event ball)
    "moves": [29, 84, 178, 86],   # Headbutt, ThunderShock, Cotton Spore, Thunder Wave
    "ivs": [31, 31, 31, 31, 31, 31],  # HP, Atk, Def, Spe, SpA, SpD (fixed; see README)
    "classic_ribbon": True,       # "A Ribbon that proclaims love for Pokemon."

    # The Original Trainer shown on the summary screen
    "ot_name": "P2WIN",           # max 7 characters
    "ot_gender": "male",
    "tid": 2,                     # Trainer ID shown in game
    "sid": 2024,                  # hidden Secret ID
    "language": 2,                # 2 = English
    "met_location": 60,           # stored as (met - 3000); 60 -> "Pokemon Event"

    # The Wonder Card itself
    "card_id": 1001,              # unique per event; official cards used 0-184
    "title": "BULKY from Play2Win Games!",   # max 36 characters
    "description": [              # max ~36 characters per line
        "Thanks for visiting",
        "Play2Win Games!",
        "Meet BULKY, the coolest goat",
        "around. Be sure to save after",
        "you pick him up at a Poké Mart.",
    ],
    "games": ["diamond", "pearl"],  # add "platinum", "heartgold", "soulsilver"
    "share_limit": 0,             # times a player may re-share the card (0-255; 255 = unlimited)
}

# Base data from PKHeX's personal_dp table: base stats (HP/Atk/Def/Spe/SpA/SpD),
# the two ability IDs, gender ratio, base friendship and growth rate.
SPECIES = {
    "mareep":   dict(id=179, base=(55, 40, 40, 35, 65, 45),   abilities=(9, 9),    gender_ratio=127, friendship=70, growth=3),
    "tauros":   dict(id=128, base=(75, 100, 95, 110, 40, 70), abilities=(22, 83),  gender_ratio=0,   friendship=70, growth=5),
    "stantler": dict(id=234, base=(73, 95, 62, 85, 85, 65),   abilities=(22, 119), gender_ratio=127, friendship=70, growth=5),
}

# ---------------------------------------------------------------------------
# Game data
# ---------------------------------------------------------------------------

VERSION_BITS = {"heartgold": 7, "soulsilver": 8, "diamond": 10, "pearl": 11, "platinum": 12}

NATURES = ["Hardy", "Lonely", "Brave", "Adamant", "Naughty", "Bold", "Docile",
           "Relaxed", "Impish", "Lax", "Timid", "Hasty", "Serious", "Jolly",
           "Naive", "Modest", "Mild", "Quiet", "Bashful", "Rash", "Calm",
           "Gentle", "Sassy", "Careful", "Quirky"]

# Base PP of every Gen 4 move, indexed by move ID (PKHeX MoveInfo4.PP).
MOVE_PP = [int(x) for x in """
0,35,25,10,15,20,20,15,15,15,35,30,5,10,30,30,35,35,20,15,20,20,15,20,30,5,25,15,15,15,25,20,5,35,15,20,20,20,15,30,
35,20,20,30,25,40,20,15,20,20,20,30,25,15,30,25,5,15,10,5,20,20,20,5,35,20,25,20,20,20,15,25,15,10,40,25,10,35,30,15,
20,40,10,15,30,15,20,10,15,10,5,10,10,25,10,20,40,30,30,20,20,15,10,40,15,10,30,20,20,10,40,40,30,30,30,20,30,10,10,20,
5,10,30,20,20,20,5,15,10,20,15,15,35,20,15,10,20,30,15,40,20,15,10,5,10,30,10,15,20,15,40,40,10,5,15,10,10,10,15,30,
30,10,10,20,10,1,1,10,10,10,5,15,25,15,10,15,30,5,40,15,10,25,10,30,10,20,10,10,10,10,10,20,5,40,5,5,15,5,10,5,
15,10,10,10,20,20,40,15,10,20,20,25,5,15,10,5,20,15,20,25,20,5,30,5,10,20,40,5,20,40,20,15,35,10,5,5,5,15,5,20,
5,5,15,20,10,5,5,15,15,15,15,10,10,10,20,10,10,10,10,15,15,15,10,20,20,10,20,20,20,20,20,10,10,10,20,20,5,15,10,10,
15,10,20,5,5,10,10,20,5,10,20,10,20,20,20,5,5,15,20,10,15,20,15,10,10,15,10,5,5,10,15,10,5,20,25,5,40,10,5,40,
15,20,20,5,15,20,30,15,15,5,10,30,20,30,15,5,40,15,5,20,5,15,25,40,15,20,15,20,15,20,10,20,20,5,5,10,5,40,10,10,
5,10,10,15,10,20,30,30,10,20,5,10,10,15,10,10,5,15,5,10,10,30,20,20,10,10,5,5,10,5,20,10,20,10,15,10,20,20,20,15,
15,10,15,20,15,10,10,10,20,5,30,5,10,15,10,10,5,20,30,10,30,15,15,15,15,30,10,20,15,10,10,20,15,5,5,15,15,5,10,5,
20,5,15,20,5,20,20,20,20,10,20,10,15,20,15,10,10,5,10,5,5,10,5,5,10,5,5,5
""".split(",")]

# Half-width Western glyphs of the Gen 4 character table, starting at 0x121.
# "\0" marks slots that hold symbols with no plain Unicode equivalent.
_G4_WESTERN = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖ\0ØÙÚÛÜÝÞßàáâãäåæçèéêëìíîïðñòóôõö\0øùúûüýþÿŒœŞşªº"
    "\0\0\0$¡¿!?,.\0･/‘'“”„«»()♂♀+-*#=&~:;\0\0\0\0\0\0\0\0\0\0@\0%\0\0\0\0\0\0\0\0\0\0\0 "
)
G4_ENCODE = {ch: 0x121 + i for i, ch in enumerate(_G4_WESTERN) if ch != "\0"}
G4_ENCODE["’"] = G4_ENCODE["'"]
G4_DECODE = {v: k for k, v in G4_ENCODE.items() if k != "’"}
G4_NEWLINE = 0xE000
G4_TERMINATOR = 0xFFFF

PK4_PARTY_SIZE = 0xEC
PGT_SIZE = 0x104
PCD_SIZE = 0x358

# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------


def encode_text(text, max_chars, field):
    """Encode a string as Gen 4 text, terminated and padded with 0xFFFF."""
    values = []
    for ch in text:
        if ch == "\n":
            values.append(G4_NEWLINE)
        elif ch in G4_ENCODE:
            values.append(G4_ENCODE[ch])
        else:
            raise ValueError(f"{field}: character {ch!r} is not in the Gen 4 character set")
    if len(values) > max_chars:
        raise ValueError(f"{field}: {len(values)} characters, max is {max_chars}")
    values += [G4_TERMINATOR] * (max_chars + 1 - len(values))
    return struct.pack(f"<{len(values)}H", *values)


def decode_text(data):
    out = []
    for (v,) in struct.iter_unpack("<H", data):
        if v in (G4_TERMINATOR, 0):
            break
        out.append("\n" if v == G4_NEWLINE else G4_DECODE.get(v, f"{{{v:04X}}}"))
    return "".join(out)

# ---------------------------------------------------------------------------
# Pokemon math
# ---------------------------------------------------------------------------


def exp_for_level(growth, n):
    """Total EXP at level n for the six Gen 3/4 growth rates."""
    if n <= 1:
        return 0
    if growth == 0:  # Medium Fast
        return n ** 3
    if growth == 1:  # Erratic
        if n <= 50:
            return n ** 3 * (100 - n) // 50
        if n <= 68:
            return n ** 3 * (150 - n) // 100
        if n <= 98:
            return n ** 3 * ((1911 - 10 * n) // 3) // 500
        return n ** 3 * (160 - n) // 100
    if growth == 2:  # Fluctuating
        if n <= 15:
            return n ** 3 * ((n + 1) // 3 + 24) // 50
        if n <= 36:
            return n ** 3 * (n + 14) // 50
        return n ** 3 * (n // 2 + 32) // 50
    if growth == 3:  # Medium Slow
        return 6 * n ** 3 // 5 - 15 * n ** 2 + 100 * n - 140
    if growth == 4:  # Fast
        return 4 * n ** 3 // 5
    if growth == 5:  # Slow
        return 5 * n ** 3 // 4
    raise ValueError(f"unknown growth rate {growth}")


def calc_stats(base, ivs, level, nature):
    """Party stats (HP, Atk, Def, Spe, SpA, SpD) with zero EVs."""
    up, down = nature // 5, nature % 5  # index into Atk/Def/Spe/SpA/SpD
    hp = (2 * base[0] + ivs[0]) * level // 100 + level + 10
    stats = [hp]
    for i in range(5):
        value = (2 * base[i + 1] + ivs[i + 1]) * level // 100 + 5
        if up != down:
            if i == up:
                value = value * 110 // 100
            elif i == down:
                value = value * 90 // 100
        stats.append(value)
    return stats


def gender_from_pid(pid, ratio):
    if ratio == 255:
        return 2
    if ratio == 254:
        return 1
    if ratio == 0:
        return 0
    return 1 if (pid & 0xFF) < ratio else 0


def is_shiny(pid, tid, sid):
    return (tid ^ sid ^ (pid >> 16) ^ (pid & 0xFFFF)) < 8


def find_pid(nature, gender, ratio, tid, sid, shiny, start=0xB0117000):
    """Deterministically pick a fixed PID with the wanted nature/gender/shininess.

    Shininess is judged against the gift's own OT IDs, which every recipient
    keeps, so a fixed PID makes Bulky shiny (or not) in every game.
    """
    if shiny:
        # Shiny when the two PID halves XOR to within 8 of TID ^ SID.
        candidates = ((((tid ^ sid ^ low ^ k) << 16) | low)
                      for low in range(start & 0xFFFF, 0x10000) for k in range(8))
    else:
        candidates = range(start, start + 0x100000)
    for pid in candidates:
        if (pid % 25 == nature and gender_from_pid(pid, ratio) == gender
                and is_shiny(pid, tid, sid) == shiny):
            return pid
    raise RuntimeError("no PID found")

# ---------------------------------------------------------------------------
# PK4 encryption (PokeCrypto.Encrypt45 / Decrypt45)
# ---------------------------------------------------------------------------

BLOCK_POSITION = [
    0, 1, 2, 3, 0, 1, 3, 2, 0, 2, 1, 3, 0, 3, 1, 2, 0, 2, 3, 1, 0, 3, 2, 1,
    1, 0, 2, 3, 1, 0, 3, 2, 2, 0, 1, 3, 3, 0, 1, 2, 2, 0, 3, 1, 3, 0, 2, 1,
    1, 2, 0, 3, 1, 3, 0, 2, 2, 1, 0, 3, 3, 1, 0, 2, 2, 3, 0, 1, 3, 2, 0, 1,
    1, 2, 3, 0, 1, 3, 2, 0, 2, 1, 3, 0, 3, 1, 2, 0, 2, 3, 1, 0, 3, 2, 1, 0,
]
BLOCK_POSITION_INVERT = [0, 1, 2, 4, 3, 5, 6, 7, 12, 18, 13, 19,
                         8, 10, 14, 20, 16, 22, 9, 11, 15, 21, 17, 23]


def _crypt(data, seed):
    out = bytearray(data)
    for i in range(0, len(out), 2):
        seed = (0x41C64E6D * seed + 0x6073) & 0xFFFFFFFF
        (v,) = struct.unpack_from("<H", out, i)
        struct.pack_into("<H", out, i, v ^ (seed >> 16))
    return bytes(out)


def _shuffle(data, sv):
    blocks = [data[i * 32:(i + 1) * 32] for i in range(4)]
    return b"".join(blocks[BLOCK_POSITION[sv * 4 + i]] for i in range(4))


def pk4_checksum(pk):
    return sum(struct.unpack_from("<64H", pk, 8)) & 0xFFFF


def encrypt_pk4(pk):
    pid, = struct.unpack_from("<I", pk, 0)
    chk, = struct.unpack_from("<H", pk, 6)
    body = _crypt(_shuffle(pk[8:0x88], BLOCK_POSITION_INVERT[((pid >> 13) & 31) % 24]), chk)
    return pk[:8] + body + _crypt(pk[0x88:], pid)


def decrypt_pk4(pk):
    pid, = struct.unpack_from("<I", pk, 0)
    chk, = struct.unpack_from("<H", pk, 6)
    body = _shuffle(_crypt(pk[8:0x88], chk), ((pid >> 13) & 31) % 24)
    return pk[:8] + body + _crypt(pk[0x88:], pid)


def is_encrypted_pk4(pk):
    # PKHeX heuristic: unused ribbon bits at 0x64 are always zero when decrypted.
    return struct.unpack_from("<I", pk, 0x64)[0] != 0

# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

GENDERS = {"male": 0, "female": 1, "genderless": 2}


def build_pk4(cfg):
    sp = SPECIES[cfg["species"]]
    nature = NATURES.index(cfg["nature"])
    gender = GENDERS[cfg["gender"]]
    if gender != gender_from_pid(0x80, sp["gender_ratio"]) and sp["gender_ratio"] in (0, 254, 255):
        raise ValueError(f"{cfg['species']} cannot be {cfg['gender']}")
    if len(cfg["ivs"]) != 6 or not any(cfg["ivs"]) or max(cfg["ivs"]) > 31:
        # All-zero IVs tell the game to roll random IVs, which also wipes the
        # nickname flag stored in the same word -- keep them fixed.
        raise ValueError("ivs: six values 0-31, not all zero")
    level = cfg["level"]
    pid = find_pid(nature, gender, sp["gender_ratio"], cfg["tid"], cfg["sid"], cfg["shiny"])
    ivs = cfg["ivs"]

    pk = bytearray(PK4_PARTY_SIZE)
    struct.pack_into("<I", pk, 0x00, pid)
    struct.pack_into("<H", pk, 0x08, sp["id"])
    struct.pack_into("<H", pk, 0x0A, cfg["held_item"])
    struct.pack_into("<HH", pk, 0x0C, cfg["tid"], cfg["sid"])
    struct.pack_into("<I", pk, 0x10, exp_for_level(sp["growth"], level))
    pk[0x14] = sp["friendship"]
    pk[0x15] = sp["abilities"][pid & 1] or sp["abilities"][0]
    pk[0x17] = cfg["language"]
    if cfg["classic_ribbon"]:
        pk[0x27] |= 1 << 2

    moves = (list(cfg["moves"]) + [0, 0, 0, 0])[:4]
    struct.pack_into("<4H", pk, 0x28, *moves)
    pk[0x30:0x34] = bytes(MOVE_PP[m] for m in moves)

    iv32 = sum(iv << (5 * i) for i, iv in enumerate(ivs)) | 0x80000000  # nicknamed
    struct.pack_into("<I", pk, 0x38, iv32)
    pk[0x40] = 1 | (gender << 1)  # fateful encounter, gender, form 0

    pk[0x48:0x5E] = encode_text(cfg["nickname"], 10, "nickname")
    pk[0x5F] = 10  # origin game; official D/P gifts use Diamond
    pk[0x68:0x78] = encode_text(cfg["ot_name"], 7, "ot_name")
    struct.pack_into("<H", pk, 0x7E, cfg["met_location"])  # met = this + 3000
    pk[0x83] = cfg["ball"]
    pk[0x84] = level | (GENDERS[cfg["ot_gender"]] << 7)

    stats = calc_stats(sp["base"], ivs, level, nature)
    pk[0x8C] = level
    struct.pack_into("<7H", pk, 0x8E, stats[0], *stats)

    struct.pack_into("<H", pk, 0x06, pk4_checksum(pk))
    return bytes(pk)


def build_pcd(cfg):
    pk = build_pk4(cfg)

    pgt = bytearray(PGT_SIZE)
    pgt[0x00] = 1  # gift type: Pokemon
    struct.pack_into("<I", pgt, 0x04, 1)  # as on every official Pokemon card
    pgt[0x08:0x08 + PK4_PARTY_SIZE] = encrypt_pk4(pk)
    if cfg["classic_ribbon"]:
        pgt[0xF9] = 0x40  # Classic Ribbon description, as used by official cards

    card = bytearray(PCD_SIZE)
    card[:PGT_SIZE] = pgt
    card[0x104:0x14C] = encode_text(cfg["title"], 35, "title")
    struct.pack_into("<H", card, 0x14C, sum(1 << VERSION_BITS[g] for g in cfg["games"]))
    struct.pack_into("<H", card, 0x150, cfg["card_id"])
    card[0x152] = 0x0D  # unknown flags; 0x0D on 234 of 247 official Pokemon cards
    card[0x154:0x348] = encode_text("\n".join(cfg["description"]), 249, "description")
    card[0x348] = cfg["share_limit"]
    struct.pack_into("<3H", card, 0x34A, 0, SPECIES[cfg["species"]]["id"], 0)
    return bytes(card)

# ---------------------------------------------------------------------------
# Inspection
# ---------------------------------------------------------------------------


def describe_pcd(card):
    if len(card) != PCD_SIZE:
        raise ValueError(f"expected {PCD_SIZE} bytes, got {len(card)}")
    games = struct.unpack_from("<H", card, 0x14C)[0]
    lines = [
        f"Title:       {decode_text(card[0x104:0x14C])}",
        f"Card ID:     {struct.unpack_from('<H', card, 0x150)[0]}",
        f"Games:       {', '.join(g for g, b in VERSION_BITS.items() if games >> b & 1) or 'none'}",
        f"Share limit: {card[0x348]}",
        f"Icons:       {struct.unpack_from('<3H', card, 0x34A)}",
        "Description:",
        *("    " + line for line in decode_text(card[0x154:0x348]).split("\n")),
    ]
    if card[0] != 1:
        lines.append(f"Gift type {card[0]} (not a Pokemon)")
        return "\n".join(lines)

    raw = card[8:8 + PK4_PARTY_SIZE]
    pk = decrypt_pk4(raw) if is_encrypted_pk4(raw) else raw
    pid, = struct.unpack_from("<I", pk, 0)
    species, item, tid, sid = struct.unpack_from("<HHHH", pk, 0x08)
    iv32, = struct.unpack_from("<I", pk, 0x38)
    ok = pk4_checksum(pk) == struct.unpack_from("<H", pk, 6)[0]
    lines += [
        "Pokemon:",
        f"    Nickname:  {decode_text(pk[0x48:0x5E])}  (species #{species}, Lv. {pk[0x84] & 0x7F})",
        f"    OT:        {decode_text(pk[0x68:0x78])}  TID {tid:05d}  SID {sid:05d}",
        f"    PID:       {pid:#010x}  nature {NATURES[pid % 25]}  shiny {is_shiny(pid, tid, sid)}",
        f"    Item:      {item}   Ball: {pk[0x83]}   Ability: {pk[0x15]}",
        f"    Moves:     {struct.unpack_from('<4H', pk, 0x28)}  PP {tuple(pk[0x30:0x34])}",
        f"    IVs:       {[iv32 >> (5 * i) & 31 for i in range(6)]}  nicknamed {bool(iv32 >> 31)}",
        f"    Stats:     {struct.unpack_from('<6H', pk, 0x90)}",
        f"    Met:       location {struct.unpack_from('<H', pk, 0x7E)[0] + 3000}",
        f"    Encrypted: {is_encrypted_pk4(raw)}   checksum OK: {ok}",
    ]
    return "\n".join(lines)


def self_check(card, cfg):
    pk = build_pk4(cfg)
    stored = card[8:8 + PK4_PARTY_SIZE]
    assert is_encrypted_pk4(stored), "gift data should be stored encrypted"
    assert decrypt_pk4(stored) == pk, "encrypt/decrypt round trip failed"
    assert pk4_checksum(pk) == struct.unpack_from("<H", pk, 6)[0]
    assert decode_text(pk[0x48:0x5E]) == cfg["nickname"]
    assert decode_text(card[0x104:0x14C]) == cfg["title"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("-o", "--output", default="bulky.pcd", help="output .pcd path")
    parser.add_argument("--info", metavar="PCD", help="print the contents of an existing .pcd and exit")
    args = parser.parse_args(argv)

    if args.info:
        with open(args.info, "rb") as f:
            print(describe_pcd(f.read()))
        return 0

    card = build_pcd(CONFIG)
    self_check(card, CONFIG)
    with open(args.output, "wb") as f:
        f.write(card)
    print(f"Wrote {args.output} ({len(card)} bytes)\n")
    print(describe_pcd(card))
    return 0


if __name__ == "__main__":
    sys.exit(main())
