"""Chinese text for the five China specializations (Osama 24 Nov 2026 11:0x PST, thread 1567745029781454889: "read these localization changes" with
the Chinese community's file work/loc-096-1124/0.9.6.txt, then "seems pretty good").
- Descriptions: each UIDescription becomes "English Chinese", the same bilingual form as the names; LangNames.cs shows the half for the game
  language (it splits at the last space before the first Chinese character). The English text is unchanged.
- Names: 1.1, 1.2, 1.3 and 1.5 keep their Chinese names (the file confirms them). 1.4 PLAN Naval/Special Forces: 海军与特战部队 ->
  海军参谋部远域特种作战大队 (the file's proposal; its English name is marked "to be revised", so the English half stays).
- 1.3 description: the file's "一支旧机队(也在)提供空中掩护" written without the brackets.
Runs right after the 23 Nov spec-name block."""
ZH = {17: (None, '中国人民解放军空军部署有中国最现代化的歼击机、轰炸机和隐形喷气式战机，空降兵部队乘坐直升机在主力部队之前开辟战场。'),
      18: (None, '陆军的重型合成旅有中国最新最重的坦克和步兵战车，并且有自行火炮和机动防空的加持。但是这种程度的火力的代价是没有固定翼。'),
      19: (None, '火箭军部队和预备役部队合编共同执行战斗任务。火箭军的弹道导弹与远火落入敌方领土的同时，预备役部队的动员军人、老坦克将填充在防线的每一处。一支旧机队也在提供空中掩护。'),
      20: ('海军参谋部远域特种作战大队', '该专精设定是解放军海军与各特种部队联合作战的部队（并非只指海军自己的特种部队）。在海军战斗群的航母与长航时无人机支援下，精锐特战部队与陆战队深入敌后进行空中打击。'),
      21: (None, '解放军陆军的中型合成旅的专精内容是：快速轮式车辆携带大量部队，在自行火箭炮兵和防空系统的支持下，进行猛烈打击并保持机动。')}
import re
CJK = re.compile(r'[　-〿㐀-鿿＀-￯]')


def apply(t, g, ok, rec):
    S = t['SpecializationsJson']; out = {}
    for i, (name_zh, desc_zh) in ZH.items():
        s = S[i]; en_desc = s['UIDescription']
        ok(s['CountryId'] == 4 and en_desc and not CJK.search(en_desc), ('spec', i, 'English-only description before'))
        m = CJK.search(s['UIName']); en_name, old_zh = s['UIName'][:m.start()].strip(), s['UIName'][m.start():].strip()
        new = {'UIDescription': en_desc + ' ' + desc_zh}
        if name_zh: new['UIName'] = en_name + ' ' + name_zh
        g.put('SpecializationsJson', i, new)
        ok(S[i]['UIDescription'].startswith(en_desc + ' ') and S[i]['UIName'].startswith(en_name + ' '), ('spec', i, 'bilingual'))
        out[i] = {'name': S[i]['UIName'], 'old_zh_name': old_zh}
    rec['china_spec_zh_1124'] = out
    print('CHINA SPEC ZH', {i: v['name'] for i, v in out.items()})
