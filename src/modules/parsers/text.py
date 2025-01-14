import re
import string

from yargy import Parser, rule, or_
from yargy.predicates import dictionary, gram, type as t1

from src.config.regions import regions


class TextParser:
    def __init__(self):
        self.regions = regions

    def parse_inn(self, card):
        INT = t1('INT')
        rule_inn = rule(
            dictionary({'инн'}),
            gram('NOUN').optional(),
            INT.repeatable().optional(),
            INT.repeatable()
        )
        parser_inn = Parser(rule_inn)

        inn = ''
        for match in parser_inn.findall(card):
            if True not in ['банка' in x.value.lower() for x in match.tokens]:
                if len([x.value for x in match.tokens]) == 4:
                    inn = ' '.join([x.value for x in match.tokens[1:]]).split(' ')[-2]
                if len(inn) == 0:
                    inn = ' '.join([x.value for x in match.tokens[1:]]).replace(' ', '')
                if 'банк' in card.split(inn)[0][-110:]:
                    inn = ''

        if len(inn) == 0 and 'инн' in card.lower():
            for card_part in card.split('инн', maxsplit=card.count('инн')):
                part = card_part.lower().split('инн')[-1]
                inn_candidate = [x for x in part.split(' ') if len(x) > 0 and not x[0].isalpha()]
                if len(inn_candidate) >= 1 and 'банк' not in card.split(inn_candidate[0])[0][-110:]:
                    inn = inn_candidate[0]

        if len(inn) not in (12, 10):
            cadidates = [x for x in card.split()]
            cadidate = [x for x in cadidates
                        if len(x) in (12, 10) and x.isnumeric() and x[:2] in regions.keys()
                        and x != '7707083893']  # exclude sber inn
            if len(cadidate) >= 1:
                inn = cadidate[0]

        sewed_inn = ''.join(re.findall(r'\d+', inn.__str__()))
        if len(sewed_inn) > 11:
            # физлицо
            return sewed_inn[:12]
        # юрлицо
        return sewed_inn[:10]

    @staticmethod
    def parse_r_account(card):
        def chunkstring(string, length=20):
            return (string[0 + i:length + i] for i in range(0, len(string), length))

        INT = t1('INT')
        rule_r_account1 = rule(
            or_(
                dictionary({'р'}), dictionary({'расчсчет'}), dictionary({'расчетный'}), dictionary({'рас'}),
                ),
            or_(
                dictionary({'сч'}), dictionary({'с'}), dictionary({'счет'}),
            ),
            or_(dictionary({'RUR'})).optional(),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_r_account1 = Parser(rule_r_account1)

        parser_r_account2 = rule(
            or_(
                dictionary({'рсчет'}), dictionary({'расчсчет'}), dictionary({'рассчет'}),
            ),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_r_account2 = Parser(parser_r_account2)

        r_account = ''
        for match in parser_r_account1.findall(card):
            r_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        if len(r_account) == 0:
            for match in parser_r_account2.findall(card):
                r_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        if len(r_account) != 20:
            cadidates = [chunkstring(x) for x in card.split()]
            cadidate = [x for x in [item for sublist in cadidates for item in sublist]
                        if len(x) % 20 == 0
                        and x.isnumeric()
                        and x[:3] in ('406', '407', '408')
                        and x[3:5] in ('01', '02', '03')]
            if len(cadidate) >= 1:
                r_account = cadidate[0]

        return ''.join(re.findall(r'\d+', r_account))

    @staticmethod
    def parse_bik(card):
        INT = t1('INT')
        rule_bik = rule(
            dictionary({'бик'}),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_bik = Parser(rule_bik)
        bik = ''
        for match in parser_bik.findall(card):
            bik = ''.join([x.value for x in match.tokens[1:]])

        if len(bik) == 0 and 'бик' in card.lower():
            bik = card.lower().split('бик')[-1]
            bik = [x for x in bik.split(' ') if len(x) > 0 and not x[0].isalpha()]
            if len(bik) >= 1:
                bik = bik[0]

        if len(bik) != 9:
            cadidates = [x for x in card.split()]
            cadidate = [x for x in cadidates if len(x) == 9 and x.isnumeric() and x[:2] == '04']
            if len(cadidate) == 1:
                bik = cadidate[0]
        bik = bik.replace('О', '0')
        return ''.join(re.findall(r'\d+', bik.__str__()))[:9]

    def parse_tel(self, card):
        mask = r'\d\s\d{3}\s\d{3}\s\d{2}\s\d{2}'
        if len(card.lower().split('моб тел ')) >= 2:
            tel_part = card.lower().split('моб тел')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('тел ')) >= 2:
            tel_part = card.lower().split('тел')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('т ф ')) >= 2:
            tel_part = card.lower().split('т ф')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('телефон ')) >= 2:
            tel_part = card.lower().split('телефон')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('tel ')) >= 2:
            tel_part = card.lower().split('tel')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('phone ')) >= 2:
            tel_part = card.lower().split('phone')
            tel = ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(re.findall(mask, card)) > 0:
            tel_part = self.clean_text(re.findall(mask, card)[0])
            tel = ''.join(re.findall(r'\d+', tel_part))[:11]
        else:
            return ''

        return tel if len(tel) == 11 else ''

    def clean_text(self, text):
        exclude = set(string.punctuation + '№')
        clean_text = text.replace("\n", " ")
        for ch in exclude:
            processed_txt = clean_text.replace(ch, ' ')
            clean_text = processed_txt
        while clean_text.count(2 * " ") > 0:
            clean_text = clean_text.replace(2 * " ", " ")

        no_conseq_dupl = []
        cuts = clean_text.split(' ')
        for n, x in enumerate(cuts[:-3]):
            if cuts[n] != cuts[n+1]:
                no_conseq_dupl.append(x)
            else:
                # If its just singe repeat -> there is no consecutive repeats, we can add item
                if cuts[n + 2] != cuts[n + 3]:
                    no_conseq_dupl.append(x)
        no_conseq_dupl.extend(cuts[-3:])

        return " ".join(no_conseq_dupl)
