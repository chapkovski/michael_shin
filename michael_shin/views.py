from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import json


def vars_for_all_templates(self):
    if self.round_number > 1:
        previous_precs = [p.get_prec() for p in self.player.in_previous_rounds()]
        nones = [None for _ in range(Constants.num_rounds - len(previous_precs))]
        prices = json.dumps([i.price for i in previous_precs] + nones)
        expected_prices = json.dumps([i.expected_price for i in previous_precs] + nones)
        return {'previous_precs': previous_precs,
                'rounds': list(range(1, Constants.num_rounds + 1)),
                'prices_series': prices,
                'expected_prices_series': expected_prices}


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
        if self.round_number==models.Constants.num_rounds:
            for p in self.group.get_players():
                p.set_payoff()


class Results(Page):
    pass


page_sequence = [
    Introduction,
    ForecastPrice,
    Participation,
    ResultsWaitPage,
    Results
]
