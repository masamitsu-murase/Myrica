#!/usr/bin/python
# -*- coding: utf-8 -*-

#
# Author: Tomokuni SEKIYA
#
# This script is for generating ``myrica'' font
#
# * Inconsolata  : Inconsolata-Regular.ttf           : 1.016 (Google Fonts)
# * 源真ゴシック : GenShinGothic-Monospace-Light.ttf : 1.002.20150607
#
# 以下のように構成されます。
# ・英数字記号は、Inconsolata
# ・他の文字は、源真ゴシック
# ・一部の文字を視認性向上のために migu の特徴を取込み
#     半濁点（ぱぴぷぺぽパピプペポ の右上の円）を大きくして、濁点と判別しやすく
#     「カ力 エ工 ロ口 ー一 ニ二」（カタカナ・漢字）の区別
#     ～〜（FULLWIDTH TILDE・WAVE DASH）の区別
#     ー一－（カタカナ・漢字・マイナス）の区別

# version
newfont_version      = "2.012.20180119"
newfont_sfntRevision = 0x00010000

# set font name
newfontC  = ("../Work/MuraseC.ttf", "MuraseC", "Murase C", "Murase Console")

# source file
srcfontIncosolata    = "../SourceTTF/Inconsolata-Regular.ttf"
srcfontIncosolataOrg = "../SourceTTF/Inconsolata-Regular-org.ttf"
srcfontGenShin       = "../SourceTTF/GenShinGothic-Monospace-Light.ttf"
srcfontReplaceParts  = "myrica_ReplaceParts.ttf"

# out file
outfontNoHint = "../Work/MyricaM_NoHint.ttf"

# flag
scalingDownIfWidth_flag = True

# set ascent and descent (line width parameters)
newfont_ascent  = 840
newfont_descent = 184
newfont_em = newfont_ascent + newfont_descent

newfont_winAscent   = 840
newfont_winDescent  = 170
newfont_typoAscent  = newfont_winAscent
newfont_typoDescent = -newfont_winDescent
newfont_typoLinegap = 0
newfont_hheaAscent  = newfont_winAscent
newfont_hheaDescent = -newfont_winDescent
newfont_hheaLinegap = 0

# define
generate_flags = ('opentype', 'PfEd-lookups', 'TeX-table')
panoseBase = (2, 11, 5, 9, 2, 2, 3, 2, 2, 7)

########################################
# setting
########################################

import copy
import os
import sys
import shutil
import fontforge
import psMat
import json

# 縦書きのために指定する
fontforge.setPrefs('CoverageFormatsAllowed', 1)
# 大変更時に命令を消去 0:オフ 1:オン
fontforge.setPrefs('ClearInstrsBigChanges', 0)
# TrueType命令をコピー 0:オフ 1:オン
fontforge.setPrefs('CopyTTFInstrs', 1)

########################################
# pre-process
########################################

print 
print 
print "myrica generator " + newfont_version
print 
print "This script is for generating 'myrica' font"
print 
if os.path.exists( srcfontIncosolata ) == False:
    print "Error: " + srcfontIncosolata + " not found"
    sys.exit( 1 )
if os.path.exists( srcfontReplaceParts ) == False:
    print "Error: " + srcfontReplaceParts + " not found"
    sys.exit( 1 )
if os.path.exists( srcfontGenShin ) == False:
    print "Error: " + srcfontGenShin + " not found"
    sys.exit( 1 )

########################################
# define function
########################################
def matRescale(origin_x, origin_y, scale_x, scale_y):
    return psMat.compose(
        psMat.translate(-origin_x, -origin_y), psMat.compose(
        psMat.scale(scale_x, scale_y), 
        psMat.translate(origin_x, origin_y)))

def matMove(move_x, move_y):
    return psMat.translate(move_x, move_y)

def rng(start, end):
    return range(start, end + 1)

def flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)):
            for f in flatten(e):
                yield f
        else:
            yield e

def select(font, *codes):
    font.selection.none()
    selectMore(font, codes)

def selectMore(font, *codes):
    flat = flatten(codes)
    for c in flat:
        if isinstance(c, (unicode, )):
            font.selection.select(("more",), ord(c))
        else:
            font.selection.select(("more",), c)

def selectLess(font, *codes):
    flat = flatten(codes)
    for c in flat:
        if isinstance(c, (unicode, )):
            font.selection.select(("less",), ord(c))
        else:
            font.selection.select(("less",), c)

def selectExistAll(font):
    font.selection.none()
    for glyphName in font:
        if font[glyphName].isWorthOutputting() == True:
            font.selection.select(("more",), glyphName)

def copyAndPaste(srcFont, srcCodes, dstFont, dstCodes):
    select(srcFont, srcCodes)
    srcFont.copy()
    select(dstFont, dstCodes)
    dstFont.paste()

def copyAndPasteInto(srcFont, srcCodes, dstFont, dstCodes, pos_x, pos_y):
    select(srcFont, srcCodes)
    srcFont.copy()
    select(dstFont, dstCodes)
    dstFont.transform(matMove(-pos_x, -pos_y))
    dstFont.pasteInto()
    dstFont.transform(matMove(pos_x, pos_y))

def scalingDownIfWidth(font, scaleX, scaleY):
    for glyph in font.selection.byGlyphs:
        width = glyph.width
        glyph.transform(matRescale(width / 2, 0, scaleX, scaleY))
        glyph.width = width

def centerInWidth(font):
    for glyph in font.selection.byGlyphs:
        w  = glyph.width
        wc = w / 2
        bb = glyph.boundingBox()
        bc = (bb[0] + bb[2]) / 2
        glyph.transform(matMove(wc - bc, 0))
        glyph.width = w

def setWidth(font, width):
    for glyph in font.selection.byGlyphs:
        glyph.width = width

def setAutoWidthGlyph(glyph, separation):
    bb = glyph.boundingBox()
    bc = (bb[0] + bb[2]) / 2
    nw = (bb[2] - bb[0]) + separation * 2
    if glyph.width > nw:
        wc = nw / 2
        glyph.transform(matMove(wc - bc, 0))
        glyph.width = nw

def autoHintAndInstr(font, *codes):
    removeHintAndInstr(font, codes)
    font.autoHint()
    font.autoInstr()

def removeHintAndInstr(font, *codes):
    select(font, codes)
    for glyph in font.selection.byGlyphs:
        if glyph.isWorthOutputting() == True:
            glyph.manualHints = False
            glyph.ttinstrs = ()
            glyph.dhints = ()
            glyph.hhints = ()
            glyph.vhints = ()

def copyTti(srcFont, dstFont):
    for glyphName in dstFont:
        dstFont.setTableData('fpgm', srcFont.getTableData('fpgm'))
        dstFont.setTableData('prep', srcFont.getTableData('prep'))
        dstFont.setTableData('cvt',  srcFont.getTableData('cvt'))
        dstFont.setTableData('maxp', srcFont.getTableData('maxp'))
        copyTtiByGlyphName(srcFont, dstFont, glyphName)

def copyTtiByGlyphName(srcFont, dstFont, glyphName):
    try:
        dstGlyph = dstFont[glyphName]
        srcGlyph = srcFont[glyphName]
        if srcGlyph.isWorthOutputting() == True and dstGlyph.isWorthOutputting() == True:
            dstGlyph.manualHints = True
            dstGlyph.ttinstrs = srcFont[glyphName].ttinstrs
            dstGlyph.dhints = srcFont[glyphName].dhints
            dstGlyph.hhints = srcFont[glyphName].hhints
            dstGlyph.vhints = srcFont[glyphName].vhints
    except TypeError:
        pass

def setFontProp(font, fontInfo):
    font.fontname   = fontInfo[1]
    font.familyname = fontInfo[2]
    font.fullname   = fontInfo[3]
    font.weight = "Book"
    font.copyright =  "Copyright (c) 2006-2012 Raph Levien (Inconsolata)\n"
    font.copyright += "Copyright (c) 2013 M+ FONTS PROJECT (M+)\n"
    font.copyright += "Copyright (c) 2013 itouhiro (Migu)\n"
    font.copyright += "Copyright (c) 2014 MM (GenShinGothic)\n"
    font.copyright += "Copyright (c) 2014 Adobe Systems Incorporated. (NotoSansJP)\n"
    font.copyright += "Licenses:\n"
    font.copyright += "SIL Open Font License Version 1.1 "
    font.copyright += "(http://scripts.sil.org/ofl)\n"
    font.version = newfont_version
    font.sfntRevision = newfont_sfntRevision
    font.sfnt_names = (('English (US)', 'UniqueID', fontInfo[2]), )

    font.hasvmetrics = True
    font.head_optimized_for_cleartype = True

    font.os2_panose = panoseBase
    font.os2_vendor = "ES"
    font.os2_version = 1

    font.os2_winascent       = newfont_winAscent
    font.os2_winascent_add   = 0
    font.os2_windescent      = newfont_winDescent
    font.os2_windescent_add  = 0
    font.os2_typoascent      = newfont_typoAscent
    font.os2_typoascent_add  = 0
    font.os2_typodescent     = newfont_typoDescent
    font.os2_typodescent_add = 0
    font.os2_typolinegap     = newfont_typoLinegap
    font.hhea_ascent         = newfont_hheaAscent
    font.hhea_ascent_add     = 0
    font.hhea_descent        = newfont_hheaDescent
    font.hhea_descent_add    = 0
    font.hhea_linegap        = newfont_hheaLinegap

    font.upos = 45

charASCII  = rng(0x0021, 0x007E)
charZHKana = list(u"ぁあぃいぅうぇえぉおかがきぎくぐけげこごさざしじすずせぜそぞただちぢっつづてでとどなにぬねのはばぱひびぴふぶぷへべぺほぼぽまみむめもゃやゅゆょよらりるれろゎわゐゑをん"),
charZKKana = list(u"ァアィイゥウェエォオカガキギクグケゲコゴサザシジスズセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴヵヶ"),
charHKKana = list(u"､｡･ｰﾞﾟ｢｣ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜｦﾝｧｨｩｪｫｬｭｮｯ")
charZEisu = list(u"０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ")

########################################
# modified ReplaceParts
########################################

print
print "Open " + srcfontReplaceParts
fRp = fontforge.open( srcfontReplaceParts )

# modify em
fRp.em  = newfont_em
fRp.ascent  = newfont_ascent
fRp.descent = newfont_descent

# post-process
fRp.selection.all()
fRp.round()

########################################
# modified Inconsolata
########################################

print
print "Open " + srcfontIncosolata
fIn = fontforge.open( srcfontIncosolata )
fIn.mergeFonts( srcfontIncosolataOrg )

# modify
print "modify"
# 拡大 "'`
select(fIn, 0x0022, 0x0027, 0x0060)
fIn.transform(matRescale(250, 600, 1.15, 1.15))
setWidth(fIn, 1000 / 2)

# 拡大 ,.:;
select(fIn, 0x002c, 0x002e, 0x003a, 0x003b)
fIn.transform(matRescale(250, 0, 1.20, 1.20))
setWidth(fIn, 1000 / 2)

# 移動 ~
select(fIn, 0x007e)
fIn.transform(matMove(0, 120))

# 移動 ()
select(fIn, list(u"()"))
fIn.transform(matMove(0, 89))

# 移動 []
select(fIn, list(u"[]"))
fIn.transform(matMove(0, 15))

# 移動 {}
select(fIn, list(u"{}"))
fIn.transform(matMove(0, 91))

# | -> broken | (Inconsolata's glyph)
copyAndPaste(fIn, 0x00a6, fIn, 0x007c)
select(fIn, 0x007c)
fIn.transform(matMove(0, 100))

# D -> D of Eth (D with cross-bar)
copyAndPaste(fIn, 0x0110, fIn, 0x0044)

# r -> r of serif (Inconsolata's unused glyph)
copyAndPaste(fIn,  65548, fIn, 0x0072)

removeHintAndInstr(fIn, 0x0022, 0x0027, 0x0060, list(u"\"'`,.:;()~[]{}|"))

# modify em
fIn.em  = newfont_em
fIn.ascent  = newfont_ascent
fIn.descent = newfont_descent

# 文字の置換え
print "merge ReplaceParts"
for glyph in fRp.glyphs():
    if glyph.unicode > 0:
        select(fRp, glyph.glyphname)
        fRp.copy()
        select(fIn, glyph.glyphname)
        fIn.paste()

# # 必要文字(半角英数字記号)だけを残して削除
# select(fIn, rng(0x0021, 0x007E))
# fIn.selection.invert()
# fIn.clear()

fIn.selection.all()
fIn.round()

fIn.generate("../Work/modIncosolata.ttf", '', generate_flags)
fIn.close()

########################################
# modified GenShin
########################################

print
print "Open " + srcfontGenShin
fGs = fontforge.open( srcfontGenShin )

# modify
print "modify"

# modify em
fGs.em  = newfont_em
fGs.ascent  = newfont_ascent
fGs.descent = newfont_descent

# 文字の置換え
print "merge ReplaceParts"
for glyph in fRp.glyphs():
    if glyph.unicode > 0:
        select(fRp, glyph.glyphname)
        fRp.copy()
        select(fGs, glyph.glyphname)
        fGs.paste()

# 半角英数字記号を削除
select(fGs, rng(0x0021, 0x007E))
fGs.clear()

# scaling down
if scalingDownIfWidth_flag == True:
    print "While scaling, wait a little..."
    # 0.91はRictyに準じた。
    selectExistAll(fGs)
    selectLess(fGs, (charASCII, charHKKana, charZHKana, charZKKana, charZEisu))
    scalingDownIfWidth(fGs, 0.91, 0.91)
    # 平仮名/片仮名のサイズを調整
    select(fGs, (charZHKana,charZKKana))
    scalingDownIfWidth(fGs, 0.97, 0.97)
    # 全角英数の高さを調整 (半角英数の高さに合わせる)
    select(fGs, charZEisu)
    scalingDownIfWidth(fGs, 0.91, 0.86)

for l in fGs.gsub_lookups:
    fGs.removeLookup(l)
for l in fGs.gpos_lookups:
    fGs.removeLookup(l)

#autoHintAndInstr(fGs, (charZHKana, charZKKana, charHKKana, charZEisu))

fGs.generate("../Work/modGenShin.ttf", '', generate_flags)
os2_unicoderanges = fGs.os2_unicoderanges
os2_codepages = fGs.os2_codepages

fGs.close()
fRp.close()

########################################
# create Myrica Console
########################################
fMc = fontforge.open("../Work/modIncosolata.ttf")

print
print "Build " + newfontC[0]

# pre-process
setFontProp(fMc, newfontC)

eaw_to_width = {
    "F": 2,
    "W": 2,
    "A": 1,
    "H": 1,
    "Na": 1,
    "N": 1
}

# merge GenShin
print "merge GenShin"
# マージ
fMc.mergeFonts( "../Work/modGenShin.ttf" )
fMc.os2_unicoderanges = os2_unicoderanges
fMc.os2_codepages = os2_codepages

with open("east_asian_width.json", "r") as f:
    east_asian_width = json.load(f)
negative_chars = [
    0x024EB,  # ⓫
    0x024EC,  # ⓬
    0x024ED,  # ⓭
    0x024EE,  # ⓮
    0x024EF,  # ⓯
    0x024F0,  # ⓰
    0x024F1,  # ⓱
    0x024F2,  # ⓲
    0x024F3,  # ⓳
    0x024F4,  # ⓴
    0x024FF,  # ⓿
    0x02776,  # ❶
    0x02777,  # ❷
    0x02778,  # ❸
    0x02779,  # ❹
    0x0277A,  # ❺
    0x0277B,  # ❻
    0x0277C,  # ❼
    0x0277D,  # ❽
    0x0277E,  # ❾
    0x0277F,  # ❿
    0x0278A,  # ➊
    0x0278B,  # ➋
    0x0278C,  # ➌
    0x0278D,  # ➍
    0x0278E,  # ➎
    0x0278F,  # ➏
    0x02790,  # ➐
    0x02791,  # ➑
    0x02792,  # ➒
    0x02793,  # ➓
    0x1F150,  # 🅐
    0x1F151,  # 🅑
    0x1F152,  # 🅒
    0x1F153,  # 🅓
    0x1F154,  # 🅔
    0x1F155,  # 🅕
    0x1F156,  # 🅖
    0x1F157,  # 🅗
    0x1F158,  # 🅘
    0x1F159,  # 🅙
    0x1F15A,  # 🅚
    0x1F15B,  # 🅛
    0x1F15C,  # 🅜
    0x1F15D,  # 🅝
    0x1F15E,  # 🅞
    0x1F15F,  # 🅟
    0x1F160,  # 🅠
    0x1F161,  # 🅡
    0x1F162,  # 🅢
    0x1F163,  # 🅣
    0x1F164,  # 🅤
    0x1F165,  # 🅥
    0x1F166,  # 🅦
    0x1F167,  # 🅧
    0x1F168,  # 🅨
    0x1F169,  # 🅩
    0x1F170,  # 🅰
    0x1F171,  # 🅱
    0x1F172,  # 🅲
    0x1F173,  # 🅳
    0x1F174,  # 🅴
    0x1F175,  # 🅵
    0x1F176,  # 🅶
    0x1F177,  # 🅷
    0x1F178,  # 🅸
    0x1F179,  # 🅹
    0x1F17A,  # 🅺
    0x1F17B,  # 🅻
    0x1F17C,  # 🅼
    0x1F17D,  # 🅽
    0x1F17E,  # 🅾
    0x1F17F,  # 🅿
    0x1F180,  # 🆀
    0x1F181,  # 🆁
    0x1F182,  # 🆂
    0x1F183,  # 🆃
    0x1F184,  # 🆄
    0x1F185,  # 🆅
    0x1F186,  # 🆆
    0x1F187,  # 🆇
    0x1F188,  # 🆈
    0x1F189,  # 🆉
    0x1F18A,  # 🆊
    0x1F18B,  # 🆋
    0x1F18C,  # 🆌
    0x1F18D,  # 🆍
    0x1F18F,  # 🆏
]
negative_chars_set = set(negative_chars)
# Change size of ambiguous characters.
for glyph in fMc.glyphs():
    if glyph.unicode > 0:
        s = "\\U%08x" % glyph.unicode
        ch = s.decode('unicode-escape')
        width = glyph.width

        if width not in (0, 512, 1024):
            print("Warning: Unknown width: ", "0x%X" % glyph.unicode, width)

        eaw = east_asian_width[ch]
        if width > 0 and eaw_to_width[eaw] * 512 != width:
            if width == 1024:
                scaleX = scaleY = 0.5
                glyph.transform(matRescale(0, 0, scaleX, scaleY))
                glyph.width = width / 2
                if glyph.unicode not in negative_chars_set:
                    weight = 9
                    glyph.changeWeight(weight)
                else:
                    weight = -15
                    glyph.changeWeight(weight)

# post-process
fMc.selection.all()
fMc.round()

# generate
print "Generate " + newfontC[0]
fMc.generate(newfontC[0], '', generate_flags)

fMc.close()
