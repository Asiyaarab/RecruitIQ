import os
import pandas as pd

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle
)

from reportlab.lib import colors


os.makedirs(
    "reports",
    exist_ok=True
)


def generate_csv(candidates):

    df = pd.DataFrame(
        candidates
    )

    df.to_csv(
        "reports/report.csv",
        index=False
    )


def generate_excel(candidates):

    df = pd.DataFrame(
        candidates
    )

    df.to_excel(
        "reports/report.xlsx",
        index=False
    )

def generate_pdf(candidates):

    document = SimpleDocTemplate("reports/report.pdf")

    data = [["Name", "Score", "Recommendation"]]

    for c in candidates:
        data.append([
            str(c.get("name", "")),
            str(c.get("score", "")) + "%",
            str(c.get("recommendation", ""))
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
    ]))

    document.build([table])