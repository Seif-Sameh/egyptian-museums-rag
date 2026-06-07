# Example queries the dataset can answer

The dataset is bilingual (AR + EN). Queries below are written in Arabic — the user-facing experience for your final demo.

## Identity / "what is this?"

```
ما هي قناع توت عنخ آمون؟
ما هو حجر رشيد؟
ما هو تمثال الكاتب الجالس؟
ما هو هرم خوفو؟
ما هو معبد دندور؟
```

## Location / "where can I see it?"

```
أين توجد صلاية نعرمر؟
في أي متحف يوجد قناع توت عنخ آمون؟
أين يُعرض تمثال نفرتيتي؟
في أي قاعة من المتحف المصري الكبير يُعرض مركب خوفو الشمسية؟
أين توجد مومياء رمسيس الثاني الآن؟
```

## Period / "when was it made?"

```
إلى أي عصر يعود تمثال خفرع؟
متى صُنعت صلاية نعرمر؟
أي أسرة حكمت في عهد توت عنخ آمون؟
ما الفترة الزمنية لمعبد حتشبسوت؟
```

## Material / "what's it made of?"

```
من أي مادة صُنع قناع توت عنخ آمون؟
هل تمثال خفرع من الجرانيت أم الديوريت؟
من أي مادة صُنعت بردية آني؟
```

## Discovery / "who found it, when?"

```
من اكتشف مقبرة توت عنخ آمون؟
متى اكتُشفت بردية إدوين سميث؟
من أين أُحضرت لوحة مرنبتاح؟
```

## Provenance / "where was it found?"

```
من أي موقع أثري أتى تمثال زوسر؟
أين عُثر على صلاية نعرمر؟
أين كانت بردية ريند الرياضية في الأصل؟
```

## Aggregations / multi-hop (require reasoning over multiple records)

```
ما هي القطع الموجودة حاليًا في قاعة توت عنخ آمون بالمتحف المصري الكبير؟
كم عدد المومياوات الملكية في المتحف القومي للحضارة المصرية؟
ما القطع التي اكتُشفت في وادي الملوك؟
ما القطع المصنوعة من الذهب من الأسرة الثامنة عشرة؟
ما القطع المنسوبة لرمسيس الثاني؟
```

## Museum / hall metadata (uses _museums.json + _halls.json)

```
ما القاعات الرئيسية في المتحف المصري الكبير؟
ما هو السلم العظيم؟
متى افتُتح المتحف المصري الكبير؟
ما الفرق بين المتحف المصري بالتحرير والمتحف المصري الكبير؟
أين يقع متحف الأقصر؟
```

## Cross-language (mixing AR question with English term)

```
أين يوجد Khufu Solar Boat؟
ما تاريخ Narmer Palette؟
```

## Generative / "tell me a story"

```
احكِ لي قصة اكتشاف مقبرة توت عنخ آمون.
لماذا يُعتبر حجر رشيد مهمًا؟
ما الذي كان يحدث في مصر في عهد أخناتون؟
```

---

The auto-generated `data/_qa_eval.jsonl` ships ~5 Q/A pairs per artifact across 8 categories (identity, location, period, material, discovery, provenance, hall, summary) — usable as a ground-truth eval set for the RAG pipeline.
