"""Week 19–25/10 replacement Reels (no narration): 30 s, 80 BPM, one phrase every 3 s, AMG Carbon cards over footage."""
import json
N = {n['id']: n for n in json.load(open('narr_semana4.json'))}
CY = 1250; RED = '#E0484E'; GREEN = '#6FBF93'
TRS = ['zoom', 'whipL', 'cube', 'glitch', 'spin', 'whipU', 'leak', 'whipR']
def card(t0, t1, **k): d = dict(k); d.update(t0=t0, t1=t1); d.setdefault('cy', CY); return d
def reel(rid, tema, videos, beats, photo, caption, sfx=()):
    shots, caps, cards, scenes = [], [], [], {}
    for i, b in enumerate(beats):
        st = 3.0 * i
        if i < len(beats) - 1:
            v = videos[i]; s = {'start': st, 'video': v[0], 'from': v[1], 'vol': 0.25, 'plate': [12, 0.36]}
            if i: s.update(tr=TRS[(i - 1) % len(TRS)], td=0.4 if TRS[(i - 1) % len(TRS)] != 'leak' else 0.6)
            shots.append(s)
            caps.append({'start': st, 'end': st + 3.0, 'text': b['cap'], 'y': -650 if i == 0 else -600})
        else:
            shots.append({'start': st, 'img': photo, 'card': True, 'tr': 'slab', 'td': 0.55})
            caps.append({'start': st, 'end': 30.0, 'text': b['cap'], 'small': 'Link na bio', 'y': 380})
        for c in b.get('cards', []): cards.append(c)
        for k, v in b.get('scenes', {}).items(): scenes[k] = v
    return {'id': rid, 'duration': 30.0, 'bpm': 80, 'cover_t': 0.5, 'cap_lead': 0.15, 'word_step': 0.08, 'pulse_bar': 0.022,
            'tema': tema, 'drops': [3.0, 24.0], 'shots': shots, 'scenes': scenes, 'cards': cards, 'sfx': list(sfx), 'caps': caps, 'caption': caption}

R1 = reel('M1', 'O ponto mais caro é o que já está parado na sua conta',
  [['IMG_5481.mov', 0.5], ['IMG_9837.mov', 2.0], ['IMG_8854.mov', 1.0], ['IMG_6915.mov', 1.0], ['IMG_5030.mov', 1.0], ['IMG_9913.mov', 1.0], ['IMG_2675.mov', 3.0], ['IMG_9094.mov', 1.0]],
  [{'cap': 'O ponto mais caro é o que está [[parado]] na sua conta.', 'cards': [card(-1, 3.0, type='text', icon='clock', iconColor=RED, title=['PONTO', 'PARADO'], hl=1, hlColor=RED, sub='o mais caro que existe')]},
   {'cap': 'Muita gente gasta todo mês no cartão…', 'cards': [card(3.0, 9.0, type='people', label='QUANTAS PESSOAS VOCÊ CONHECE', lit=3.2, litColor='red', ratio=7, badge='NUNCA EMITIRAM')]},
   {'cap': '…e nunca emitiu uma passagem.'},
   {'cap': 'Não é falta de pontos.', 'cards': [card(9.0, 12.0, type='text', title=['Problema', 'de pontos?'], strike=True, strikeAt=1.0)]},
   {'cap': 'É falta de [[método]].', 'cards': [card(12.0, 18.0, type='checks', label='O PROBLEMA REAL É MÉTODO', labelColor=GREEN, at=[0.8, 1.6, 2.4],
        items=[{'icon': 'transfer', 'label': 'QUANDO', 'label2': 'TRANSFERIR'}, {'icon': 'plane', 'label': 'QUANDO', 'label2': 'EMITIR'}, {'icon': 'tag', 'label': 'QUANTO', 'label2': 'VALE A MILHA'}])]},
   {'cap': 'Quando transferir, quando emitir e quanto vale cada milha.'},
   {'cap': 'A mesma transferência de 10 mil pontos pode virar [[g:20 mil]].', 'scenes': {'coins': {'t0': 18.0, 't1': 21.0, 'cy': 1200}}},
   {'cap': 'Informação qualquer um copia. Método, não.', 'cards': [card(21.0, 24.0, type='list', title='CONTEÚDO DE MILHAS', icon='chart', items=[{'t': 'Cartão'}, {'t': 'Programa'}, {'t': 'Promoção'}], at=[0.2, 0.5, 0.8], stamp='QUALQUER UM COPIA', stampAt=1.5)]},
   {'cap': 'O método eu ensino no Duplicando Milhas.'}],
  'IMG_9903', N['N1']['caption'], sfx=[{'t': 22.5, 'dur': 0.3, 'kind': 'stamp'}, {'t': 10.0, 'dur': 0.2, 'kind': 'glitch'}])

R2 = reel('M2', 'Milha não é desconto, é dinheiro',
  [['IMG_9994.MOV', 1.0], ['IMG_0123.mov', 1.0], ['IMG_9811.mov', 2.0], ['IMG_9225.mov', 1.0], ['IMG_8684.mov', 0.5], ['IMG_1889.mov', 3.0], ['IMG_9060.mov', 3.0], ['IMG_0139.mov', 1.0]],
  [{'cap': 'Milha não é desconto. É [[dinheiro]].', 'cards': [card(-1, 3.0, type='text', title=['Desconto', 'Dinheiro'], hl=1, strike=True, strikeY=-40, strikeAt=1.0, w=860)]},
   {'cap': 'Madri por 58 mil milhas é de graça?', 'cards': [card(3.0, 6.0, type='list', title='MADRI', icon='plane', items=[{'t': '58.000 milhas', 'icon': 'plane'}, {'t': '"De graça"', 'icon': 'gift'}], at=[0.3, 1.0], stamp='SERÁ?', stampAt=1.8, stampX=250, stampY=70)]},
   {'cap': 'Com o milheiro a R$ 29,40…', 'scenes': {'receipt': dict(N['N2']['lines'][3]['scene'], t0=6.0, t1=12.0, y=600)}},
   {'cap': '…essa passagem custaria cerca de [[R$ 1.705]], mais taxas.'},
   {'cap': 'Às vezes, a passagem em dinheiro sai por menos.', 'cards': [card(12.0, 15.0, type='text', icon='scale', title=['Milhas', 'ou dinheiro?'], hl=1, sub='depende do voo')]},
   {'cap': 'Rio–Curitiba já saiu por R$ 319 ida e volta, em dinheiro.', 'cards': [card(15.0, 18.0, type='big', label='RIO ⇄ CURITIBA · EM DINHEIRO', value='R$ 319', count=True, unit='IDA E VOLTA', color=GREEN, fs=200)]},
   {'cap': 'Gastar milha num voo assim é [[jogar milha fora]].', 'cards': [card(18.0, 21.0, type='text', icon='cross', iconColor=RED, title=['Jogar milha', 'fora'], hl=1, hlColor=RED)]},
   {'cap': 'Guarde a milha para o voo que vale mais.', 'cards': [card(21.0, 24.0, type='checks', label='ONDE A MILHA VALE MAIS', labelColor=GREEN, at=[0.3, 0.9, 1.5],
        items=[{'icon': 'plane', 'label': 'VOO', 'label2': 'INTERNACIONAL'}, {'icon': 'calendar', 'label': 'DATA DE', 'label2': 'FÉRIAS'}, {'icon': 'bell', 'label': 'PROMOÇÃO', 'label2': 'RELÂMPAGO'}])]},
   {'cap': 'Essa conta eu ensino no Duplicando Milhas.'}],
  'IMG_9601', N['N2']['caption'], sfx=[{'t': 4.8, 'dur': 0.3, 'kind': 'stamp'}])

R3 = reel('M3', 'A próxima data dupla é 11/11',
  [['IMG_9913.mov', 2.0], ['IMG_5025.MOV', 2.0], ['IMG_9812.mov', 1.5], ['IMG_5486.mov', 1.0], ['IMG_9837.mov', 4.0], ['IMG_6915.mov', 3.0], ['IMG_0073.mov', 3.0], ['IMG_5174.mov', 3.0]],
  [{'cap': 'A melhor passagem do mês costuma durar [[1 dia]].', 'cards': [card(-1, 3.0, type='big', label='A MELHOR PASSAGEM DO MÊS', value='1 DIA', fs=220, color=GREEN)]},
   {'cap': 'Em 2026, a LATAM Pass deu até 40% off em voos com milhas…', 'cards': [card(3.0, 9.0, type='months', label='LATAM PASS · ATÉ 40% OFF COM MILHAS',
        months=[{'l': 'JUN', 'd': '06/06'}, {'l': 'JUL', 'd': '06/07'}, {'l': 'AGO', 'd': '09/08'}, {'l': 'SET', 'd': '08/09'}, {'l': 'OUT', 'd': '09/10'}], foot='DATAS DAS OFERTAS EM 2026', at=[0.6, 1.5, 2.4, 3.3, 4.2])]},
   {'cap': '…em junho, julho, agosto, setembro e outubro.'},
   {'cap': 'No 10.10, Curitiba–Londrina saiu por 2.939 milhas o trecho.', 'cards': [card(9.0, 12.0, type='big', label='CURITIBA → LONDRINA · 10.10', value='2.939', count=True, unit='MILHAS O TRECHO, MAIS TAXAS', color=GREEN)]},
   {'cap': 'A maioria dessas promoções valeu por um dia.', 'scenes': {'countdown': {'t0': 12.0, 't1': 15.0, 'cy': 1200}}},
   {'cap': 'Quem tinha os pontos no banco, e não na companhia, perdeu.', 'cards': [card(15.0, 18.0, type='text', icon='bank', title=['Pontos no banco,', 'não na companhia'], fs=88, w=960, stamp='PERDEU', stampAt=1.6)]},
   {'cap': 'Quem se prepara sabe 3 coisas antes da promoção.', 'cards': [card(18.0, 21.0, type='checks', label='QUEM SE PREPARA SABE', labelColor=GREEN, at=[0.4, 1.1, 1.8],
        items=[{'icon': 'plane', 'label': 'QUANTO CUSTA', 'label2': 'O DESTINO'}, {'icon': 'wallet', 'label': 'ONDE ESTÃO', 'label2': 'OS PONTOS'}, {'icon': 'tag', 'label': 'QUANTO VALE', 'label2': 'CADA MILHA'}])]},
   {'cap': 'A próxima data dupla é [[11.11]].', 'cards': [card(21.0, 24.0, type='big', label='PRÓXIMA DATA DUPLA', value='11.11', fs=250, color=GREEN)]},
   {'cap': 'Para chegar pronto: Duplicando Milhas.'}],
  'IMG_9241', N['N3']['caption'], sfx=[{'t': 16.6, 'dur': 0.3, 'kind': 'stamp'}])

json.dump([R1, R2, R3], open('reels_semana4.json', 'w'), ensure_ascii=False, indent=1)
print('ok')
