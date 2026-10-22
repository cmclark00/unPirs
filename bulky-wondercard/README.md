# Bulky the Goat: a Gen 4 Mystery Gift event

This folder has the tools to give **BULKY**, the Play2Win Games mascot, to customers'
copies of **Pokémon Diamond and Pearl** over local wireless, the same way stores ran
official Pokémon events in 2008–2010.

| File | Purpose |
|---|---|
| `make_bulky_card.py` | Builds the Wonder Card (`bulky.pcd`). Edit the `CONFIG` block to change anything. |
| `bulky.pcd` | The ready-built card (856 bytes). PKHeX can open it. |
| `patch_distro.py` | Puts any `.pcd` into a dump of the official *Deoxys 2008* distribution cart. |

Everything is plain Python 3 with no extra packages.

## Who Bulky is in the game

Diamond and Pearl can only receive Pokémon species that already exist in the game.
Mystery Gift can't add a new sprite or species to a retail cartridge. That needs a
ROM hack of each player's game. So Bulky is an existing Pokémon dressed up to match
the mascot:

| Mascot | In game |
|---|---|
| Cream, woolly goat | **Mareep** (#179), the fluffy cream sheep, nicknamed **BULKY** |
| Blue sunglasses | Holds **BlackGlasses** |
| Gold chain, VIP energy | **Cherish Ball** (the official event ball) and the **Classic Ribbon** |
| Laid-back attitude | **Relaxed** nature, always male, never shiny |
| Big horns | Knows **Headbutt**, plus ThunderShock, Cotton Spore, Thunder Wave |
| From the store | OT **P2WIN**, ID No. 00002, met at "Pokémon Event", level 10 |

The level is 10 because traded and event Pokémon won't obey a player who has no badges
if they're higher than that. Every customer gets the same Bulky: same nature, same IVs
(all 31) and the same personality value, which is how official events worked too. The
IVs have to stay fixed. If they're left blank, the game rolls new ones and clears the
nickname flag, and then BULKY would be renamed FLAAFFY when he evolves.

The `SPECIES` table also has **Tauros** and **Stantler** presets if you'd rather have
horns than wool. Change `"species"` and the moves in `CONFIG`.

The card the player sees reads:

```
BULKY from Play2Win Games!

Thanks for visiting
Play2Win Games!
Meet BULKY, the coolest goat
around. Be sure to save after
you pick him up at a Poké Mart.
```

## 1. Build the card

```sh
python3 make_bulky_card.py            # writes bulky.pcd and prints what's inside
python3 make_bulky_card.py --info bulky.pcd
```

The script checks its own output (encryption round trip, checksum, text) before
writing. To check the file independently, open `bulky.pcd` in
[PKHeX](https://github.com/kwsch/PKHeX). It should show the card and Bulky's summary.

## 2. Send it out wirelessly

You need a device that sends the Gen 4 Mystery Gift wireless signal. There are two ways.

### Option A: a patched distribution ROM on a DS (the "distro cart")

Official distribution cartridges are mask ROMs, so you can't rewrite the cart itself.
Instead you dump it, patch the dump, and run the patched ROM from a flashcart. The
flashcart then works as your distribution cart.

1. Dump the **Deoxys 2008** distribution cart. A DSi or 3DS running GodMode9i
   can dump DS cartridges. The patcher only knows this ROM
   (MD5 `cc30a203c5489440ea2315db3c791866`). Other event carts store the card in
   different places.
2. Patch it:
   ```sh
   python3 patch_distro.py DEOXYS2008.nds bulky.pcd bulky_distro.nds
   ```
   This uses the offsets from MicShadow's Wondercard Distribution Patcher. It replaces
   the Wonder Card and its two header copies, sets the language (English by default,
   `--language` for others), and sets the distribution date window to "always".
3. Copy `bulky_distro.nds` to a DS-mode flashcart (R4-style) and run it on a DS or
   DS Lite. Community reports say TWiLight Menu++ on a modded DSi or 3DS also works.
   Test this before relying on it.
4. Leave it running at the counter. Any number of customers can receive the card from
   it, one after another.

### Option B: a Linux laptop (no ROM or second DS)

[wc-beacon](https://github.com/eiskasten/wc-beacon) sends the same wireless beacons from
a PC Wi-Fi card that supports monitor mode:

```sh
sudo ./scripts/prepare-wifi.sh wlan0     # monitor mode, channel 7
sudo ./wc-beacon dist -p bulky.pcd -r en -d wlan0
```

Not every Wi-Fi chip works. A cheap USB adapter that supports injection is the usual fix.

## 3. What customers do

1. **Unlock Mystery Gift** (once per save). Go to Jubilife TV, 3rd floor. Answer the
   producer's question with `EVERYONE HAPPY` and then `WI-FI CONNECTION`.
2. On the title screen, pick **MYSTERY GIFT → Receive via Wireless Communication**
   while near the distribution DS or laptop.
3. Load the game, walk into **any Poké Mart**, and talk to the delivery person in green
   to collect Bulky. Then **save**.

Each save can receive card ID 1000 once. If you run a new event later (a different
Bulky or an item), give it a new `card_id`.

## Before going live

- **Test on one cartridge first.** The card format was checked byte by byte against
  the 247 official Gen 4 Pokémon Wonder Cards in PKHeX's event database (including
  the precomputed stats). The ROM patch offsets come from a widely used community tool.
  This hasn't been tested on real hardware yet.
- **Language matters.** An English distribution only reaches English games. Run the
  patcher once per language if needed.
- **Platinum and HeartGold/SoulSilver** can receive it too. Add `"platinum"`,
  `"heartgold"` and `"soulsilver"` to `games` in `CONFIG` and rebuild.
- **It's a fan event.** Bulky works normally in the game, in battles and in trades.
  Legality checkers will flag him because he isn't an official event, so Pokémon Bank,
  Poké Transporter or competitive play may reject him.
- **Branding.** This is a fan-made gift using Nintendo and Game Freak's games. Check
  how you advertise it, and don't present it as an official Pokémon event.

## References

- PKHeX: `PCD.cs`, `PGT.cs`, `PK4.cs` and `PokeCrypto.cs` for the Wonder Card and
  Pokémon layouts and encryption.
- [wc-beacon](https://github.com/eiskasten/wc-beacon) for the Wonder Card fields
  (icons, share limit, date received) and the wireless protocol notes.
- [WCDPatcher](https://github.com/Wokann/GEN4_WCDPatcher_CHS) for the Deoxys 2008
  distribution ROM offsets.
