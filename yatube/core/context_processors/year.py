import datetime


def year(request):
    """Добавляет в контекст год."""
    return {
        'year': datetime.date.today().year,
    }
