from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)

author = 'Mike Shin'

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
    max_price = 200  # max value for expected price
    paying_round = 1
    max_rounds_in_table = 5
    instructions_template = 'michael_shin/Instructions.html'


class Subsession(BaseSubsession):
    def creating_session(self):
        for p in self.get_players():
            p.paying_round = self.session.config.get('paying_round', Constants.paying_round)


class Group(BaseGroup):
    average_expectations = models.FloatField()
    price = models.FloatField()
    total_participation = models.FloatField()

    def get_old_prices(self):
        ...

    def price_calculate(self):
        players = self.get_players()
        self.average_expectations = sum([p.previous_expected() for p in players]) / Constants.players_per_group
        self.total_participation = sum([p.participation for p in players]) / Constants.players_per_group
        adjustment_term = Constants.A * (1 / self.total_participation - 1) if self.total_participation > 0 else 0
        self.price = round((1 / Constants.R) * (self.average_expectations + Constants.mu - adjustment_term), 2)
        for p in players:
            p.temp_payoff = max(self.price - p.previous_expected(), 0)


class Player(BasePlayer):
    temp_payoff = models.CurrencyField(
        doc='field for storing temporary payoff; a final one defned by paying round field')
    paying_round = models.IntegerField(doc='round to pay')
    expected_price = models.PositiveIntegerField(max=Constants.max_price,
                                                 verbose_name='Predict the price in the next round')
    expected_price1 = models.PositiveIntegerField(max=Constants.max_price,
                                                  doc='expected price for round 1',
                                                  verbose_name='Predict the price in this round')
    participation = models.BooleanField(choices=[(False, 'No'), (True, 'Yes')], widget=widgets.RadioSelect)

    def get_old_predictions(self):
        ...

    def previous_expected(self):
        if self.round_number == 1:
            expected_price = self.expected_price1
        else:
            expected_price = self.in_round(self.round_number - 1).expected_price
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

    def set_payoff(self):
        self.payoff = self.in_round(self.paying_round).temp_payoff
