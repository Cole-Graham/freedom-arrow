# China voice lines v2 - Move fill (Osama 18 Nov 2026 01:3x PST, thread 1571014792016171120: "each unit should have 10 voice lines for
# selection, move and attack, between unique and general and type voice lines. word for word check it all"; "make sure to retain the original
# styles and characters of the unit"). Selection and Attack already had 10 per set; Move and Move_CBT had 3. These add 7 each, in each set's own
# voice and character. Format "tags|Mandarin|English". Lines are full phrases (5+ characters): one- and two-word shouts were the ones the
# voice doubled ("投弹！" -> "投弹，投弹"). No sound-prone tags (see sanitize.py).
MOVE_ADD = {
 ('Infantry','SF'): {   # Philip: calm, clipped, professional radio talk
  '03_Move': [
   "[calm] [professional] [clipped]|收到，向下一个点位机动。|Copy, moving to the next point.",
   "[cool] [steady] [focused]|分队前出，保持静默。|Team pushing out, stay quiet.",
   "[calm] [matter-of-fact] [steady]|明白，沿着掩护线走。|Understood, moving along cover.",
   "[professional] [quiet] [confident]|收到，按计划路线前进。|Copy, on the planned route.",
   "[calm] [crisp] [focused]|两人一组，交替前进。|Pairs, bounding forward.",
   "[cool] [professional] [steady]|收到，正在转移位置。|Copy, relocating now.",
   "[calm] [clipped] [confident]|明白，我们去那边看看。|Understood, we'll check it out."],
  '04_Move_CBT': [
   "[urgent] [tense] [clipped]|交替掩护，下一组走！|Bounding, next pair go!",
   "[urgent] [professional] [commanding]|压住火力，我们转移！|Suppress, we're moving!",
   "[tense] [focused] [urgent]|换到右侧，快！|Shift right, now!",
   "[urgent] [crisp] [commanding]|烟幕后面走，跟上！|Move behind the smoke, on me!",
   "[tense] [clipped] [steady]|收到，边打边撤！|Copy, fighting withdrawal!",
   "[urgent] [commanding] [focused]|离开这个位置，快走！|Get off this spot, move!",
   "[tense] [urgent] [crisp]|保持队形，冲过去！|Keep spacing, push through!"]},
 ('Infantry','Regular'): {   # Kang: plain soldier talk
  '03_Move': [
   "[calm] [crisp] [steady]|是，马上出发！|Yes sir, moving now!",
   "[alert] [matter-of-fact] [steady]|明白，向那边前进。|Understood, heading over there.",
   "[eager] [crisp] [loud]|全班跟上，出发！|Squad, on me, move out!",
   "[calm] [steady] [crisp]|收到，正在前进。|Copy, on the move.",
   "[alert] [crisp] [steady]|明白，按命令行动。|Understood, following orders.",
   "[confident] [loud] [eager]|向目标点前进！|Advancing to the objective!",
   "[calm] [matter-of-fact] [steady]|收到，我们这就过去。|Copy, we're heading over."],
  '04_Move_CBT': [
   "[urgent] [shouting] [tense]|快跑，别在这儿停！|Run, don't stop here!",
   "[urgent] [loud] [tense]|一组掩护，二组走！|Team one cover, team two go!",
   "[shouting] [urgent] [crisp]|低头前进，快！|Heads down, move!",
   "[tense] [urgent] [loud]|跟紧我，冲过去！|Stay close, push through!",
   "[urgent] [shouting] [tense]|换个位置，快点！|Change position, hurry!",
   "[shouting] [tense] [urgent]|别管了，快撤！|Forget it, fall back!",
   "[urgent] [crisp] [loud]|压住他们，我们上！|Pin them, we're going!"]},
 ('Infantry','Conscript'): {   # Brody: over-the-top Mao-era slogans
  '03_Move': [
   "[shouting] [zealous] [eager]|为人民服务，出发！|Serve the people, march!",
   "[fervent] [proud] [loud]|一切行动听指挥！|All actions follow command!",
   "[shouting] [patriotic] [eager]|同志们，向前进！|Comrades, forward!",
   "[zealous] [shouting] [proud]|革命的队伍，前进！|The revolutionary ranks, advance!",
   "[eager] [fervent] [loud]|毛主席指引我们前进！|Chairman Mao guides our advance!",
   "[shouting] [proud] [zealous]|团结就是力量，出发！|Unity is strength, march!",
   "[fervent] [shouting] [eager]|向着红旗前进！|Advance toward the red flag!"],
  '04_Move_CBT': [
   "[shouting] [fanatical] [urgent]|革命不怕流血，冲啊！|The revolution fears no blood, charge!",
   "[shouting] [zealous] [defiant]|一不怕苦，二不怕死！|Fear no hardship, fear no death!",
   "[fervent] [shouting] [urgent]|为了新中国，冲上去！|For New China, charge!",
   "[defiant] [shouting] [zealous]|纸老虎吓不倒我们！|Paper tigers can't scare us!",
   "[shouting] [urgent] [fanatical]|同志们，跟着红旗冲！|Comrades, follow the red flag!",
   "[zealous] [shouting] [defiant]|人民战争，冲锋向前！|People's war, charge forward!",
   "[shouting] [fervent] [urgent]|宁死不退，冲上去！|Rather die than retreat, charge!"]},
 ('Tank','Regular'): {   # Philip: gruff, aggressive tank crew
  '03_Move': [
   "[confident] [gruff] [loud]|装甲分队，开始机动。|Armour, moving out.",
   "[gruff] [steady] [confident]|收到，坦克前进。|Copy, tank advancing.",
   "[aggressive] [crisp] [eager]|发动机全开，出发！|Full throttle, rolling!",
   "[gruff] [matter-of-fact] [steady]|明白，沿公路前进。|Understood, taking the road.",
   "[confident] [loud] [gruff]|车组注意，向前推进。|Crew, pushing forward.",
   "[steady] [gruff] [focused]|收到，转向目标方向。|Copy, turning toward the target.",
   "[aggressive] [confident] [loud]|履带碾过去，前进！|Tracks rolling, advance!"],
  '04_Move_CBT': [
   "[aggressive] [shouting] [urgent]|倒车，换个射击位置！|Reverse, new firing position!",
   "[urgent] [gruff] [loud]|装甲正面对敌，前进！|Front armour to the enemy, advance!",
   "[shouting] [aggressive] [tense]|别停车，冲过火力区！|Don't stop, through the fire zone!",
   "[gruff] [urgent] [aggressive]|开过去，碾碎他们！|Drive through, crush them!",
   "[urgent] [shouting] [gruff]|放烟幕，转移阵地！|Smoke, change position!",
   "[aggressive] [urgent] [loud]|侧面有敌人，快转向！|Enemy flank, turn now!",
   "[shouting] [gruff] [urgent]|全速冲锋，跟上我！|Full speed, follow me!"]},
 ('Tank','Conscript'): {   # Brody: zealous PLARF tank crews
  '03_Move': [
   "[shouting] [zealous] [eager]|钢铁洪流，前进！|Steel torrent, advance!",
   "[fervent] [proud] [loud]|人民的坦克，开动！|The people's tank, roll out!",
   "[shouting] [patriotic] [eager]|开往前线，保卫祖国！|To the front, defend the motherland!",
   "[zealous] [shouting] [proud]|坦克兵同志们，出发！|Tank comrades, move out!",
   "[eager] [fervent] [loud]|向前开，革命到底！|Drive on, revolution to the end!",
   "[shouting] [proud] [zealous]|轰隆隆，前进前进！|Roaring forward, onward!",
   "[fervent] [shouting] [eager]|为了人民，全速前进！|For the people, full speed!"],
  '04_Move_CBT': [
   "[shouting] [fanatical] [urgent]|撞上去，和敌人拼了！|Ram them, fight to the end!",
   "[urgent] [shouting] [defiant]|开过去，压倒一切敌人！|Drive over, crush every enemy!",
   "[shouting] [zealous] [urgent]|坦克不停，革命不止！|The tank won't stop, the revolution won't stop!",
   "[defiant] [shouting] [fervent]|顶着炮火冲上去！|Charge through the shellfire!",
   "[fanatical] [shouting] [urgent]|全车同志，冲锋！|All crew, charge!",
   "[shouting] [urgent] [zealous]|宁可战死，绝不后退！|Die fighting, never retreat!",
   "[defiant] [fervent] [shouting]|碾碎帝国主义！|Crush the imperialists!"]},
 ('Vehicle','Regular'): {   # Kang: crisp vehicle crews
  '03_Move': [
   "[calm] [crisp] [steady]|收到，车辆出发。|Copy, vehicle moving.",
   "[matter-of-fact] [steady] [calm]|明白，沿公路前进。|Understood, taking the road.",
   "[confident] [crisp] [loud]|发动车辆，出发！|Start up, move out!",
   "[calm] [steady] [crisp]|收到，正在转移。|Copy, relocating.",
   "[crisp] [confident] [steady]|明白，向目标点开进。|Understood, driving to the point.",
   "[calm] [matter-of-fact] [steady]|收到，马上过去。|Copy, heading over now.",
   "[eager] [crisp] [loud]|全速前进，跟上队伍！|Full speed, keep with the column!"],
  '04_Move_CBT': [
   "[urgent] [loud] [tense]|倒车，离开火力区！|Reverse, out of the fire zone!",
   "[shouting] [urgent] [crisp]|加速，冲过去！|Speed up, push through!",
   "[urgent] [tense] [loud]|找掩护，快转移！|Find cover, move now!",
   "[tense] [urgent] [crisp]|别停在开阔地！|Don't stop in the open!",
   "[urgent] [shouting] [tense]|放烟幕，换位置！|Smoke, reposition!",
   "[urgent] [loud] [crisp]|边打边撤，快！|Fight and pull back, now!",
   "[tense] [urgent] [shouting]|快开走，敌人瞄准我们了！|Drive, they're aiming at us!"]},
 ('Artillery','Regular'): {   # Kang: artillery crews relocating
  '03_Move': [
   "[calm] [crisp] [steady]|收到，炮车出发。|Copy, guns moving.",
   "[calm] [matter-of-fact] [steady]|明白，转移到新阵地。|Understood, moving to a new position.",
   "[crisp] [confident] [steady]|收炮，准备机动。|Guns stowed, ready to move.",
   "[calm] [steady] [crisp]|收到，向指定地点转移。|Copy, relocating to the point.",
   "[matter-of-fact] [calm] [steady]|明白，炮兵阵地前移。|Understood, moving the battery up.",
   "[confident] [crisp] [loud]|全炮连，出发！|Whole battery, move out!",
   "[calm] [crisp] [steady]|收到，换个位置继续打。|Copy, new spot, keep firing."],
  '04_Move_CBT': [
   "[urgent] [shouting] [tense]|被发现了，马上转移！|We're spotted, move now!",
   "[urgent] [loud] [crisp]|反炮兵火力，快离开！|Counter-battery, get out!",
   "[tense] [urgent] [loud]|打完这一轮就走！|Fire this round, then go!",
   "[urgent] [shouting] [crisp]|收炮，快撤！|Stow the guns, pull out!",
   "[tense] [urgent] [shouting]|别留在原地，快走！|Don't stay put, move!",
   "[urgent] [loud] [tense]|换阵地，动作快！|Change position, quickly!",
   "[urgent] [crisp] [shouting]|敌人炮弹来了，转移！|Incoming fire, relocate!"]},
 ('Helicopter','Regular'): {   # Kang: helicopter pilots
  '03_Move': [
   "[calm] [crisp] [steady]|收到，飞往目标区。|Copy, flying to the area.",
   "[calm] [matter-of-fact] [steady]|明白，改变航向。|Understood, changing heading.",
   "[confident] [crisp] [loud]|直升机，起飞出发！|Helicopter, lifting off!",
   "[calm] [steady] [crisp]|收到，贴着地形飞过去。|Copy, hugging the terrain.",
   "[calm] [crisp] [steady]|明白，正在前往航点。|Understood, en route to the waypoint.",
   "[confident] [steady] [crisp]|收到，低空转场。|Copy, low-level transit.",
   "[calm] [matter-of-fact] [steady]|航线已更新，正在飞行。|Route updated, flying now."]},
 ('Plane','SF'): {   # Philip: cool 5th/6th-gen pilots
  '03_Move': [
   "[calm] [professional] [clipped]|收到，飞往指定空域。|Copy, heading to the airspace.",
   "[cool] [steady] [confident]|明白，保持隐身航线。|Understood, holding the stealth route.",
   "[calm] [quiet] [focused]|收到，改变航向。|Copy, changing heading.",
   "[professional] [calm] [clipped]|航点确认，正在飞行。|Waypoint confirmed, en route.",
   "[cool] [confident] [steady]|明白，加速前往。|Understood, speeding up.",
   "[calm] [professional] [focused]|收到，进入巡逻航线。|Copy, entering the patrol route.",
   "[cool] [clipped] [steady]|明白，雷达静默飞行。|Understood, flying radar silent."]},
 ('Plane','Regular'): {   # Kang: regular pilots
  '03_Move': [
   "[calm] [crisp] [steady]|收到，飞往目标空域。|Copy, flying to the target area.",
   "[calm] [matter-of-fact] [steady]|明白，正在调整航向。|Understood, adjusting heading.",
   "[confident] [crisp] [loud]|加力，前往航点！|Throttle up, to the waypoint!",
   "[calm] [steady] [crisp]|收到，航线已确认。|Copy, route confirmed.",
   "[calm] [crisp] [steady]|明白，保持编队飞行。|Understood, holding formation.",
   "[confident] [steady] [crisp]|收到，正在前往。|Copy, on my way.",
   "[calm] [matter-of-fact] [steady]|收到，转向新的航点。|Copy, turning to the new waypoint."]},
 ('Plane','Conscript'): {   # Brody: zealous PLARF pilots
  '03_Move': [
   "[shouting] [zealous] [eager]|为了人民，飞向前线！|For the people, to the front!",
   "[fervent] [proud] [loud]|人民的飞行员，出发！|The people's pilot, taking off!",
   "[shouting] [patriotic] [eager]|祖国的天空，由我守护！|I guard the motherland's sky!",
   "[zealous] [shouting] [proud]|驾驶战鹰，飞向胜利！|Flying the war eagle to victory!",
   "[eager] [fervent] [loud]|革命飞行员，听从命令！|Revolutionary pilot, following orders!",
   "[shouting] [proud] [zealous]|为了新中国，起飞！|For New China, take off!",
   "[fervent] [shouting] [eager]|飞吧，飞向敌人！|Fly, fly at the enemy!"]},
}
