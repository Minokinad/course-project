from typing import Dict, Any
from weasyprint import HTML
from src.templating import templates

# Данные о провайдере (в реальном приложении лучше вынести в конфиг)
PROVIDER_DETAILS = {
    "name": "ООО «БгуирТелСвязь»",
    "address": "220005, г. Минск, ул. Платонова, д. 39, каб. 108",
    "unp": "190123456",
    "bank_account": "BY28BSUIR30122B12340010270000",
    "bank_name": "ЗАО «Бгуир-Банк»",
    "bank_code": "BSUIRBY2X"
}

# Для красивого отображения даты
MONTHS_RU = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 5: "мая", 6: "июня",
    7: "июля", 8: "августа", 9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}


def generate_contract_pdf(contract_data: Dict[str, Any]) -> bytes:
    """
    Рендерит HTML-шаблон договора и преобразует его в PDF.
    """
    context = {
        "request": {},
        "contract": contract_data,
        "provider": PROVIDER_DETAILS,
        "months": MONTHS_RU
    }

    rendered_html = templates.get_template("pdf/contract_pdf.html").render(context)
    pdf_bytes = HTML(string=rendered_html).write_pdf()

    return pdf_bytes