import re
import string
import tldextract
from tld import get_tld
from tld.exceptions import TldBadUrl
from tld.exceptions import TldDomainNotFound
from yargy import Parser, rule, or_
from yargy.predicates import dictionary, gram, type as t1

from natasha import (
    Segmenter,
    MorphVocab,
    NamesExtractor,
    AddrExtractor,
)

segmenter = Segmenter()
morph_vocab = MorphVocab()

names_extractor = NamesExtractor(morph_vocab)
adr_ext = AddrExtractor(morph_vocab)


class Parsers:
    @staticmethod
    def parse_inn(card):
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
                if 'банк' not in card.split(inn)[0][-110:]:
                    # print(str([x.value for x in match.tokens]) + ' - ' + str(inn))
                    break

        sewed_inn = ''.join(re.findall(r'\d+', inn))
        if len(sewed_inn) > 11:
            # физлицо
            return sewed_inn[:12]
        else:
            # юрлицо
            return sewed_inn[:10]

    @staticmethod
    def parse_corr_account(card):
        INT = t1('INT')
        rule_corr_account1 = rule(
            or_(
                dictionary({'к'}), dictionary({'кор'}), dictionary({'корр'}), dictionary({'корреспондентский'}),
                ),
            or_(
                dictionary({'сч'}), dictionary({'с'}), dictionary({'счет'}),
            ),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_corr_account1 = Parser(rule_corr_account1)

        rule_corr_account2 = rule(
            or_(
                dictionary({'корсчет'}), dictionary({'коррсчет'}), dictionary({'ксчет'}),
            ),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_corr_account2 = Parser(rule_corr_account2)

        corr_account = ''
        for match in parser_corr_account1.findall(card):
            corr_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        if len(corr_account) == 0:
            for match in parser_corr_account2.findall(card):
                corr_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        return ''.join(re.findall(r'\d+', corr_account))

    @staticmethod
    def parse_r_account(card):
        INT = t1('INT')
        rule_oper_account1 = rule(
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
        parser_oper_account1 = Parser(rule_oper_account1)

        rule_oper_account2 = rule(
            or_(
                dictionary({'рсчет'}), dictionary({'расчсчет'}), dictionary({'рассчет'}),
            ),
            gram('NOUN').optional(),
            INT.repeatable()
        )
        parser_oper_account2 = Parser(rule_oper_account2)

        oper_account = ''
        for match in parser_oper_account1.findall(card):
            # print([x.value for x in match.tokens])
            oper_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        if len(oper_account) == 0:
            for match in parser_oper_account2.findall(card):
                oper_account = ' '.join([x.value for x in match.tokens[2:]]).replace(' ', '')

        return ''.join(re.findall(r'\d+', oper_account))

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
            bik = ' '.join([x.value for x in match.tokens[1:]]).split(' ')[-1]

        return bik

    @staticmethod
    def parse_kpp(card):
        INT = t1('INT')
        rule_kpp = rule(
            gram('NOUN').optional(),
            dictionary({'кпп'}),
            INT.repeatable().optional(),
            INT.repeatable()
        )
        parser_kpp1 = Parser(rule_kpp)

        kpp = ''
        for match in parser_kpp1.findall(card):
            kpp = ' '.join([x.value for x in match.tokens[1:]]).split(' ')[-1]

        return kpp

    @staticmethod
    def parse_tel(card):
        if len(card.lower().split('моб тел ')) >= 2:
                tel_part = card.lower().split('моб тел')
                return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('тел ')) >= 2:
                tel_part = card.lower().split('тел')
                return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('т ф ')) >= 2:
                tel_part = card.lower().split('т ф')
                return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('телефон ')) >= 2:
            tel_part = card.lower().split('телефон')
            return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('tel ')) >= 2:
            tel_part = card.lower().split('tel')
            return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        elif len(card.lower().split('phone ')) >= 2:
            tel_part = card.lower().split('phone')
            return ''.join(re.findall(r'\d+', tel_part[-1][:30]))[:11]
        else:
            return ''

    @staticmethod
    def get_website(message_text: str):
        exclude = list(filter(lambda x: x != '.' and x != '//' and x != ':', list(string.punctuation)))
        clean_text = message_text.replace("\n", " ")
        for ch in exclude:
            processed_txt = clean_text.replace(ch, ' ')
            clean_text = processed_txt
        while clean_text.count(2 * " ") > 0:
            clean_text = clean_text.replace(2 * " ", " ")

        if 'http' in clean_text:
            search = re.findall(r'(https?://\S+)', message_text)
            return min(search, key=len) if len(search) > 0 else ''
        elif 'www.' in clean_text:
            site = clean_text.split('www.')[-1].split(' ')[0]
            if site != '' and 'yandex' not in site and 'gmail' not in site and 'mail.ru' not in site and 'bk.ru' not in site:
                return 'www.' + site
        else:
            return ''

    @staticmethod
    def parse_website(message_text, email):
        website_check = (
                len(Parsers.get_website(message_text)) == 0 and len(email) > 0
                and
                'yandex' not in email and 'gmail' not in email and 'mail.ru' not in email and 'bk.ru' not in email
        )
        website = 'www.' + email.split('@')[-1] if website_check else Parsers.get_website(message_text)

        try:
            url_obj = get_tld(website, as_object=True)
            print(f'{url_obj.domain}.{url_obj.tld}')
        except (TldBadUrl, TldDomainNotFound, ValueError) as ex:
            print('Cant parse url: ', ex)
            return website

        return f'{url_obj.domain}.{url_obj.tld}'

    @staticmethod
    def get_address(card: str):
        def _parse_address_msg(addr_in_msg: str) -> str:
            if [len(x.value) > 0 for x in adr_ext.find(addr_in_msg).fact.parts if x.type in ['дом', 'строение', 'корпус']][0]:
                return ''.join(
                        [''.join([x.value, ', ']) for x in adr_ext.find(addr_in_msg).fact.parts if x.type == 'индекс'] +
                        [''.join([x.value, ' край, ']) for x in adr_ext.find(addr_in_msg).fact.parts if x.type == 'край'] +
                        [''.join([x.value, ' обл., ']) for x in adr_ext.find(addr_in_msg).fact.parts if x.type == 'область'] +
                        [''.join([x.type, ' ', x.value, ', ']) for x in adr_ext.find(addr_in_msg).fact.parts if x.type not in ['индекс', 'край', 'область']]
                    )
            else:
                return ''

        address = ''
        check1 = len(card.lower().replace('факту', '').split('факт')) > 1
        check2 = len(card.lower().split('факт')[-1].split('дрес')) > 1
        if check1 and check2:
            try:
                address_in_message = ' '.join(card.split('акт')[1].split('дрес')[-1][:150].split(' ')[1:12])
                print(address_in_message)
                address = _parse_address_msg(address_in_message)
            except Exception:
                address = ''

        check3 = len(card.lower().split('юрид')[-1].split('дрес')) > 1
        if len(address) == 0 and check3:
            try:
                address_in_message = ' '.join(card.split('рид')[1].split('дрес')[-1][:150].split(' ')[1:12])
                print(address_in_message)
                address = _parse_address_msg(address_in_message)
            except Exception:
                address = ''

        return address.strip(', ')

    @staticmethod
    def get_name(msg_text: str, header_from: str):
        mark, cleaned_msg = 'важением', ''
        if mark in msg_text:
            cleaned_msg = Parsers.clean_text(header_from + msg_text.split(mark)[0][-100:] + msg_text.split(mark)[1])
        else:
            cleaned_msg = Parsers.clean_text(header_from + msg_text[-200:]).split(' ')

        first, last, middle = '', '', ''
        name_in_message_lst = (
                    [
                        x for x in cleaned_msg
                        if len(x) > 3 and x[0].isupper() and x[1].islower()
                    ]
                )
        for n in range(len(name_in_message_lst)):
            name_in_message = ' '.join(name_in_message_lst[:n+1])
            try:
                first = names_extractor.find(name_in_message).fact.first
                last = names_extractor.find(name_in_message).fact.last
                middle = names_extractor.find(name_in_message).fact.middle
                print(n, first, last, middle)
                first = '' if str(first) == 'None' else first
                last = '' if str(last) == 'None' else last
                middle = '' if str(middle) == 'None' else middle
                if n >= 1 and str(first) != '' and str(last) != '':
                    print("Name recognized successfully")
                    return first, last, middle

            except Exception as ex:
                print('cant parse names - ', ex)

        return first, last, middle

    @staticmethod
    def get_email(message_text, header_from):
        def _excluded_email(eml: str):
            EXCLUDED_WORDS = ['mailto:', 'rusbelt', 'rusbelt.ru', 'fabuza.ru', 'eugeny.varseev']
            for word in EXCLUDED_WORDS:
                eml = eml.replace(word, '')
            suff_len = len(tldextract.extract(eml).suffix)
            if '@' in eml and '.' in eml and suff_len > 0:
                return eml
            else:
                return ''

        punct = string.punctuation
        exclude = list(
            filter(
                lambda x: x != '@' and x != '.' and x != '<' and x != '>' and x != ':' and x != '-',
                list(punct))
        )
        clean_text = message_text.replace("\n", " ")
        for ch in exclude:
            processed_txt = clean_text.replace(ch, ' ')
            clean_text = processed_txt
        while clean_text.count(2 * " ") > 0:
            clean_text = clean_text.replace(2 * " ", " ")

        try:
            email = clean_text.split('From:')[1].split('To:')[0].split('<')[1].split('>')[0]
        except Exception:
            clean_text = (header_from + ' ' + clean_text).replace("@rusbelt.ru", " ")
            if "@" in clean_text:
                name_part = clean_text.split('@')[0]
                domain_part = clean_text.split('@')[1]
                email = name_part.split(' ')[-1].strip('<') + '@' + domain_part.split(' ')[0].strip(':').strip('>')
                _excluded_email(email)
            else:
                return ''

        return _excluded_email(email)

    @staticmethod
    def clean_text(text):
        exclude = set(string.punctuation + '№')
        clean_text = text.replace("\n", " ")
        for ch in exclude:
            processed_txt = clean_text.replace(ch, ' ')
            clean_text = processed_txt
        while clean_text.count(2 * " ") > 0:
            clean_text = clean_text.replace(2 * " ", " ")

        no_conseq_dupl = []
        cuts = clean_text.split(' ')
        for n, x in enumerate(cuts[:-1]):
            if cuts[n] != cuts[n+1]:
                no_conseq_dupl.append(x)
        no_conseq_dupl.append(cuts[-1])

        return " ".join(no_conseq_dupl)
