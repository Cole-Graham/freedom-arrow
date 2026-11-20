"""[FA] [PvE] maps (Osama 17 Nov 2026 13:0x-13:1x PST, thread 1571014792016171120): "a multiplayer scenario that has bots in it and people are
playing PVE against the Bots ... everyone joins one team", "it's a preset scenario", "option 1 add a section to our map selection that is PVE",
"make an AI PVE 1v1 2v2 and 3v3 scenario? Fighting China".

Each PvE map is an existing FA map: 1, 2 or 3 open human slots on Alpha and, from 0.9.2-dev.1, the same number of AI bot slots on Bravo
(the Workshop scenario "TEST YOUR DECK" pattern; ArrowQueue shows its "AI bot in the lobby" warning for these), every other slot locked. The map script spawns China waves for Bravo Player 1 at Bravo's ground spawns and
sends each wave to capture zones on roads, again and again; waves grow with time and with the number of players. Scoring is the normal FA
conquest. Script shape copied from vanilla Dam_Skirmish: node_player -> spawnMultiUnits.PlayerOwner, getSpMultUnData -> UnitInfo,
getTag (a type-6 tag object) -> TargetTag, then captureObj (tgz2 c-2, pathf Fast, moveAttack) for the wave's UnitGroup.
Answered by the dev.41 player logs: an empty, locked Bravo slot is not a player online, so units bought for it went to an empty Alpha slot
and stood idle. Hence the bot slots. Still untested: that the online bot slots start with 1-3 humans. The Skirmish flavor (offline
test) has bots as in every FA Skirmish flavor; offline, LocalSkirmish may swap the units spawned for a bot that has an AI deck (BALocalSkirmish.dll is carried unchanged).
"""
import copy, json, shutil, tempfile, uuid
from pathlib import Path
import common as C
import dead_center_1v1, highway_2v2, dam_3v3, klaipeda_1v1, chkalovsk_2v2, baltiisk_3v3, jelgava_1v1, dead_center_2v2, airport_5v5

# (players, base module, online base name, title, enemy specializations). Osama 13:2x PST: "I want to make sure as many specs are played in these
# scenarios. Dead center should be SF rocket". Every China specialization fights on at least one map. The base's zone weights are copied to the
# PvE names (settings.json MapZoneWeights).
# Osama 19 Nov 2026 22:3x PST (thread 1567745029781454889): "Can you make US versions and different maps? And Russia so people can play against
# their faction of choice"; names lead with the player count ("early on you need to say (1p) (2p) (3p)"). The title is the WAVES/AI_CARDS key.
BASES=[(1,dead_center_1v1,dead_center_1v1.NAME,'Dead Center vs China','PLAN Special Forces + PLARF Rocket Conscript Force'),
       (2,highway_2v2,highway_2v2.NAME,'Highway vs China','PLAGF Motorized + PLAGF Armored Force'),
       (3,dam_3v3,dam_3v3.NAME,'Dam vs China','PLAAF Air Force (airborne) + PLAGF Armored Force'),
       (1,klaipeda_1v1,klaipeda_1v1.NAME,'Klaipeda vs USA','USMC'),
       (2,chkalovsk_2v2,chkalovsk_2v2.NAME,'Chkalovsk vs USA','Stryker Cavalry regiment + Armored Brigade'),
       (3,baltiisk_3v3,baltiisk_3v3.NAME,'Baltiisk vs USA','Airborne infantry + Special Operations Forces'),
       (1,jelgava_1v1,jelgava_1v1.NAME,'Jelgava vs Russia','VDV Brigade'),
       (2,dead_center_2v2,dead_center_2v2.NAME,'Dead Center vs Russia','Motorized Infantry + Mechanized Infantry'),
       (3,airport_5v5,airport_5v5.NAME,'Airport vs Russia','Guard Tank Brigade + Coastal Troops')]
# Osama 19 Nov 2026 23:0x: "the scenario name ... gets cut off after about 20 characters": player count and enemy first, then the map.
# "[FA]" is kept (ThirdPartyGuard lists only [FA] maps); the lobby's PvE tab matches "[FA] PvE " (LobbyMapTabs.cs).
FACTION_CODE={'China':'CN','USA':'US','Russia':'RU'}
def names(players,title):
    where,enemy=title.split(' vs ')
    n=f'[FA] PvE {players}P {FACTION_CODE[enemy]} {where} 0.2';return n,n.replace(' 0.2',' Skirmish 0.2')
# Retired with the 0.2 names (bot slots on Bravo): runtime-qa Runtime.cs RetiredScenarios lists their GUIDs.
OLD_NAMES=[f'[FA] [PvE] {t} vs China ({p}P){x} 0.1' for p,t in ((1,'Dead Center'),(2,'Highway of Death'),(3,'Dam')) for x in ('',' Skirmish')]
ALL_NAMES=[x for p,_,_,t,_ in BASES for x in names(p,t)]

# China units of those specializations, default options (0.9.0-dev.36 data): unitId -> (ucat = CategoryType, [(modification, option)]).
# Ground only: the waves are capture orders, which aircraft and artillery do not fly or fire well. queued_checks.py checks every id per build.
UNITS={1166:(1,[]),1175:(1,[]),1172:(1,[]),1183:(1,[]),1192:(1,[]),1181:(1,[]),1258:(0,[(2018888,31053)]),1060:(2,[]),1061:(2,[]),
       1272:(2,[]),1261:(2,[]),909:(3,[]),1051:(3,[]),
       1205:(1,[]),1201:(0,[]),1059:(2,[]),1196:(1,[]),938:(2,[]),1163:(1,[]),1082:(2,[]),1080:(2,[(2019214,31077)]),1052:(3,[]),
       904:(2,[(2019383,31098)]),905:(2,[]),1198:(1,[]),1049:(3,[]),
       1136:(1,[]),1146:(1,[]),1257:(0,[]),1268:(2,[]),1139:(1,[]),1083:(2,[(2019401,31101)]),925:(3,[]),1143:(1,[]),906:(2,[]),1137:(1,[]),
       # AI purchase cards (default loadouts): aircraft ucat 6, helicopters 5
       943:(6,[(2016862,24458)]),975:(6,[(2016971,24479)]),1092:(6,[(2016997,24483)]),1270:(5,[(2019263,31085)]),1041:(3,[]),
       917:(6,[(2016532,24398)]),955:(6,[(2016601,24406)]),1242:(6,[(2016697,24420)]),1103:(5,[(2017279,24523)]),1033:(3,[]),
       923:(6,[(2016794,24442)]),916:(6,[(2016642,24412)]),924:(6,[(2016825,24450)]),913:(5,[(2017056,24493)]),1040:(3,[])}
# USA and Russia (Osama 19 Nov 2026 22:3x PST): base-game cards only (no DLC units), default option of each modification.
UNITS.update({4:(3,[(386, 1434)]),
       8:(5,[(128, 348), (129, 347)]),
       9:(2,[(237, 1449), (238, 624), (239, 626)]),
       10:(3,[(25, 65), (26, 67)]),
       14:(2,[(532, 1904), (575, 2041)]),
       20:(3,[(545, 1936), (33, 69)]),
       25:(2,[(424, 1528), (17, 43)]),
       27:(3,[(6, 16), (21, 55), (556, 1966)]),
       30:(2,[(9, 22), (8, 20)]),
       31:(3,[(136, 371)]),
       34:(3,[(573, 2037), (11, 26)]),
       35:(0,[(12, 28)]),
       46:(5,[(75, 208), (76, 211), (77, 213)]),
       50:(3,[(440, 1583), (36, 86)]),
       53:(2,[(46, 116), (398, 1470)]),
       54:(2,[(47, 118), (397, 1468)]),
       57:(1,[]),
       60:(1,[]),
       61:(0,[(401, 1477)]),
       62:(1,[]),
       63:(1,[(399, 1472)]),
       65:(0,[]),
       66:(1,[]),
       70:(1,[(423, 1520)]),
       72:(1,[]),
       86:(5,[(57, 166), (58, 169), (59, 171)]),
       92:(3,[(445, 1605)]),
       94:(3,[(478, 1737)]),
       99:(0,[(68, 192)]),
       108:(1,[(743, 3128)]),
       109:(1,[]),
       110:(1,[(417, 1508)]),
       111:(1,[]),
       114:(0,[]),
       116:(0,[(414, 1502)]),
       117:(1,[(571, 2030)]),
       123:(0,[]),
       126:(1,[]),
       132:(1,[(551, 1955)]),
       133:(1,[]),
       134:(1,[]),
       144:(2,[(94, 260), (562, 1985)]),
       150:(1,[(518, 1849)]),
       151:(2,[(100, 275), (589, 2089)]),
       152:(0,[(101, 277)]),
       157:(2,[(240, 628), (241, 633)]),
       158:(2,[(217, 563)]),
       168:(6,[(346, 1164), (345, 1155), (344, 1140), (120, 1137)]),
       169:(6,[(343, 1999), (342, 1125), (121, 1119)]),
       182:(2,[(451, 1620)]),
       183:(2,[(140, 380), (141, 382)]),
       207:(3,[(175, 467)]),
       209:(0,[(180, 478), (470, 1709)]),
       211:(3,[(182, 482)]),
       213:(2,[(185, 489), (390, 1450)]),
       215:(0,[(471, 1711), (188, 496)]),
       217:(0,[(192, 506), (193, 508)]),
       233:(3,[(209, 546)]),
       236:(2,[(212, 553)]),
       238:(2,[(215, 559), (216, 561)]),
       239:(2,[(218, 567)]),
       240:(2,[(219, 572), (220, 574)]),
       243:(2,[(225, 588)]),
       244:(2,[(226, 594)]),
       245:(2,[(227, 597)]),
       247:(3,[(444, 1601)]),
       249:(0,[(230, 606), (231, 608), (559, 1972)]),
       256:(5,[(248, 649), (249, 653), (395, 1463)]),
       270:(5,[(263, 700), (264, 705), (265, 707)]),
       271:(5,[(267, 712), (268, 715)]),
       277:(0,[]),
       280:(6,[(379, 1391), (378, 1388), (377, 1387)]),
       283:(6,[(293, 831), (292, 824), (294, 834)]),
       285:(6,[(301, 868), (300, 865), (299, 856), (302, 872)]),
       286:(6,[(304, 882), (303, 877)]),
       287:(6,[(308, 900), (307, 897), (306, 891), (305, 884), (543, 1929)]),
       288:(6,[(312, 951), (311, 945), (310, 939), (309, 934)]),
       291:(6,[(320, 992), (319, 989), (318, 982)]),
       292:(6,[(538, 1921), (324, 1018), (323, 1788), (322, 1864)]),
       293:(6,[(325, 1024)]),
       300:(6,[(336, 1085), (337, 1094), (541, 1925)]),
       306:(6,[(349, 1192), (348, 1182), (347, 1172)]),
       307:(6,[(353, 1225), (352, 1218), (351, 1215), (350, 1203)]),
       310:(6,[(361, 1277), (360, 1269), (359, 1266)]),
       312:(6,[(368, 1324), (367, 1319), (366, 1312), (365, 1304)]),
       317:(6,[(380, 1398)]),
       319:(6,[(384, 1424), (383, 1417), (382, 1412), (381, 1408)]),
       350:(0,[(742, 3126)]),
       351:(1,[]),
       372:(1,[(452, 1622)]),
       398:(1,[]),
       401:(1,[]),
       407:(1,[(514, 1842)]),
       408:(1,[]),
       416:(1,[]),
       449:(1,[]),
       452:(3,[(591, 2099), (547, 1945)]),
       453:(2,[(548, 1948), (549, 1950)]),
       459:(1,[(560, 1975)]),
       701:(1,[]),
       703:(2,[(806, 3323), (807, 3324)]),
       714:(0,[(2000250, 2049), (2000251, 20000)]),
       716:(2,[(2000294, 564)]),
       719:(2,[(2000351, 381), (2000352, 20008)]),
       722:(2,[(2000575, 261), (2000576, 20013)])})
# Waves for one player (unitId: count); counts are multiplied by the number of players. Minute = after the deployment pause. The last wave
# repeats every REPEAT_MINUTES.
WAVES={
 'Dead Center vs China':[(1,{1166:2,1258:1}),                                   # Conscripts, ZBD-86 Recon
                (4,{1175:2,1172:1,1060:1}),                            # Infantry, PF-98 Team, ZTZ-59
                (7,{1192:2,1061:2,1051:1}),                            # Marines, ZTZ-80, PGZ-88
                (10,{1183:1,1181:1,1261:1,1272:1,909:1})],             # Blood Wolves, Godswords, VT-5, WZ1224, PGZ-09
 'Highway vs China':[(1,{1205:2,1201:1,1059:1}),                       # Light Riflemen, Recon Patrol, PTL-02
                     (4,{1196:2,1163:1,938:1}),                        # Moto. Riflemen, Mech. Rifles, ZTL-11
                     (7,{1082:2,1080:1,1052:1}),                       # ZTZ-96A, ZTL-191, PGZ-95
                     (10,{904:1,905:1,1198:2,1049:1})],                # ZTZ-99A, ZTZ-96B, AT Troopers, HQ-17A
 'Dam vs China':[(1,{1136:1,1146:1,1257:1}),                                    # Airborne, Assault Raiders, ZBD-03 Recon
        (4,{1163:2,1139:1,1268:1}),                                    # Mech. Rifles, Tank Hunters, ZTQ-15 Light
        (7,{1082:1,1083:1,1143:1,925:1}),                              # ZTZ-96A, ZTZ-99, Thunder Gods, HQ-7B
        (10,{904:1,905:1,906:1,1137:1,1052:1})]}                       # ZTZ-99A, ZTZ-96B, ZTQ-15, HJ-12 Team, PGZ-95
WAVES.update({
 'Klaipeda vs USA':[(1, {407: 2, 99: 1}), (4, {63: 2, 30: 1, 14: 1}), (7, {70: 1, 408: 1, 53: 2, 34: 1}), (10, {54: 1, 61: 1, 63: 2, 53: 1})],
 'Chkalovsk vs USA':[(1, {701: 2, 277: 1, 35: 1}), (4, {57: 2, 25: 1, 453: 1}), (7, {245: 2, 62: 1, 20: 1}), (10, {243: 1, 244: 1, 449: 2, 27: 1})],
 'Baltiisk vs USA':[(1, {351: 1, 72: 1, 249: 1}), (4, {66: 1, 416: 1, 183: 1, 350: 1}), (7, {182: 2, 150: 1, 10: 1}), (10, {719: 2, 150: 1, 714: 1})],
 'Jelgava vs Russia':[(1, {111: 2, 152: 1}), (4, {132: 1, 108: 1, 144: 1}), (7, {111: 2, 722: 1, 109: 1, 114: 1}), (10, {151: 1, 116: 1, 722: 1, 110: 1})],
 'Dead Center vs Russia':[(1, {60: 2, 217: 1}), (4, {398: 2, 215: 1, 9: 1}), (7, {157: 2, 459: 1, 94: 1}), (10, {703: 1, 213: 1, 401: 2, 233: 1})],
 'Airport vs Russia':[(1, {133: 1, 126: 1, 209: 1}), (4, {158: 1, 240: 1, 117: 1}), (7, {236: 1, 239: 1, 134: 1, 31: 1}), (10, {238: 1, 716: 1, 372: 1, 211: 1})]})
REPEAT_MINUTES=3
# With the Lua AI: only the first wave is fixed (the opening deployment); after that the AI buys its own units. Cards it can buy, one per
# kind, each purchase = that card x number of players. ba_purchase.lua channel 1 (inputs 1-5): fighter, strike, bomber, attack helicopter,
# ground seed (rebuild when wiped out); channel 2: air defence, artillery, infantry, recon, main armour, picked by BA_MIND.scorePurchase
# from what the enemy fields and what it already has. Card cooldowns as a player's; at most AI_MAX_UNITS x players live units.
AI_CARDS={
 'Dead Center vs China':dict(ch1=[943,975,1092,1270,1175],ch2=[1051,1041,1192,1258,1061]),   # J-15, J-8D, J-7, Z-10U, Infantry | PGZ-88, PLZ-83, Marines, ZBD-86 Recon, ZTZ-80
 'Highway vs China':dict(ch1=[917,955,1242,1103,1196],ch2=[1052,1033,1196,1201,1082]),  # J-10C, J-10S, J-11D, Z-19, Moto. Riflemen | PGZ-95, PCL-09, Moto. Riflemen, Recon Patrol, ZTZ-96A
 'Dam vs China':dict(ch1=[923,916,924,913,1136],ch2=[925,1040,1136,1257,1083])}              # J-11BS, J-16, Su-30MKK, Z-10K, Airborne | HQ-7B, PLZ-70, Airborne, ZBD-03 Recon, ZTZ-99
# ch1 fighter, strike, bomber, attack helicopter, ground seed | ch2 AA, artillery, infantry, recon, main armour (as the China cards).
AI_CARDS.update({
 'Klaipeda vs USA':dict(ch1=[291, 288, 292, 86, 407],ch2=[34, 247, 407, 61, 54]),
 'Chkalovsk vs USA':dict(ch1=[285, 286, 300, 8, 701],ch2=[20, 452, 701, 65, 244]),
 'Baltiisk vs USA':dict(ch1=[283, 287, 293, 270, 351],ch2=[10, 50, 351, 350, 719]),
 'Jelgava vs Russia':dict(ch1=[169, 168, 317, 46, 111],ch2=[109, 207, 111, 114, 722]),
 'Dead Center vs Russia':dict(ch1=[310, 307, 306, 256, 60],ch2=[233, 92, 398, 123, 157]),
 'Airport vs Russia':dict(ch1=[319, 312, 280, 271, 133],ch2=[31, 4, 133, 209, 238])})
AI_MAX_UNITS=14

# Opening ASF (Osama 19 Nov 2026 23:3x): the fighter card (AI_CARDS ch1[0]) flies an air-to-air loadout. These cards are used only in that slot.
UNITS.update({291:(6,[(320,992),(319,987),(318,982)]),   # F/A-18E: 2 + 4 + 4 AIM-120
              285:(6,[(299,857),(300,860),(301,867),(302,872)]),   # F-16C: 4 + 2 AIM-120, fuel, default ECM slot
              319:(6,[(384,1422),(383,1416),(382,1411),(381,1407)])})   # Su-30SM: 4 + 2 + 2 R-77, 4 R-73
AI_CARDS['Dead Center vs China']['ch1'][0]=923   # J-11BS Light CAP instead of the J-15 (its default is CAS rockets)
# AI money is unlimited (Osama 19 Nov 2026 22:4x: "the AI gets access to everything ... no cap for points"); the live-unit cap and purchase
# intervals still apply. Random whole-faction decks were asked for too, but held back for now (Osama 22:5x: "be conservative with the decks").
TRANSPORT={57:41,60:253,62:22,63:180,66:82,70:180,72:392,75:184,108:141,109:142,110:141,111:141,112:141,117:254,119:212,122:216,126:212,127:365,130:253,132:141,133:254,134:254,146:41,150:392,351:82,353:254,370:41,372:212,398:365,399:365,401:365,407:180,408:180,416:184,419:212,449:33,459:253,701:22,1136:1228,1137:1228,1139:1228,1143:1228,1146:1228,1154:1248,1157:1248,1163:1248,1166:1230,1172:1064,1175:1064,1176:1064,1181:1230,1182:1076,1183:1076,1185:1076,1192:1076,1196:1079,1198:1079,1205:1079}
UNITS.update({22:(2,[(4, 9), (3, 7)]),
       33:(2,[(13, 31), (16, 41)]),
       41:(2,[(24, 61), (23, 59)]),
       82:(2,[(279, 754)]),
       141:(2,[(88, 244)]),
       142:(2,[(385, 1430), (590, 2091)]),
       180:(2,[(139, 377), (552, 1957)]),
       184:(0,[(142, 384)]),
       212:(2,[(183, 484), (184, 487)]),
       216:(2,[(189, 498)]),
       253:(2,[(242, 635), (244, 639)]),
       254:(2,[(245, 641), (246, 644)]),
       365:(2,[(448, 1612), (449, 1616)]),
       392:(2,[(503, 1809)]),
       1064:(2,[]),
       1076:(2,[(2018994, 31061)]),
       1079:(2,[]),
       1228:(2,[(2016080, 24360)]),
       1230:(2,[]),
       1248:(2,[])})
def opening(waves,cards=None):
    """The AI's opening deployment, as a player's first buy: waves 1 and 2 together (infantry mounted), 1 minute after the deployment pause.
    Osama 19 Nov 2026 22:4x: "opening should be moto, helo and air heavy": plus 2 attack helicopters per player; fixed-wing aircraft come from the
    purchase channel, which starts buying at 20 s (FIRST_BUY 45 -> 20)."""
    merged={}
    for _,c in waves[:2]:
        for u,n in c.items():merged[u]=merged.get(u,0)+n
    if cards:merged[cards['ch1'][3]]=merged.get(cards['ch1'][3],0)+2
    return [(1,merged)]

# ---- Lua decision AI (Osama 13:2x PST: "we should be using real AI", "Plug it into all of them but make sure they fast move and use roads").
# BrokenArrowAI (seaborndan/BrokenArrowAI 4e4e6450, the pinned checkout on the deck; NOT copied into this repo, see LICENSE NOTE) commands the
# China units: it reads the battlefield every few seconds, picks objectives, supports, flanks, pulls damaged units back and moves on roads
# (MoveToFast) for anything further than FAST_MOVE_MIN, attack-moving the last leg. The waves above stay as its reinforcements; the scripted
# capture/escort orders are left out when the AI is in, so two commanders never fight over one unit. Terrain (cover, chokepoints, overwatch)
# comes from pve_terrain/ba_terrain_<scene>.lua, baked from the game's Navigation files by its tools/bake_terrain.py.
# Changes to the pinned source, applied here so the checkout stays pristine:
# - commanders: the Bravo players (AI bot slots online from 0.9.2-dev.1, and offline), instead of IsBot only;
# - FAST_MOVE_MIN 700 -> 150 m; a unit's first order after it is called in, and any non-attack move beyond 100 m, use the roads (Osama 19 Nov 2026:
#   "sometimes when it calls in a new unit they don't use the roads").
# LICENSE NOTE: the repository has no licence file; ask the author before shipping it outside the team.
import os
AI_SRC=Path(os.environ.get('FA_PVE_AI_SRC','/home/sam/tars/work/ba-dev/replicas/codex/work/ba-tool-verification-20261102/toolkit/sources/BrokenArrowAI'))
AI_FILES=['ba_tactics.lua','ba_roles.lua','ba_doctrine.lua','ba_field.lua','ba_mind.lua','ba_brain.lua']
TERRAIN=Path(__file__).resolve().parent/'pve_terrain'
def ai_code(scene):
    """One Lua chunk: PvE flag + baked terrain + the AI modules + the commander (tools/deploy_lua.py order)."""
    parts=['BA_FA_PVE = true   -- Freedom Arrow PvE: the AI commands the Bravo players',
           (TERRAIN/f"ba_terrain_{scene.replace(' ','_')}.lua").read_text(encoding='utf-8')]
    parts+=[(AI_SRC/'ai'/f).read_text(encoding='utf-8') for f in AI_FILES]
    code='\n'.join(parts)
    old_cond="    if safe(function() return p.IsBot end, false) then\n      local uid = safe(function() return p.UID end)"
    # The Bravo players: AI bot slots online (from 0.9.2-dev.1) and offline. LuaPlayer.TeamName is the team
    # object's name ("Bravo team" in every FA map); TeamID 1 = TeamSide.Bravo is the fallback.
    new_cond=("    local fa_bravo = string.find(tostring(safe(function() return p.TeamName end, '')), 'Bravo', 1, true) ~= nil\n"
              "                     or safe(function() return p.TeamID end, -1) == 1\n"
              "    if (BA_FA_PVE and fa_bravo) or (not BA_FA_PVE and safe(function() return p.IsBot end, false)) then\n"
              "      local uid = safe(function() return p.UID end)")
    for a,b in ((old_cond,new_cond),('  FAST_MOVE_MIN   = 700,','  FAST_MOVE_MIN   = 150,'),
                ("    far = (dx * dx + dz * dz) > (CFG.FAST_MOVE_MIN * CFG.FAST_MOVE_MIN)\n",
                 "    local d2 = dx * dx + dz * dz\n"
                 "    local uid0 = safe(function() return u.UID end)\n"
                 "    BA.faFirst = BA.faFirst or {}\n"
                 "    local first = uid0 ~= nil and not BA.faFirst[uid0]\n"
                 "    if uid0 ~= nil then BA.faFirst[uid0] = true end\n"
                 "    far = d2 > (CFG.FAST_MOVE_MIN * CFG.FAST_MOVE_MIN) or (first and d2 > 2500) or (not attack and d2 > 10000)\n"
                 "    BA.faD = math.sqrt(d2)\n"),
                # Move log (Osama 19 Nov 2026 23:1x "they dont fast move"): the first 80 orders and the fast-move count, so a test log shows
                # which command each unit got.
                ("  if ok and far then BA.stats.fastMoves = (BA.stats.fastMoves or 0) + 1 end\n",
                 "  if ok and far then BA.stats.fastMoves = (BA.stats.fastMoves or 0) + 1 end\n"
                 "  BA.faLog = (BA.faLog or 0) + 1\n"
                 "  if BA.faLog <= 80 then say(string.format(\"[MOVE] %s fast=%s d=%.0f attack=%s kind=%s ok=%s\", tostring(safe(function() return u.Name end)), tostring(far), BA.faD or -1, tostring(attack), tostring(kind), tostring(ok))) end\n"),
                ('      BA.stats.orders, BA.stats.latched, BA.stats.fires, BA.stats.withdraws,',
                 '      BA.stats.orders .. " fast=" .. tostring(BA.stats.fastMoves or 0), BA.stats.latched, BA.stats.fires, BA.stats.withdraws,'),
                ('"orders=%d latched=%d','"orders=%s latched=%d')):
        assert code.count(a)==1,('BrokenArrowAI changed: '+a[:40]);code=code.replace(a,b)
    return code
def pve_header(objects,players):
    bravo=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Bravo team')
    sp=[o['pos'] for o in objects if o.get('_type')==10 and o['team']['id']==bravo and 5 not in o.get('spawnType2',[])]
    spawns=', '.join(f"{{x={q['X']:.1f}, y={q['Y']:.1f}, z={q['Z']:.1f}}}" for q in sp)
    return f'''BA_FA_PVE = true   -- Freedom Arrow PvE: the AI commands and buys for the Bravo players
BA_FA_MAX_UNITS = {AI_MAX_UNITS*players}
FA_UNLIMITED = true   -- AI money unlimited (Osama 19 Nov 2026)
BA_FA_SPAWNS = {{ {spawns} }}   -- Bravo ground spawns: purchases arrive here, as a player's do
local fa_pick = 0
function FA_SPAWN()
  fa_pick = fa_pick % #BA_FA_SPAWNS + 1
  local s = BA_FA_SPAWNS[fa_pick]
  return Vectors.CreateVector3(s.x, s.y, s.z)
end
local function fa_isbravo(p)
  local ok, n = pcall(function() return p.TeamName end)
  if ok and n ~= nil and string.find(tostring(n), 'Bravo', 1, true) ~= nil then return true end
  local ok2, t = pcall(function() return p.TeamID end)
  return ok2 and t == 1
end
function FA_IS_BRAVO(uid)
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return false end
  for _, p in pairs(ps) do
    local ok2, u = pcall(function() return p.UID end)
    if ok2 and u == uid then return fa_isbravo(p) end
  end
  return false
end
-- Budget parity: the richest human's current money.
function FA_HUMAN_MONEY()
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return 0 end
  local best = 0
  for _, p in pairs(ps) do
    if not fa_isbravo(p) then
      local ok2, m = pcall(function() return p:GetMoney() end)
      if ok2 and type(m) == 'number' and m > best then best = m end
    end
  end
  return best
end
-- The owner of the bought units: the Bravo AI players in turn (online they are bot slots, as in "TEST YOUR DECK"), so each bot in a
-- 2v2 or 3v3 gets its share. If no Bravo player is a bot, "Bravo Player 1", else the lowest Bravo UID.
local fa_turn = 0
function FA_BRAVO_UID()
  local ok, ps = pcall(function() return API.GetAllPlayers() end)
  if not ok or ps == nil then return nil end
  local bots, first, best = {{}}, nil, nil
  for _, p in pairs(ps) do
    if fa_isbravo(p) then
      local ok2, u = pcall(function() return p.UID end)
      local ok3, nm = pcall(function() return p.PlayerName end)
      local ok4, b = pcall(function() return p.IsBot end)
      if ok2 and u ~= nil then
        if ok4 and b then bots[#bots + 1] = u end
        if ok3 and nm == 'Bravo Player 1' then first = u end
        if best == nil or u < best then best = u end
      end
    end
  end
  if #bots > 0 then
    table.sort(bots)
    fa_turn = fa_turn % #bots + 1
    return bots[fa_turn]
  end
  return first or best
end
'''
PURCHASE_FILES=['ba_tactics.lua','ba_roles.lua','ba_doctrine.lua','ba_field.lua','ba_mind.lua','ba_purchase.lua']
def purchase_code(scene,header):
    parts=[header,(TERRAIN/f"ba_terrain_{scene.replace(' ','_')}.lua").read_text(encoding='utf-8')]
    parts+=[(AI_SRC/'ai'/f).read_text(encoding='utf-8') for f in PURCHASE_FILES]
    code='\n'.join(parts)
    for a,b in (('local function rallyPoint(units)\n','local function rallyPoint(units)\n  if BA_FA_SPAWNS ~= nil then return FA_SPAWN() end\n'),
                ('local function fallbackDrop(uid)\n','local function fallbackDrop(uid)\n  if BA_FA_SPAWNS ~= nil then return FA_SPAWN() end\n'),
                ('local function ownerUID(slot)\n','local function ownerUID(slot)\n  if BA_FA_PVE then return FA_BRAVO_UID() end\n'),
                ('local function isBotUID(uid)\n','local function isBotUID(uid)\n  if BA_FA_PVE then return FA_IS_BRAVO(uid) end\n'),
                ('  MAX_UNITS   = 26,','  MAX_UNITS   = BA_FA_MAX_UNITS or 26,'),
                ('  FIRST_BUY   = 45.0,','  FIRST_BUY   = 20.0,'),
                # Osama 19 Nov 2026 23:3x: "force the AI to buy ASF at the start", "at least 1 per player": the first channel-1 purchase is the
                # fighter pin (input_1, 1 x players), without waiting for an enemy-air mission; later air buys stay mission-driven.
                ('  local kind = CYCLE[((BUY.slot[slot].step - 1) % #CYCLE) + 1]\n',
                 '  local kind = CYCLE[((BUY.slot[slot].step - 1) % #CYCLE) + 1]\n'
                 '  if BA_FA_PVE and not BUY.slot[slot].faAsf then BUY.slot[slot].faAsf = true; kind = "fighter"; say(slot .. ": opening ASF (forced)") end\n'),
                # Upstream bug: tick() calls situation() before its `local function` line, so with ba_field/ba_mind loaded (the deploy
                # order its README uses) channel 1 hit a nil global and never bought. Measured with its own test_purchase.lua: 9 of 24 fail
                # with field+mind loaded, all 24 pass with this forward declaration.
                ('local function tick(slot)','local situation   -- forward declaration (see pve.py)\nlocal function tick(slot)'),
                ('local function situation(uid, team, units)','situation = function(uid, team, units)'),
                # Budget parity (the toolkit's own principle): the empty Bravo slot has no money, so channel 2 would rate every card
                # unaffordable. In PvE it is rated against the richest human's money instead; spending is still capped by the purchase
                # interval, card cooldowns and BA_FA_MAX_UNITS.
                ('  ctx.money = (type(money) == "number") and money or 0','  ctx.money = (type(money) == "number") and money or 0\n  if BA_FA_PVE then ctx.money = FA_UNLIMITED and 1000000000 or FA_HUMAN_MONEY() end')):
        assert code.count(a)==1,('BrokenArrowAI ba_purchase changed: '+a[:40]);code=code.replace(a,b)
    return code
def add_purchase(nodes,objects,scene,players,cards):
    """Two buying channels for BP1 (ba_purchase.lua Buy_BP1 / Buy2_BP1), wired as tools/inject_purchase.py does: start -> looped LuaNode,
    static payloads on input_1..5, output_1 -> spawn.UnitInfo, output_2 -> spawn.targetVec, out -> spawn.in, error -> self."""
    owner=next(o['_uid'] for o in objects if o.get('_type')==13 and o['_dname']=='Bravo Player 1')
    start=[b['id'] for b in nodes['b'] if b['nnKey']=='start'][0]
    code=purchase_code(scene,pve_header(objects,players))
    nid=max(b['id'] for b in nodes['b'])+500
    def node(key,props,x,y):
        nonlocal nid;nid+=1;nodes['b'].append({'v':0,'nnKey':key,'px':x,'py':y,'id':nid,'rtpt':True,'props_v2':props});return nid
    def wire(a,c,b,d):nodes['c'].append({'a':a,'b':b,'c':c,'d':d,'e':b})
    player=node('node_player',[p('value',f'c{owner}')],-3400.0,8000.0)
    store=node('mission_storage',[p('value','BP1'),p('actOnSt','False')],-3000.0,8000.0);wire(store,'in',player,'out')
    for k,(enter,ids) in enumerate((('Buy_BP1',cards['ch1']),('Buy2_BP1',cards['ch2']))):
        y=8300.0+k*600.0
        lua=node('LuaNode',[p('EnterMethod',enter),p('Loop','True'),p('Code',code),p('hotreload','False')],-2600.0,y)
        wire(lua,'in',start,'flow');wire(lua,'in',lua,'error')
        for i,uid in enumerate(ids):
            data=node('getSpMultUnData',[p('val',payload({uid:1},players))],-3000.0,y+100+i*60);wire(lua,f'input_{i+1}',data,'out')
        spawn=node('spawnMultiUnits',[p('TargetTag','',1),p('TargetSpawnPoint','',1),p('PlayerOwner','c0',1),p('UnitInfo','',1),
                                      p('UnitGroup',f'FAPVEBUY{k+1}'),p('CargoUnitGroup',f'FAPVEBUY{k+1}C'),p('assign','False')],-2000.0,y)
        wire(spawn,'UnitInfo',lua,'output_1');wire(spawn,'targetVec',lua,'output_2');wire(spawn,'in',lua,'out');wire(spawn,'PlayerOwner',player,'out')

def add_ai(nodes,scene):
    """start.flow -> LuaNode(AiTick, looped, code embedded so no file path is needed); its error output re-enters it."""
    start=[b['id'] for b in nodes['b'] if b['nnKey']=='start'];assert len(start)==1,start
    nid=max(b['id'] for b in nodes['b'])+1
    nodes['b'].append({'v':0,'nnKey':'LuaNode','px':-3000.0,'py':3600.0,'id':nid,'rtpt':True,'props_v2':[
        p('EnterMethod','AiTick'),p('Loop','True'),p('Code',ai_code(scene)),p('hotreload','False')]})
    nodes['c'].append({'a':nid,'b':start[0],'c':'in','d':'flow','e':start[0]})
    nodes['c'].append({'a':nid,'b':nid,'c':'in','d':'error','e':nid})
    return nid

def _unit(uid,cargos=()):
    ucat,items=UNITS[uid]
    return {'unitId':uid,'ucat':ucat,'items':[{'mod':m,'opt':o} for m,o in items],'skin':0,
            'cargo':{'totals':0,'taken':0,'totalHL':0,'takenHL':0,'cargos':list(cargos),'supply':0}}
def payload(counts,players):
    units=[]
    for uid,n in counts.items():
        for _ in range(n*players):
            units.append(_unit(TRANSPORT[uid],[_unit(uid)]) if uid in TRANSPORT else _unit(uid))
    return json.dumps({'Units':units,'TotalUnitsCount':len(units)},separators=(',',':')).replace('"','¨')

def p(k,v,t=3):return {'k':k,'v':v,'t':t}

# Doctrine (Osama 13:2x PST: "make sure the AI are pre programmed with a smart strategy", "It should play like a PVP game and get players ready
# for pvp"). Each wave is split by role into its own group, the way a player uses combined arms:
# - recon (ucat 0): takes the nearest open zone first and stays there as a forward screen;
# - infantry (ucat 1, and recon infantry): takes a zone and holds it for HOLD_SECONDS, then takes the next;
# - armour (ucat 2): overwatch: every 20 s it attack-moves to its infantry; with no infantry left it spearheads zone to zone itself;
# - air defence (ucat 3): escorts the armour every 15 s (the infantry when no armour is left).
# Scripted, not adaptive: no retreat, no artillery fire missions, no aircraft yet.
HOLD_SECONDS=120
INF_RECON={1201}   # Recon Patrol: infantry that scouts, moves with the infantry group
def role(uid):
    ucat=UNITS[uid][0]
    return 'I' if ucat==1 or uid in INF_RECON else {0:'R',2:'A',3:'S',5:'A',6:'A'}[ucat]   # helicopters in the opener (22:5x) go with the armour

def add_waves(nodes,objects,players,after,waves,orders=True):
    """after = (node id, out port) that fires when the deployment pause ends."""
    bravo=next(o['_uid'] for o in objects if o.get('_type')==3 and o['_dname']=='Bravo team')
    owner=next(o['_uid'] for o in objects if o.get('_type')==13 and o['_dname']=='Bravo Player 1')
    spawns=[o for o in objects if o.get('_type')==10 and o['team']['id']==bravo and 5 not in o.get('spawnType2',[])]
    assert spawns,'no Bravo ground spawn'
    uid=C.new_uid(objects);tags=[]
    for i,s in enumerate(spawns):
        objects.append({'info':'','noArrow':False,'color':0,'pos':copy.deepcopy(s['pos']),'rotate':copy.deepcopy(s['rotate']),
                        'scale':{'X':1.0,'Y':1.0,'Z':1.0,'SqrMagnitude':3.0},'v':1,'_uid':uid+i,'_type':6,'_dname':f'PVE spawn {i+1}'})
        tags.append(uid+i)
    nid=max(b['id'] for b in nodes['b'])+1000
    def node(key,props,x,y):
        nonlocal nid;nid+=1;nodes['b'].append({'v':0,'nnKey':key,'px':x,'py':y,'id':nid,'rtpt':True,'props_v2':props});return nid
    def wire(a,c,b,d):nodes['c'].append({'a':a,'b':b,'c':c,'d':d,'e':b})
    def delay(sec,x,y):return node('delay',[p('Time',str(sec),1),p('igGmSp','False',1)],x,y)
    def capture(group,x,y):
        return node('captureObj',[p('tgz2','c-2',1),p('AggressiveRadius2','600:0:0',1),p('forUnit2','c0'),p('forGroup2',group),p('pathf','Fast'),
                                  p('moveAttack','True'),p('lt','60'),p('bl','True')],x,y)
    def follow(group,leader,radius,x,y):
        """getObjPos(leader centre) -> moveComplex(group, attack-move). Returns (position node, move node)."""
        pos=node('getObjPos',[p('forGroup',leader),p('center','True')]+[p(k,'c0') for k in ('targetUnitLink','targetTriggerLink','targetTagLink',
                 'targetZoneLink','targetWayLink','targetSPLink')],x,y)
        mv=node('moveComplex',[p('tt2','c0',1),p('AggressiveRadius2',f'{radius}:0:0',1),p('forUnit2','c0'),p('forGroup2',group),p('pathf','Fast'),
                p('moveAttack','True'),p('speedLimit','True'),p('tranBeh','LoadInTransport'),p('duringRide','UnloadWhenEngaged'),p('atDest','Nothing'),
                p('ErrorRadius','80'),p('lt','-1'),p('bl','True')],x+400,y)
        wire(mv,'targetVec3',pos,'outPos');wire(mv,'in2',pos,'outFound')
        return pos,mv
    player=node('node_player',[p('value',f'c{owner}')],-3000.0,4000.0)
    prev,prev_port,t=after[0],after[1],0
    for i,(minute,counts) in enumerate(waves):
        y=4300.0+i*1200.0;g=f'FAPVE{i+1}'
        wait=delay((minute-t)*60,-3000.0,y);t=minute;wire(wait,'in2',prev,prev_port)
        go=delay(1,-2700.0,y);wire(go,'in2',wait,'out2')
        roles={}
        for u,n in counts.items():roles.setdefault(role(u),{})[u]=n
        tag=node('getTag',[p('val',f'c{tags[i%len(tags)]}')],-2400.0,y-150)
        settled={}
        for k,(r,c) in enumerate(sorted(roles.items())):
            yy=y+k*250.0
            data=node('getSpMultUnData',[p('val',payload(c,players))],-2400.0,yy+100)
            spawn=node('spawnMultiUnits',[p('TargetTag','c0',1),p('TargetSpawnPoint','c0',1),p('PlayerOwner','c0',1),p('UnitInfo','',1),
                                          p('UnitGroup',g+r),p('CargoUnitGroup',g+r+'C'),p('assign','False')],-2000.0,yy)
            wire(spawn,'in',go,'out2');wire(spawn,'UnitInfo',data,'out');wire(spawn,'TargetTag',tag,'out');wire(spawn,'PlayerOwner',player,'out')
            settled[r]=delay(3,-1600.0,yy);wire(settled[r],'in2',spawn,'out')
        x=-1200.0
        if not orders:prev,prev_port=wait,'out2';continue   # the Lua AI gives the orders
        if 'R' in settled:   # recon: one zone, then stay as a screen
            cap=capture(g+'R',x,y);wire(cap,'in2',settled['R'],'out2')
            retry=delay(30,x+400,y);wire(retry,'in2',cap,'outFailed');wire(cap,'in2',retry,'out2')
        if 'I' in settled:   # infantry: take a zone, hold it, take the next
            cap=capture(g+'I',x,y+250);wire(cap,'in2',settled['I'],'out2')
            hold=delay(HOLD_SECONDS,x+400,y+250);wire(hold,'in2',cap,'out2');wire(cap,'in2',hold,'out2')
            retry=delay(30,x+400,y+350);wire(retry,'in2',cap,'outFailed');wire(cap,'in2',retry,'out2')
        if 'A' in settled:   # armour: overwatch on its infantry, else spearhead
            tick=delay(20,x,y+500);wire(tick,'in2',settled['A'],'out2')
            if 'I' in settled:
                pos,mv=follow(g+'A',g+'I',500,x+400,y+500)
                wire(pos,'in',tick,'out2');wire(tick,'in2',mv,'out2');wire(tick,'in2',mv,'outFailed')
                lead=capture(g+'A',x+1200,y+500);wire(lead,'in2',pos,'outMiss')
            else:
                lead=capture(g+'A',x+400,y+500);wire(lead,'in2',tick,'out2')
            wire(tick,'in2',lead,'out2');wire(tick,'in2',lead,'outFailed')
        if 'S' in settled:   # air defence: escort the armour, else the infantry
            leader=g+'A' if 'A' in settled else g+'I' if 'I' in settled else None
            tick=delay(15,x,y+750);wire(tick,'in2',settled['S'],'out2')
            if leader:
                pos,mv=follow(g+'S',leader,300,x+400,y+750)
                wire(pos,'in',tick,'out2');wire(tick,'in2',mv,'out2');wire(tick,'in2',mv,'outFailed');wire(tick,'in2',pos,'outMiss')
            else:
                lead=capture(g+'S',x+400,y+750);wire(lead,'in2',tick,'out2');wire(tick,'in2',lead,'out2');wire(tick,'in2',lead,'outFailed')
        prev,prev_port=wait,'out2'
    # The last wave again every REPEAT_MINUTES (scripted mode only; the Lua AI buys its own reinforcements).
    if orders:
        loop=delay(REPEAT_MINUTES*60,-3000.0,4300.0+len(waves)*1200.0)
        wire(loop,'in2',go,'out2');wire(go,'in2',loop,'out2')
    return len(waves),len(tags)

def configure_slots(objects,meta,players):
    """Online lobby, as in the Workshop scenario "TEST YOUR DECK" (Osama 19 Nov 2026 19:26 PST: "Test your deck scenario is what we should
    copy"): Alpha's first `players` slots are open for humans; Bravo's first `players` slots are AI bot slots (meta bot=True, botId = the
    player object's _uid, player object isBot=True); all other slots locked. Until 0.9.2-dev.1 Bravo had no bot, and online the units bought
    for the empty Bravo slot went to an empty Alpha slot and stood idle (dev.41 player logs)."""
    uid={o['_dname']:o['_uid'] for o in objects if o.get('_type')==13}
    for t in meta['teams']:
        for i,s in enumerate(t['slots']):
            s.pop('botId',None)
            human=t['teamName']=='Alpha team' and i<players
            bot=t['teamName']=='Bravo team' and i<players
            s['bot']=bot;s['lock']=not(human or bot)
            if bot:s['botId']=uid[s['playerName']]
    slots={s['playerName']:s for t in meta['teams'] for s in t['slots']}
    for o in objects:
        if o.get('_type')==13 and o['_dname'] in slots:
            s=slots[o['_dname']];o['isBot']=s['bot'];o['lock']=s['lock']
    humans=[n for n,s in slots.items() if not s['lock'] and not s['bot']];bots=[n for n,s in slots.items() if s['bot']]
    assert len(humans)==players and len(bots)==players and 'Bravo Player 1' in bots,(humans,bots)
    assert all(n.startswith('Alpha') for n in humans) and all(n.startswith('Bravo') for n in bots),(humans,bots)

def build(game,out):
    settings=C.settings();ai=(AI_SRC/'ai'/'ba_brain.lua').exists()
    print('PvE commander:','BrokenArrowAI Lua' if ai else f'scripted orders ({AI_SRC} not found)')
    for players,mod,base_name,title,enemy in BASES:
        name,skirmish=names(players,title)
        W=settings['MapZoneWeights'];assert W.get(name)==W[base_name] and W.get(skirmish)==W[mod.SKIRMISH_NAME],(name,'zone weights must equal those of',base_name)
        with tempfile.TemporaryDirectory() as tmp:
            mod.build(game,Path(tmp))
            base={k:C.read_bascr(Path(tmp)/nm,nm) for k,nm in ((2,base_name),(3,mod.SKIRMISH_NAME))}
        desc=(f'Freedom Arrow PvE: {players} player{"s" if players>1 else ""} on Alpha against {title.split(" vs ")[1]} ({enemy}; AI bots on Bravo). '
              +base[2][0]['desc'])
        for flavor,kind in ((name,2),(skirmish,3)):
            h,n,o,m=copy.deepcopy(base[kind])
            if kind==3:
                start=[b['id'] for b in n['b'] if b['nnKey']=='start'];assert len(start)==1
                waves=add_waves(n,o,players,(start[0],'flow'),opening(WAVES[title],AI_CARDS[title]) if ai else WAVES[title],orders=not ai)
                if ai:add_ai(n,h['map']);add_purchase(n,o,h['map'],players,AI_CARDS[title])   # the base Skirmish flavor: bots, no deployment pause
            else:
                # Waves start when the deployment pause ends: the delay that unpauses the game.
                off=[b['id'] for b in n['b'] if b['nnKey']=='pauseGame' and any(q['k']=='val' and q['v']=='False' for q in b['props_v2'])];assert len(off)==1,off
                wait=[c['b'] for c in n['c'] if c['a']==off[0] and c['d']=='out2'];assert len(wait)==1,wait
                waves=add_waves(n,o,players,(wait[0],'out2'),opening(WAVES[title],AI_CARDS[title]) if ai else WAVES[title],orders=not ai)
                if ai:add_ai(n,h['map']);add_purchase(n,o,h['map'],players,AI_CARDS[title])
                configure_slots(o,m,players)
            C.check_spawns(flavor,h,o)
            C.check_limit(flavor,desc)
            C.stamp(h,m,flavor,str(uuid.uuid5(uuid.NAMESPACE_URL,flavor)),desc,'Freedom Arrow',kind,kind==2)
            C.write(out,flavor,h,o,n,m)
            print(f'{flavor}: {waves[0]} waves from {waves[1]} Bravo spawns, {players} human slot(s)')
