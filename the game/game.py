#!/usr/bin/env python3
"""
PIKA QUEST  —  A Pokemon GBC-style adventure
Inspired by the visual aesthetics of Pokemon Yellow & Pokemon Silver

Controls:
  Arrow keys / WASD   —  Move
  Enter  / Space / Z  —  Interact with NPCs and read signs
  Escape              —  Quit
"""

import pygame, sys, random
pygame.init()

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
T    = 32        # pixels per tile
MW   = 40        # map width  in tiles
MH   = 36        # map height in tiles
SW   = 640       # screen width  (20 tiles)
SH   = 576       # screen height (18 tiles)
FPS  = 60
SPD  = 4         # walk pixels per frame

# ── Outdoor tile IDs ──────────────────────────────────────────────────────────
G=0; PT=1; WT=2; TR=3; WA=4; TG=5; FL=6; SD=7
SOLID = {WT, TR, WA}

# ── Interior tile IDs ─────────────────────────────────────────────────────────
IF_FLOOR    = 0   # walkable floor
IF_WALL     = 1   # solid wall
IF_COUNTER  = 2   # solid counter / desk
IF_MAT      = 3   # walkable coloured mat
IF_EXIT     = 4   # exit warp tile (walkable — stepping on it warps you out)
IF_PLANT    = 5   # solid decorative plant
IF_SHELF    = 6   # solid bookshelf
IF_TABLE    = 7   # solid table
IF_DOORWALL = 8   # wall tile that shows a door opening visual

IF_SOLID = {IF_WALL, IF_COUNTER, IF_PLANT, IF_SHELF, IF_TABLE, IF_DOORWALL}

# ─────────────────────────────────────────────────────────────────────────────
# GBC COLOUR PALETTE  (outdoor)
# ─────────────────────────────────────────────────────────────────────────────
cGR1=(136,192, 56); cGR2=( 96,152, 24)
cPT1=(216,200,152); cPT2=(184,160,104)
cWT1=( 96,168,232); cWT2=( 56,120,192)
cTR1=( 72,136, 24); cTR2=( 48, 88,  8); cTRK=(128,88,40)
cSD1=(232,208,144); cSD2=(200,168, 96)
cTG1=( 80,136, 32); cTG2=( 48, 96, 16)
cFL1=(248,224, 64); cFL2=(248, 80, 64)
cWL1=(208,200,184); cWL2=(136,128,112)
cR1 =(216, 88, 64); cR2 =(168, 48, 32)
cR3 =( 80,128,200); cR4 =( 48, 88,160)
cR5 =( 80,160, 80); cR6 =( 48,112, 48)
cDR1=(160,112, 56); cDR2=(104, 64, 16)
cWN1=(168,216,248); cWN2=(200,232,255)
cSN1=(240,216, 72); cSN2=(160,128, 24)
cSK =(240,200,160); cHR =( 80, 56, 24)
cCP =(208, 56, 48); cBRM=(248,248,248)
cPSH=(208, 56, 48); cPN =( 64, 88,168)
cSHO=( 64, 48, 24); cBLT=(176,136, 72)
cUIBG=(248,248,248); cUIBD=(32,32,32); cUIGY=(168,168,168)
cBLK=(  8, 16, 24); cWHT=(248,248,248)
cTBG=( 16, 32, 64); cTYL=(248,208, 48)

# Interior palette
iFL1=(224,192,144); iFL2=(192,160,112)
iWL1=(152,136,112); iWL2=(112, 96, 72)
iCN1=(152,104, 48); iCN2=(104, 64, 24)
iPL1=( 80,160, 40); iPL2=( 48,112, 16)
iTB1=(168,120, 64)

# NPC palettes  (shirt, pants, hair)
NPC_PAL = [
    (( 80,160, 80), ( 64, 88,168), ( 80, 56, 24)),   # 0 green
    ((200, 80,200), ( 40, 40, 40), (160, 96, 32)),   # 1 purple
    (( 80,160,200), (100, 72, 32), ( 24, 24, 24)),   # 2 blue
    ((248,176, 48), (112, 80, 32), ( 80,120,200)),   # 3 yellow
    ((248,248,248), (248,160,184), (248,160,184)),   # 4 Nurse Joy (white/pink)
    (( 56,104,192), ( 32, 64,144), ( 40, 32, 16)),   # 5 Mart Clerk (blue uniform)
    ((160,120, 72), ( 96, 72, 40), ( 24, 16,  8)),   # 6 Brock (brown/dark)
    ((176,136, 80), ( 72, 88,168), (144, 80, 32)),   # 7 House resident
]

# ─────────────────────────────────────────────────────────────────────────────
# OUTDOOR WORLD DATA
# ─────────────────────────────────────────────────────────────────────────────
BUILDINGS = [
    {"x": 4,"y": 3,"w":6,"h":4,"dx": 7,"dy": 6,"roof":"r","lbl":"POKEMON CENTER"},
    {"x":13,"y": 3,"w":5,"h":3,"dx":15,"dy": 5,"roof":"g","lbl":"POKE MART"},
    {"x":27,"y": 3,"w":6,"h":5,"dx":30,"dy": 7,"roof":"b","lbl":"PALLET GYM"},
    {"x": 4,"y":10,"w":4,"h":3,"dx": 6,"dy":12,"roof":"r","lbl":""},
    {"x":11,"y":10,"w":4,"h":3,"dx":13,"dy":12,"roof":"r","lbl":""},
    {"x":24,"y":10,"w":4,"h":3,"dx":26,"dy":12,"roof":"g","lbl":""},
]

SIGN_DATA = [
    {"tx":18,"ty":15,"pages":["PALLET TOWN","A tranquil place\nwhere Pokemon\nsing at dawn.","Population: 3"]},
    {"tx": 4,"ty": 7,"pages":["POKEMON CENTER","Nurse Joy heals\nyour Pokemon\nto full health!"]},
    {"tx":13,"ty": 6,"pages":["POKE MART","Fine goods at\nfine prices!"]},
    {"tx":27,"ty": 8,"pages":["PALLET GYM","Leader: BROCK\nSpecialty: ROCK\nAll challengers\nare welcome!"]},
]

NPC_DATA = [
    {"tx": 9,"ty":14,"dir":"down","pal":0,"name":"PROF. OAK",
     "pages":["Welcome to the\nworld of Pokemon!","I am Professor\nOAK.","This is\nPALLET TOWN.","Your journey as\na Trainer begins\nright HERE!"]},
    {"tx":16,"ty":15,"dir":"left","pal":1,"name":"GIRL",
     "pages":["Tall grass is\ndangerous!","Wild Pokemon\nhide in there.","Make sure you\nhave Poke Balls!"]},
    {"tx":25,"ty":12,"dir":"up","pal":2,"name":"FISHER",
     "pages":["I love fishing\nby the lake!","I always catch\na Magikarp.","It is always\na Magikarp..."]},
    {"tx": 8,"ty":25,"dir":"right","pal":3,"name":"HIKER",
     "pages":["I have been lost\nin tall grass","for three days!","Could you show\nme the way out?"]},
]

# ─────────────────────────────────────────────────────────────────────────────
# MAP GENERATION  (outdoor)
# ─────────────────────────────────────────────────────────────────────────────
def make_map():
    m = [[G] * MW for _ in range(MH)]
    for i in range(MW):
        m[0][i] = m[1][i] = m[MH-2][i] = m[MH-1][i] = TR
    for j in range(MH):
        m[j][0] = m[j][1] = m[j][MW-2] = m[j][MW-1] = TR
    for j in range(MH):
        m[j][18] = m[j][19] = PT
    for i in range(2, MW-2):
        m[16][i] = m[17][i] = PT
    for j in range(7, 17):
        m[j][6] = m[j][7] = PT
        m[j][14] = m[j][15] = PT
    for j in range(8, 17):
        m[j][29] = m[j][30] = PT
    for tx2, ty2 in [
        (22,5),(23,5),(22,6),(35,3),(36,3),(3,18),(4,18),(3,19),
        (20,22),(21,22),(20,23),(7,28),(8,28),(7,29),(34,14),(35,14),
        (34,15),(32,20),(33,20),(5,33),(6,33),(15,33),(16,33),
    ]:
        if 2 <= ty2 < MH-2 and 2 <= tx2 < MW-2:
            m[ty2][tx2] = TR
    rng_tg = random.Random(42)
    for j in range(20, 34):
        for i in range(3, 17):
            if m[j][i] == G and rng_tg.random() < 0.65:
                m[j][i] = TG
    for j in range(13, 16):
        for i in range(21, 28):
            if m[j][i] == G and rng_tg.random() < 0.5:
                m[j][i] = TG
    for j in range(22, 32):
        for i in range(27, 39):
            m[j][i] = WT
    for j in range(21, 33):
        for i in range(25, 39):
            if m[j][i] in (G, TG):
                adj = any(
                    0 <= j+dj < MH and 0 <= i+di < MW and m[j+dj][i+di] == WT
                    for dj, di in [(-1,0),(1,0),(0,-1),(0,1)]
                )
                if adj:
                    m[j][i] = SD
    rng_fl = random.Random(999)
    for _ in range(32):
        fi = rng_fl.randint(3, MW-4); fj = rng_fl.randint(4, MH-4)
        if m[fj][fi] == G:
            m[fj][fi] = FL
    for b in BUILDINGS:
        for j in range(b["y"], b["y"] + b["h"]):
            for i in range(b["x"], b["x"] + b["w"]):
                m[j][i] = WA
        m[b["dy"]][b["dx"]] = PT
    for s in SIGN_DATA:
        m[s["ty"]][s["tx"]] = WA
    return m

# ─────────────────────────────────────────────────────────────────────────────
# OUTDOOR TILE DRAWING
# ─────────────────────────────────────────────────────────────────────────────
def dtile(surf, tile, x, y, tick=0):
    D = pygame.draw; R = pygame.Rect
    if tile == G:
        D.rect(surf, cGR1, R(x, y, T, T))
        for bx, by in ((x+6,y+8),(x+17,y+5),(x+25,y+15),(x+11,y+23),(x+28,y+21)):
            D.rect(surf, cGR2, R(bx, by, 2, 4))
    elif tile == PT:
        D.rect(surf, cPT1, R(x, y, T, T))
        D.rect(surf, cPT2, R(x, y, T, 1))
        D.rect(surf, cPT2, R(x, y, 1, T))
    elif tile == WT:
        wo = (tick // 10) % 4
        D.rect(surf, cWT1, R(x, y, T, T))
        for wy in range(y + 2 + wo * 2, y + T, 8):
            D.rect(surf, cWT2, R(x+3, wy, T-6, 2))
    elif tile == TR:
        D.rect(surf, cGR1, R(x, y, T, T))
        D.rect(surf, cTRK, R(x+12, y+20, 8, 12))
        D.ellipse(surf, cTR1, R(x+2, y+1, 28, 23))
        D.ellipse(surf, cTR2, R(x+5, y+4, 22, 14))
    elif tile == WA:
        D.rect(surf, cWL1, R(x, y, T, T))
        D.rect(surf, cWL2, R(x, y, T, 1))
        D.rect(surf, cWL2, R(x, y, 1, T))
    elif tile == TG:
        D.rect(surf, cTG1, R(x, y, T, T))
        for bx, by in ((x+4,y+3),(x+10,y+1),(x+18,y+5),(x+24,y+2),(x+13,y+15),(x+26,y+18)):
            D.rect(surf, cTG2, R(bx, by, 3, 9))
        D.rect(surf, cTG2, R(x+8, y+11, 2, 7))
    elif tile == FL:
        D.rect(surf, cGR1, R(x, y, T, T))
        for bx, by in ((x+6,y+8),(x+17,y+5),(x+25,y+15)):
            D.rect(surf, cGR2, R(bx, by, 2, 4))
        D.circle(surf, cFL1, (x+16, y+16), 5)
        D.circle(surf, (255,200,100), (x+16, y+16), 2)
        D.circle(surf, cFL2, (x+8, y+22), 3)
        D.circle(surf, (255,220,180), (x+8, y+22), 1)
    elif tile == SD:
        D.rect(surf, cSD1, R(x, y, T, T))
        for bx, by in ((x+5,y+7),(x+14,y+5),(x+22,y+13),(x+8,y+21),(x+26,y+23),(x+18,y+27)):
            D.rect(surf, cSD2, R(bx, by, 2, 2))


def draw_sign_tile(surf, x, y, fnt):
    D = pygame.draw; R = pygame.Rect
    D.rect(surf, cGR1, R(x, y, T, T))
    for bx, by in ((x+6,y+8),(x+17,y+5),(x+25,y+15)):
        D.rect(surf, cGR2, R(bx, by, 2, 4))
    D.rect(surf, (96,64,24), R(x+14, y+14, 4, 18))
    D.rect(surf, cSN1, R(x+3, y+3, 26, 14))
    D.rect(surf, cSN2, R(x+3, y+3, 26, 14), 2)
    t = fnt.render("!", True, (64,32,8))
    surf.blit(t, (x+13, y+4))


def draw_building(surf, b, sx, sy, fnt):
    D = pygame.draw; R = pygame.Rect
    bw = b["w"] * T; bh = b["h"] * T; rh = 2 * T; wh = bh - rh
    rc1, rc2 = {"r":(cR1,cR2), "g":(cR5,cR6), "b":(cR3,cR4)}[b["roof"]]
    drel = b["dx"] - b["x"]
    D.rect(surf, cWL1, R(sx, sy+rh, bw, wh))
    D.rect(surf, cWL2, R(sx, sy+rh, bw, 1))
    D.rect(surf, cWL2, R(sx, sy+rh, 1, wh))
    D.rect(surf, cWL2, R(sx+bw-1, sy+rh, 1, wh))
    for wi in range(b["w"]):
        if wi == drel:
            continue
        wx = sx + wi*T + 8; wy = sy + rh + 8
        D.rect(surf, cWN1, R(wx, wy, 16, 12))
        D.rect(surf, (32,32,32), R(wx, wy, 16, 12), 1)
        D.rect(surf, cWN2, R(wx+1, wy+1, 7, 5))
    dsx = sx + drel * T; dsy = sy + (b["dy"] - b["y"]) * T
    D.rect(surf, cDR2, R(dsx+6, dsy, 20, T))
    D.rect(surf, cDR1, R(dsx+8, dsy+2, 16, T-2))
    D.rect(surf, (32,32,32), R(dsx+6, dsy, 20, T), 1)
    D.circle(surf, (200,160,80), (dsx+16, dsy + T//2 + 2), 2)
    D.rect(surf, rc1, R(sx, sy, bw, rh))
    D.rect(surf, rc2, R(sx + bw//4, sy+4, bw//2, rh-8))
    D.rect(surf, (32,32,32), R(sx, sy, bw, rh), 2)
    if b["lbl"]:
        lbl = fnt.render(b["lbl"], True, cWHT)
        surf.blit(lbl, (sx + bw//2 - lbl.get_width()//2, sy + 6))

# ─────────────────────────────────────────────────────────────────────────────
# INTERIOR TILE DRAWING
# ─────────────────────────────────────────────────────────────────────────────
def draw_interior_tile(surf, tile, x, y, mat_col=(216,64,56), tick=0):
    D = pygame.draw; R = pygame.Rect

    if tile == IF_FLOOR:
        D.rect(surf, iFL1, R(x, y, T, T))
        D.rect(surf, iFL2, R(x, y+10, T, 2))
        D.rect(surf, iFL2, R(x, y+22, T, 2))

    elif tile == IF_WALL:
        D.rect(surf, iWL1, R(x, y, T, T))
        D.rect(surf, iWL2, R(x, y, T, 2))
        D.rect(surf, iWL2, R(x, y, 2, T))
        D.rect(surf, iWL2, R(x+4, y+10, T-8, 2))
        D.rect(surf, iWL2, R(x+18, y+16, 2, T-18))

    elif tile == IF_COUNTER:
        D.rect(surf, iCN1, R(x, y, T, T))
        D.rect(surf, iCN2, R(x, y, T, 3))
        D.rect(surf, iCN2, R(x, y, 2, T))
        D.rect(surf, (176,128,72), R(x+4, y+8, T-8, T-12))
        D.rect(surf, iCN2, R(x+4, y+8, T-8, T-12), 1)

    elif tile == IF_MAT:
        D.rect(surf, iFL1, R(x, y, T, T))
        D.rect(surf, mat_col, R(x+3, y+3, T-6, T-6))
        D.rect(surf, (0,0,0), R(x+3, y+3, T-6, T-6), 1)
        dk = tuple(max(0, c-50) for c in mat_col)
        D.rect(surf, dk, R(x+3, y+T//2-1, T-6, 2))
        D.rect(surf, dk, R(x+T//2-1, y+3, 2, T-6))

    elif tile == IF_EXIT:
        D.rect(surf, iFL1, R(x, y, T, T))
        D.rect(surf, (200,160,100), R(x+3, y+3, T-6, T-6))
        D.rect(surf, (152,112,56), R(x+3, y+3, T-6, T-6), 1)
        # Down arrows suggesting exit
        pygame.draw.polygon(surf, (100,64,16),
                            [(x+16,y+20),(x+10,y+12),(x+22,y+12)])
        pygame.draw.polygon(surf, (100,64,16),
                            [(x+16,y+27),(x+10,y+19),(x+22,y+19)])

    elif tile == IF_PLANT:
        D.rect(surf, iFL1, R(x, y, T, T))
        D.rect(surf, (160,104,48), R(x+10, y+20, 12, 10))
        D.rect(surf, (120,72,24), R(x+8, y+18, 16, 4))
        D.circle(surf, iPL1, (x+16, y+11), 10)
        D.circle(surf, iPL2, (x+16, y+11), 6)
        D.circle(surf, iPL1, (x+10, y+14), 7)
        D.circle(surf, iPL1, (x+22, y+14), 7)

    elif tile == IF_SHELF:
        D.rect(surf, (136,96,48), R(x, y, T, T))
        D.rect(surf, (80,48,16), R(x, y, T, 2))
        D.rect(surf, (80,48,16), R(x, y, 2, T))
        book_cols = [(208,56,48),(56,104,200),(72,160,72),(240,200,40),(176,72,192)]
        for bi, bc in enumerate(book_cols):
            bx2 = x + 2 + bi*6
            D.rect(surf, bc, R(bx2, y+4, 5, 24))
            D.rect(surf, (0,0,0), R(bx2, y+4, 5, 24), 1)

    elif tile == IF_TABLE:
        D.rect(surf, iFL1, R(x, y, T, T))
        D.rect(surf, iTB1, R(x+4, y+4, T-8, T-8))
        D.rect(surf, iCN2, R(x+4, y+4, T-8, T-8), 1)
        D.rect(surf, iCN2, R(x+5, y+22, 4, 8))
        D.rect(surf, iCN2, R(x+23, y+22, 4, 8))

    elif tile == IF_DOORWALL:
        D.rect(surf, iWL1, R(x, y, T, T))
        D.rect(surf, iWL2, R(x, y, T, 2))
        D.rect(surf, cDR2, R(x+6, y, 20, T))
        D.rect(surf, cDR1, R(x+8, y+2, 16, T-2))
        D.rect(surf, (32,32,32), R(x+6, y, 20, T), 1)
        D.circle(surf, (200,160,80), (x+16, y + T//2 + 2), 2)

# ─────────────────────────────────────────────────────────────────────────────
# INTERIOR ROOM DEFINITIONS
# ─────────────────────────────────────────────────────────────────────────────
def _build_room(name, tile_rows, mat_col, player_start, exit_tile, npc_defs):
    """Create a room dict from a 2-D tile list and NPC definitions."""
    from copy import deepcopy
    npcs = []
    for d in npc_defs:
        npcs.append({
            "tx": d["tx"], "ty": d["ty"], "dir": d["dir"],
            "pal": d["pal"], "name": d["name"], "pages": d["pages"],
        })
    return {
        "name":         name,
        "tiles":        tile_rows,
        "w":            len(tile_rows[0]),
        "h":            len(tile_rows),
        "mat_col":      mat_col,
        "player_start": player_start,
        "exit_tile":    exit_tile,
        "npc_defs":     npcs,
    }


def _make_rooms():
    W=IF_WALL; F=IF_FLOOR; C=IF_COUNTER; M=IF_MAT
    E=IF_EXIT; P=IF_PLANT; S=IF_SHELF; Tb=IF_TABLE; D=IF_DOORWALL

    rooms = {}

    # ── 0: Pokemon Center (12×9) ──────────────────────────────────────────
    rooms[0] = _build_room(
        "POKEMON CENTER",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W,W,W],
            [W,F,F,F,F,F,F,F,F,F,F,W],
            [W,C,C,C,C,C,C,C,C,C,C,W],   # counter row — NPC placed here
            [W,F,F,P,F,F,F,F,P,F,F,W],
            [W,F,F,F,F,F,F,F,F,F,F,W],
            [W,F,M,F,F,F,F,F,M,F,F,W],
            [W,F,F,F,F,F,F,F,F,F,F,W],
            [W,F,F,F,F,E,F,F,F,F,F,W],   # exit mat
            [W,W,W,W,W,D,W,W,W,W,W,W],   # door wall
        ],
        mat_col=(216, 64, 56),     # red mat
        player_start=(5, 6),
        exit_tile=(5, 7),
        npc_defs=[{
            "tx":5,"ty":2,"dir":"down","pal":4,"name":"NURSE JOY",
            "pages":["Welcome to the\nPOKEMON CENTER!",
                     "We restore your\nPokemon to full\nhealth!",
                     "Shall we rest\nyour Pokemon?",
                     "OK! We'll take\nyour Pokemon for\na short time.",
                     "Your Pokemon\nare fighting fit!",
                     "Please come\nagain!"],
        }],
    )

    # ── 1: Poké Mart (10×8) ──────────────────────────────────────────────
    rooms[1] = _build_room(
        "POKE MART",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W],
            [W,S,S,F,F,F,F,S,S,W],
            [W,S,S,F,F,F,F,S,S,W],
            [W,C,C,C,C,C,C,C,C,W],   # counter row — NPC here
            [W,F,F,F,F,F,F,F,F,W],
            [W,F,M,F,F,F,F,M,F,W],
            [W,F,F,F,E,F,F,F,F,W],   # exit
            [W,W,W,W,D,W,W,W,W,W],
        ],
        mat_col=(64, 104, 200),    # blue mat
        player_start=(4, 5),
        exit_tile=(4, 6),
        npc_defs=[{
            "tx":4,"ty":3,"dir":"down","pal":5,"name":"CLERK",
            "pages":["Welcome to the\nPOKE MART!",
                     "How may I help\nyou today?",
                     "We stock Poke Balls,\nPotions and more!",
                     "Come back soon!"],
        }],
    )

    # ── 2: Gym (14×11) ───────────────────────────────────────────────────
    rooms[2] = _build_room(
        "PALLET GYM",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W,W,W,W,W],
            [W,F,F,F,F,F,F,F,F,F,F,F,F,W],   # NPC at (6,1)
            [W,F,M,M,M,M,M,M,M,M,M,M,F,W],
            [W,F,M,F,F,F,F,F,F,F,F,M,F,W],
            [W,F,M,F,F,F,F,F,F,F,F,M,F,W],
            [W,F,M,F,F,F,F,F,F,F,F,M,F,W],
            [W,F,M,F,F,F,F,F,F,F,F,M,F,W],
            [W,F,M,M,M,M,M,M,M,M,M,M,F,W],
            [W,F,F,F,F,F,F,F,F,F,F,F,F,W],
            [W,F,F,F,F,F,E,F,F,F,F,F,F,W],   # exit
            [W,W,W,W,W,W,D,W,W,W,W,W,W,W],
        ],
        mat_col=(168, 144, 72),    # sandy/gold mat for arena
        player_start=(6, 8),
        exit_tile=(6, 9),
        npc_defs=[{
            "tx":6,"ty":1,"dir":"down","pal":6,"name":"BROCK",
            "pages":["I am BROCK,\nGym Leader!",
                     "I train ROCK-type\nPokemon.",
                     "Rock is tough,\nresistant,\nand unyielding!",
                     "Do you dare\nchallenge me?",
                     "Come back when\nyou are ready,\nTrainer!"],
        }],
    )

    # ── 3: House 1 (10×8) ────────────────────────────────────────────────
    rooms[3] = _build_room(
        "HOUSE",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W],
            [W,S,S,F,F,F,F,F,F,W],
            [W,S,S,F,Tb,Tb,F,F,F,W],
            [W,F,F,F,Tb,Tb,F,F,F,W],
            [W,F,F,F,F,F,F,F,F,W],
            [W,F,M,M,F,F,F,F,F,W],
            [W,F,F,F,F,E,F,F,F,W],
            [W,W,W,W,W,D,W,W,W,W],
        ],
        mat_col=(80, 160, 80),     # green mat
        player_start=(4, 5),
        exit_tile=(4, 6),
        npc_defs=[{
            "tx":2,"ty":3,"dir":"right","pal":7,"name":"OLD MAN",
            "pages":["Ah, a visitor!",
                     "I have lived here\nmy whole life.",
                     "Legend says a\nrare Pokemon\nlives in our lake.",
                     "Nobody has ever\ncaught it though.",
                     "Maybe you will\nbe the first!"],
        }],
    )

    # ── 4: House 2 (10×8) ────────────────────────────────────────────────
    rooms[4] = _build_room(
        "HOUSE",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W],
            [W,F,F,F,F,F,S,S,F,W],
            [W,F,Tb,Tb,F,F,S,S,F,W],
            [W,F,Tb,Tb,F,F,F,F,F,W],
            [W,F,F,F,F,F,F,F,F,W],
            [W,F,F,F,F,M,M,F,F,W],
            [W,F,F,F,F,E,F,F,F,W],
            [W,W,W,W,W,D,W,W,W,W],
        ],
        mat_col=(200, 80, 200),    # purple mat
        player_start=(4, 5),
        exit_tile=(4, 6),
        npc_defs=[{
            "tx":6,"ty":2,"dir":"left","pal":1,"name":"WOMAN",
            "pages":["Oh, hello!",
                     "I make the best\nOran Berry pie\nin Pallet Town!",
                     "Have you visited\nPROF. OAK yet?",
                     "He knows all\nabout Pokemon!"],
        }],
    )

    # ── 5: House 3 (10×8) ────────────────────────────────────────────────
    rooms[5] = _build_room(
        "HOUSE",
        tile_rows=[
            [W,W,W,W,W,W,W,W,W,W],
            [W,F,F,F,F,F,F,S,S,W],
            [W,F,F,F,F,F,F,S,S,W],
            [W,F,F,Tb,Tb,F,F,F,F,W],
            [W,F,F,Tb,Tb,F,F,F,F,W],
            [W,M,M,F,F,F,F,F,F,W],
            [W,F,F,F,F,E,F,F,F,W],
            [W,W,W,W,W,D,W,W,W,W],
        ],
        mat_col=(248, 176, 48),    # yellow mat
        player_start=(4, 5),
        exit_tile=(4, 6),
        npc_defs=[{
            "tx":4,"ty":3,"dir":"down","pal":3,"name":"KID",
            "pages":["I want to be\na Pokemon Trainer!",
                     "But Mom says I\nhave to finish\nmy homework first.",
                     "Do you have any\nPokemon yet?",
                     "So lucky!"],
        }],
    )

    return rooms


ROOMS = _make_rooms()

# ─────────────────────────────────────────────────────────────────────────────
# CHARACTER DRAWING
# ─────────────────────────────────────────────────────────────────────────────
def draw_char(surf, x, y, direction, wframe, sh, pn, hr, is_player):
    D = pygame.draw

    def rc(col, ox, oy, w, h):
        D.rect(surf, col, pygame.Rect(x+ox, y+oy, w, h))

    ll = lr = 0
    if wframe == 1: ll, lr = -2,  2
    elif wframe == 2: ll, lr =  2, -2

    if direction in ("down", "up"):
        back = (direction == "up")
        rc(cSHO,  8, 28+ll, 7, 3)
        rc(cSHO, 17, 28+lr, 7, 3)
        rc(pn,  8, 23+ll, 7, 5)
        rc(pn, 17, 23+lr, 7, 5)
        rc(cBLT, 8, 22, 16, 2)
        rc(sh,  4, 14, 5, 7)
        rc(sh, 23, 14, 5, 7)
        rc(sh,  8, 14, 16, 9)
        rc(cSK,  4, 20, 4, 3)
        rc(cSK, 24, 20, 4, 3)
        rc(cSK, 13, 12, 6, 3)
        if back:
            rc(hr,  9, 4, 14, 10)
            rc(hr, 10, 3, 12,  2)
        else:
            rc(cSK, 10, 9, 12, 7)
            rc(hr, 12, 12, 2, 2)
            rc(hr, 18, 12, 2, 2)
            rc(hr,  8, 10, 3, 3)
            rc(hr, 21, 10, 3, 3)
        if is_player:
            rc(cCP,   9, 2, 14, 8)
            rc(cCP,  10, 1, 12, 2)
            rc(cBRM,  7, 9, 18, 2)
        else:
            rc(hr,  9, 4, 14, 7)
            rc(hr, 10, 3, 12, 2)

    elif direction in ("left", "right"):
        fr = (direction == "right")
        rc(cSHO, 9, 28, 14, 3)
        rc(pn, 9, 22, 14, 6)
        rc(cBLT, 9, 21, 14, 2)
        rc(sh, 9, 13, 14, 8)
        fa_ox = 22 if fr else 3; ba_ox = 3 if fr else 22
        rc(sh,  fa_ox, 13+ll, 5, 8)
        rc(cSK, fa_ox, 20+ll, 4, 3)
        rc(sh, ba_ox, 15, 5, 6)
        face_ox = 12 if fr else 8
        rc(cSK, face_ox, 8, 12, 8)
        nose_ox = 22 if fr else 8
        rc(cSK, nose_ox, 12, 2, 2)
        eye_ox = 18 if fr else 11
        rc(hr, eye_ox, 12, 2, 2)
        if is_player:
            cap_ox = 10 if fr else 8
            rc(cCP, cap_ox, 2, 14, 8)
            brim_ox = 9 if fr else 5; brim_w = 16 if fr else 17
            rc(cBRM, brim_ox, 9, brim_w, 2)
        else:
            rc(hr, 9 if fr else 8, 3, 14, 8)

# ─────────────────────────────────────────────────────────────────────────────
# DIALOG BOX
# ─────────────────────────────────────────────────────────────────────────────
class Dialog:
    H = 128

    def __init__(self, fnt, sfnt):
        self.fnt = fnt; self.sfnt = sfnt
        self.active = False; self.pages = []; self.page = 0
        self.cidx = 0; self.done = False; self.spk = ""; self.timer = 0

    def show(self, pages, speaker=""):
        self.pages = pages; self.page = 0; self.cidx = 0
        self.done = False; self.spk = speaker; self.active = True; self.timer = 0

    def update(self):
        if not self.active: return
        self.timer += 1
        if not self.done and self.timer % 2 == 0:
            self.cidx += 1
            if self.cidx >= len(self.pages[self.page]):
                self.cidx = len(self.pages[self.page]); self.done = True

    def advance(self):
        if not self.active: return
        if not self.done:
            self.cidx = len(self.pages[self.page]); self.done = True
        else:
            self.page += 1
            if self.page >= len(self.pages): self.active = False
            else: self.cidx = 0; self.done = False

    def draw(self, surf):
        if not self.active: return
        bx, by = 0, SH - self.H; bw, bh = SW, self.H
        pygame.draw.rect(surf, cUIBG, (bx, by, bw, bh))
        pygame.draw.rect(surf, cUIBD, (bx, by, bw, bh), 4)
        pygame.draw.rect(surf, cUIGY, (bx+4, by+4, bw-8, bh-8), 2)
        if self.spk:
            tw = self.fnt.size(self.spk)[0] + 16
            pygame.draw.rect(surf, cUIBD, (bx+12, by-26, tw, 26))
            pygame.draw.rect(surf, cUIBG, (bx+14, by-24, tw-4, 22))
            surf.blit(self.fnt.render(self.spk, True, cUIBD), (bx+20, by-22))
        visible = self.pages[self.page][:self.cidx]; tx2, ty2 = bx+18, by+14
        for ln in visible.split("\n"):
            surf.blit(self.fnt.render(ln, True, cUIBD), (tx2, ty2)); ty2 += 24
        if self.done and (pygame.time.get_ticks() // 350) % 2 == 0:
            pygame.draw.polygon(surf, cUIBD,
                [(SW-26, SH-26), (SW-12, SH-26), (SW-19, SH-12)])
        surf.blit(self.sfnt.render(f"{self.page+1}/{len(self.pages)}", True, cUIGY),
                  (SW-48, by+6))

# ─────────────────────────────────────────────────────────────────────────────
# PLAYER
# ─────────────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, tx, ty):
        self.tx = tx; self.ty = ty
        self.px = tx * T; self.py = ty * T
        self.dtx = tx; self.dty = ty
        self.moving = False; self.prog = 0
        self.dir = "down"; self.steps = 0; self.wf = 0
        self.just_arrived = False   # True for exactly one frame after a step completes

    def move(self, dx, dy, tmap, npct, solid_set=None):
        if self.moving: return
        if solid_set is None: solid_set = SOLID
        nx, ny = self.tx + dx, self.ty + dy
        if dx > 0:   self.dir = "right"
        elif dx < 0: self.dir = "left"
        elif dy > 0: self.dir = "down"
        elif dy < 0: self.dir = "up"
        if (0 <= nx < len(tmap[0]) and 0 <= ny < len(tmap)
                and tmap[ny][nx] not in solid_set
                and (nx, ny) not in npct):
            self.dtx = nx; self.dty = ny; self.moving = True; self.prog = 0

    def update(self):
        self.just_arrived = False
        if not self.moving: return
        self.prog += SPD
        dx, dy = self.dtx - self.tx, self.dty - self.ty
        self.px = self.tx * T + dx * self.prog
        self.py = self.ty * T + dy * self.prog
        half = T // 2
        self.wf = (1 if self.steps % 2 == 0 else 2) if self.prog <= half else \
                  (2 if self.steps % 2 == 0 else 1)
        if self.prog >= T:
            self.tx = self.dtx; self.ty = self.dty
            self.px = self.tx * T; self.py = self.ty * T
            self.moving = False; self.prog = 0
            self.steps += 1; self.wf = 0
            self.just_arrived = True

    def draw(self, surf, ox, oy):
        draw_char(surf, ox + self.px, oy + self.py, self.dir, self.wf,
                  cPSH, cPN, cHR, is_player=True)

# ─────────────────────────────────────────────────────────────────────────────
# NPC
# ─────────────────────────────────────────────────────────────────────────────
class NPC:
    def __init__(self, d):
        self.tx = d["tx"]; self.ty = d["ty"]
        self.px = self.tx * T; self.py = self.ty * T
        self.dir = d["dir"]
        self.sh, self.pn, self.hr = NPC_PAL[d["pal"]]
        self.pages = d["pages"]; self.name = d["name"]

    def face(self, player):
        dx = player.tx - self.tx; dy = player.ty - self.ty
        if abs(dx) >= abs(dy): self.dir = "right" if dx > 0 else "left"
        else: self.dir = "down" if dy > 0 else "up"

    def draw(self, surf, ox, oy):
        draw_char(surf, ox + self.px, oy + self.py, self.dir, 0,
                  self.sh, self.pn, self.hr, is_player=False)

# ─────────────────────────────────────────────────────────────────────────────
# CAMERA  (outdoor only — interiors are centred statically)
# ─────────────────────────────────────────────────────────────────────────────
class Camera:
    def __init__(self): self.x = self.y = 0.0
    def update(self, p):
        self.x = max(0.0, min(float(p.px) - SW/2 + T/2, float(MW*T - SW)))
        self.y = max(0.0, min(float(p.py) - SH/2 + T/2, float(MH*T - SH)))

# ─────────────────────────────────────────────────────────────────────────────
# TITLE SCREEN
# ─────────────────────────────────────────────────────────────────────────────
def draw_title(surf, tick):
    surf.fill(cTBG)
    rng = random.Random(7)
    for _ in range(90):
        br = rng.choice([140, 180, 220, 255]); sz = rng.choice([1, 1, 2])
        pygame.draw.rect(surf, (br,br,br), (rng.randint(0,SW), rng.randint(0,SH-160), sz, sz))
    pygame.draw.rect(surf, (80,128,16),  (0, SH-100, SW, 100))
    pygame.draw.rect(surf, (96,152,24),  (0, SH-108, SW, 10))
    pygame.draw.rect(surf, cPT1,         (SW//2-36, SH-108, 72, 108))
    for tx2 in (50, 130, 220, 380, 470, 560):
        pygame.draw.rect(surf, cTRK, (tx2+6, SH-100, 10, 28))
        pygame.draw.ellipse(surf, cTR1, (tx2-4, SH-120, 28, 26))
        pygame.draw.ellipse(surf, cTR2, (tx2, SH-116, 20, 18))
    draw_char(surf, SW//2-16, SH-170, "down", (tick//12)%3, cPSH, cPN, cHR, True)
    lw, lh = 360, 72; lx, ly = SW//2 - lw//2, 50
    pygame.draw.rect(surf, cBLK, (lx+4, ly+4, lw, lh))
    pygame.draw.rect(surf, cTYL, (lx, ly, lw, lh))
    pygame.draw.rect(surf, (192,152,24), (lx, ly, lw, lh), 3)
    fB = pygame.font.SysFont("monospace", 46, bold=True)
    fS = pygame.font.SysFont("monospace", 14, bold=True)
    fE = pygame.font.SysFont("monospace", 17, bold=True)
    fC = pygame.font.SysFont("monospace", 10)
    sh = fB.render("PIKA QUEST", True, (80,60,0))
    tx_s = fB.render("PIKA QUEST", True, (32,16,0))
    surf.blit(sh,   (lx + lw//2 - sh.get_width()//2   + 3, ly + lh//2 - sh.get_height()//2   + 3))
    surf.blit(tx_s, (lx + lw//2 - tx_s.get_width()//2,     ly + lh//2 - tx_s.get_height()//2))
    sub = fS.render("A Pokemon GBC-style Adventure", True, (248,240,180))
    surf.blit(sub, (SW//2 - sub.get_width()//2, ly + lh + 10))
    ctrl = fC.render("Arrow Keys / WASD = Move    Enter / Space = Talk    Esc = Quit", True, (140,160,200))
    surf.blit(ctrl, (SW//2 - ctrl.get_width()//2, ly + lh + 32))
    if (tick // 28) % 2 == 0:
        et = fE.render("> PRESS ENTER TO START <", True, (248,248,200))
        surf.blit(et, (SW//2 - et.get_width()//2, SH - 54))
    ct = fC.render("(c) 2026  PIKA QUEST  --  Built with Python & Pygame", True, (80,100,140))
    surf.blit(ct, (SW//2 - ct.get_width()//2, SH - 16))

# ─────────────────────────────────────────────────────────────────────────────
# HUD
# ─────────────────────────────────────────────────────────────────────────────
_hud_msg = ""; _hud_t = 0

def set_hud(msg, dur=200):
    global _hud_msg, _hud_t
    _hud_msg = msg; _hud_t = dur

def draw_hud(surf, fnt):
    global _hud_t
    if _hud_t <= 0: return
    _hud_t -= 1
    tw = fnt.size(_hud_msg)[0] + 20; hx = SW//2 - tw//2
    bg = pygame.Surface((tw, 26)); bg.set_alpha(210); bg.fill((24,32,40))
    surf.blit(bg, (hx, 6))
    pygame.draw.rect(surf, cTYL, (hx, 6, tw, 26), 2)
    surf.blit(fnt.render(_hud_msg, True, (248,240,180)), (hx+10, 10))

# ─────────────────────────────────────────────────────────────────────────────
# GAME
# ─────────────────────────────────────────────────────────────────────────────
FADE_SPEED = 14      # alpha steps per frame during fade
DOOR_TILES = {(b["dx"], b["dy"]): i for i, b in enumerate(BUILDINGS)}


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SW, SH))
        pygame.display.set_caption("PIKA QUEST  —  A Pokemon GBC-style Adventure")
        self.clock = pygame.time.Clock()
        self.tick  = 0
        self.state = "title"       # "title" | "play" | "interior" | "fading"

        # Outdoor world
        self.tilemap  = make_map()
        self.out_npcs = [NPC(d) for d in NPC_DATA]
        self.out_npct = {(n.tx, n.ty) for n in self.out_npcs}
        self.stiles   = {(s["tx"], s["ty"]): s for s in SIGN_DATA}

        # Interior state
        self.current_room     = None    # currently loaded room dict
        self.current_bldg_idx = None    # which BUILDINGS entry we entered
        self.room_npcs        = []      # NPC objects for current room

        # Fade / warp
        self.fade_alpha   = 0
        self.fade_dir     = 0    # +1 = going dark,  -1 = going bright
        self.fade_dest    = ""   # "interior" or "play"
        self.pending_room = None

        # Entities
        self.player = Player(19, 14)
        self.cam    = Camera()
        self.cam.update(self.player)

        # Fonts
        self.fnt_dlg = pygame.font.SysFont("monospace", 15, bold=True)
        self.fnt_sm  = pygame.font.SysFont("monospace", 11)
        self.fnt_bld = pygame.font.SysFont("monospace",  9, bold=True)
        self.fnt_hud = pygame.font.SysFont("monospace", 13, bold=True)

        self.dlg = Dialog(self.fnt_dlg, self.fnt_sm)
        set_hud("PALLET TOWN", 240)

    # ── Helpers ────────────────────────────────────────────────────────────
    def _room_offset(self):
        """Screen pixel offset (ox, oy) to centre the current interior room."""
        r = self.current_room
        return (SW - r["w"] * T) // 2, (SH - r["h"] * T) // 2

    def _room_npct(self):
        return {(n.tx, n.ty) for n in self.room_npcs}

    # ── Warp logic ─────────────────────────────────────────────────────────
    def _start_fade(self, dest, pending_room=None):
        """Begin fade-out.  dest is 'interior' or 'play'."""
        self.fade_dir   = 1
        self.fade_alpha = 0
        self.fade_dest  = dest
        self.pending_room = pending_room
        self.state = "fading"

    def _execute_warp(self):
        if self.fade_dest == "interior":
            idx  = self.pending_room
            room = ROOMS[idx]
            self.current_room     = room
            self.current_bldg_idx = idx
            self.room_npcs = [NPC(d) for d in room["npc_defs"]]
            sx, sy = room["player_start"]
            self.player.tx = sx; self.player.ty = sy
            self.player.px = sx * T; self.player.py = sy * T
            self.player.dtx = sx; self.player.dty = sy
            self.player.moving = False; self.player.wf = 0
            self.player.dir = "down"
            set_hud(room["name"], 180)

        else:   # back to town
            b   = BUILDINGS[self.current_bldg_idx]
            tx2 = b["dx"]; ty2 = b["dy"] + 1   # one tile south of the door
            self.player.tx = tx2; self.player.ty = ty2
            self.player.px = tx2 * T; self.player.py = ty2 * T
            self.player.dtx = tx2; self.player.dty = ty2
            self.player.moving = False; self.player.wf = 0
            self.player.dir = "down"
            self.current_room     = None
            self.current_bldg_idx = None
            self.room_npcs        = []
            self.cam.update(self.player)
            set_hud("PALLET TOWN", 180)

    # ── Main loop ──────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.tick += 1
            self._events()
            self._update()
            self._draw()
            self.clock.tick(FPS)

    # ── Events ─────────────────────────────────────────────────────────────
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if self.state == "title":
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "play"
                elif self.state in ("play", "interior"):
                    if ev.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z):
                        if self.dlg.active: self.dlg.advance()
                        else: self._interact()

    # ── Interaction ────────────────────────────────────────────────────────
    def _interact(self):
        dmap = {"down":(0,1),"up":(0,-1),"left":(-1,0),"right":(1,0)}
        dx, dy = dmap[self.player.dir]
        fx, fy = self.player.tx + dx, self.player.ty + dy

        if self.state == "interior":
            for npc in self.room_npcs:
                if npc.tx == fx and npc.ty == fy:
                    npc.face(self.player); self.dlg.show(npc.pages, npc.name); return
            return

        # Outdoor
        for npc in self.out_npcs:
            if npc.tx == fx and npc.ty == fy:
                npc.face(self.player); self.dlg.show(npc.pages, npc.name); return
        if (fx, fy) in self.stiles:
            s = self.stiles[(fx, fy)]; self.dlg.show(s["pages"], "SIGN"); return
        for b in BUILDINGS:
            if fx == b["dx"] and fy == b["dy"] and b["lbl"]:
                self.dlg.show([f"You enter\n{b['lbl']}."], ""); return

    # ── Update ─────────────────────────────────────────────────────────────
    def _update(self):
        # ── Fade / warp transition ──
        if self.state == "fading":
            if self.fade_dir == 1:          # fading out (getting darker)
                self.fade_alpha = min(255, self.fade_alpha + FADE_SPEED)
                if self.fade_alpha >= 255:
                    self._execute_warp()
                    self.fade_dir = -1      # now fade in
            elif self.fade_dir == -1:       # fading in (getting brighter)
                self.fade_alpha = max(0, self.fade_alpha - FADE_SPEED)
                if self.fade_alpha <= 0:
                    self.state = self.fade_dest
                    self.fade_dir = 0
            return

        if self.state not in ("play", "interior"):
            return

        self.dlg.update()

        if not self.dlg.active:
            if self.state == "interior":
                tmap  = self.current_room["tiles"]
                npct  = self._room_npct()
                sol   = IF_SOLID
            else:
                tmap  = self.tilemap
                npct  = self.out_npct
                sol   = SOLID

            k = pygame.key.get_pressed()
            if k[pygame.K_LEFT]  or k[pygame.K_a]: self.player.move(-1, 0, tmap, npct, sol)
            if k[pygame.K_RIGHT] or k[pygame.K_d]: self.player.move( 1, 0, tmap, npct, sol)
            if k[pygame.K_UP]    or k[pygame.K_w]: self.player.move( 0,-1, tmap, npct, sol)
            if k[pygame.K_DOWN]  or k[pygame.K_s]: self.player.move( 0, 1, tmap, npct, sol)

        self.player.update()

        # ── Warp detection (only fires the frame a step completes) ──
        if self.player.just_arrived and not self.dlg.active:
            tx, ty = self.player.tx, self.player.ty
            if self.state == "play":
                if (tx, ty) in DOOR_TILES:
                    bldg_idx = DOOR_TILES[(tx, ty)]
                    if bldg_idx in ROOMS:
                        self._start_fade("interior", pending_room=bldg_idx)
                        return
            elif self.state == "interior":
                if (tx, ty) == self.current_room["exit_tile"]:
                    self._start_fade("play")
                    return

        if self.state == "play":
            self.cam.update(self.player)

    # ── Draw ───────────────────────────────────────────────────────────────
    def _draw(self):
        if self.state == "title":
            draw_title(self.screen, self.tick)
        elif self.state in ("play", "fading") and self.current_room is None:
            self._draw_outdoor()
        elif self.state in ("interior", "fading") and self.current_room is not None:
            self._draw_interior()
        else:
            self._draw_outdoor()   # fallback during transition

        # Fade overlay
        if self.fade_dir != 0 or self.state == "fading":
            if self.fade_alpha > 0:
                fade_surf = pygame.Surface((SW, SH))
                fade_surf.set_alpha(self.fade_alpha)
                fade_surf.fill((0, 0, 0))
                self.screen.blit(fade_surf, (0, 0))

        pygame.display.flip()

    def _draw_outdoor(self):
        cx = int(self.cam.x); cy = int(self.cam.y)
        x0 = max(0, cx//T);     x1 = min(MW, x0 + SW//T + 2)
        y0 = max(0, cy//T);     y1 = min(MH, y0 + SH//T + 2)
        for tj in range(y0, y1):
            for ti in range(x0, x1):
                sx2 = ti*T - cx; sy2 = tj*T - cy
                if (ti, tj) in self.stiles:
                    draw_sign_tile(self.screen, sx2, sy2, self.fnt_bld)
                else:
                    dtile(self.screen, self.tilemap[tj][ti], sx2, sy2, self.tick)
        for b in BUILDINGS:
            bsx = b["x"]*T - cx; bsy = b["y"]*T - cy
            if -b["w"]*T < bsx < SW and -b["h"]*T < bsy < SH:
                draw_building(self.screen, b, bsx, bsy, self.fnt_bld)
        entities = [(npc.ty, "npc", npc) for npc in self.out_npcs]
        entities.append((self.player.ty, "player", self.player))
        entities.sort(key=lambda e: e[0])
        for _, kind, ent in entities:
            ent.draw(self.screen, -cx, -cy)
        self.dlg.draw(self.screen)
        draw_hud(self.screen, self.fnt_hud)

    def _draw_interior(self):
        room = self.current_room
        ox, oy = self._room_offset()

        # Dark border background
        self.screen.fill((24, 16, 8))

        # Tiles
        for tj in range(room["h"]):
            for ti in range(room["w"]):
                draw_interior_tile(self.screen, room["tiles"][tj][ti],
                                   ox + ti*T, oy + tj*T,
                                   room["mat_col"], self.tick)

        # Entities sorted by Y
        entities = [(npc.ty, "npc", npc) for npc in self.room_npcs]
        entities.append((self.player.ty, "player", self.player))
        entities.sort(key=lambda e: e[0])
        for _, kind, ent in entities:
            ent.draw(self.screen, ox, oy)

        self.dlg.draw(self.screen)
        draw_hud(self.screen, self.fnt_hud)

# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
