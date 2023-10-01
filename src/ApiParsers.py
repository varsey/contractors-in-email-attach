import re
import string
from yargy import Parser, rule, or_
from yargy.predicates import dictionary, gram, type as t1

regions = {'01' :  'Республика Адыгея (Адыгея)', '02' : 'Республика Башкортостан',
           '03' : 'Республика Бурятия', '04' : 'Республика Алтай', '05' : 'Республика Дагестан',
           '06' : 'Республика Ингушетия', '07' : 'Кабардино-Балкарская Республика', '08' : 'Республика Калмыкия',
           '09' : 'Карачаево-Черкесская Республика', '10' : 'Республика Карелия', '11' : 'Республика Коми',
           '12' : 'Республика Марий Эл', '13' : 'Республика Мордовия', '14' : 'Республика Саха (Якутия)',
           '15' : 'Республика Северная Осетия - Алания', '16' : 'Республика Татарстан (Татарстан)',
           '17' : 'Республика Тыва', '18' : 'Удмуртская Республика', '19' : 'Республика Хакасия',
           '20' : 'Чеченская Республика', '21' : 'Чувашская Республика - Чувашия', '22' : 'Алтайский край',
           '23' : 'Краснодарский край', '24' : 'Красноярский край', '25' : 'Приморский край',
           '26' : 'Ставропольский край', '27' : 'Хабаровский край', '28' : 'Амурская область',
           '29' : 'Архангельская область', '30' : 'Астраханская область', '31' : 'Белгородская область',
           '32' : 'Брянская область', '33' : 'Владимирская область', '34' : 'Волгоградская область',
           '35' : 'Вологодская область', '36' : 'Воронежская область', '37' : 'Ивановская область',
           '38' : 'Иркутская область', '39' : 'Калининградская область', '40' : 'Калужская область',
           '41' : 'Камчатский край', '42' : 'Кемеровская область - Кузбасс', '43' : 'Кировская область',
           '44' : 'Костромская область', '45' : 'Курганская область', '46' : 'Курская область',
           '47' : 'Ленинградская область', '48' : 'Липецкая область', '49' : 'Магаданская область',
           '50' : 'Московская область', '51' : 'Мурманская область', '52' : 'Нижегородская область',
           '53' : 'Новгородская область', '54' : 'Новосибирская область', '55' : 'Омская область',
           '56' : 'Оренбургская область', '57' : 'Орловская область', '58' : 'Пензенская область',
           '59' : 'Пермский край', '60' : 'Псковская область', '61' : 'Ростовская область', '62' : 'Рязанская область',
           '63' : 'Самарская область', '64' : 'Саратовская область', '65' : 'Сахалинская область',
           '66' : 'Свердловская область', '67' : 'Смоленская область', '68' : 'Тамбовская область',
           '69' : 'Тверская область', '70' : 'Томская область', '71' : 'Тульская область',
           '72' : 'Тюменская область', '73' : 'Ульяновская область', '74' : 'Челябинская область',
           '75' : 'Забайкальский край', '76' : 'Ярославская область', '77' : 'г. Москва',
           '78' : 'г. Санкт-Петербург', '79' : 'Еврейская автономная область',
           '83' : 'Ненецкий автономный округ', '86' : 'Ханты-Мансийский автономный округ - Югра',
           '87' : 'Чукотский автономный округ', '89' : 'Ямало-Ненецкий автономный округ',
           '91' : 'Республика Крым', '92' : 'г. Севастополь',
           '99' : 'Иные территории, включая город и космодром Байконур'
           }


class ApiParsers:
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
            print([x.value.lower() for x in match.tokens])
            if True not in ['банка' in x.value.lower() for x in match.tokens]:
                if len([x.value for x in match.tokens]) == 4:
                    inn = ' '.join([x.value for x in match.tokens[1:]]).split(' ')[-2]
                if len(inn) == 0:
                    inn = ' '.join([x.value for x in match.tokens[1:]]).replace(' ', '')
                if 'банк' not in card.split(inn)[0][-110:]:
                    # print(str([x.value for x in match.tokens]) + ' - ' + str(inn))
                    break

        if len(inn) == 0 and 'инн' in card.lower():
            inn = card.lower().split('инн')[-1]
            inn = [x for x in inn.split(' ') if len(x) > 0 and not x[0].isalpha()]
            if len(inn) >= 1:
                inn = inn[0]

        if len(inn) not in (12, 10):
            cadidates = [x for x in card.split()]
            cadidate = [x for x in cadidates if len(x) in (12, 10) and x.isnumeric() and x[:2] in regions.keys()]
            if len(cadidate) == 1:
                inn = cadidate[0]

        print('inn', inn)
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
            print([x.value for x in match.tokens])
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

        print('r_account', r_account)
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
            print([x.value for x in match.tokens[1:]])
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

        print('bik', bik)
        return ''.join(re.findall(r'\d+', bik.__str__()))[:9]

    def parse_tel(self, card):
        print(card)
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

        print('tel_part', tel_part)
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
