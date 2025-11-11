"""
Keyboards package
Клавиатуры бота (inline и reply)
"""

from .reply import (
    get_main_menu,
    get_cancel_keyboard,
    get_confirmation_keyboard,
    get_report_frequency_keyboard
)

from .inline import (
    get_article_actions_keyboard,
    get_articles_list_keyboard,
    get_delete_confirmation_keyboard,
    get_back_button,
    get_url_button
)

__all__ = [
    # Reply keyboards
    "get_main_menu",
    "get_cancel_keyboard",
    "get_confirmation_keyboard",
    "get_report_frequency_keyboard",
    
    # Inline keyboards
    "get_article_actions_keyboard",
    "get_articles_list_keyboard",
    "get_delete_confirmation_keyboard",
    "get_back_button",
    "get_url_button",
]
