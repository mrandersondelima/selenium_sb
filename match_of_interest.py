from enum import Enum

# class syntax
class HomeAway(Enum):
    Home = 1
    Away = 2    

class MatchOfInterest:

    def __init__(self, home_away, team_name, team_id, event_name, 
                 alert_sent=False, bet_made=False, bet_number=None, 
                 market_id=None, is_running=True):
        self.home_away = home_away
        self.team_id = team_id
        self.team_name = team_name
        self.event_name = event_name
        self.alert_sent = alert_sent        
        self.bet_made = bet_made
        self.bet_number = bet_number
        self.market_id = market_id
        self.is_running= is_running

    def __str__(self):
     return self.team_name