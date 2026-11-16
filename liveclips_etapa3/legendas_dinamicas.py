"""Legendas ASS: frases curtas e destaque somente com tempos por palavra."""
import math
import textwrap


def tempo(seconds):
    value = max(0, round(seconds * 100))
    hours, value = divmod(value, 360000)
    minutes, value = divmod(value, 6000)
    seconds, centis = divmod(value, 100)
    return f'{hours}:{minutes:02}:{seconds:02}.{centis:02}'


def seguro(text):
    return ' '.join(str(text).split()).replace('\\', '＼').replace('{', '｛').replace('}', '｝')


def grupos(words):
    group = []
    for word in words:
        if group and (len(group) >= 4 or
                      len(' '.join(w['text'] for w in group + [word])) > 26 or
                      word['start'] - group[-1]['end'] > .45):
            yield group
            group = []
        group.append(word)
    if group:
        yield group


def make_ass(segments, start, end):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Principal,Arial,46,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,70,90,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events = []
    cursor = 0.0

    def event(a, b, text):
        nonlocal cursor
        a, b = max(0, a - start, cursor), min(end, b) - start
        if b <= a or tempo(a) == tempo(b):
            return
        events.append(f'Dialogue: 0,{tempo(a)},{tempo(b)},Principal,,0,0,0,,{text}')
        cursor = b

    for seg in sorted(segments, key=lambda s: float(s['start'])):
        if float(seg['end']) <= start or float(seg['start']) >= end:
            continue
        words = []
        for w in seg.get('words') or []:
            a, b = float(w['start']), float(w['end'])
            text = seguro(w.get('word', ''))
            if math.isfinite(a) and math.isfinite(b) and b > a and text and b > start and a < end:
                words.append({'start': max(start, a), 'end': min(end, b), 'text': text})
        if not words:
            # Legado: sem inventar precisao por palavra. Mostra a frase sem destaque.
            text = seguro(seg['text'])
            a, b = max(start, float(seg['start'])), min(end, float(seg['end']))
            lines = textwrap.wrap(text, width=26)
            chunks = [lines[i:i+2] for i in range(0, len(lines), 2)]
            for i, lines in enumerate(chunks):
                event(a + (b-a)*i/len(chunks), a + (b-a)*(i+1)/len(chunks), r'\N'.join(lines))
            continue
        words.sort(key=lambda w: w['start'])
        for group in grupos(words):
            plain = ' '.join(w['text'] for w in group)
            for i, word in enumerate(group):
                a = word['start']
                b = min(word['end'], group[i+1]['start']) if i+1 < len(group) else word['end']
                line = ' '.join((r'{\c&H00E8FF&}' + w['text'] + r'{\c&HFFFFFF&}')
                                if j == i else w['text'] for j, w in enumerate(group))
                event(a, b, line)
                if i+1 < len(group) and b < group[i+1]['start']:
                    event(b, group[i+1]['start'], plain)
    return header + '\n'.join(events) + '\n'
