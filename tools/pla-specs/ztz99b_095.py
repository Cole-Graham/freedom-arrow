"""ZTZ-99B on the ZTZ-99A card (Osama 22 Nov 2026 01:0x PST, thread 1572407822849810463: "Shawn uploaded the ZTZ-99B, this is an upgrade variant of
the ZTZ-99A, when someone gets the APS option, they get this model. so there's Jammer for +20, APS for +70, LSDW for +100 and the LSDW+APS for +120.
When combined LSDW and APS, the APS overrides (you get the two charges and normal cd) the LSDW but you get the LSDW weapon also"; "next patch, not for
the hotfix"). Protection slot of unit 904 (modification 2019383): None 0, JD-3 jammer +20, GL-6 APS +70 (new), LSDW +100, LSDW + GL-6 APS +150 (new; +120 until 23 Nov).
APS = existing ability row 82 "APS IronFist NoModel" (2 charges, the normal 10 s cooldown; the ZBD-20 / US option row), linked, not a new row.
The combined option keeps the LSDW turret 2019389 (the LSDW weapon) with ability 82 in slot 2 instead of the LSDW laser defence 2019386.
The two APS options rename the card ZTZ-99B (ReplaceUnitName, Osama 22 Nov 02:1x). The 99B model for the two APS options is chosen by FAModels from models.json "variants" (FAModels 0.3.39). Called from batch_0_9_5b.py."""
def apply(t,g,ok,rec):
    U,M,O,AB,UA=t['Units'],t['ModificationsJson'],t['OptionsJson'],t['AbilitiesJson'],t['UnitAbilitiesJson']
    ok((U[904].get('HUDName') or '').strip()=='ZTZ-99A' and M[2019383]['UnitId']==904,'ZTZ-99A protection slot')
    opts={o['Id']:o for o in O.values() if o and o.get('ModificationId')==2019383}
    ok(sorted(opts)==[31098,31099,31100],('ZTZ-99A protection options',sorted(opts)))
    ok([(opts[i]['UIName'],opts[i]['Cost'],opts[i]['Order'],opts[i]['Ability2Id']) for i in (31098,31099,31100)]==
       [('Custom_Option_None',0,0,4),('JD-3 jammer',20,1,80),('LSDW',100,2,2019386)],'99A options as in 0.9.4')
    ok(O[31100]['Turret0Id']==2019389 and O[31099]['Turret0Id']==2009072,'LSDW option carries the LSDW turret')
    a=AB[82];ok(a['IsAPS'] and a['APSQuantity']==2 and a['APSCooldown']==10.0 and not a.get('ModelFileName') and not a['IsDefault'],('APS row 82',a['APSQuantity'],a['APSCooldown']))
    pic=sorted({o['OptionPicture'] for o in O.values() if o and o.get('Ability2Id')==82 and o.get('OptionPicture') and 'Iron Fist' in (o.get('Name') or '')})
    ok(len(pic)>=1,('Iron Fist option picture',pic));pic=pic[0]
    aps=g.add('OptionsJson',O[31099],{'Name':'PLA ZTZ-99A GL-6 APS (ZTZ-99B)','UIName':'GL-6 APS','Order':2,'Cost':70,'Ability2Id':82,'OptionPicture':pic,'IsDefault':False,'ReplaceUnitName':'ZTZ-99B'})
    g.put('OptionsJson',31100,{'Order':3})
    # Osama 23 Nov 2026 11:4x (thread 1573561286803980289): "LSDW + GL-6 APS +120 loadout (which should be +150)".
    # 11:5x: "you need to make that change for the +150 loadout": its loadout picture is the standard APS one (as GL-6 APS), not the LSDW picture.
    both=g.add('OptionsJson',O[31100],{'Name':'PLA ZTZ-99A LSDW + GL-6 APS (ZTZ-99B)','UIName':'LSDW + GL-6 APS','Order':4,'Cost':150,'Ability2Id':82,'OptionPicture':pic,'IsDefault':False,'ReplaceUnitName':'ZTZ-99B'})
    ua={r['AbilityId']:r for r in UA.values() if r and r.get('UnitId')==904}
    ok(80 in ua and 2019386 in ua and 82 not in ua,('ZTZ-99A ability links',sorted(ua)))
    g.add('UnitAbilitiesJson',ua[80],{'AbilityId':82})
    ok(O[both]['OptionPicture']==O[aps]['OptionPicture']==pic and O[31100]['OptionPicture']=='FA_PLA_WP_LSDW_DAZZLER','APS picture on both 99B loadouts, LSDW picture on LSDW')
    ok(O[both]['Turret0Id']==2019389 and O[aps]['Turret0Id']==2009072 and O[both]['Ability1Id']==O[aps]['Ability1Id']==2000197,'turrets and smoke kept')
    # Osama 22 Nov 02:1x: "When the ZTZ-99A equips the GL-6 APS loadout or the LSDW+GL-6 APS upgrade, it should be called ZTZ-99B". Native rename,
    # as the vanilla options that swap the unit name (Stryker Dragoon 15 'M1296 Dragoon', Paladin 305 'M1299 IronThunder'): ReplaceUnitName only (ConcatenateWithUnitName is a text suffix, left empty).
    ok(all(O[o]['ReplaceUnitName']=='ZTZ-99B' and not O[o].get('ConcatenateWithUnitName') for o in (aps,both)) and not O[31099].get('ReplaceUnitName') and not O[31100].get('ReplaceUnitName'),'APS loadouts named ZTZ-99B, others stay ZTZ-99A')
    rec['ztz99b']={'unit':904,'options':{'GL-6 APS':[aps,70],'LSDW + GL-6 APS':[both,150]},'order':['None','JD-3 jammer +20','GL-6 APS +70','LSDW +100','LSDW + GL-6 APS +150'],'aps_ability':82,'option_picture':pic}
    return aps,both
