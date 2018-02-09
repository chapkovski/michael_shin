from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random, json
from otree.models import Participant
from django.db.models.signals import post_save
from django.dispatch import receiver

author = 'Mike Shin, Philipp Chapkovski'

doc = """
Learning-to-forecast Sample
"""

import collections

PRec = collections.namedtuple('PRec', 'round_number expected_price participation_rate ego_participation payoff price')


class Constants(BaseConstants):
    name_in_url = 'ltf_sample'
    players_per_group = 2
    num_rounds = 2

    R = 1.05  # Interest Rate
    mu = 3  # Dividends
    A = 4  # Supply
    d = 0  # the entry payoff for non particpants
    c = 1  # constant c for calculating payoff for a forecast
    max_price = 200  # max value for expected price
    paying_round = 1
    max_rounds_in_table = 5
    instructions_template = 'michael_shin/Instructions.html'
    # if no info in session config about different payment rounds for forecastig and entry, then we take the info
    # from the follwoing constant:
    simultaneous_ef_payment = True
    ub = 3  # upper bound for costs in group
    cost_step = ub / (players_per_group - 1 or 1)


class Subsession(BaseSubsession):
    def creating_session(self):
        k = Constants.cost_step
        for g in self.get_groups():
            for i, p in enumerate(g.get_players()):
                p.cost = i * k


class Group(BaseGroup):
    average_expectations = models.FloatField()
    price = models.FloatField()
    total_participation = models.FloatField()

    def price_temppayoff_calculate(self):
        mu = Constants.mu
        r = Constants.R
        a = Constants.A
        players = self.get_players()
        self.average_expectations = sum([p.e_price_now for p in players]) / Constants.players_per_group
        self.total_participation = sum([p.participation for p in players]) / Constants.players_per_group
        adjustment_term = a * (1 / self.total_participation - 1) if self.total_participation > 0 else 0
        self.price = round((1 / r) * (self.average_expectations + mu - adjustment_term), 2)
        for p in players:
            p.set_forecasting_payoff()
            p.set_entry_payoff()

    def set_payoffs(self):
        # the following condition is  a bit overcontrolling but just in case we call them before the final round:
        if self.round_number == Constants.num_rounds:
            for p in self.get_players():
                p.set_payoff()


class Player(BasePlayer):
    cost = models.FloatField(doc='personal cost for entry')
    participant_vars_dump = models.StringField(doc='to store participant vars')
    payoff_forecasting = models.CurrencyField(initial=0, doc='payoff for forecasting')
    payoff_entry = models.CurrencyField(initial=0, doc='payoff for entry in the previous round')
    paying_round_f = models.IntegerField(doc='round to pay for forecasting')
    paying_round_e = models.IntegerField(doc='round to pay for entry')
    temp_payoff = models.CurrencyField(initial=0, doc='temporary payoff in round')
    e_price_next = models.PositiveIntegerField(max=Constants.max_price,
                                               doc='expected price for next round',
                                               verbose_name='Predict the price in the next round')
    e_price_now = models.PositiveIntegerField(max=Constants.max_price,
                                              doc='expected price for current round',
                                              verbose_name='Predict the price in this round')
    participation = models.BooleanField(choices=[(False, 'No'), (True, 'Yes')], widget=widgets.RadioSelect)

    def previous_expected(self):
        if self.round_number == 1:
            expected_price = self.e_price_now
        else:
            expected_price = self.in_round(self.round_number - 1).e_price_next
        return expected_price

    def get_prec(self):
        if self.group.total_participation is not None:
            participation_rate = "{0:.0f}%".format(self.group.total_participation * 100)
        else:
            participation_rate = None
        record = PRec(round_number=self.round_number,
                      expected_price=self.previous_expected(),
                      price=self.group.price,
                      participation_rate=participation_rate,
                      ego_participation=self.participation,
                      payoff=self.temp_payoff,
                      )
        return record

    def set_entry_payoff(self):
        if self.round_number == 1:
            return
        p = self.in_round(self.round_number - 1)
        price_t_2 = self.group.price
        price_t = p.group.price
        r = Constants.R
        mu = Constants.mu
        e = p.participation
        d = Constants.d
        k = self.cost
        if e:
            ep = e * (price_t_2 + mu - r * price_t + d - k)
        else:
            ep = d
        self.payoff_entry = ep

    def set_forecasting_payoff(self):
        if self.round_number == 1:
            return
        p = self.in_round(self.round_number - 1)
        e_pt1 = p.e_price_next
        e_pt2 = self.e_price_now
        p_t = self.group.price
        c = Constants.c
        fp = c / (1 + abs(p_t - e_pt1) + abs(p_t - e_pt2))
        self.payoff_forecasting = fp

    def set_payoff(self):
        # we set final payoff only in the last round!
        if self.round_number == Constants.num_rounds:
            same_ef_round = self.session.config.get('simultaneous_ef_payment', Constants.simultaneous_ef_payment)
            self.paying_round_f = random.randint(1, Constants.num_rounds)
            if same_ef_round:
                self.paying_round_e = self.paying_round_f
            else:
                self.paying_round_e = random.randint(1, Constants.num_rounds)
            self.payoff = self.in_round(self.paying_round_f).payoff_forecasting + self.in_round(
                self.paying_round_e).payoff_entry
        else:
            self.payoff = 0
