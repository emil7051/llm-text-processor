import pdfplumber
import re
import csv

# 1) Topics and subtopics you want to categorize by
TOPIC_CATEGORIES = {
    "Economic Growth": [
        r"economic growth", r"growth rate", r"gdp",
    ],
    "Unemployment": [
        r"unemployment", r"jobless", r"labour market",
    ],
    "Inflation": [
        r"inflation", r"cpi",
    ],
    "Environmental Sustainability": [
        r"environment", r"sustainab",
    ],
    "External Stability": [
        r"balance of payments", r"external stability", r"current account", r"foreign debt",
    ],
    "Distribution of Income and Wealth": [
        r"distribution of income", r"gini", r"inequality", r"lorenz",
    ],
    # Subtopics under 'Economic Policies' ...
    "Fiscal Policy": [
        r"fiscal policy", r"budget deficit", r"budget surplus",
    ],
    "Monetary Policy": [
        r"monetary policy", r"interest rate", r"cash rate", r"reserve bank",
    ],
    "Microeconomic Policy": [
        r"microeconomic reform", r"competition policy", r"deregulation",
    ],
    "Labour Market Policy": [
        r"industrial relations", r"wage determination", r"fair work", r"enterprise agreement",
    ],
    "Environmental Policy": [
        r"environmental policy", r"pollution permit", r"environmental regulation",
    ],
    "Effectiveness and Limitations of Economic Policy": [
        r"policy limitations", r"time lag", r"implementation lag",
    ],
}

# 2) Simple heuristics to detect short-answer style question blocks
SHORT_ANSWER_HEADING = re.compile(r"(Question\s+\d+\s*\(\d+\s*marks\)|Short Answer|Explain|Discuss|Outline|Why|Distinguish)", re.IGNORECASE)

# 3) Provide a list of PDF file paths you want to parse
pdf_files = [
    r"./pdfs/2010-hsc-economics.pdf",
    r"./pdfs/2011-hsc-economics.pdf",
    r"./pdfs/2012-hsc-economics.pdf",
    r"./pdfs/2013-hsc-economics.pdf",
    r"./pdfs/2014-hsc-economics.pdf",
    r"./pdfs/2015-hsc-economics.pdf",
    r"./pdfs/2016-hsc-economics.pdf",
    r"./pdfs/2017-hsc-economics.pdf",
    r"./pdfs/2018-hsc-economics.pdf",
    r"./pdfs/2019-hsc-economics.pdf",
    r"./pdfs/2020-hsc-economics.pdf",
    r"./pdfs/2021-hsc-economics.pdf",
    r"./pdfs/2022-hsc-economics.pdf",
]


def categorize_question(question_text):
    """
    Return one or more categories that match question_text.
    """
    text_lower = question_text.lower()
    matched_topics = []
    for topic, patterns in TOPIC_CATEGORIES.items():
        for pat in patterns:
            if re.search(pat, text_lower):
                matched_topics.append(topic)
                break
    if not matched_topics:
        matched_topics.append("Uncategorised")
    return matched_topics

all_short_answers = []

for pdf_file in pdf_files:
    try:
        with pdfplumber.open(pdf_file) as pdf:
            question_buffer = []
            current_question = None

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                for line in lines:
                    if SHORT_ANSWER_HEADING.search(line):
                        # finalize previous
                        if current_question:
                            categories = categorize_question("\n".join(question_buffer))
                            all_short_answers.append({
                                "pdf_file": pdf_file,
                                "page": page_num,
                                "question_heading": current_question,
                                "question_text": "\n".join(question_buffer),
                                "categories": categories
                            })
                            question_buffer = []
                        current_question = line
                    else:
                        if current_question:
                            question_buffer.append(line)

            # finalize last question if any
            if current_question and question_buffer:
                categories = categorize_question("\n".join(question_buffer))
                all_short_answers.append({
                    "pdf_file": pdf_file,
                    "page": page_num,
                    "question_heading": current_question,
                    "question_text": "\n".join(question_buffer),
                    "categories": categories
                })

    except Exception as e:
        print(f"Error reading {pdf_file}: {e}")

# 4) Write out to CSV
output_csv = "extracted_short_answer_questions.csv"
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["pdf_file", "page", "question_heading", "question_text", "categories"])
    for entry in all_short_answers:
        writer.writerow([
            entry["pdf_file"],
            entry["page"],
            entry["question_heading"],
            entry["question_text"],
            ";".join(entry["categories"])
        ])

print(f"Extraction complete. Short answer questions saved to {output_csv}.")
