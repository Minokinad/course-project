from fastapi.templating import Jinja2Templates
from markupsafe import escape

def nl2br(value: str) -> str:
    """
    Преобразует переносы строк в HTML-тег <br>.
    """
    if not isinstance(value, str):
        return value
    return escape(value).replace('\n', '<br>\n')

templates = Jinja2Templates(directory="templates")

templates.env.add_extension('jinja2.ext.do')

templates.env.filters['nl2br'] = nl2br