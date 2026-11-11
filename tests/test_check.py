"""Prove that the checks fire.

usage: python3 -I -m unittest discover -s tests

Each test copies a small good fixture, breaks one thing, and asserts the validator reports the
matching error code. The fixture itself must pass with no errors. The last class repeats a few
mutations on the real data, if data/ and cache/sections.json exist.
"""
import os, sys, json, copy, hashlib, tempfile, unittest, struct, zlib, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import storylib as L
import check_story as C

SECTIONS = {
    'Notes': ['I have adopted in this book our Calendar throughout, instead of the former Russian Calendar, '
              'which was thirteen days earlier.'],
    'IV': ['It was 10.40 P. M. when Dan rang the bell. We walked down the Nevsky to the Duma, on Wednesday, '
           'November 7th, and on Thursday, November 16th, nothing happened.',
           'Underfoot the sidewalk was littered with broken stucco, from the cornice of the Palace where two '
           'shells from the battleship _Avrora_ had struck. Smolny was ablaze with lights. John Reed.',
           'Sailors marched up the Nevsky in a column. A red flag crudely lettered in gold, “Peace! Land!” floated over them.',
           'Soviet troops surrounded the Palace and opened fire, with two armoured cars. The cars went cruising back and forth, '
           'their guns trained on the walls; waves of Red Guards, assaulting, crumpled under the fire.'],
    'App.III.7': ['At 1 A. M. a detachment of soldiers and sailors from Smolny occupied the Telegraph Agency. '
                  'At 1.35 the Post Office was occupied by the Military Revolutionary Committee of the '
                  'Provisional Government.'],
    'V': ['So we came into the great meeting-hall, under the white chandeliers. The Red Guards sat on the left. '
          'On the platform sat the presidium, the Sailors among them. Kameniev rang the bell. Fifty delegates got up and '
          'pushed their way out, in a storm of hoots. Only part of the Sailors left the Congress; the rest were going to stay. '
          'Kameniev asked all in favour to hold up their cards. And thereupon the Congress was dissolved. '
          '"I\'m going now!" answered Kameniev, and left the platform. The Sailors and the Red Guards were embracing; '
          'behind them was the empty frame from which the picture had been torn.',
          'In the high, amphitheatrical hall the galleries were thronged with workers. About a hundred people were grouped '
          'around the platform, where Kameniev was speaking, and from the right came imprecations. Others cried, "Down with the traitors!" '
          'Whereupon the Sailors left the chamber. It was evident that most of the delegates were hostile, and Kameniev was hooted down; '
          'the Red Guards held a bare fifth of the seats.',
          'Then Kameniev demanded the floor once more. He was interrupted by a great burst of laughter; and he left the room. '
          'At the end Kameniev announced the arrival of the Sailors, greeted with a rising ovation. Upon his arrival the Sailor was arrested. '
          'They went to slaughter and be slaughtered.',
          'There stretched the rows of Red Guard seats--empty since they had gone. Uproar from the Left. '
          'When Kameniev had stepped down he strode out with his suite of officers.'],
    'IX': ['Pulkovo. Staff. 2.10 A.M. The night of October 30th to 31st will go down in history.',
           "It was almost three o'clock in the morning when Holtzman came running.",
           'The hall rose, thundering.',
           'Kameniev spoke, and then Holtzman. He left the hall at once.',
           'Kameniev began. ' + 'The debate went on and on, and nobody listened. ' * 14 + 'At last he left the hall.',
           'Signed: KAMENIEV. Then he left the hall.'],
}


def book_json():
    secs = [{'id': k, 'kind': 'chapter', 'title': k, 'paras': v} for k, v in SECTIONS.items()]
    sha = hashlib.sha256(json.dumps(SECTIONS, sort_keys=True).encode()).hexdigest()
    return {'source': {'url': 'fixture', 'sha256': sha}, 'sections': secs, 'graphics': []}


def good():
    sha = book_json()['source']['sha256']
    meta = {'meta': {
        'title': 'fixture',
        'text': {'gutenberg': 3076, 'body_sha256': sha},
        'calendar': {'store': 'NS', 'os_lag': 13, 'ref': {'sec': 'Notes', 'q': 'I have adopted in this book our Calendar throughout'}},
        'clock': {'petrograd': {'offset_min': 181.3, 'src': ['tzdb']}},
        'range': ['1917-09-01', '1917-12-31'],
        'zones': {'city': [59.83, 30.15, 60.03, 30.55], 'front': [59.5, 29.95, 59.85, 30.75], 'moscow': [55.55, 37.35, 55.95, 37.85]},
        'speed_kmh': {'foot': 6, 'march': 5, 'cavalry': 12, 'cab': 15, 'tram': 15, 'car': 45, 'truck': 30, 'armoured': 25, 'rail': 45, 'ship': 20, 'air': 150, 'unknown': 45},
        'blocs': {'soviet': 'for', 'government': 'the deposed government'},
        'tags': ['background', 'shooting']},
        'days': [{'d': '1917-11-07', 'os': '1917-10-25', 'label': '7 Nov', 'name': 'The rising'}]}
    sources = [{'id': 'ref1917', 'kind': 'reference', 'cite': 'A reference work on Petrograd in 1917'},
               {'id': 'tzdb', 'kind': 'data', 'cite': 'IANA tz database'}]
    actors = [
        {'id': 'reed', 'kind': 'person', 'bloc': 'observer', 'track': True, 'name': 'John Reed', 'reed': ['John Reed']},
        {'id': 'mrc', 'kind': 'organ', 'bloc': 'soviet', 'name': 'Military Revolutionary Committee', 'reed': ['Military Revolutionary Committee'],
         'stance': [{'from': '1917-11-06', 's': 'support', 'ref': {'sec': 'App.III.7', 'q': 'At 1.35 the Post Office was occupied'}}]},
        {'id': 'pg', 'kind': 'organ', 'bloc': 'government', 'name': 'Provisional Government', 'reed': ['Provisional Government']},
        {'id': 'sailors', 'kind': 'unit', 'bloc': 'soviet', 'name': 'Sailors', 'reed': ['sailors']},
        {'id': 'red-guards', 'kind': 'unit', 'bloc': 'soviet', 'name': 'Red Guards', 'reed': ['Red Guards']},
    ]
    g = {'m': 'hand', 'on': '2026-10-29'}
    places = [
        {'id': 'smolny', 'kind': 'building', 'zone': 'city', 'll': [59.947473, 30.395867], 'acc': 60, 'conf': 'named', 'exists': True,
         'osm': 'relation/2133719', 'geo': g, 'name': 'Smolny Institute', 'reed': ['Smolny']},
        {'id': 'telegraph-agency', 'kind': 'building', 'zone': 'city', 'll': [59.9333, 30.3200], 'acc': 200, 'conf': 'conjectural',
         'exists': None, 'src': ['ref1917'], 'geo': g,
         'ctl0': {'state': 'held', 'holder': 'pg', 'as_of': '1917-11-06', 'ref': {'sec': 'App.III.7', 'q': 'occupied the Telegraph Agency'}},
         'name': 'Telegraph Agency', 'reed': ['Telegraph Agency'], 'ident': 'Address unknown.'},
        {'id': 'nevsky', 'kind': 'street', 'zone': 'city', 'll': [59.9345, 30.3300], 'acc': 2000, 'conf': 'named', 'geo': g,
         'name': 'Nevsky Prospekt', 'reed': ['Nevsky']},
        {'id': 'duma', 'kind': 'building', 'zone': 'city', 'll': [59.9339, 30.3290], 'acc': 30, 'conf': 'named', 'exists': True,
         'osm': 'way/1', 'geo': g, 'name': 'City Duma', 'reed': ['Duma']},
        {'id': 'winter-palace', 'kind': 'building', 'zone': 'city', 'll': [59.9405, 30.3145], 'acc': 60, 'conf': 'named', 'exists': True,
         'osm': 'way/2', 'geo': g, 'ctl0': {'state': 'held', 'holder': 'pg', 'as_of': '1917-11-07', 'ev': 'dan-bell'},
         'name': 'Winter Palace', 'reed': ['Palace']},
        {'id': 'pulkovo', 'kind': 'town', 'zone': 'front', 'll': [59.7714, 30.327], 'acc': 800, 'conf': 'named', 'geo': g,
         'name': 'Pulkovo', 'reed': ['Pulkovo']},
    ]
    events = [
        {'id': 'telegraph-occupied', 't': '1917-11-07T01:00', 'tq': 'stated', 'tp': 'At 1 A. M.', 'cal': 'none', 'sec': 'App.III.7',
         'loc': 'telegraph-agency', 'witness': 'reported', 'title': 'The Telegraph Agency occupied', 'sum': 'A detachment takes it.',
         'q': 'At 1 A. M. a detachment of soldiers and sailors from Smolny occupied the Telegraph Agency.',
         'moves': [{'who': 'mrc', 'size': 'a detachment of soldiers and sailors', 'from': 'smolny', 'to': 'telegraph-agency', 'mode': 'unknown', 'rc': 'none', 'stay': True}],
         'ctl': [{'place': 'telegraph-agency', 'state': 'held', 'holder': 'mrc'}],
         'present': [{'who': 'sailors', 'size': 'a detachment of soldiers and sailors', 'n': 20}]},
        {'id': 'reed-walks', 't': '1917-11-07T20:30', 'tq': 'inferred', 'tr': ['1917-11-07T20:00', '1917-11-07T21:00'], 'cal': 'NS',
         'dp': 'Wednesday, November 7th', 'sec': 'IV', 'loc': 'duma', 'witness': 'seen', 'title': 'Down the Nevsky',
         'why': 'Before the bell at 10.40.', 'sum': 'Reed walks to the Duma.', 'q': 'We walked down the Nevsky to the Duma',
         'moves': [{'who': 'reed', 'from': 'smolny', 'via': ['nevsky'], 'to': 'duma', 'mode': 'foot', 'rc': 'stated'}],
         'present': [{'who': 'sailors', 'place': 'nevsky', 'kit': ['flag:1'], 'say': ['Peace! Land!'], 'form': 'column', 'march': True, 'brief': True,
                      'ref': {'sec': 'IV', 'q': 'Sailors marched up the Nevsky in a column. A red flag crudely lettered in gold'}}]},
        {'id': 'dan-bell', 't': '1917-11-07T22:40', 'tq': 'stated', 'tp': 'It was 10.40 P. M.', 'cal': 'none', 'sec': 'IV', 'loc': 'duma',
         'witness': 'seen', 'title': 'The bell', 'sum': 'Dan rings the bell.', 'q': 'It was 10.40 P. M. when Dan rang the bell.',
         'present': [{'who': 'pg', 'place': 'winter-palace', 'ref': {'sec': 'App.III.7', 'q': 'the Military Revolutionary Committee of the Provisional Government'}}]},
        {'id': 'cornice', 't': '1917-11-08T03:05', 'tq': 'inferred', 'tr': ['1917-11-08T03:00', '1917-11-08T03:40'], 'cal': 'none',
         'sec': 'IV', 'loc': 'winter-palace', 'witness': 'seen', 'title': 'Broken stucco', 'why': 'After the palace fell.',
         'sum': 'Stucco on the pavement.',
         'q': ['Underfoot the sidewalk was littered with broken stucco', 'two shells from the battleship _Avrora_ had struck'],
         'moves': [{'who': 'reed', 'from': 'duma', 'to': 'winter-palace', 'mode': 'foot', 'rc': 'inferred'}],
         'ctl': [{'place': 'winter-palace', 'state': 'held', 'holder': 'mrc'}], 'tags': ['shooting'],
         'present': [{'who': 'sailors', 'place': 'winter-palace', 'fire': True, 'at': 'winter-palace', 'ref': {'sec': 'IV', 'q': 'two shells from the battleship _Avrora_ had struck'}},
                     {'who': 'red-guards', 'place': 'winter-palace', 'kit': ['armoured:2'], 'form': 'ring', 'fire': True, 'assault': 'repulsed', 'patrol': True,
                      'ref': {'sec': 'IV', 'q': 'Soviet troops surrounded the Palace and opened fire, with two armoured cars. The cars went cruising back and forth, their guns trained on the walls; waves of Red Guards, assaulting, crumpled under the fire.'}}]},
        {'id': 'holtzman', 't': '1917-11-13T02:55', 'tq': 'approx', 'tr': ['1917-11-13T02:30', '1917-11-13T03:00'],
         'tp': "almost three o'clock in the morning", 'cal': 'none', 'sec': 'IX', 'loc': 'smolny', 'witness': 'seen',
         'title': 'Kerensky is smashed', 'sum': 'Holtzman runs in with the telegram.',
         'q': "It was almost three o'clock in the morning when Holtzman came running.",
         'doc': {'at': 'pulkovo', 't': '1917-11-13T02:10', 'tp': '2.10 A.M.', 'cal': 'OS', 'dp': 'The night of October 30th to 31st',
                 'q': 'Pulkovo. Staff. 2.10 A.M. The night of October 30th to 31st will go down in history.'},
         'moves': [{'who': 'reed', 'from': 'winter-palace', 'to': 'smolny', 'mode': 'unknown', 'rc': 'none'}]},
    ]
    pictures = [{'id': 'pass', 'kind': 'facsimile', 'from': 'reed-1919', 'file': 'media/pass.png', 'w': 4, 'h': 3, 'scenes': ['dan-bell'],
                 'license': 'Public domain: printed in a book of 1919', 'url': 'https://example.org/book.pdf', 'page': 1, 'title': 'A pass',
                 'ref': {'sec': 'IV', 'q': 'Smolny was ablaze with lights.'}}]
    return {'meta': meta, 'sources': sources, 'actors': actors, 'places': places, 'events': events, 'pictures': pictures}


def png(path, w, h):
    """a small grey PNG, standard library only"""
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    raw = b''.join(b'\x00' + b'\x80\x80\x80' * w for _ in range(h))
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


def write(d, tmp):
    data = os.path.join(tmp, 'data')
    os.makedirs(data, exist_ok=True)
    os.makedirs(os.path.join(tmp, 'media'), exist_ok=True)
    png(os.path.join(tmp, 'media', 'pass.png'), 4, 3)
    for n, obj in d.items():
        text = L.canonical(n, obj if n == 'meta' else L.sort_table(n, obj))
        L.write_text(os.path.join(data, n + '.json'), text)
    text = os.path.join(tmp, 'sections.json')
    L.write_text(text, json.dumps(book_json()))
    return data, text


def errors(d, raw=None):
    with tempfile.TemporaryDirectory() as tmp:
        data, text = write(d, tmp)
        for name, content in (raw or {}).items():
            L.write_text(os.path.join(data, name + '.json'), content)
        _, F = C.run(data, text)
        return F.codes('ERROR')


def ev(d, i):
    return next(e for e in d['events'] if e['id'] == i)


def pl(d, i):
    return next(p for p in d['places'] if p['id'] == i)


class Fixture(unittest.TestCase):
    def test_good_fixture_passes(self):
        self.assertEqual(errors(good()), [])

    def test_formatter_is_idempotent(self):
        d = good()
        for n in L.TABLES:
            once = L.canonical(n, L.sort_table(n, d[n]))
            again = L.canonical(n, L.sort_table(n, json.loads(once)))
            self.assertEqual(once, again)


def case(code, mutate=None, raw=None, only=False):
    def test(self):
        d = good()
        if mutate:
            mutate(d)
        got = errors(d, raw(d) if raw else None)
        self.assertIn(code, got, f'expected {code}, got {got}')
        if only:
            self.assertEqual(set(got), {code}, f'expected only {code}, got {got}')
    return test


def _set(path_fn, key, value):
    def m(d):
        path_fn(d)[key] = value
    return m


def _del(path_fn, key):
    def m(d):
        del path_fn(d)[key]
    return m


class Breaks(unittest.TestCase):
    pass


CASES = {
    'json.duplicate-key': dict(raw=lambda d: {'sources': '[\n{"id": "a", "id": "b", "kind": "data", "cite": "x"}\n]\n'}),
    'json.syntax': dict(raw=lambda d: {'sources': '[{"id": }]'}),
    'fmt.layout': dict(raw=lambda d: {'sources': json.dumps(d['sources'], indent=4)}),
    'field.unknown': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'colour', 'red'), only=True),
    'field.missing': dict(mutate=_del(lambda d: ev(d, 'dan-bell'), 'title'), only=True),
    'field.type': dict(mutate=_set(lambda d: pl(d, 'duma'), 'acc', '30'), only=True),
    'field.enum': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'witness', 'overheard'), only=True),
    'field.pattern': dict(mutate=_set(lambda d: d['sources'][0], 'id', 'Elov_1923')),
    'field.length': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'title', 'x' * 61), only=True),
    'id.duplicate': dict(mutate=lambda d: d['sources'].append(dict(d['sources'][0]))),
    'ref.unknown': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'loc', 'nowhere')),
    'ref.cycle': dict(mutate=lambda d: (pl(d, 'nevsky').update({'in': 'duma'}), pl(d, 'duma').update({'in': 'nevsky'}))),
    'text.section-unknown': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'sec', 'XIII')),
    'quote.not-found': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'q', 'It was 10.40 P. M. when Dan rang the bells.'), only=True),
    'quote.not-unique': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'q', 'the'), only=True),
    'quote.order': dict(mutate=lambda d: ev(d, 'cornice').update({'q': list(reversed(ev(d, 'cornice')['q']))}), only=True),
    'phrase.not-near': dict(mutate=_set(lambda d: ev(d, 'holtzman'), 'tp', 'half-past four in the afternoon'), only=True),
    'spelling.not-in-book': dict(mutate=_set(lambda d: d['actors'][0], 'reed', ['Trotsky']), only=True),
    'time.format': dict(mutate=_set(lambda d: ev(d, 'telegraph-occupied'), 't', '1917-11-07 01:00')),
    'time.range': dict(mutate=_set(lambda d: ev(d, 'telegraph-occupied'), 't', '1917-08-01T01:00')),
    'time.bounds': dict(mutate=_set(lambda d: ev(d, 'reed-walks'), 't', '1917-11-07T21:30'), only=True),
    'time.tp-mismatch': dict(mutate=_set(lambda d: ev(d, 'telegraph-occupied'), 't', '1917-11-07T01:05'), only=True),
    'time.tp-unparsed': dict(mutate=_set(lambda d: ev(d, 'telegraph-occupied'), 'tp', 'At'), only=True),
    'date.dp-mismatch': dict(mutate=lambda d: ev(d, 'reed-walks').update({'dp': 'November 7th', 't': '1917-11-07T20:30'}) or
                             ev(d, 'holtzman')['doc'].update({'cal': 'NS'}), only=True),
    'date.dp-unparsed': dict(mutate=_set(lambda d: ev(d, 'reed-walks'), 'dp', 'Wednesday'), only=True),
    'date.weekday': dict(mutate=lambda d: ev(d, 'reed-walks').update({'dp': 'Thursday, November 16th', 't': '1917-11-16T12:00',
                                                                         'tr': ['1917-11-16T00:00', '1917-11-16T23:59']})),
    'date.cal-none': dict(mutate=_set(lambda d: ev(d, 'reed-walks'), 'cal', 'none'), only=True),
    'doc.after-event': dict(mutate=lambda d: ev(d, 'holtzman')['doc'].update({'t': '1917-11-13T03:10', 'tp': '3.10'})),
    'days.os': dict(mutate=lambda d: d['meta']['days'][0].update({'os': '1917-10-24'}), only=True),
    'geo.zone': dict(mutate=_set(lambda d: pl(d, 'pulkovo'), 'zone', 'city')),
    'geo.precision': dict(mutate=_set(lambda d: pl(d, 'nevsky'), 'll', [59.9345123, 30.33]), only=True),
    'geo.ll-required': dict(mutate=_set(lambda d: pl(d, 'nevsky'), 'll', None)),
    'geo.osm-required': dict(mutate=_del(lambda d: pl(d, 'duma'), 'osm'), only=True),
    'geo.osm-forbidden': dict(mutate=_set(lambda d: pl(d, 'duma'), 'exists', False), only=True),
    'geo.pending': dict(mutate=lambda d: pl(d, 'nevsky').update({'geo': {'m': 'pending'}}), only=True),
    'geo.parent-distance': dict(mutate=_set(lambda d: pl(d, 'telegraph-agency'), 'in', 'smolny'), only=True),
    'track.chain': dict(mutate=lambda d: ev(d, 'holtzman')['moves'][0].update({'from': 'duma'})),
    'track.seen-elsewhere': dict(mutate=_set(lambda d: ev(d, 'dan-bell'), 'loc', 'winter-palace'), only=True),
    'track.offmap-waypoint': dict(mutate=lambda d: (pl(d, 'pulkovo').update({'zone': 'offmap'}),
                                                    ev(d, 'reed-walks')['moves'][0].update({'via': ['pulkovo']}))),
    'ctl.kind': dict(mutate=lambda d: ev(d, 'cornice')['ctl'].append({'place': 'nevsky', 'state': 'held', 'holder': 'mrc'}), only=True),
    'ctl.state': dict(mutate=lambda d: ev(d, 'cornice')['ctl'][0].update({'state': 'besieged'}), only=True),
    'ctl0.after-first': dict(mutate=lambda d: pl(d, 'winter-palace')['ctl0'].update({'as_of': '1917-11-09'}), only=True),
    'evidence.missing': dict(mutate=lambda d: d['actors'][1]['stance'][0].pop('ref'), only=True),
    'stance.order': dict(mutate=lambda d: d['actors'][1]['stance'].append({'from': '1917-11-01', 's': 'support', 'ev': 'dan-bell'}), only=True),
    'speed.implausible': dict(mutate=lambda d: ev(d, 'dan-bell').update({'moves': [{'who': 'reed', 'from': 'duma', 'to': 'pulkovo', 'mode': 'foot', 'rc': 'none'},
                                                                                   {'who': 'reed', 'from': 'pulkovo', 'to': 'duma', 'mode': 'foot', 'rc': 'none'}]})),
}
for code, kw in CASES.items():
    setattr(Breaks, 'test_' + code.replace('.', '_').replace('-', '_'), case(code, **kw))
Breaks.test_ref_unknown_place_src = case('ref.unknown', mutate=_set(lambda d: pl(d, 'duma'), 'src', ['nobody']), only=True)
Breaks.test_event_without_a_quote = case('field.missing', mutate=_del(lambda d: ev(d, 'dan-bell'), 'q'), only=True)
Breaks.test_no_fact_checks = case('field.unknown', mutate=_set(lambda d: ev(d, 'cornice'), 'check', []), only=True)
# presence: who stays where between scenes
Breaks.test_presence_kind = case('presence.kind', mutate=lambda d: ev(d, 'dan-bell')['present'].append({'who': 'reed'}), only=True)
Breaks.test_presence_unnamed = case('presence.unnamed', mutate=lambda d: ev(d, 'dan-bell')['present'].append({'who': 'mrc'}), only=True)
Breaks.test_presence_unlocated = case('presence.unlocated', mutate=lambda d: (pl(d, 'nevsky').update({'ll': None, 'conf': 'unlocated'}), pl(d, 'nevsky').pop('acc'),
                                                                           ev(d, 'dan-bell')['present'].append({'who': 'mrc', 'place': 'nevsky', 'ref': {'sec': 'App.III.7', 'q': 'At 1.35 the Post Office was occupied by the Military Revolutionary Committee'}})), only=True)
Breaks.test_presence_not_there = case('presence.not-there', mutate=lambda d: ev(d, 'holtzman').update({'gone': [{'who': 'pg', 'place': 'winter-palace', 'ref': {'sec': 'App.III.7', 'q': 'the Military Revolutionary Committee of the Provisional Government'}}]}), only=True)
Breaks.test_kit_not_in_text = case('kit.not-in-text', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'kit': ['torch']}), only=True)
Breaks.test_kit_enum = case('field.enum', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'kit': ['cannonball']}), only=True)
Breaks.test_n_needs_size = case('field.missing', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].pop('size'), only=True)
Breaks.test_n_range = case('field.range', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'n': 500}), only=True)
# what a banner or a flag says: Reed's words, near the passage, on a banner or a flag he counts
Breaks.test_say_needs_a_flag = case('field.missing', mutate=lambda d: ev(d, 'reed-walks')['present'][0].pop('kit'), only=True)
Breaks.test_say_more_than_flags = case('field.range', mutate=lambda d: ev(d, 'reed-walks')['present'][0].update({'say': ['Peace! Land!', 'Peace!']}), only=True)
Breaks.test_say_not_near = case('phrase.not-near', mutate=lambda d: ev(d, 'reed-walks')['present'][0].update({'say': ['All power to the Soviets!']}), only=True)
Breaks.test_flag_is_not_a_banner = case('kit.not-in-text', mutate=lambda d: ev(d, 'reed-walks')['present'][0].update({'kit': ['banner:1']}), only=True)
# formations: each with its word in the passage or the size phrase; a body on the move is a brief column
Breaks.test_form_not_in_text = case('form.not-in-text', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'form': 'ranks'}), only=True)
Breaks.test_form_enum = case('field.enum', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'form': 'square'}), only=True)
Breaks.test_march_needs_brief = case('field.missing', mutate=lambda d: ev(d, 'reed-walks')['present'][0].pop('brief'), only=True)
Breaks.test_march_not_in_text = case('form.not-in-text', mutate=lambda d: ev(d, 'telegraph-occupied')['present'][0].update({'form': 'column', 'march': True, 'brief': True}), only=True)
# which way a marching body goes is its facing ("Sailors marched up the Nevsky"); a bridge opened needs the words
def _standing_heading(d):   # the same words, but the body stands: "up the" is no word for looking
    r = ev(d, 'reed-walks')['present'][0]
    r.update({'face': 'duma'}); r.pop('march'); r.pop('form')
Breaks.test_heading_needs_a_march = case('form.not-in-text', mutate=_standing_heading)
Breaks.test_raised_needs_a_bridge = case('ref.unknown', mutate=lambda d: ev(d, 'reed-walks').update({'raised': ['nevsky']}))
Breaks.test_raised_needs_its_words = case('fight.not-in-text', mutate=lambda d: ev(d, 'reed-walks').update({'raised': ['nevsky']}))
# the fighting: who fires, at what, from the windows or not; who lies dead or flat; who runs at the enemy
def _cornice_fire(d):
    return ev(d, 'cornice')['present'][0]
Breaks.test_fire_needs_the_tag = case('tag.shooting', mutate=lambda d: ev(d, 'cornice').pop('tags'), only=True)
Breaks.test_fire_from_windows_needs_the_word = case('fight.not-in-text', mutate=lambda d: _cornice_fire(d).update({'fire': 'windows'}), only=True)
Breaks.test_fire_enum = case('field.enum', mutate=lambda d: _cornice_fire(d).update({'fire': 'cannon'}), only=True)
Breaks.test_fire_at_unknown = case('ref.unknown', mutate=lambda d: _cornice_fire(d).update({'at': 'nowhere'}), only=True)
Breaks.test_at_needs_fire = case('field.missing', mutate=lambda d: _cornice_fire(d).pop('fire'), only=True)
Breaks.test_pose_needs_its_words = case('fight.not-in-text', mutate=lambda d: _cornice_fire(d).update({'pose': 'fallen'}), only=True)
Breaks.test_pose_enum = case('field.enum', mutate=lambda d: _cornice_fire(d).update({'pose': 'kneeling'}), only=True)
Breaks.test_run_needs_its_word = case('fight.not-in-text', mutate=lambda d: ev(d, 'cornice')['moves'][0].update({'run': True}), only=True)
# a body that surrounds a building, assaults it, cruises round it in its cars
def _ring(d):
    return ev(d, 'cornice')['present'][1]
_FIRST = 'Soviet troops surrounded the Palace and opened fire, with two armoured cars.'
Breaks.test_ring_not_in_text = case('form.not-in-text', mutate=lambda d: _cornice_fire(d).update({'form': 'ring'}), only=True)
Breaks.test_ring_needs_a_building = case('form.ring-place', mutate=lambda d: _ring(d).update({'place': 'nevsky'}), only=True)
Breaks.test_lane_needs_its_words = case('form.not-in-text', mutate=lambda d: _cornice_fire(d).update({'form': 'lane'}), only=True)
Breaks.test_assault_enum = case('field.enum', mutate=lambda d: _ring(d).update({'assault': 'won'}), only=True)
Breaks.test_assault_repulsed_needs_its_words = case('fight.not-in-text', mutate=lambda d: (_ring(d).pop('patrol'), _ring(d)['ref'].update({'q': _FIRST})), only=True)
Breaks.test_assault_carried_needs_its_words = case('fight.not-in-text', mutate=lambda d: _ring(d).update({'assault': 'carried'}), only=True)
Breaks.test_patrol_needs_its_words = case('fight.not-in-text', mutate=lambda d: (_ring(d).pop('assault'), _ring(d)['ref'].update({'q': _FIRST})), only=True)
Breaks.test_patrol_needs_a_vehicle = case('field.missing', mutate=lambda d: _ring(d).pop('kit'), only=True)
# what a body looks at: a known place or body, with Reed's word for looking
Breaks.test_face_needs_its_word = case('form.not-in-text', mutate=lambda d: _cornice_fire(d).update({'face': 'duma'}), only=True)
Breaks.test_face_unknown = case('ref.unknown', mutate=lambda d: _ring(d).update({'face': 'nowhere'}), only=True)
# a body indoors: in a building, with Reed's word for it, and not formed up or firing in the open
Breaks.test_inside_needs_its_word = case('form.not-in-text', mutate=lambda d: ev(d, 'dan-bell')['present'][0].update({'inside': True}), only=True)
Breaks.test_inside_does_not_form_up = case('field.range', mutate=lambda d: ev(d, 'dan-bell').update({'present': [{'who': 'pg', 'place': 'winter-palace', 'inside': True, 'form': 'line', 'size': 'Smolny was ablaze with lights', 'ref': {'sec': 'IV', 'q': 'Underfoot the sidewalk was littered with broken stucco, from the cornice of the Palace'}}]}))
Breaks.test_tag_shooting = case('tag.shooting', mutate=lambda d: ev(d, 'dan-bell').update({'tags': ['shooting']}), only=True)
Breaks.test_geo_stage = case('geo.stage', mutate=lambda d: pl(d, 'duma').update({'stage': [59.95, 30.33]}), only=True)
Breaks.test_stay_kind = case('presence.kind', mutate=lambda d: ev(d, 'reed-walks')['moves'][0].update({'stay': True}), only=True)
# pictures: the file, its size, its licence, Reed's caption
Breaks.test_picture_file = case('picture.file', mutate=lambda d: d['pictures'][0].update({'file': 'media/none.png'}), only=True)
Breaks.test_picture_size = case('picture.size', mutate=lambda d: d['pictures'][0].update({'w': 5}), only=True)
Breaks.test_picture_license = case('picture.license', mutate=lambda d: d['pictures'][0].update({'license': 'CC BY-SA 4.0'}), only=True)
Breaks.test_picture_license_needs_its_rule = case('picture.license', mutate=lambda d: d['pictures'][0].update({'license': 'Public domain (Wikimedia Commons)'}), only=True)
Breaks.test_picture_needs_caption = case('field.missing', mutate=lambda d: d['pictures'][0].pop('ref'), only=True)
Breaks.test_picture_scene = case('ref.unknown', mutate=lambda d: d['pictures'][0].update({'scenes': ['nowhere']}), only=True)
Breaks.test_picture_caption_quote = case('quote.not-found', mutate=lambda d: d['pictures'][0]['ref'].update({'q': 'Smolny was ablaze with light.'}), only=True)
Breaks.test_picture_commons_needs_author = case('field.missing', mutate=lambda d: (d['pictures'][0].update({'from': 'commons', 'caption': 'A pass.', 'date': '1917'}), d['pictures'][0].pop('ref')), only=True)


class Implicit(unittest.TestCase):
    """a presence without `place` stands at its scene's place, and the checks that need the place's kind use that"""
    def test_ring_at_the_scene_place(self):
        d = good()
        ev(d, 'cornice')['present'][1].pop('place')          # the cornice scene is at the Winter Palace, a building
        self.assertEqual(errors(d), [])

    def test_inside_at_the_scene_place(self):
        d = good()
        ev(d, 'cornice')['present'].append({'who': 'pg', 'inside': True, 'ref': {'sec': 'IV', 'q': 'Underfoot the sidewalk was littered with broken stucco, from the cornice of the Palace'}})
        got = errors(d)
        self.assertNotIn('field.range', got, got)   # the place (the scene's, a building) is fine
        self.assertIn('form.not-in-text', got, got)   # but the passage has no word for indoors


class Review(unittest.TestCase):
    """defects the code review found in the checker"""
    def test_a_list_where_a_word_belongs_is_reported_not_a_crash(self):
        d = good()
        ev(d, 'cornice')['present'][0]['pose'] = ['fallen']
        self.assertIn('field.type', errors(d))

    def test_face_own_place_when_the_place_is_implicit(self):
        d = good()
        r = ev(d, 'cornice')['present'][1]
        r.pop('place'); r['face'] = 'winter-palace'   # the scene's place, the body's own
        self.assertIn('field.range', errors(d))

    def test_inside_inherited_by_a_later_ring(self):
        d = good()
        ev(d, 'dan-bell')['present'] = [{'who': 'red-guards', 'place': 'winter-palace', 'inside': True,
                                         'ref': {'sec': 'IV', 'q': 'Underfoot the sidewalk was littered with broken stucco, from the cornice of the Palace'}}]
        got = errors(d)
        self.assertTrue(any(c == 'field.range' for c in got), got)   # the cornice's later ring inherits inside


class Presence(unittest.TestCase):
    def spans(self, d):
        evs = L.sort_table('events', d['events'])
        return [(s['who'], s['place'], evs[s['start']]['id'] if s['start'] < len(evs) else None,
                 evs[s['end']]['id'] if s['end'] is not None and s['end'] < len(evs) else s['end'], s['end_by'])
                for s in L.presence_spans(evs, d['actors'], d['places'])[0]]

    def test_fixture_spans(self):
        got = self.spans(good())
        # the sailors stay; the detachment that moved in stays from the next scene; the government's
        # people leave the palace after the scene in which it falls to the other side
        self.assertIn(('sailors', 'telegraph-agency', 'telegraph-occupied', None, None), got)
        self.assertIn(('mrc', 'telegraph-agency', 'reed-walks', None, None), got)
        self.assertIn(('pg', 'winter-palace', 'dan-bell', 'holtzman', 'control'), got)

    def test_brief_and_gone(self):
        d = good()
        ev(d, 'telegraph-occupied')['present'][0]['brief'] = True
        self.assertIn(('sailors', 'telegraph-agency', 'telegraph-occupied', 'reed-walks', 'brief'), self.spans(d))
        d = good()
        ev(d, 'reed-walks')['gone'] = [{'who': 'sailors', 'place': 'telegraph-agency', 'ref': {'sec': 'App.III.7', 'q': 'a detachment of soldiers and sailors'}}]
        self.assertIn(('sailors', 'telegraph-agency', 'telegraph-occupied', 'dan-bell', 'gone'), self.spans(d))
        self.assertEqual(errors(d), [])


    def test_formation_is_the_scenes(self):
        # a formation holds only in the span that states it; a column marching past is a body of its own
        acts = [{'id': 'g', 'kind': 'unit', 'bloc': 'soviet'}]
        pls = [{'id': 'nevsky', 'kind': 'street'}]
        evs = [{'id': 'a', 'loc': 'nevsky', 'present': [{'who': 'g', 'kit': ['fire'], 'form': 'line'}]},
               {'id': 'b', 'loc': 'nevsky', 'present': [{'who': 'g', 'size': 'more of them'}]},
               {'id': 'c', 'loc': 'nevsky', 'present': [{'who': 'g', 'form': 'column', 'march': True, 'brief': True}]},
               {'id': 'd', 'loc': 'nevsky', 'present': [{'who': 'g', 'brief': True}]}]
        sp = L.presence_spans(evs, acts, pls)[0]
        by = {(s['ev'], s['end_by']): s for s in sp}
        self.assertEqual(by[('a', 'update')].get('form'), 'line')
        self.assertNotIn('form', by[('b', None)])                         # carried on, but not its formation
        self.assertEqual(by[('b', None)].get('kit'), ['fire'])
        self.assertEqual((by[('c', 'brief')].get('form'), by[('c', 'brief')].get('kit')), ('column', None))   # passing: nothing absorbed
        self.assertEqual(by[('d', 'brief')].get('kit'), ['fire'])         # an ordinary brief adds to the body there


class Parsers(unittest.TestCase):
    def test_time_phrases(self):
        self.assertEqual(L.parse_tp('At 1 A. M.'), {(1, 0)})
        self.assertEqual(L.parse_tp('At 1.35 the Post Office'), {(1, 35), (13, 35)})
        self.assertEqual(L.parse_tp('It was 10.40 P. M.'), {(22, 40)})
        self.assertEqual(L.parse_tp('It was exactly 5:17 A.M.'), {(5, 17)})
        self.assertEqual(L.parse_tp('38 minutes past 9 a. m.'), {(9, 38)})
        self.assertEqual(L.parse_tp("almost three o'clock in the morning"), {(3, 0)})
        self.assertEqual(L.parse_tp('at five o’clock'), {(5, 0), (17, 0)})
        self.assertEqual(L.parse_tp('at midnight'), {(0, 0)})
        self.assertEqual(L.parse_tp('toward evening'), set())
        self.assertEqual(L.parse_tp('At ten in the evening Lenin addressed'), {(22, 0)})
        self.assertEqual(L.parse_tp('At seven in the morning he sent word'), {(7, 0)})

    def test_date_phrases(self):
        ns, wd = L.parse_dp('Wednesday, November 7th', 'NS')
        self.assertEqual((ns, wd), ([dt.date(1917, 11, 7)], 2))
        ns, _ = L.parse_dp('The night of October 30th to 31st', 'OS')
        self.assertEqual(ns, [dt.date(1917, 11, 12), dt.date(1917, 11, 13), dt.date(1917, 11, 14)])
        ns, wd = L.parse_dp('Thursday, November 16th', 'OS')
        self.assertEqual(ns[0].weekday(), wd)                      # 29 Nov NS was a Thursday
        ns, wd = L.parse_dp('Thursday, November 16th', 'NS')
        self.assertNotEqual(ns[0].weekday(), wd)                   # 16 Nov NS was a Friday
        ns, _ = L.parse_dp('6th of November, 1917', 'OS')
        self.assertEqual(ns, [dt.date(1917, 11, 19)])
        ns, _ = L.parse_dp('On the morning of the 5th', 'OS', dt.date(1917, 11, 18))
        self.assertIn(dt.date(1917, 11, 18), ns)

    def test_sun(self):
        # 7 Nov 1917, Palace Square, clock UTC+3:01: sunrise about 08:36, sunset about 16:51
        off = dt.timedelta(minutes=181.3)
        el = lambda h, m: L.sun_elevation(59.9398, 30.3146, dt.datetime(1917, 11, 7, h, m) - off)
        self.assertLess(el(8, 0), -0.83)
        self.assertGreater(el(9, 15), -0.83)
        self.assertGreater(el(16, 30), -0.83)
        self.assertLess(el(17, 15), -0.83)
        self.assertLess(el(1, 0), -18)


REAL_DATA = os.path.join(ROOT, 'data')
REAL_TEXT = os.path.join(ROOT, 'cache', 'sections.json')


@unittest.skipUnless(os.path.exists(os.path.join(REAL_DATA, 'events.json')) and os.path.exists(REAL_TEXT),
                     'needs data/ and cache/sections.json')
class RealData(unittest.TestCase):
    def load(self):
        # the who's who and the pictures too: a scene's speaker is a person in it, and a faction's photograph a picture
        return {n: L.load_json(os.path.join(REAL_DATA, n + '.json')) for n in ['meta'] + L.TABLES + ['pictures', 'factions', 'people']}

    def errors(self, d):
        with tempfile.TemporaryDirectory() as tmp:
            data = os.path.join(tmp, 'data')
            os.makedirs(data)
            os.symlink(os.path.join(ROOT, 'media'), os.path.join(tmp, 'media'))   # the pictures' files, beside data/
            for n, obj in d.items():
                text = L.canonical(n, obj if n == 'meta' else L.sort_table(n, obj))
                L.write_text(os.path.join(data, n + '.json'), text)
            _, F = C.run(data, REAL_TEXT)
            return F.codes('ERROR')

    def test_real_data_passes(self):
        self.assertEqual(self.errors(self.load()), [])

    def test_one_character_breaks_a_quote(self):
        d = self.load()
        e = next(e for e in d['events'] if isinstance(e.get('q'), str) and len(e['q']) > 20)
        e['q'] = e['q'][:10] + ('X' if e['q'][10] != 'X' else 'Y') + e['q'][11:]
        self.assertIn('quote.not-found', self.errors(d))

    def test_pulkovo_bulletin_is_old_style(self):
        d = self.load()
        docs = [e for e in d['events'] if e.get('doc', {}).get('cal') == 'OS' and 'dp' in e['doc']]
        self.assertTrue(docs, 'expected at least one Old Style document')
        docs[0]['doc']['cal'] = 'NS'
        self.assertIn('date.dp-mismatch', self.errors(d))

    def test_moving_reed_breaks_his_track(self):
        d = self.load()
        seen = [e for e in d['events'] if e.get('witness') == 'seen' and not any(m.get('who') == 'reed' for m in e.get('moves', []))]
        far = next(p['id'] for p in d['places'] if p.get('zone') == 'front' and p.get('ll'))
        seen[len(seen) // 2]['loc'] = far
        self.assertIn('track.seen-elsewhere', self.errors(d))


if __name__ == '__main__':
    unittest.main()


class Heading(unittest.TestCase):
    def test_a_marching_body_faces_the_way_it_goes(self):
        d = good()
        ev(d, 'reed-walks')['present'][0]['face'] = 'duma'
        self.assertFalse(errors(d), 'a column that "marched up the Nevsky" may face the way it goes')


class Outside(unittest.TestCase):
    """a body Reed does not give, from another source, checked against that source's words"""
    def body(self, d, **o):
        r = {'who': 'red-guards', 'place': 'winter-palace', 'size': 'a detachment of Red Guards', 'brief': True,
             'outside': dict({'source': 'ref1917', 'q': 'A detachment of Red Guards stood at the palace.'}, **o)}
        ev(d, 'cornice')['present'].append(r)
        return r

    def test_backed_by_its_source(self):
        d = good(); self.body(d)
        self.assertFalse(errors(d))

    def test_unknown_source(self):
        d = good(); self.body(d, source='nowhere')
        self.assertIn('ref.unknown', errors(d))

    def test_needs_the_sources_words(self):
        d = good(); self.body(d, q='')
        self.assertIn('field.missing', errors(d))

    def test_the_source_must_name_the_body(self):
        d = good(); self.body(d, q='Somebody stood at the palace.')
        self.assertIn('presence.unnamed', errors(d))

    def test_size_must_be_the_sources(self):
        d = good(); self.body(d)['size'] = 'an interminable column of soldiers'
        self.assertIn('phrase.not-near', errors(d), 'an unchecked size must not vouch for a formation')

    def test_size_from_the_sources_english(self):
        d = good(); r = self.body(d, q='Отряд красногвардейцев стоял у дворца.', en='A detachment of Red Guards stood at the palace.')
        self.assertFalse(errors(d), 'a source in Russian is checked against its English too')

    def test_banner_words_must_be_the_sources(self):
        d = good(); r = self.body(d); r['kit'] = ['banner:1']; r['say'] = ['Words Reed never wrote']
        self.assertIn('phrase.not-near', errors(d))

    def test_kit_needs_the_sources_word(self):
        d = good(); self.body(d)['kit'] = ['gun:1']
        self.assertIn('kit.not-in-text', errors(d))

    def test_reeds_body_placed_by_another_source(self):
        d = good(); r = ev(d, 'cornice')['present'][0]
        r['outside'] = {'source': 'ref1917', 'q': 'The gun fired from the embankment.'}
        self.assertFalse(errors(d), 'Reed backs the body; the source only says where it stood')
        r['outside']['source'] = 'nowhere'
        self.assertIn('ref.unknown', errors(d))


class Done(unittest.TestCase):
    """a move told as already over: allowed when Reed did not see it, and not as a skip"""
    def move(self, d, eid='telegraph-occupied'):
        m = ev(d, eid)['moves'][0]; m['done'] = True
        return m

    def test_told_move_may_be_done(self):
        d = good(); self.move(d)
        self.assertFalse(errors(d))

    def test_not_in_a_scene_reed_sees(self):
        d = good(); self.move(d, 'reed-walks')
        self.assertIn('move.done', errors(d))

    def test_not_with_gap(self):
        d = good(); self.move(d)['gap'] = True
        self.assertIn('move.done', errors(d))


class Glossary(unittest.TestCase):
    """the who's who: Reed's words checked against the text, the rest cited, the links held"""
    def add(self, d):
        d['factions'] = [{'id': 'mrc-f', 'kind': 'committee', 'group': 'soviets', 'order': 1, 'side': 'for', 'actors': ['mrc'], 'members': ['holtzman-p'],
                          'name': 'Military Revolutionary Committee', 'names': ['Military Revolutionary Committee'], 'sum': 'It takes the city.',
                          'def': {'sec': 'App.III.7', 'q': 'occupied by the Military Revolutionary Committee'},
                          'background': {'source': 'ref1917', 'url': 'https://example.org/mrc', 'en': 'Set up by the Petrograd Soviet.'}}]
        d['people'] = [{'id': 'holtzman-p', 'factions': ['mrc-f'], 'name': 'Holtzman', 'names': ['Holtzman'], 'role': 'A messenger',
                        'bio': {'source': 'ref1917', 'url': 'https://example.org/h', 'en': 'He ran.'}}]
        return d['factions'][0], d['people'][0]

    def test_a_good_entry_passes(self):
        d = good(); self.add(d)
        self.assertFalse(errors(d))

    def test_reeds_words_must_be_his(self):
        d = good(); f, _ = self.add(d); f['def']['q'] = 'the committee took everything'
        self.assertIn('quote.not-found', errors(d))

    def test_names_must_be_reeds(self):
        d = good(); f, _ = self.add(d); f['names'] = ['MRC']
        self.assertIn('glossary.name', errors(d))

    def test_members_name_their_faction(self):
        d = good(); _, p = self.add(d); p['factions'] = []
        self.assertIn('glossary.member', errors(d))

    def test_what_is_not_in_reed_cites_a_source(self):
        d = good(); _, p = self.add(d); p['bio']['source'] = 'nowhere'
        self.assertIn('ref.unknown', errors(d))

    def test_side_is_one_of_the_four(self):
        d = good(); f, _ = self.add(d); f['side'] = 'neutral'
        self.assertIn('field.enum', errors(d))


class Hall(unittest.TestCase):
    """a meeting-hall in its building: who sits where, who walks out (all or part), the house's response,
    the speaker at the tribune and the end of the session, each with Reed's words"""
    def add(self, d):
        g = {'m': 'hand', 'on': '2026-10-29'}
        d['places'].append({'id': 'hall', 'kind': 'room', 'zone': 'city', 'in': 'smolny', 'll': [59.947473, 30.395867], 'acc': 60,
                            'conf': 'named', 'geo': g, 'name': 'The great hall', 'reed': ['great meeting-hall'],
                            'hall': {'ll': [59.9472, 30.3962], 'dims': [40, 18], 'axis': 180, 'plan': 'rows',
                                     'features': [{'k': 'chandeliers', 'ref': {'sec': 'V', 'q': 'under the white chandeliers'}}]}})
        Glossary.add(self, d)
        d['factions'][0]['members'].append('kam-p')
        d['people'].append({'id': 'kam-p', 'factions': ['mrc-f'], 'name': 'Kameniev', 'names': ['Kameniev'], 'role': 'In the chair',
                            'bio': {'source': 'ref1917', 'url': 'https://example.org/k', 'en': 'He chaired.'}})
        base = {'tq': 'inferred', 'cal': 'none', 'sec': 'V', 'loc': 'hall', 'witness': 'reported', 'why': 'In the night.', 'sum': 'In the hall.'}
        d['events'] += [
            dict(base, id='session', t='1917-11-08T01:00', tr=['1917-11-08T00:30', '1917-11-08T01:30'], title='The session',
                 q='So we came into the great meeting-hall', speaker='kam-p',
                 house={'pose': 'vote', 'ref': {'sec': 'V', 'q': 'Kameniev asked all in favour to hold up their cards.'}},
                 present=[{'who': 'red-guards', 'size': 'The Red Guards', 'n': 20, 'bench': 'left', 'ref': {'sec': 'V', 'q': 'The Red Guards sat on the left.'}},
                          {'who': 'sailors', 'size': 'Fifty delegates', 'n': 10, 'bench': 'platform', 'ref': {'sec': 'V', 'q': 'On the platform sat the presidium, the Sailors among them.'}}]),
            dict(base, id='leaving', t='1917-11-08T01:40', tr=['1917-11-08T01:35', '1917-11-08T01:50'], title='Some leave',
                 q='Only part of the Sailors left the Congress',
                 present=[{'who': 'sailors', 'size': 'Only part of the Sailors', 'n': 3, 'walkout': True, 'part': True,
                           'ref': {'sec': 'V', 'q': 'Only part of the Sailors left the Congress; the rest were going to stay.'}}]),
            dict(base, id='over', t='1917-11-08T02:00', tr=['1917-11-08T01:55', '1917-11-08T02:30'], title='Dissolved',
                 q='And thereupon the Congress was dissolved.',
                 gone=[{'who': 'red-guards', 'place': 'hall', 'all': True, 'ref': {'sec': 'V', 'q': 'And thereupon the Congress was dissolved.'}}]),
        ]
        return ev(d, 'session'), ev(d, 'leaving'), ev(d, 'over'), pl(d, 'hall')

    def test_a_good_hall_passes(self):
        d = good(); self.add(d)
        self.assertEqual(errors(d), [])

    def test_a_hall_is_a_room_of_a_fit_size(self):
        d = good(); *_, h = self.add(d); h['kind'] = 'building'
        self.assertIn('hall.kind', errors(d))
        d = good(); *_, h = self.add(d); h['hall']['dims'] = [400, 18]
        self.assertIn('field.range', errors(d))

    def test_a_feature_needs_its_word(self):
        d = good(); *_, h = self.add(d); h['hall']['features'][0]['k'] = 'columns'
        self.assertIn('phrase.not-in-text', errors(d))

    def test_benches_only_in_a_hall(self):
        d = good(); self.add(d); ev(d, 'reed-walks')['present'][0]['bench'] = 'left'
        self.assertIn('hall.none', errors(d))

    def test_the_platform_needs_its_word(self):
        d = good(); s, *_ = self.add(d); s['present'][0]['bench'] = 'platform'
        self.assertIn('phrase.not-in-text', errors(d))

    def test_a_walkout_needs_its_words(self):
        d = good(); _, l, *_ = self.add(d); l['present'][0]['ref']['q'] = 'the rest were going to stay.'
        self.assertIn('phrase.not-in-text', errors(d))

    def test_part_only_for_a_walkout(self):
        d = good(); s, *_ = self.add(d); s['present'][0]['part'] = True
        self.assertIn('phrase.not-in-text', errors(d))

    def test_the_house_needs_its_word(self):
        d = good(); s, *_ = self.add(d); s['house']['pose'] = 'cheer'
        self.assertIn('phrase.not-in-text', errors(d))

    def test_the_speaker_is_a_person_in_the_hall(self):
        d = good(); s, *_ = self.add(d); s['speaker'] = 'nobody'
        self.assertIn('ref.unknown', errors(d))
        d = good(); self.add(d); ev(d, 'dan-bell')['speaker'] = 'kam-p'
        self.assertIn('hall.none', errors(d))

    def test_all_needs_words_for_the_end(self):
        d = good(); *_, o, _ = self.add(d); o['gone'][0]['ref']['q'] = 'Kameniev rang the bell.'
        self.assertIn('phrase.not-in-text', errors(d))

    def test_spans(self):
        d = good(); self.add(d)
        evs = L.sort_table('events', d['events'])
        ids = [e['id'] for e in evs]
        sp = L.presence_spans(evs, d['actors'], d['places'])[0]
        at = lambda who, i: [(s.get('n'), s.get('walkout'), s['end_by']) for s in sp
                             if s['who'] == who and s['place'] == 'hall' and s['start'] <= i and (s['end'] is None or i < s['end'])]
        i0, i1, i2 = ids.index('session'), ids.index('leaving'), ids.index('over')
        self.assertEqual(at('sailors', i0), [(10, None, 'walkout')])
        # part of them leave: the rest, fewer by the leavers, stay in their seats until the session is over
        self.assertEqual(sorted(at('sailors', i1), key=str), sorted([(7, None, 'gone'), (3, True, 'walkout')], key=str))
        self.assertEqual(at('sailors', i2), [(7, None, 'gone')])
        self.assertEqual(at('red-guards', i2), [(20, None, 'gone')])
        self.assertEqual(at('red-guards', i2 + 1) + at('sailors', i2 + 1), [])

    # the review's cases: each word, each combination the checker must refuse
    def test_a_walkin_needs_its_words(self):
        d = good(); s, *_ = self.add(d); s['present'][1]['walkin'] = True
        self.assertIn('phrase.not-in-text', errors(d))

    def test_a_walkout_is_not_brief_nor_a_walkin(self):
        d = good(); _, l, *_ = self.add(d); l['present'][0]['brief'] = True
        self.assertIn('field.range', errors(d))
        d = good(); _, l, *_ = self.add(d); l['present'][0]['walkin'] = True
        self.assertIn('field.range', errors(d))

    def test_the_house_only_in_a_hall_and_its_own_scene(self):
        d = good(); self.add(d); ev(d, 'dan-bell')['house'] = {'pose': 'vote', 'ref': {'sec': 'V', 'q': 'Kameniev asked all in favour to hold up their cards.'}}
        self.assertIn('hall.none', errors(d))
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'stand', 'ref': {'sec': 'IX', 'q': 'The hall rose, thundering.'}}
        self.assertIn('phrase.not-near', errors(d))

    def test_the_speaker_is_named_as_a_whole_word(self):
        d = good(); s, *_ = self.add(d); s['speaker'] = 'holtzman-p'
        self.assertIn('presence.unnamed', errors(d))
        d = good(); s, *_ = self.add(d)
        d['people'].append({'id': 'kamen-p', 'factions': ['mrc-f'], 'name': 'Kamen', 'names': ['Kamen'], 'role': 'Nobody',
                            'bio': {'source': 'ref1917', 'url': 'https://example.org/x', 'en': 'Not here.'}}); d['factions'][0]['members'].append('kamen-p')
        s['speaker'] = 'kamen-p'
        self.assertIn('presence.unnamed', errors(d))

    def test_a_bad_bench(self):
        d = good(); s, *_ = self.add(d); s['present'][0]['bench'] = 'balcony'
        self.assertIn('field.enum', errors(d))
        d = good(); s, *_ = self.add(d); s['present'][0]['bench'] = ['left']
        self.assertIn('field.type', errors(d))

    def test_part_needs_its_words_and_a_number(self):
        d = good(); _, l, *_ = self.add(d); l['present'][0]['ref']['q'] = 'Fifty delegates got up and pushed their way out'; l['present'][0]['size'] = 'Fifty delegates'
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); _, l, *_ = self.add(d); del l['present'][0]['n']
        self.assertIn('field.missing', errors(d))

    def test_prop_needs_a_count(self):
        d = good(); s, *_ = self.add(d); s['present'][0]['prop'] = 'the presidium'
        self.assertIn('field.missing', errors(d))

    def test_part_spans_without_a_number_and_with_all_of_them(self):
        acts = [{'id': 'g', 'kind': 'party', 'bloc': 'opposition'}]
        pls = [{'id': 'hall', 'kind': 'room'}]
        evs = [{'id': 'a', 'loc': 'hall', 'present': [{'who': 'g', 'n': 10}]},
               {'id': 'b', 'loc': 'hall', 'present': [{'who': 'g', 'walkout': True, 'part': True}]},
               {'id': 'c', 'loc': 'hall'}]
        sp = L.presence_spans(evs, acts, pls)[0]
        at = lambda i: sorted((s.get('n'), s['end_by'] or '') for s in sp if s['start'] <= i and (s['end'] is None or i < s['end']))
        self.assertEqual(at(1), [(5, ''), (5, 'walkout')])   # half of them leave when Reed gives no number
        self.assertEqual(at(2), [(5, '')])
        evs[1]['present'][0]['n'] = 10                           # all of them: nobody is left behind
        sp = L.presence_spans(evs, acts, pls)[0]
        self.assertEqual(at(2), [])

    def test_all_ends_the_others_without_its_own(self):
        d = good(); s, *_ = self.add(d); s['present'] = s['present'][1:]   # the Red Guards never sat there
        self.assertEqual(errors(d), [])
        evs = L.sort_table('events', d['events']); ids = [e['id'] for e in evs]
        sp = L.presence_spans(evs, d['actors'], d['places'])[0]
        self.assertFalse([x for x in sp if x['place'] == 'hall' and (x['end'] is None or x['end'] > ids.index('over') + 1)])   # shown in its scene, gone after it

    # phase 2: the speaker who leaves, the embrace, the empty frame, two brief words on one body
    def test_the_speaker_leaves_in_words(self):
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': '"I\'m going now!" answered Kameniev, and left the platform.'}
        self.assertEqual(errors(d), [])
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': 'Kameniev asked all in favour to hold up their cards.'}
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); s, *_ = self.add(d); del s['speaker']; s['speaker_out'] = {'sec': 'V', 'q': '"I\'m going now!" answered Kameniev, and left the platform.'}
        self.assertIn('field.missing', errors(d))

    def test_the_embrace_is_two_bodies_on_the_platform_one_walking_in(self):
        q = {'sec': 'V', 'q': 'On the platform sat the presidium, the Sailors among them.'}
        e = {'sec': 'V', 'q': 'The Sailors and the Red Guards were embracing'}
        def two(d, s):
            s['present'][0].update({'bench': 'platform', 'pose': 'embrace', 'ref': {'sec': 'V', 'q': 'The Sailors and the Red Guards were embracing'}})
            s['present'].append({'who': 'red-guards', 'bench': 'platform', 'ref': q})
            s['present'][1].update({'pose': 'embrace', 'walkin': True, 'ref': e})
        d = good(); s, *_ = self.add(d); s['present'] = [s['present'][1], {'who': 'red-guards', 'ref': dict(q)}]
        s['present'][0].update({'pose': 'embrace', 'ref': dict(e)}); del s['present'][0]['bench']   # a lone embrace, on the benches
        self.assertIn('field.range', errors(d))
        d = good(); s, *_ = self.add(d); s['present'][1]['pose'] = 'embrace'   # no word for it
        self.assertIn('fight.not-in-text', errors(d))
        d = good(); self.add(d); ev(d, 'reed-walks')['present'][0]['pose'] = 'embrace'
        self.assertIn('hall.none', errors(d))

    def test_a_whole_hall_does_not_embrace(self):
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'embrace', 'ref': {'sec': 'V', 'q': 'The Sailors and the Red Guards were embracing'}}
        self.assertIn('field.enum', errors(d))

    def test_the_speaker_leaving_is_named_and_not_coming_in(self):
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': 'Fifty delegates got up and pushed their way out'}
        self.assertIn('presence.unnamed', errors(d))
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': '"I\'m going now!" answered Kameniev, and left the platform.'}
        s['present'][0]['walkin'] = True; s['present'][0]['ref']['q'] = 'So we came into the great meeting-hall'
        self.assertIn('field.range', errors(d))

    def test_the_empty_frame_is_a_feature(self):
        d = good(); *_, h = self.add(d); h['hall']['features'].append({'k': 'frame', 'ref': {'sec': 'V', 'q': 'the empty frame from which the picture had been torn'}})
        self.assertEqual(errors(d), [])
        d = good(); *_, h = self.add(d); h['hall']['features'].append({'k': 'frame', 'ref': {'sec': 'V', 'q': 'under the white chandeliers'}})
        self.assertIn('phrase.not-in-text', errors(d))

    def test_two_brief_words_on_one_body_in_one_scene_are_one_body(self):
        acts = [{'id': 'g', 'kind': 'party', 'bloc': 'soviet'}]
        pls = [{'id': 'hall', 'kind': 'room'}]
        evs = [{'id': 'a', 'loc': 'hall', 'present': [{'who': 'g', 'n': 34, 'size': '34', 'brief': True}, {'who': 'g', 'pose': 'jeer', 'brief': True}]}]
        sp = L.presence_spans(evs, acts, pls)[0]
        self.assertEqual([(x.get('n'), x.get('pose')) for x in sp], [(34, 'jeer')])
        # a column marching past stays a body of its own; brief words in different scenes stay apart; and two
        # brief words add to a body already there, as one
        evs = [{'id': 'a', 'loc': 'hall', 'present': [{'who': 'g', 'n': 10}]},
               {'id': 'b', 'loc': 'hall', 'present': [{'who': 'g', 'n': 4, 'brief': True}, {'who': 'g', 'pose': 'jeer', 'brief': True},
                                                      {'who': 'g', 'form': 'column', 'march': True, 'brief': True}]},
               {'id': 'c', 'loc': 'hall', 'present': [{'who': 'g', 'pose': 'cheer', 'brief': True}]}]
        sp = L.presence_spans(evs, acts, pls)[0]
        at = lambda i: sorted((x.get('n') or 0, x.get('pose') or '', bool(x.get('march'))) for x in sp if x['start'] <= i and (x['end'] is None or i < x['end']) and x['end_by'] != 'update')
        self.assertEqual(at(1), sorted([(4, 'jeer', False), (0, '', True), (10, '', False)]))
        self.assertEqual(at(2), sorted([(10, 'cheer', False), (10, '', False)]))

    # phase 3: an amphitheatre, a gallery, those grouped round the platform, the hooting
    def test_an_amphitheatre_needs_its_word(self):
        q = 'In the high, amphitheatrical hall the galleries were thronged with workers.'
        d = good(); *_, h = self.add(d); h['hall']['plan'] = 'amphitheatre'; h['hall']['ref'] = {'sec': 'V', 'q': q}
        self.assertEqual(errors(d), [])
        d = good(); *_, h = self.add(d); h['hall']['plan'] = 'amphitheatre'
        self.assertIn('field.missing', errors(d))
        d = good(); *_, h = self.add(d); h['hall']['plan'] = 'amphitheatre'; h['hall']['ref'] = {'sec': 'V', 'q': 'So we came into the great meeting-hall'}
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); *_, h = self.add(d); h['hall']['plan'] = 'gallery'
        self.assertIn('field.enum', errors(d))

    def test_the_gallery_is_a_feature_and_its_people_stay(self):
        q = 'In the high, amphitheatrical hall the galleries were thronged with workers.'
        def up(d, s):
            s['present'][0].update({'bench': 'gallery', 'ref': {'sec': 'V', 'q': q}})
        d = good(); s, *_, h = self.add(d); up(d, s)
        self.assertIn('field.range', errors(d))   # the hall has no gallery
        d = good(); s, *_, h = self.add(d); up(d, s); h['hall']['features'].append({'k': 'gallery', 'ref': {'sec': 'V', 'q': q}})
        self.assertEqual(errors(d), [])
        d = good(); s, *_, h = self.add(d); h['hall']['features'].append({'k': 'gallery', 'ref': {'sec': 'V', 'q': q}})
        s['present'][0].update({'bench': 'gallery'})   # "The Red Guards sat on the left": no word for a gallery
        self.assertIn('phrase.not-in-text', errors(d))

    def test_grouped_round_the_platform(self):
        q = 'About a hundred people were grouped around the platform, where Kameniev was speaking'
        d = good(); s, *_ = self.add(d); s['present'][0].update({'bench': 'front', 'brief': True, 'size': 'About a hundred people', 'ref': {'sec': 'V', 'q': q}})
        self.assertEqual(errors(d), [])
        d = good(); s, *_ = self.add(d); s['present'][0].update({'bench': 'front', 'brief': True})   # "sat on the left"
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); s, *_ = self.add(d); s['present'][0].update({'bench': 'front', 'brief': True, 'walkin': True, 'ref': {'sec': 'V', 'q': q}})
        self.assertIn('field.range', errors(d))

    def test_imprecations_and_down_with_are_hooting(self):
        for q in ('from the right came imprecations', 'Others cried, "Down with the traitors!"'):   # each word on its own
            d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'jeer', 'ref': {'sec': 'V', 'q': q}}
            self.assertEqual(errors(d), [], q)
        d = good(); s, *_ = self.add(d); s['present'][0].update({'pose': 'jeer', 'bench': 'right', 'ref': {'sec': 'V', 'q': 'from the right came imprecations'}})
        self.assertEqual(errors(d), [])

    def test_the_gallery_does_not_walk(self):
        q = 'In the high, amphitheatrical hall the galleries were thronged with workers.'
        d = good(); _, l, *_, h = self.add(d); h['hall']['features'].append({'k': 'gallery', 'ref': {'sec': 'V', 'q': q}})
        l['present'][0].update({'bench': 'gallery', 'ref': {'sec': 'V', 'q': q + ' About a hundred people'}})
        l['present'][0]['ref']['q'] = 'Whereupon the Sailors left the chamber.'   # a walk-out, but no word for a gallery
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); s, *_, h = self.add(d); h['hall']['features'].append({'k': 'gallery', 'ref': {'sec': 'V', 'q': q}})
        s['present'][0].update({'bench': 'gallery', 'walkin': True, 'ref': {'sec': 'V', 'q': q}})
        self.assertIn('field.range', errors(d))

    def test_left_the_chamber_is_a_walkout(self):
        d = good(); _, l, *_ = self.add(d); l['present'][0].update({'part': False, 'ref': {'sec': 'V', 'q': 'Whereupon the Sailors left the chamber.'}})
        del l['present'][0]['part']
        self.assertEqual(errors(d), [])

    def test_the_speaker_may_be_named_near_another_passage(self):
        d = good(); s, *_ = self.add(d); s['speaker'] = 'holtzman-p'
        self.assertIn('presence.unnamed', errors(d))
        s['also'] = [{'sec': 'IX', 'q': 'The hall rose, thundering.'}]   # Holtzman comes running a line before
        self.assertNotIn('presence.unnamed', errors(d))

    def test_a_proportion_in_words(self):
        q = 'the Red Guards held a bare fifth of the seats.'
        d = good(); s, *_ = self.add(d); s['present'][0].update({'size': 'a bare fifth', 'prop': 'the seats', 'ref': {'sec': 'V', 'q': q}})
        self.assertNotIn('field.missing', errors(d))
        d = good(); s, *_ = self.add(d); s['present'][0].update({'size': 'the Red Guards', 'prop': 'the seats', 'ref': {'sec': 'V', 'q': q}})
        self.assertIn('field.missing', errors(d))

    def test_hooted_by_all_needs_the_word(self):
        d = good(); s, *_ = self.add(d)
        s['house'] = {'pose': 'jeer', 'all': True, 'ref': {'sec': 'V', 'q': 'It was evident that most of the delegates were hostile, and Kameniev was hooted down'}}
        self.assertEqual(errors(d), [])
        s['house'] = {'pose': 'jeer', 'all': True, 'ref': {'sec': 'V', 'q': 'from the right came imprecations'}}
        self.assertIn('phrase.not-in-text', errors(d))
        s['house'] = {'pose': 'vote', 'all': True, 'ref': {'sec': 'V', 'q': 'Kameniev asked all in favour to hold up their cards.'}}
        self.assertIn('field.range', errors(d))
        s['house'] = {'pose': 'jeer', 'all': False, 'ref': {'sec': 'V', 'q': 'from the right came imprecations'}}
        self.assertIn('field.range', errors(d))

    def test_round_the_platform_is_brief_and_still(self):
        q = 'About a hundred people were grouped around the platform, where Kameniev was speaking'
        d = good(); s, *_ = self.add(d); s['present'][0].update({'bench': 'front', 'size': 'About a hundred people', 'ref': {'sec': 'V', 'q': q}})
        s['present'][0].pop('brief', None)
        self.assertIn('field.range', errors(d))   # not brief
        d = good(); s, *_ = self.add(d); s['present'][0].update({'bench': 'front', 'brief': True, 'size': 'About a hundred people', 'ref': {'sec': 'V', 'q': q}})
        self.assertEqual(errors(d), [])
        s['speaker_out'] = {'sec': 'V', 'q': '"I\'m going now!" answered Kameniev, and left the platform.'}
        self.assertIn('field.range', errors(d))   # someone walking out past them

    def test_a_halls_ref_is_its_shape_and_names_it(self):
        d = good(); *_, h = self.add(d); h['hall']['ref'] = {'sec': 'V', 'q': 'So we came into the great meeting-hall'}
        self.assertIn('field.range', errors(d))   # rows take no ref
        d = good(); *_, h = self.add(d); h['hall']['plan'] = 'amphitheatre'; h['hall']['ref'] = {'sec': 'V', 'q': 'a glass dome and forty amphitheatrical columns'}
        self.assertIn('quote.not-found', errors(d))
        d = good(); *_, h = self.add(d); h['reed'] = ['the Nicolai Hall']; h['hall']['plan'] = 'amphitheatre'
        h['hall']['ref'] = {'sec': 'V', 'q': 'In the high, amphitheatrical hall the galleries were thronged with workers.'}
        h['hall']['features'] = []
        self.assertIn('presence.unnamed', errors(d))

    # phase 4: laughter, an arrival, a speaker who leaves as "he"
    def test_laughter_needs_its_word(self):
        q = 'He was interrupted by a great burst of laughter'
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'laugh', 'ref': {'sec': 'V', 'q': q}}
        self.assertEqual(errors(d), [])
        d = good(); s, *_ = self.add(d); s['present'][0].update({'pose': 'laugh', 'ref': {'sec': 'V', 'q': q}})
        self.assertEqual(errors(d), [])
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'laugh', 'ref': {'sec': 'V', 'q': 'from the right came imprecations'}}
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); self.add(d); ev(d, 'reed-walks')['present'][0].update({'pose': 'laugh', 'ref': {'sec': 'V', 'q': q}})
        self.assertIn('hall.none', errors(d))

    def test_an_arrival_is_a_walk_in(self):
        q = 'At the end Kameniev announced the arrival of the Sailors, greeted with a rising ovation.'
        d = good(); s, *_ = self.add(d); s['present'][1].update({'walkin': True, 'ref': {'sec': 'V', 'q': q}}); del s['present'][1]['bench']
        self.assertNotIn('phrase.not-in-text', errors(d))
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'stand', 'ref': {'sec': 'V', 'q': q}}
        self.assertEqual(errors(d), [])

    def test_the_speaker_leaving_may_be_he(self):
        q = 'He was interrupted by a great burst of laughter; and he left the room.'
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': q}   # Kameniev, named last before it
        self.assertEqual(errors(d), [])
        d = good(); s, *_ = self.add(d); s['speaker'] = 'holtzman-p'; s['also'] = [{'sec': 'IX', 'q': 'The hall rose, thundering.'}]
        s['speaker_out'] = {'sec': 'V', 'q': q}   # "he" is Kameniev, not Holtzman
        self.assertIn('presence.unnamed', errors(d))

    # the phase-4 review's cases
    def test_he_is_the_last_one_named_and_near(self):
        def leave(speaker, q):
            d = good(); s, *_ = self.add(d); s['speaker'] = speaker; s['also'] = [{'sec': 'IX', 'q': 'The hall rose, thundering.'}]
            s['speaker_out'] = {'sec': 'IX', 'q': q}
            return errors(d)
        self.assertIn('presence.unnamed', leave('kam-p', 'He left the hall at once.'))          # Holtzman is named after Kameniev
        self.assertNotIn('presence.unnamed', leave('holtzman-p', 'He left the hall at once.'))
        self.assertIn('presence.unnamed', leave('kam-p', 'At last he left the hall.'))          # Kameniev is named too far back
        self.assertNotIn('presence.unnamed', leave('kam-p', 'Then he left the hall.'))          # "KAMENIEV", in capitals
        d = good(); s, *_ = self.add(d)
        s['speaker_out'] = {'sec': 'V', 'q': 'Fifty delegates got up and pushed their way out'}   # no "he" at all
        self.assertIn('presence.unnamed', errors(d))

    def test_slaughter_is_not_laughter_nor_an_arrival_a_walk_in(self):
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'laugh', 'ref': {'sec': 'V', 'q': 'They went to slaughter and be slaughtered.'}}
        self.assertIn('phrase.not-in-text', errors(d))
        d = good(); s, *_ = self.add(d); s['present'][1].update({'walkin': True, 'ref': {'sec': 'V', 'q': 'Upon his arrival the Sailor was arrested.'}}); del s['present'][1]['bench']
        self.assertIn('phrase.not-in-text', errors(d))

    # phase 5: seats kept empty, a suite walking out behind the speaker, "strode out", "uproar"
    def test_empty_seats(self):
        q = 'There stretched the rows of Red Guard seats--empty since they had gone.'
        def empty(**kw):
            d = good(); s, *_ = self.add(d); s['present'][0].update(dict({'empty': True, 'brief': True, 'ref': {'sec': 'V', 'q': q}}, **kw))
            return errors(d)
        self.assertEqual(empty(), [])
        self.assertIn('phrase.not-in-text', empty(ref={'sec': 'V', 'q': 'So we came into the great meeting-hall'}))
        self.assertIn('field.range', empty(brief=False))
        self.assertIn('field.range', empty(pose='jeer'))
        self.assertIn('field.missing', empty(bench='platform'))

    def test_a_suite_follows_the_speaker_out(self):
        q = 'When Kameniev had stepped down he strode out with his suite of officers.'
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': q}
        s['present'][1].update({'walkout': True, 'suite': True, 'ref': {'sec': 'V', 'q': q}}); del s['present'][1]['bench']
        self.assertEqual(errors(d), [])
        del s['speaker_out']
        self.assertIn('field.range', errors(d))   # no speaker leaving to follow
        d = good(); s, *_ = self.add(d); s['speaker_out'] = {'sec': 'V', 'q': q}
        s['present'][1].update({'walkout': True, 'suite': True, 'ref': {'sec': 'V', 'q': 'Fifty delegates got up and pushed their way out'}}); del s['present'][1]['bench']
        self.assertIn('phrase.not-in-text', errors(d))   # no word for a suite

    def test_uproar_is_hooting(self):
        d = good(); s, *_ = self.add(d); s['house'] = {'pose': 'jeer', 'ref': {'sec': 'V', 'q': 'Uproar from the Left.'}}
        self.assertEqual(errors(d), [])
