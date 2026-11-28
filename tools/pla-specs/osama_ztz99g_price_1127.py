"""ZTZ-99G 180 -> 165 pts (Osama 27 Nov 2026 17:2x PST, thread 1567745029781454889: "ztz-99g 165 points"). After osama_ztz99_split_1127.finish."""
Z99G, OLD, NEW = 948, 180, 165


def apply(t, g, ok, rec):
    U = t['Units']
    ok(U[Z99G]['HUDName'] == 'ZTZ-99G' and U[Z99G]['Cost'] == OLD and not U[Z99G].get('OriginalCost'), ('ZTZ-99G as read', U[Z99G]['HUDName'], U[Z99G]['Cost']))
    g.put('Units', Z99G, {'Cost': NEW})
    rec['osama_ztz99g_price_1127'] = {'unit': Z99G, 'cost': [OLD, NEW]}
    print('ZTZ-99G PRICE', rec['osama_ztz99g_price_1127'])
