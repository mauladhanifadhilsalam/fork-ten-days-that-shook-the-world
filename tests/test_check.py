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
    'IX': ['Pulkovo. Staff. 2.10 A.M. The night of October 30th to 31st will go down in history.',
           "It was almost three o'clock in the morning when Holtzman came running."],
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
                 'license': 'Public domain: a test', 'url': 'https://example.org/book.pdf', 'page': 1, 'title': 'A pass',
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
        return {n: L.load_json(os.path.join(REAL_DATA, n + '.json')) for n in ['meta'] + L.TABLES}

    def errors(self, d):
        with tempfile.TemporaryDirectory() as tmp:
            for n, obj in d.items():
                text = L.canonical(n, obj if n == 'meta' else L.sort_table(n, obj))
                L.write_text(os.path.join(tmp, n + '.json'), text)
            _, F = C.run(tmp, REAL_TEXT)
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
