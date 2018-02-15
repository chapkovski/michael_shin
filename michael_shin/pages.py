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
        expected_prices = json.dumps([float(i.expected_price) for i in previous_precs] + nones)
        return {'previous_precs': previous_precs,
                'rounds': list(range(1, Constants.num_rounds + 1)),
                'prices_series': prices,
                'expected_prices_series': expected_prices}


class Introduction(Page):
    def is_displayed(self):
        return self.round_number == 1


class ForecastPrice(Page):
    form_model = 'player'
    form_fields = ['e_price_now', 'e_price_next', ]

    def vars_for_template(self):
        label = "Predict the price in this round"
        addendum = " (your last prediction for this round was {prev})?".format(
            prev=self.player.previous_expected()) if self.round_number > 1 else ''
        label += addendum
        return {'label': label}


class Participation(Page):
    form_model = 'player'
    form_fields = ['participation']

    def is_displayed(self):
        return self.subsession.participation_stage

    def vars_for_template(self):
        label = """
        Do you want to participate this period? (Your cost of participating is {cost}. 
        Your prediction for this round is {now_price} and next round is {price_next}).
        """.format(cost=self.player.cost, now_price=self.player.e_price_now, price_next=self.player.e_price_next)
        return {'label': label}


class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(self):
        self.group.price_temppayoff_calculate()
        if self.round_number == Constants.num_rounds:
            self.group.set_payoffs()


class Results(Page):
    pass


class FinalResults(Page):
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

    def vars_for_template(self):
        ef = self.session.config.get('simultaneous_ef_payment', Constants.simultaneous_ef_payment)
        f_payoff = self.player.in_round(self.player.paying_round_f).payoff_forecasting

        if not ef and not self.subsession.participation_stage:
            e_payoff = self.player.in_round(self.player.paying_round_e).payoff_forecasting
        else:
            e_payoff = self.player.in_round(self.player.paying_round_e).payoff_entry

        return {'ef': ef,
                'f_payoff': f_payoff,
                'e_payoff': e_payoff, }


page_sequence = [
    Introduction,
    ForecastPrice,
    Participation,
    ResultsWaitPage,
    Results,
    FinalResults
]
