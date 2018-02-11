from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
import json


def vars_for_all_templates(self):
    if self.round_number > 1:
        previous_precs = [p.get_prec() for p in self.player.in_previous_rounds()]
        previous_precs = previous_precs[:self.session.config.get('max_rounds_in_table', Constants.max_rounds_in_table)]
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
    form_model = 'player'
    form_fields = [ 'e_price_now','e_price_next',]



class Participation(Page):
    form_model = 'player'
    form_fields = ['participation']


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.price_temppayoff_calculate()
        if self.round_number == Constants.num_rounds:
            self.group.set_payoffs()


class Results(Page):
    pass


page_sequence = [
    Introduction,
    ForecastPrice,
    Participation,
    ResultsWaitPage,
    Results
]
