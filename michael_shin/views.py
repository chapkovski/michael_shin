from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants


def vars_for_all_templates(self):
    if self.round_number > 1:
        previous_precs = [p.get_prec() for p in self.player.in_previous_rounds()]
        return {'previous_precs': previous_precs}


class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1


class ForecastPrice(Page):
    form_model = models.Player

    def get_form_fields(self):
        fields = ['expected_price']
        if self.round_number == 1:
            fields.append('expected_price1')
        return fields


class Participation(Page):
    form_model = models.Player
    form_fields = ['participation']


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.price_calculate()


class Results(Page):
    pass


page_sequence = [
    Introduction,
    ForecastPrice,
    Participation,
    ResultsWaitPage,
    Results
]
