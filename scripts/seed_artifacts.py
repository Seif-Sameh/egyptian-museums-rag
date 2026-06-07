"""Curated seed list of famous Egyptian artifacts.
Each entry pairs an English Wikipedia title (canonical) with the Arabic Wikipedia title.
The Arabic titles are best-effort; the pipeline will resolve via interlanguage links if missing.
"""

# Format: (artifact_id, en_title, ar_title_hint, museum_hint)
# museum_hint: "GEM" (Grand Egyptian Museum), "EMC" (Egyptian Museum Cairo),
#              "NMEC" (National Museum of Egyptian Civilization), "LUX" (Luxor Museum),
#              "BERLIN" (Neues Museum Berlin), "BM" (British Museum), "MET" (Met),
#              "LOUVRE" (Louvre), "TURIN" (Museo Egizio)

SEED = [
    # ─── Tutankhamun treasure (KV62) ──────────────────────────────────────
    ("TUT_MASK", "Mask of Tutankhamun", "قناع توت عنخ آمون الذهبي", "GEM"),
    ("TUT_THRONE", "Golden Throne of Tutankhamun", "العرش الذهبي لتوت عنخ آمون", "GEM"),
    ("TUT_DAGGER", "Tutankhamun's meteoric iron dagger", "خنجر توت عنخ آمون النيزكي", "GEM"),
    ("TUT_INNER_COFFIN", "Coffin of Tutankhamun", "التابوت الذهبي لتوت عنخ آمون", "GEM"),
    ("TUT_CANOPIC", "Tutankhamun's tomb", "الصندوق الكانوبي لتوت عنخ آمون", "GEM"),
    ("TUT_CHARIOT", "Chariots of Tutankhamun", "عربات توت عنخ آمون", "GEM"),
    ("TUT_TOMB", "Tomb of Tutankhamun", "مقبرة توت عنخ آمون KV62", "VOK"),
    # ─── Predynastic / Early Dynastic ─────────────────────────────────────
    ("NARMER_PALETTE", "Narmer Palette", "صلاية نعرمر", "EMC"),
    ("BULL_PALETTE", "Bull Palette", "صلاية الثيران", "LOUVRE"),
    ("HUNTERS_PALETTE", "Hunters Palette", "صلاية الصيد", "BM"),
    ("LIBYAN_PALETTE", "Libyan Palette", "صلاية المدن", "EMC"),
    ("SCORPION_MACEHEAD", "Scorpion Macehead", "رأس صولجان الملك العقرب", "OXFORD"),
    ("NARMER_MACEHEAD", "Narmer Macehead", "رأس صولجان نارمر", "OXFORD"),
    ("DEN_LABEL", "Den (pharaoh)", "الملك دن", "BM"),
    # ─── Old Kingdom / Pyramid Age ────────────────────────────────────────
    ("KHUFU_STATUETTE", "Khufu", "الملك خوفو", "EMC"),
    ("KHUFU_SOLAR_BOAT", "Khufu ship", "مركب خوفو الشمسية", "GEM"),
    ("KHAFRE_ENTHRONED", "Khafre Enthroned", "تمثال خفرع الجالس", "EMC"),
    ("MENKAURE_TRIAD", "Menkaure", "الملك منكاورع", "EMC"),
    ("RAHOTEP_NOFRET", "Rahotep", "تمثال رع حتب ونفرت", "EMC"),
    ("SEATED_SCRIBE", "The Seated Scribe", "الكاتب الجالس", "LOUVRE"),
    ("SHEIKH_EL_BALAD", "Sheikh el-Beled", "تمثال شيخ البلد", "EMC"),
    ("HEMIUNU", "Hemiunu", "تمثال حم إيونو", "HILDESHEIM"),
    ("PYRAMIDION_AMENEMHAT", "Pyramidion of Amenemhat III", "هرم رأسي لأمنمحات الثالث", "EMC"),
    ("KAGEMNI_MASTABA", "Kagemni", "كاجمني", "SAQQARA"),
    # ─── Middle Kingdom ───────────────────────────────────────────────────
    ("AMENEMHAT_III_SPHINX", "Amenemhat III", "أمنمحات الثالث", "EMC"),
    ("MENTUHOTEP_II", "Mentuhotep II", "منتوحتب الثاني", "EMC"),
    ("SENUSRET_I_PILLARS", "Senusret I", "سنوسرت الأول", "EMC"),
    # ─── New Kingdom — Hatshepsut / Thutmose / Amenhotep ──────────────────
    ("HATSHEPSUT_SEATED", "Hatshepsut", "حتشبسوت", "MET"),
    ("HATSHEPSUT_TEMPLE", "Mortuary temple of Hatshepsut", "معبد حتشبسوت الجنائزي", "DEIRELBAHRI"),
    ("THUTMOSE_III", "Thutmose III", "تحتمس الثالث", "EMC"),
    ("AMENHOTEP_III_COLOSSI", "Colossi of Memnon", "تمثالا ممنون", "LUXOR_W"),
    ("YUYA_TUYA", "Yuya and Tjuyu", "يويا وتويا", "EMC"),
    # ─── Amarna / Akhenaten / Nefertiti ───────────────────────────────────
    ("AKHENATEN_COLOSSAL", "Colossal statue of Akhenaten from Karnak", "التمثال الضخم لأخناتون", "EMC"),
    ("NEFERTITI_BUST", "Nefertiti Bust", "تمثال نفرتيتي", "BERLIN"),
    ("AMARNA_PRINCESSES", "Akhetaten", "بنات أخناتون", "OXFORD"),
    ("AMARNA_LETTERS", "Amarna letters", "ألواح تل العمارنة", "BERLIN"),
    # ─── Ramesside ────────────────────────────────────────────────────────
    ("RAMSES_II_TURIN", "Ramesses II", "رمسيس الثاني", "TURIN"),
    ("RAMSES_II_MEMPHIS", "Memphis, Egypt", "ممفيس", "GEM"),
    ("RAMSES_II_LUXOR", "Luxor Temple", "معبد الأقصر", "LUXOR"),
    ("RAMSES_II_ABU_SIMBEL", "Abu Simbel", "معابد أبو سمبل", "ABUSIMBEL"),
    ("MERNEPTAH_STELE", "Merneptah Stele", "لوحة مرنبتاح", "EMC"),
    ("SETI_I_TOMB", "KV17", "مقبرة سيتي الأول", "VOK"),
    ("RAMSES_VI_TOMB", "KV9", "مقبرة رمسيس السادس", "VOK"),
    # ─── Royal mummies ────────────────────────────────────────────────────
    ("RAMSES_II_MUMMY", "Ramesses II", "مومياء رمسيس الثاني", "NMEC"),
    ("SETI_I_MUMMY", "Seti I", "مومياء سيتي الأول", "NMEC"),
    ("THUTMOSE_III_MUMMY", "Thutmose III", "مومياء تحتمس الثالث", "NMEC"),
    ("HATSHEPSUT_MUMMY", "Hatshepsut", "مومياء حتشبسوت", "NMEC"),
    ("AMENHOTEP_I_MUMMY", "Amenhotep I", "مومياء أمنحتب الأول", "NMEC"),
    # ─── Late / Ptolemaic / Roman ────────────────────────────────────────
    ("ROSETTA_STONE", "Rosetta Stone", "حجر رشيد", "BM"),
    ("CANOPUS_DECREE", "Canopus Decree", "مرسوم كانوبوس", "EMC"),
    ("ALEXANDER_SARCOPHAGUS", "Alexander Sarcophagus", "تابوت الإسكندر", "ISTANBUL"),
    ("FAYUM_PORTRAITS", "Fayum mummy portraits", "بورتريهات الفيوم", "VARIOUS"),
    ("DENDERA_ZODIAC", "Dendera zodiac", "بروج دندرة", "LOUVRE"),
    ("PHILAE_OBELISK", "Philae obelisk", "مسلة فيلة", "KINGSTON"),
    # ─── Architecture / Temples / Pyramids (treated as artifact entries) ──
    ("GREAT_PYRAMID", "Great Pyramid of Giza", "هرم خوفو", "GIZA"),
    ("GREAT_SPHINX", "Great Sphinx of Giza", "أبو الهول", "GIZA"),
    ("STEP_PYRAMID", "Pyramid of Djoser", "هرم زوسر المدرج", "SAQQARA"),
    ("BENT_PYRAMID", "Bent Pyramid", "الهرم المنحني", "DAHSHUR"),
    ("RED_PYRAMID", "Red Pyramid", "الهرم الأحمر", "DAHSHUR"),
    ("KARNAK_TEMPLE", "Karnak", "معابد الكرنك", "LUXOR"),
    ("LUXOR_TEMPLE", "Luxor Temple", "معبد الأقصر", "LUXOR"),
    ("MEDINET_HABU", "Medinet Habu", "معبد مدينة هابو", "LUXOR_W"),
    ("DEIR_EL_BAHARI", "Deir el-Bahari", "الدير البحري", "LUXOR_W"),
    ("VALLEY_OF_KINGS", "Valley of the Kings", "وادي الملوك", "LUXOR_W"),
    ("VALLEY_OF_QUEENS", "Valley of the Queens", "وادي الملكات", "LUXOR_W"),
    ("ABYDOS", "Abydos, Egypt", "أبيدوس", "ABYDOS"),
    ("EDFU_TEMPLE", "Temple of Edfu", "معبد إدفو", "EDFU"),
    ("PHILAE_TEMPLE", "Philae", "معبد فيلة", "ASWAN"),
    ("DENDERA_TEMPLE", "Dendera Temple complex", "معبد دندرة", "DENDERA"),
    ("KOM_OMBO", "Kom Ombo", "معبد كوم أمبو", "KOMOMBO"),
    # ─── Sacred animal mummies / Apis ────────────────────────────────────
    ("APIS_BULL", "Apis (deity)", "ثور أبيس", "VARIOUS"),
    ("SERAPEUM_SAQQARA", "Serapeum of Saqqara", "سيرابيوم سقارة", "SAQQARA"),
    # ─── Funerary papyri & literature ─────────────────────────────────────
    ("BOOK_OF_DEAD", "Book of the Dead", "كتاب الموتى", "VARIOUS"),
    ("PAPYRUS_ANI", "Papyrus of Ani", "بردية آني", "BM"),
    ("PAPYRUS_HUNEFER", "Papyrus of Hunefer", "بردية حونفر", "BM"),
    ("EBERS_PAPYRUS", "Ebers Papyrus", "بردية إبيرس", "LEIPZIG"),
    ("EDWIN_SMITH_PAPYRUS", "Edwin Smith Papyrus", "بردية إدوين سميث", "NYAM"),
    ("RHIND_PAPYRUS", "Rhind Mathematical Papyrus", "بردية ريند الرياضية", "BM"),
    ("PYRAMID_TEXTS", "Pyramid Texts", "متون الأهرام", "VARIOUS"),
    ("COFFIN_TEXTS", "Coffin Texts", "متون التوابيت", "VARIOUS"),
    # ─── Daily life / ushabti / canopic ───────────────────────────────────
    ("USHABTI", "Ushabti", "تمثال أوشابتي", "VARIOUS"),
    ("CANOPIC_JARS", "Canopic jar", "أواني الأحشاء", "VARIOUS"),
    # ─── Iconic statues outside Egypt ─────────────────────────────────────
    ("DJOSER_STATUE", "Statue of Djoser", "تمثال زوسر", "EMC"),
    ("SAHURE_NOME_GOD", "Sahure and a Nome God", "تمثال ساحورع وإله الإقليم", "MET"),
    # ─── 21st-Dynasty / Tanis ─────────────────────────────────────────────
    ("PSUSENNES_MASK", "Funerary mask of Psusennes I", "قناع بسوسنس الأول", "EMC"),
    ("TANIS_TREASURES", "Tanis", "كنوز تانيس", "EMC"),
    ("AMENEMOPE_TREASURE", "Amenemope (pharaoh)", "كنوز أمنموبي", "EMC"),
    # ─── Late Period & Saite ──────────────────────────────────────────────
    ("PSAMTIK_OFFERING", "Psamtik I", "تمثال بسماتيك الأول", "EMC"),
    ("MONTUEMHAT", "Montuemhat", "تمثال منتومحات", "EMC"),
    # ─── Daily life / decorative arts ─────────────────────────────────────
    ("MEIDUM_GEESE", "Meidum Geese", "إوز ميدوم", "EMC"),
    ("FAIRY_TALE_PRINCESS", "Princess Nofret", "تمثال الأميرة نفرت", "EMC"),
    # ─── Coptic / Late antique ────────────────────────────────────────────
    ("COPTIC_TEXTILES", "Coptic art", "الفن القبطي", "COPTIC_MUSEUM"),
    # ─── Islamic Cairo monuments (museum offers Islamic galleries) ────────
    ("AL_AZHAR_MOSQUE", "Al-Azhar Mosque", "الجامع الأزهر", "CAIRO"),
    ("MOSQUE_IBN_TULUN", "Mosque of Ibn Tulun", "مسجد ابن طولون", "CAIRO"),
    ("SULTAN_HASSAN", "Mosque-Madrasa of Sultan Hassan", "مسجد ومدرسة السلطان حسن", "CAIRO"),
    # ─── Modern museum buildings themselves ───────────────────────────────
    ("GEM_BUILDING", "Grand Egyptian Museum", "المتحف المصري الكبير", "GEM"),
    ("EMC_BUILDING", "Egyptian Museum", "المتحف المصري", "EMC"),
    ("NMEC_BUILDING", "National Museum of Egyptian Civilization", "المتحف القومي للحضارة المصرية", "NMEC"),
    ("LUXOR_MUSEUM", "Luxor Museum", "متحف الأقصر", "LUX"),
]

# ─── Museum master metadata (location / hall structure to seed manually) ─
MUSEUMS = {
    "GEM": {
        "ar": {
            "name": "المتحف المصري الكبير",
            "city": "الجيزة",
            "country": "مصر",
            "summary": "أكبر متحف أثري في العالم مخصص لحضارة واحدة، يقع على هضبة الجيزة بجوار الأهرامات. يضم قاعات رئيسية كقاعة كنوز توت عنخ آمون، السلم العظيم، قاعة مركب خوفو الشمسية، والقاعات الكبرى المرتبة حسب المحاور الزمنية والملكية والمعتقدات والمجتمع.",
        },
        "en": {
            "name": "Grand Egyptian Museum",
            "city": "Giza",
            "country": "Egypt",
            "summary": "The largest archaeological museum in the world devoted to a single civilization, located on the Giza Plateau next to the pyramids. Halls include the Tutankhamun Galleries, the Grand Staircase, the Khufu Solar Boat Hall, and the Main Galleries arranged by chronology, kingship, beliefs, and society.",
        },
        "halls": [
            ("TUT_GALLERIES", "قاعات توت عنخ آمون", "Tutankhamun Galleries", "تعرض ما يقرب من 5,400 قطعة من مقتنيات الملك توت لأول مرة كاملة في مكان واحد."),
            ("GRAND_STAIRCASE", "السلم العظيم", "Grand Staircase", "سلم احتفالي بطول 64 مترًا ترتفع على جوانبه تماثيل ضخمة من جميع العصور المصرية."),
            ("ATRIUM", "البهو الرئيسي", "Atrium", "يستقبل الزائرين بتمثال رمسيس الثاني الذي تم نقله من ميدان رمسيس بالقاهرة."),
            ("KHUFU_BOAT_HALL", "قاعة مركب خوفو الشمسية", "Khufu Solar Boat Hall", "تعرض مركب الملك خوفو الجنائزية، أقدم وأكبر سفينة خشبية محفوظة في العالم."),
            ("MAIN_GALLERIES", "القاعات الرئيسية الـ12", "Main Twelve Galleries", "12 قاعة رئيسية ترتب القطع وفق ثلاثة محاور: الملكية، المعتقدات، المجتمع، عبر أربع حقب: عصر ما قبل الأسرات والدولة القديمة، الدولة الوسطى، الدولة الحديثة، والعصر المتأخر والبطلمي والروماني."),
            ("CHILDREN_MUSEUM", "متحف الأطفال", "Children's Museum", "قاعات تفاعلية مخصصة لتعريف الأطفال بالحضارة المصرية القديمة."),
        ],
    },
    "EMC": {
        "ar": {
            "name": "المتحف المصري",
            "city": "القاهرة",
            "country": "مصر",
            "summary": "متحف بميدان التحرير افتُتح عام 1902، يضم أكبر مجموعة من الآثار الفرعونية في العالم. يحتفظ بمقتنيات بارزة مثل صلاية نعرمر، تماثيل خوفو وخفرع ومنكاورع، كنوز يويا وتويا، ومجموعة من أهم المومياوات الملكية قبل نقلها إلى المتحف القومي للحضارة.",
        },
        "en": {
            "name": "Egyptian Museum",
            "city": "Cairo",
            "country": "Egypt",
            "summary": "Founded in 1902 on Tahrir Square, holds the world's largest collection of Pharaonic antiquities. Notable holdings include the Narmer Palette, statues of Khufu/Khafre/Menkaure, Yuya and Thuya treasure, and many royal mummies before their transfer to NMEC.",
        },
        "halls": [
            ("GROUND_FLOOR", "الطابق الأرضي", "Ground Floor", "يضم القطع الكبيرة الحجم مرتبة وفق التسلسل الزمني من عصر ما قبل الأسرات حتى العصر اليوناني الروماني."),
            ("UPPER_FLOOR", "الطابق العلوي", "Upper Floor", "يضم مقتنيات صغيرة مرتبة موضوعيًا تشمل كنوز توت عنخ آمون قبل نقلها، يويا وتويا، الحلي، التوابيت، والمومياوات."),
            ("ATRIUM_HALL", "البهو الرئيسي", "Central Atrium", "البهو المركزي بقطع ضخمة منها لوحة مرنبتاح وتماثيل الملكة حتشبسوت."),
        ],
    },
    "NMEC": {
        "ar": {
            "name": "المتحف القومي للحضارة المصرية",
            "city": "الفسطاط، القاهرة",
            "country": "مصر",
            "summary": "افتُتح بالكامل في 2021 ويستعرض الحضارة المصرية من عصور ما قبل التاريخ حتى العصر الحديث. يستضيف قاعة المومياوات الملكية بعد موكب نقل المومياوات الملكي عام 2021.",
        },
        "en": {
            "name": "National Museum of Egyptian Civilization",
            "city": "Fustat, Cairo",
            "country": "Egypt",
            "summary": "Fully opened in 2021. Showcases Egyptian civilization from prehistory to the modern era. Hosts the Royal Mummies Hall after the 2021 Pharaohs' Golden Parade.",
        },
        "halls": [
            ("ROYAL_MUMMIES", "قاعة المومياوات الملكية", "Royal Mummies Hall", "تضم 22 مومياء ملكية نُقلت في موكب المومياوات الذهبي عام 2021."),
            ("MAIN_GALLERY", "القاعة الرئيسية", "Main Gallery", "تستعرض الحضارة المصرية بشكل موضوعي عبر العصور."),
            ("CIVILIZATION_GALLERIES", "قاعات الحضارة الموضوعية", "Civilization Galleries", "قاعات بأشكال حياة المصريين، الثقافة المادية، الكتابة، الزراعة، والمعتقدات."),
        ],
    },
}
