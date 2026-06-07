"""Arabic aliases / alternative names for famous artifacts.

The Arabic Wikipedia article titles use one canonical form, but users often type
artifacts by a different common name. These aliases get folded into the search
index so retrieval still works.

Examples:
  كاعبر / كا عبر / كا-عبر  → SHEIKH_EL_BALAD (the priest Ka'aper, a.k.a. Sheikh el-Beled)
  أبو الهول الأكبر          → GREAT_SPHINX
  حجر رشيد                  → ROSETTA_STONE
"""

ALIASES: dict[str, list[str]] = {
    "TUT_MASK": [
        "قناع توت", "قناع توت عنخ آمون الذهبي", "قناع الفرعون الذهبي",
        "القناع الذهبي", "Mask of Tutankhamun",
    ],
    "TUT_THRONE": ["العرش الذهبي", "كرسي توت عنخ آمون", "كرسي الفرعون الذهبي"],
    "TUT_DAGGER": ["خنجر توت", "خنجر الفرعون النيزكي", "خنجر النيزك"],
    "TUT_INNER_COFFIN": ["التابوت الذهبي لتوت", "التابوت الذهبي الداخلي"],
    "TUT_TOMB": ["مقبرة توت عنخ آمون", "كي في 62", "KV62"],
    "NARMER_PALETTE": ["صلاية نعرمر", "صلاية الملك نعرمر", "لوحة نعرمر", "Narmer Palette"],
    "NARMER_MACEHEAD": ["مقمعة نعرمر", "صولجان نعرمر", "رأس صولجان نعرمر"],
    "BULL_PALETTE": ["صلاية الثيران", "صلاية الثور"],
    "HUNTERS_PALETTE": ["صلاية الصيد", "صلاية الصيادين"],
    "LIBYAN_PALETTE": ["صلاية المدن", "صلاية ليبيا"],
    "SHEIKH_EL_BALAD": [
        "شيخ البلد", "كاعبر", "كا عبر", "كا-عبر", "كاحبر", "كأعبر",
        "Ka'aper", "Sheikh el-Beled", "كاهن كا عبر", "تمثال كاعبر",
    ],
    "RAHOTEP_NOFRET": ["رع حتب ونفرت", "تمثال رع حتب", "رحوتب ونفرت", "تمثالا رحوتب ونفرت"],
    "SEATED_SCRIBE": ["الكاتب الجالس", "كاتب اللوفر", "تمثال الكاتب", "Seated Scribe"],
    "HEMIUNU": ["حم إيونو", "حم أيونو", "حميونو", "Hemiunu"],
    "MENKAURE_TRIAD": ["ثالوث منكاورع", "تماثيل منكاورع", "ثالوث منكاو رع"],
    "KHAFRE_ENTHRONED": ["تمثال خفرع", "خفرع الجالس", "خفرع متوج", "Khafre Enthroned", "تمثال الملك خفرع"],
    "KHUFU_STATUETTE": ["تمثال خوفو", "تمثال خوفو العاجي"],
    "KHUFU_SOLAR_BOAT": ["مركب خوفو", "مركب الشمس", "السفينة الشمسية", "مراكب خوفو", "مركب خوفو الشمسي"],
    "GREAT_PYRAMID": ["هرم خوفو", "الهرم الأكبر", "هرم الجيزة الأكبر", "Great Pyramid"],
    "GREAT_SPHINX": ["أبو الهول", "أبو الهول الأكبر", "تمثال أبو الهول", "Sphinx"],
    "STEP_PYRAMID": ["هرم زوسر", "الهرم المدرج", "هرم زوسر المدرج"],
    "BENT_PYRAMID": ["الهرم المنحني", "هرم سنفرو المنحني"],
    "RED_PYRAMID": ["الهرم الأحمر", "هرم سنفرو الشمالي"],
    "DJOSER_STATUE": ["تمثال زوسر", "تمثال الملك زوسر", "Djoser statue"],
    "ROSETTA_STONE": ["حجر رشيد", "حجر روزيتا", "Rosetta Stone"],
    "MERNEPTAH_STELE": ["لوحة مرنبتاح", "لوحة إسرائيل", "نصب مرنبتاح"],
    "NEFERTITI_BUST": ["تمثال نفرتيتي", "رأس نفرتيتي", "بست نفرتيتي", "Nefertiti Bust"],
    "AKHENATEN_COLOSSAL": ["تمثال أخناتون الضخم", "تمثال أخناتون الكولوسي"],
    "AMARNA_LETTERS": ["ألواح تل العمارنة", "رسائل العمارنة", "Amarna letters"],
    "RAMSES_II_TURIN": ["تمثال رمسيس الثاني تورينو", "تمثال رمسيس الثاني الجالس"],
    "RAMSES_II_MEMPHIS": ["تمثال رمسيس الثاني الضخم", "كولوس رمسيس الثاني", "تمثال رمسيس بميدان رمسيس"],
    "RAMSES_II_LUXOR": ["رمسيس الثاني بالأقصر", "تماثيل رمسيس بمعبد الأقصر"],
    "RAMSES_II_ABU_SIMBEL": ["معبد أبو سمبل", "معابد أبو سمبل", "Abu Simbel"],
    "BOOK_OF_DEAD": ["كتاب الموتى", "كتاب الخروج إلى النهار"],
    "PAPYRUS_ANI": ["بردية آني"],
    "PAPYRUS_HUNEFER": ["بردية حونفر", "بردية هونفر"],
    "EBERS_PAPYRUS": ["بردية إبيرس", "بردية إيبرس"],
    "EDWIN_SMITH_PAPYRUS": ["بردية إدوين سميث", "بردية إدوين-سميث"],
    "RHIND_PAPYRUS": ["بردية ريند", "بردية ريند الرياضية"],
    "PYRAMID_TEXTS": ["متون الأهرام", "نصوص الأهرام"],
    "COFFIN_TEXTS": ["متون التوابيت", "نصوص التوابيت"],
    "FAYUM_PORTRAITS": ["بورتريهات الفيوم", "تماثيل الفيوم", "صور الفيوم", "Fayum portraits"],
    "DENDERA_ZODIAC": ["بروج دندرة", "زودياك دندرة", "Dendera zodiac"],
    "PHILAE_OBELISK": ["مسلة فيلة", "مسلة فيلاي"],
    "USHABTI": ["أوشابتي", "تمثال أوشابتي", "تمثال شابتي"],
    "CANOPIC_JARS": ["أواني الأحشاء", "أواني الكانوبية", "الأواني الكانوبية", "كانوب"],
    "MEIDUM_GEESE": ["إوز ميدوم", "بطات ميدوم"],
    "MUSEUM_GEM": [
        "المتحف المصري الكبير", "متحف الجيزة", "GEM",
        "المتحف الكبير", "متحف الجيزة الكبير",
    ],
    "MUSEUM_EMC": ["المتحف المصري", "متحف التحرير", "متحف ميدان التحرير", "Egyptian Museum"],
    "MUSEUM_NMEC": [
        "متحف الحضارة", "المتحف القومي للحضارة المصرية",
        "متحف الفسطاط", "NMEC", "متحف الحضاره",
    ],
    "MUSEUM_LUX": ["متحف الأقصر"],
    "MUSEUM_BERLIN": ["متحف برلين", "المتحف الجديد ببرلين", "متحف نفرتيتي"],
    "MUSEUM_BM": ["المتحف البريطاني", "متحف لندن"],
    "MUSEUM_LOUVRE": ["متحف اللوفر", "اللوفر"],
    "MUSEUM_TURIN": ["متحف تورينو", "متحف تورين", "Museo Egizio"],
    "MUSEUM_MET": ["متحف المتروبوليتان", "المتروبوليتان", "Met Museum"],
}


def aliases_for(artifact_id: str) -> list[str]:
    return ALIASES.get(artifact_id, [])


def all_alias_pairs() -> list[tuple[str, str]]:
    """Return [(artifact_id, alias_text), ...] for every alias."""
    pairs: list[tuple[str, str]] = []
    for aid, names in ALIASES.items():
        for n in names:
            pairs.append((aid, n))
    return pairs
