#!/usr/bin/env python3

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from reportlab.lib.colors import black, toColor, HexColor, gray

import math
import sys

from typing import Tuple


def load_font(font_name: str):
    pdfmetrics.registerFont(TTFont('Arial Bold', font_name))
    print("Using font '{}' ...".format(font_name))


if "--roboto" in sys.argv:
    try:
        load_font('Roboto-Bold.ttf')
    except TTFError as e:
        print("Error: {}".format(e))
        exit(1)

else:
    for font_name in ['ArialBd.ttf', 'Arial_Bold.ttf']:
        try:
            load_font(font_name)
            break
        except TTFError:
            pass
    else:
        print("Error: Unable to load font 'Arial Bold'.")
        print("If you are on Ubuntu, you can install it with:")
        print("    sudo apt install ttf-mscorefonts-installer")
        print("Alternatively, use the 'Roboto' font by invoking this script with")
        print("the '--roboto' flag.")
        print("On Mac OS the '--roboto' flag is mandatory because this script currently")
        print("does not support Arial on Mac OS.")
        exit(1)


class PaperConfig:
    def __init__( self,
        pagesize: Tuple[float, float],
        sticker_width: float,
        sticker_height: float,
        sticker_corner_radius: float,
        left_margin: float,
        top_margin: float,
        horizontal_stride: float,
        vertical_stride: float,
        nr_of_columns: int,
        nr_of_rows: int,
    ) -> None:
        self.pagesize = pagesize
        self.sticker_width = sticker_width
        self.sticker_height = sticker_height
        self.sticker_corner_radius = sticker_corner_radius
        self.left_margin = left_margin
        self.top_margin = top_margin
        self.horizontal_stride = horizontal_stride
        self.vertical_stride = vertical_stride
        self.nr_of_columns = nr_of_columns
        self.nr_of_rows = nr_of_rows

class Resistor_draw_settings:
    def __init__(self,
        squish_width: float,
        squish_left: float,
        value_font_size: float,
        ohm_font_size: float,
        smd_font_size: float,
        space_between: float,
    ) -> None:
        self.squish_width = squish_width
        self.squish_left = squish_left
        self.value_font_size = value_font_size
        self.ohm_font_size = ohm_font_size
        self.smd_font_size = smd_font_size
        self.space_between = space_between

AVERY_5260 = PaperConfig(
    pagesize=LETTER,
    sticker_width=(2 + 5/8) * inch,
    sticker_height=1 * inch,
    sticker_corner_radius=0.1 * inch,
    left_margin=3/16 * inch,
    top_margin=1.5 * inch,
    horizontal_stride=(2 + 6/8) * inch,
    vertical_stride=1 * inch,
    nr_of_columns=3,
    nr_of_rows=10,
)

AVERY_L7157 = PaperConfig(
    pagesize=A4,
    sticker_width=64 * mm,
    sticker_height=24.3 * mm,
    sticker_corner_radius=3 * mm,
    left_margin=6.4 * mm,
    top_margin=38.4 * mm,
    horizontal_stride=66.552 * mm,
    vertical_stride=24.3 * mm,
    nr_of_columns=3,
    nr_of_rows=11,
)


AVERY_5260_AVERY_L7157_resistorsettings = Resistor_draw_settings(
    squish_width=0.1,
    squish_left=0.05,
    value_font_size=0.25,
    ohm_font_size=0.15,
    smd_font_size=0.08,
    space_between=5,
)


Avery_3474_70x37_label = PaperConfig(
    # For this label to be printed correct the printer setting should be set to print the actual size
    # do not use 'fit to page'.
    # This might not work for all printers (e.g. inkjet)
    pagesize=A4,
    sticker_width=65 * mm,
    sticker_height=18.5 * mm,
    sticker_corner_radius=0 * mm,
    left_margin=0.5 * mm,
    top_margin=18 * mm,
    horizontal_stride=70 * mm,
    vertical_stride=18.5 * mm,
    nr_of_columns=3,
    nr_of_rows=16,  # a sheet has 24 stickers without space between the labels, this will fit 2 resistor labels per sticker.
)

Avery_3474_70x37_resistorsettings = Resistor_draw_settings(
    squish_width=0.05,
    squish_left=0.025,
    value_font_size=0.125,
    ohm_font_size=0.125,
    smd_font_size=0.08,
    space_between=2.5,
)


class StickerRect:
    def __init__(self, layout: PaperConfig, row: int, column: int):
        self.left = layout.left_margin + layout.horizontal_stride * column
        self.bottom = layout.pagesize[1] - (layout.top_margin + layout.vertical_stride * row)
        self.width = layout.sticker_width
        self.height = layout.sticker_height
        self.corner = layout.sticker_corner_radius


class ResistorValue:
    def __init__(self, ohms):
        # Fixed-point value with 2 decimals precision
        ohms_exp = math.floor(math.log10(ohms))
        ohms_val = round(ohms / math.pow(10, ohms_exp - 2))
        ohms_exp -= 2

        while ohms_val >= 1000:
            ohms_exp += 1
            ohms_val //= 10

        self.ohms_val = ohms_val
        self.ohms_exp = ohms_exp + 2

        # print(self.ohms_val, self.ohms_exp, self.format_value(), self.get_value())

    def get_value(self):
        return self.ohms_val * math.pow(10, self.ohms_exp - 2)

    def get_prefix(self):
        if self.ohms_exp >= 12:
            return "T"
        if self.ohms_exp >= 9:
            return "G"
        if self.ohms_exp >= 6:
            return "M"
        if self.ohms_exp >= 3:
            return "k"
        if self.ohms_exp >= 0:
            return ""
        if self.ohms_exp >= -3:
            return "m"
        if self.ohms_exp >= -6:
            return "\u03BC"
        return "n"

    def get_prefixed_number(self):
        if self.ohms_exp % 3 == 0:
            if self.ohms_val % 100 == 0:
                return str(self.ohms_val // 100)
            elif self.ohms_val % 10 == 0:
                return str(self.ohms_val // 100) + "." + str((self.ohms_val % 100) // 10)
            else:
                return str(self.ohms_val // 100) + "." + str(self.ohms_val % 100)
        elif self.ohms_exp % 3 == 1:
            if self.ohms_val % 10 == 0:
                return str(self.ohms_val // 10)
            else:
                return str(self.ohms_val // 10) + "." + str(self.ohms_val % 10)
        else:
            return str(self.ohms_val)

    def format_value(self):

        if self.ohms_exp < 0:
            rendered_num = str(self.ohms_val)
            while rendered_num[-1] == "0":
                rendered_num = rendered_num[:-1]
            if self.ohms_exp == -1:
                return "0." + rendered_num
            if self.ohms_exp == -2:
                return "0.0" + rendered_num
            if self.ohms_exp == -3:
                return "0.00" + rendered_num

        return self.get_prefixed_number() + self.get_prefix()


def resistor_color_table(num):
    return [
        HexColor("#000000"),
        HexColor("#994d00"),
        HexColor("#FF0000"),
        HexColor("#FF9900"),
        HexColor("#FFFF00"),
        HexColor("#00FF00"),
        HexColor("#0000FF"),
        HexColor("#FF00FF"),
        HexColor("#CCCCCC"),
        HexColor("#FFFFFF"),
    ][num]


def draw_fancy_resistor_stripe(c, x, y, width, height, color_table):
    c.setFillColor(color_table[2])
    c.rect(x, y+height*5/6, width, height/6, fill=1, stroke=0)
    c.setFillColor(color_table[1])
    c.rect(x, y+height*4/6, width, height/6, fill=1, stroke=0)
    c.setFillColor(color_table[0])
    c.rect(x, y+height*3/6, width, height/6, fill=1, stroke=0)
    c.setFillColor(color_table[1])
    c.rect(x, y+height*2/6, width, height/6, fill=1, stroke=0)
    c.setFillColor(color_table[2])
    c.rect(x, y+height*1/6, width, height/6, fill=1, stroke=0)
    c.setFillColor(color_table[3])
    c.rect(x, y+height*0/6, width, height/6, fill=1, stroke=0)


def draw_resistor_stripe(c, x, y, width, height, stripe_value):

    if 0 <= stripe_value <= 9:
        c.setFillColor(resistor_color_table(stripe_value))
        c.rect(x, y, width, height, fill=1, stroke=0)
        return

    elif stripe_value == -1:
        gold_table = [
            HexColor("#fefefe"),
            HexColor("#f7febe"),
            HexColor("#effe41"),
            HexColor("#c5d24f"),
        ]

        draw_fancy_resistor_stripe(c, x, y, width, height, gold_table)
        return

    elif stripe_value == -2:
        silver_table = [
            HexColor("#fefefe"),
            HexColor("#e0e0e0"),
            HexColor("#cdcdcd"),
            HexColor("#b5b5b5"),
        ]

        draw_fancy_resistor_stripe(c, x, y, width, height, silver_table)
        return

    else:

        c.setLineWidth(0.5)
        c.setFillColor(gray, 0.3)
        c.setStrokeColorRGB(0.5, 0.5, 0.5, 1.0)
        c.rect(x, y, width, height, fill=1, stroke=1)
        c.line(x, y, x + width, y + height)
        c.line(x + width, y, x, y + height)
        return


def draw_resistor_colorcode(c, value, color1, color2, x, y, width, height, num_codes):

    if value.ohms_exp < num_codes - 4:
        return

    border = height/6
    corner = (height-2*border)/4

    c.saveState()
    p = c.beginPath()
    p.roundRect(x+border, y+border, width-2*border, height-2*border, corner)
    c.clipPath(p, stroke=0)
    c.linearGradient(x+width/2, y+border+height, x+width/2, y+border, (color1, color2))
    c.restoreState()

    width_without_corner = width - 2*border - 2*corner
    stripe_width = width_without_corner/10

    for i in range(num_codes):

        if i == num_codes - 1:
            stripe_value = value.ohms_exp + 2 - num_codes
        else:
            stripe_value = value.ohms_val
            for _ in range(2-i):
                stripe_value //= 10
            stripe_value %= 10

        draw_resistor_stripe(c,
                             x + border + corner + stripe_width / 2 + 2 * stripe_width * i,
                             y + border,
                             stripe_width,
                             height - 2 * border,
                             stripe_value)

    draw_resistor_stripe(c,
                         x + width - border - corner - stripe_width * 1.5,
                         y + border,
                         stripe_width,
                         height - 2 * border,
                         -3)

    c.setFillColor(black)
    c.setStrokeColor(black, 1)
    c.setLineWidth(0.5)
    c.roundRect(x+border, y+border, width-2*border, height-2*border, corner)


def get_3digit_code(value):
    if value.ohms_val % 10 != 0:
        return ""

    digits = str(value.ohms_val // 10)

    if value.ohms_exp > 0:
        multiplier = str(value.ohms_exp - 1)
        return digits + multiplier

    if value.ohms_exp == 0:
        return digits[0] + "R" + digits[1]

    if value.ohms_exp == -1:
        return "R" + digits

    if value.ohms_exp == -2:
        if value.ohms_val % 100 != 0:
            return ""
        return "R0" + digits[0]

    return ""


def get_4digit_code(value):
    digits = str(value.ohms_val)

    if value.ohms_exp > 1:
        multiplier = str(value.ohms_exp - 2)
        return digits + multiplier

    if value.ohms_exp == 1:
        return digits[0] + digits[1] + "R" + digits[2]

    if value.ohms_exp == 0:
        return digits[0] + "R" + digits[1] + digits[2]

    if value.ohms_exp == -1:
        return "R" + digits

    if value.ohms_exp == -2:
        if value.ohms_val % 10 != 0:
            return ""
        return "R0" + digits[0] + digits[1]

    if value.ohms_exp == -3:
        if value.ohms_val % 100 != 0:
            return ""
        return "R00" + digits[0]

    return ""


def get_eia98_code(value):
    eia98_coding_table = {
        100: "01", 178: "25", 316: "49", 562: "73",
        102: "02", 182: "26", 324: "50", 576: "74",
        105: "03", 187: "27", 332: "51", 590: "75",
        107: "04", 191: "28", 340: "52", 604: "76",
        110: "05", 196: "29", 348: "53", 619: "77",
        113: "06", 200: "30", 357: "54", 634: "78",
        115: "07", 205: "31", 365: "55", 649: "79",
        118: "08", 210: "32", 374: "56", 665: "80",
        121: "09", 215: "33", 383: "57", 681: "81",
        124: "10", 221: "34", 392: "58", 698: "82",
        127: "11", 226: "35", 402: "59", 715: "83",
        130: "12", 232: "36", 412: "60", 732: "84",
        133: "13", 237: "37", 422: "61", 750: "85",
        137: "14", 243: "38", 432: "62", 768: "86",
        140: "15", 249: "39", 442: "63", 787: "87",
        143: "16", 255: "40", 453: "64", 806: "88",
        147: "17", 261: "41", 464: "65", 825: "89",
        150: "18", 267: "42", 475: "66", 845: "90",
        154: "19", 274: "43", 487: "67", 866: "91",
        158: "20", 280: "44", 499: "68", 887: "92",
        162: "21", 287: "45", 511: "69", 909: "93",
        165: "22", 294: "46", 523: "70", 931: "94",
        169: "23", 301: "47", 536: "71", 953: "95",
        174: "24", 309: "48", 549: "72", 976: "96",
    }

    if value.ohms_val not in eia98_coding_table:
        return ""

    digits = eia98_coding_table[value.ohms_val]

    multiplier_table = ["Z", "Y", "X", "A", "B", "C", "D", "E", "F"]
    if not (0 <= value.ohms_exp+1 < len(multiplier_table)):
        return ""

    multiplier = multiplier_table[value.ohms_exp+1]

    return digits + multiplier


def draw_resistor_sticker(c, layout, resistorsettings , row, column, ohms, draw_center_line=True):
    rect = StickerRect(layout, row, column)

    # Squish horizontally by a bit, to prevent clipping
    rect.width -= resistorsettings.squish_width * inch
    rect.left += resistorsettings.squish_left * inch

    # Draw middle line
    if draw_center_line:
        c.setStrokeColor(black, 0.25)
        c.setLineWidth(0.7)
        c.line(rect.left,
               rect.bottom + rect.height/2,
               rect.left + rect.width,
               rect.bottom + rect.height/2)

    # Draw resistor value
    resistor_value = ResistorValue(ohms)
    print("Generating sticker '{}'".format(resistor_value.format_value()))

    value_font_size = resistorsettings.value_font_size * inch
    ohm_font_size = resistorsettings.ohm_font_size * inch
    smd_font_size = resistorsettings.smd_font_size * inch
    space_between = resistorsettings.space_between

    value_string = resistor_value.format_value()
    ohm_string = "\u2126"
    value_width = c.stringWidth(value_string, 'Arial Bold', value_font_size * 1.35)
    ohm_width = c.stringWidth(ohm_string, 'Arial Bold', ohm_font_size * 1.35)
    total_text_width = ohm_width + value_width + space_between
    text_left = rect.left + rect.width/4 - total_text_width/2
    text_bottom = rect.bottom + rect.height/4 - value_font_size/2

    c.setFont('Arial Bold', value_font_size * 1.35)
    c.drawString(text_left, text_bottom, value_string)
    c.setFont('Arial Bold', ohm_font_size * 1.35)
    c.drawString(text_left + value_width + space_between, text_bottom, ohm_string)

    # Draw resistor color code
    draw_resistor_colorcode(c, resistor_value,
                            toColor("hsl(55, 54%, 100%)"), toColor("hsl(55, 54%, 70%)"),
                            rect.left + rect.width/2,
                            rect.bottom + rect.height/4 - rect.height/45,
                            rect.width/4, rect.height/4,
                            3)

    draw_resistor_colorcode(c, resistor_value,
                            toColor("hsl(197, 59%, 100%)"), toColor("hsl(197, 59%, 73%)"),
                            rect.left + rect.width * 0.75,
                            rect.bottom + rect.height/4 - rect.height/45,
                            rect.width/4, rect.height/4,
                            4)

    c.setFont('Arial Bold', smd_font_size * 1.35)
    c.drawString(rect.left + rect.width/2 + rect.width/32, rect.bottom +
                 rect.height/13, get_3digit_code(resistor_value))
    c.drawCentredString(rect.left + rect.width*3/4, rect.bottom +
                        rect.height/13, get_4digit_code(resistor_value))
    c.drawRightString(rect.left + rect.width - rect.width/32, rect.bottom +
                      rect.height/13, get_eia98_code(resistor_value))


def render_stickers(layout: PaperConfig, resistorsettings: Resistor_draw_settings, values, draw_center_line=True):
    valuecntr = 0
    pagecntr = 1
    while valuecntr < len(values):
        rowId = 0
        c = canvas.Canvas("ResistorLabels_Page_" + str(pagecntr) + ".pdf", pagesize=layout.pagesize)
        while rowId < layout.nr_of_rows and valuecntr < len(values):
            columnId = 0
            while columnId < layout.nr_of_columns and valuecntr < len(values):
                value = values[valuecntr]
                draw_resistor_sticker(c, layout, resistorsettings, rowId, columnId, value, draw_center_line)
                valuecntr += 1
                columnId += 1
            rowId += 1
        if rowId == layout.nr_of_rows or valuecntr == len(values):
            # # Add this if you want to see the outlines of the labels.
            # # Recommended to be commented out for the actual printing.
            render_outlines(c, layout)
            # Finish page
            # Store canvas to PDF file
            c.showPage()
            c.save()
            print("Saved Resistor Label page '{}'".format(pagecntr))
            pagecntr += 1


def render_outlines(c, layout: PaperConfig):
    for y in range(layout.nr_of_columns):
        for x in range(layout.nr_of_rows):
            rect = StickerRect(layout, x, y)
            c.setStrokeColor(black, 0.1)
            c.setLineWidth(0)
            c.roundRect(rect.left, rect.bottom, rect.width, rect.height, rect.corner)


def main():

    # ############################################################################
    # Select the correct type of paper you want to print on.
    # ############################################################################
    # layout = AVERY_5260
    # layout = AVERY_L7157
    layout = Avery_3474_70x37_label

    # ############################################################################
    # select the font sizes for the resistor on the stickers
    # make sure the resistor settings match the page layout
    # Avery labels have one setting file.
    # ############################################################################
    # resistor_settings = AVERY_5260_AVERY_L7157_resistorsettings
    resistor_settings = Avery_3474_70x37_resistorsettings

    # ############################################################################
    # Put your own resistor values in here!
    # The number of pages needed is handled by the program.
    # The list below results in 4 pages.
    # You don't have to list resistor values for the whole page.
    # ############################################################################
    resistor_values = [
         1, 1.2, 1.3, 1.5, 1.6, 1.8, 2, 2.2, 2.4, 2.7, 3, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2,
         9.1,
         10, 11, 12, 15, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91,
         100, 110, 120, 130, 150, 160, 180, 200, 220, 240, 270, 300, 330, 360, 390, 430, 470, 510, 560, 620, 680, 750,
         820, 910,
         1000, 1100, 1200, 1500, 1600, 1800, 2000, 2200, 2400, 2700, 3000, 3300, 3600, 3900, 4300, 4700, 5100, 5600,
         6200, 6800, 7500, 8200, 9100,
         10000, 11000, 12000, 13000, 15000, 16000, 18000, 20000, 22000, 24000, 27000, 30000, 33000, 36000, 39000, 43000,
         47000, 51000, 56000, 62000, 68000, 75000, 82000, 91000,
         100000, 110000, 120000, 130000, 150000, 160000, 180000, 200000, 220000, 240000, 270000, 300000, 330000, 360000,
         390000, 430000, 470000, 510000, 560000, 620000, 680000, 750000, 820000, 910000,
         1000000, 1200000, 1500000, 1800000, 2000000, 2200000, 2400000, 2700000, 3000000, 3300000, 3600000, 3900000,
         4300000, 4700000, 5100000, 5600000, 6200000, 6800000, 7500000, 8200000, 9100000, 10000000,
    ]

    # Render the stickers
    render_stickers(layout, resistor_settings, resistor_values)

if __name__ == "__main__":
    main()
