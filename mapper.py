import re
import math
from pathlib import Path
from difflib import ndiff

import pikepdf


# TODO: Word 'наступати' on page  page 17 (num is on top right) is mega pain in the ass
# TODO: Must read -> https://github.com/pymupdf/PyMuPDF/issues/530
# TODO: Implement so you can merge two adjacent words into one e.g. реч це
class Cmapper:
    SOFT_HYPHEN_HEX_ESCAPE = "\xad"


    def perform(self, desired, parser):
        try:
            save_file = parser.file
            for word_idx, valid_word in desired.items():
                doc = pikepdf.open(
                    save_file.name, inherit_page_attributes=False, allow_overwriting_input=True
                )
                text = parser.get_text()
                text_list = text.split(" ")
                print(f"Text Length -> {len(text_list)}")
                word_idx = int(word_idx)
                invalid_word = text_list[word_idx]
                if self.SOFT_HYPHEN_HEX_ESCAPE in invalid_word:
                    # Change invalid word so it can be matched in text
                    invalid_word = "\n".join(invalid_word.split(" "))
                # It's possible that valid word is already present in text
                expected_count = text.count(invalid_word) + text.count(valid_word)
                page = doc.pages[parser.pno]
                fonts = page.Resources.Font
                for font in fonts.keys():
                    cmap = self._get_cmap(fonts, font)
                    if not cmap:
                        continue
                    print(font)
                    args = [parser, doc, valid_word, fonts, font, cmap, expected_count]
                    _DoubleUnicodeMapper(*args).perform(word_idx)
        except Exception as error:
            print(error)
            breakpoint()

    def cleanse(self, parser):
        doc = pikepdf.open(parser.file.name, allow_overwriting_input=True)
        page = doc.pages[parser.pno]
        fonts = page.Resources.Font
        for font in fonts.keys():
            cmap = self._get_cmap(fonts, font)
            if not cmap:
                continue
            cmap_name = Font.get_cmap_name(cmap)
            try:
                clean_font = Font.objects.get(kind=Font.Kind.CLEAN, cmap_name=cmap_name)
            except Font.DoesNotExist:
                continue
            data = clean_font.cmap.encode("utf-8")
            stream = doc.make_stream(data)
            fonts[font].ToUnicode = stream
        doc.save(doc.filename)

    def save_fonts(self, parser):
        doc = pikepdf.open(parser.file.name, allow_overwriting_input=True)
        page = doc.pages[parser.pno]
        fonts = page.Resources.Font
        for font in fonts.keys():
            cmap = self._get_cmap(fonts, font)
            if not cmap:
                continue
            cmap_name = Font.get_cmap_name(cmap)
            try:
                font_obj = Font.objects.get(
                    kind=Font.Kind.CLEAN, cmap_name=cmap_name
                )
                font_obj.cmap = cmap
                font_obj.save()
            except Font.DoesNotExist:
                font_obj = Font.objects.create(
                    pno=parser.pno,
                    name=font,
                    cmap=cmap,
                    cmap_name=cmap_name,
                    kind=Font.Kind.CLEAN,
                )
            with open(f"document/pages/1/fonts/{font_obj.name}.txt", "w") as f:
                f.write(cmap)
        doc.save(doc.filename)

    def _get_cmap(self, fonts, font):
        stm = fonts[font].get("/ToUnicode")
        if not stm:
            return
        data = stm.read_bytes()
        return data.decode()


class _UnicodeMapper(Cmapper):
    def __init__(self, parser, doc, fvalid_word, fonts, font, cmap, expected_count):
        self.parser = parser
        self.doc = doc
        self.valid_word = valid_word
        self.fonts: pikepdf.Object = fonts
        self.font: str = font
        self.cmap: str = cmap
        self.expected_count = expected_count

    PROPER_UNICODE_LENGTH = 4
    SPACE_UNICODE = "0020"
    WORD_JOINER_UNICODE = "2060"
    FULL_STOP_UNICODE = "002E"
    SKIP_UNICODES = [
        SPACE_UNICODE,
        WORD_JOINER_UNICODE,
        FULL_STOP_UNICODE,
    ]

    def save(self):
        data = self.cmap.encode("utf-8")
        stream = self.doc.make_stream(data)
        self.fonts[self.font].ToUnicode = stream
        self.doc.save(self.doc.filename)

    def to_unicode(self, letter):
        utf_8_encoding = hex(ord(letter))
        return utf_8_encoding.replace("x", "").zfill(4).upper()

    def to_char(self, hex_digits):
        return chr(int(hex_digits, 16))

    def normalize(self, string, exclude=[]):
        return "".join(
            [x for x in list(string) if x.isalnum() or x in exclude]
        ).replace("\n", "")


class _DoubleUnicodeMapper(_UnicodeMapper):
    ACCEPTABLE_CORRUPTED_LENGTH = 10

    def perform(self, word_idx):
        try:
            text = self.parser.get_text()
            text_list = text.split(" ")
            processed = text_list[word_idx]
            if self.expected_count == 0:
                raise "Excepted count cannot be zero"
            if text.count(self.valid_word) == self.expected_count:
                return
            baselines = self.cmap.splitlines()
            cid_charcodes = re.findall(r"<\w{4}> <\w{4,}>", self.cmap)
            corrupted = []
            for item in self.find_corrupted(baselines, cid_charcodes, processed):
                corrupted.append(item)
            # First deal with ones that have improper unicode length if they are present
            corrupted = sorted(corrupted, key=lambda x: len(x), reverse=True)
            # Reset cmap to original state
            self.cmap = "\n".join(baselines)
            self.save()
            text = self.parser.get_text()
            vw_non_word_chars = [x for x in list(self.valid_word) if not x.isalnum()]
            dot = "."
            if processed.endswith(dot) and dot not in vw_non_word_chars:
                self.valid_word += dot
                vw_non_word_chars.append(dot)
            vw = self.valid_word
            for item in corrupted:
                if processed == vw:
                    break
                print(item)
                print(processed)
                cid = item.split(" ")[0].strip("<>")
                charcode = item.split(" ")[1].strip("<>")
                if len(charcode) == self.PROPER_UNICODE_LENGTH:
                    try:
                        invalid = self.to_char(charcode)
                        normalized_processed = self.normalize(processed, vw_non_word_chars)
                        if charcode in self.SKIP_UNICODES:
                            continue
                        if (
                            len(normalized_processed) != len(vw)
                            and all(
                                len(x.split(" ")[1].strip("<>")) == self.PROPER_UNICODE_LENGTH
                                for x in corrupted
                            )
                        ):
                            # Only do this if all unicode lengths are of proper length, because usually this anomaly is present when some unicode length is more than 4
                            diff = list(ndiff(processed, vw))
                            deleted = "".join([x.strip("- ") for x in diff if x.startswith("- ")])
                            valid = "".join([x.strip("+ ") for x in diff if x.startswith("+ ")])
                            if deleted != invalid:
                                continue
                            charcodes = [self.to_unicode(x) for x in list(valid)]
                            self.cmap = self.cmap.replace(item, f"<{cid}> <{" ".join(charcodes)}>")
                            self.save()
                            processed = processed.replace(deleted, valid)
                            continue
                        if invalid not in normalized_processed:
                            print(f"Unknown character -> {invalid}")
                            # lines = self.cmap.splitlines()
                            # lines.pop(lines.index(item))
                            # self.cmap = "\n".join(lines)
                            # self.cmap = self.cmap.replace(item, f"<{cid}> <{self.SPACE_UNICODE}>")
                            # self.save()
                            # processed = processed.replace(invalid, "")
                            continue
                        invalid_idx = list(normalized_processed).index(invalid)
                        valid = vw[invalid_idx]
                        self.cmap = self.cmap.replace(item, f"<{cid}> <{self.to_unicode(valid)}>")
                        self.save()
                        text = self.parser.get_text()
                        text_list = text.split(" ")
                        print(f"After Save Text Length -> {len(text_list)}")
                        after_save = text_list[word_idx]
                        processed = after_save.replace("\n", "")
                    except Exception as err:
                        print(err)
                        breakpoint()
                else:
                    lines = self.cmap.splitlines()
                    item_idx = lines.index(item)
                    lines.pop(item_idx)
                    self.cmap = "\n".join(lines)
                    self.save()
                    text = self.parser.get_text()
                    text_list = text.split(" ")
                    after_save = text_list[word_idx]
                    normalized_processed = self.normalize(processed, vw_non_word_chars)
                    diff = [
                        x for x in list(ndiff(processed, after_save)) if x.strip(" ") != "\n"
                    ]
                    deleted = "".join([
                        x.lstrip("- ") for x in diff
                        if x.startswith("-")
                    ])
                    added = "".join([
                        x.lstrip("+ ") for x in diff
                        if x.startswith("+")
                    ])
                    invalid_idx_start = next(
                        idx for idx, x in enumerate(diff)
                        if x.startswith("+")
                    )
                    normalized_after_save = self.normalize(
                        after_save, vw_non_word_chars
                    ).replace(added, "")
                    replace = (len(vw) - len(normalized_after_save))
                    if replace > 0:
                        valid = vw[invalid_idx_start:invalid_idx_start+replace]
                    else:
                        from_behind_idx = -(len(after_save) - invalid_idx_start)
                        valid = vw[from_behind_idx]
                    charcodes = [self.to_unicode(x) for x in list(valid)]
                    lines.insert(item_idx, f"<{cid}> <{' '.join(charcodes)}>")
                    self.cmap = "\n".join(lines)
                    self.save()
                    text = self.parser.get_text()
                    text_list = text.split(" ")
                    processed = processed.replace(deleted, valid)
        except Exception as error:
            print(error)
            breakpoint()

    def find_corrupted(self, lines, corrupted, original):
        if len(corrupted) == 1:
            yield corrupted[0]
            return
        half = math.ceil(len(corrupted)/2)
        first_half = corrupted[:half]
        second_half = corrupted[half:]

        subtract = set(first_half)
        subtracted = [x for x in lines if x not in subtract]
        self.cmap = "\n".join(subtracted)
        self.save()
        text_list = self.parser.get_text().split(" ")
        corrupted_first_half = original not in text_list

        subtract = set(second_half)
        subtracted = [x for x in lines if x not in subtract]
        self.cmap = "\n".join(subtracted)
        self.save()
        text_list = self.parser.get_text().split(" ")
        corrupted_second_half = original not in text_list

        if corrupted_first_half:
            yield from self.find_corrupted(lines, first_half, original)
        if corrupted_second_half:
            yield from self.find_corrupted(lines, second_half, original)
