from logging import Logger
from time import time

from datetime import datetime
from django.db.models import Count, F, Q
from django.db.models.query import QuerySet
from .models import ChessGame as Game
from .models import Report, Color, Result


class QueriesMaker:
    """
    This class is used to create queries for the report.
    It is as most generic as possible.
    To add a new query, add a method that starts with "get_" and returns the data.
    """

    def __init__(self, report: Report, logger: Logger) -> None:
        self.report = report
        self.logger = logger
        self.get_methods = [
            method
            for method in dir(self)
            if callable(getattr(self, method)) and method.startswith("get")
        ]

    def asdict(self) -> dict:
        """
        `X` - means that given field is not ment to be visualized !!!
        For each games
        This method is used to get the data from the queries.
        it will return a dict with the name of the method (- get_) as key and the data as value.
        eg.
        get_username -> username: "miskibin"
        """
        games_per_hosts: [str, QuerySet[Game]] = {
            host["host"].replace(".", "_"): Game.objects.filter(
                report=self.report, host=host["host"]
            )
            for host in Game.objects.filter(report=self.report)
            .values("host")
            .distinct()
        }
        games_per_hosts["total"] = Game.objects.filter(report=self.report)
        data = {}
        for method in self.get_methods:
            start = time()
            data[str(method.split("get_")[1])] = {
                host_name: getattr(self, method)(games)
                for host_name, games in games_per_hosts.items()
            }
            data[str(method.split("get_")[1])]["about"] = getattr(self, method).__doc__
            self.logger.debug(f"Query {method:40} {time() - start:.3f}s")

        self.logger.debug(f"{data.keys()}")

        return data

    def get_Xanalyzed_games(self, games: QuerySet[Game]) -> int:
        return games.filter(report=self.report).count()

    def get_Xprofessional(self, games: QuerySet[Game]) -> int:
        return self.report.professional

    def get_Xgames_num(self, games: QuerySet[Game]) -> int:
        return self.report.games_num

    def get_win_per_opponent_rating(self, games: QuerySet[Game]) -> dict:
        """
        Analyze your win ratio based on opponent ELO ratings.
        </br>
        <b>Insights:</b>
        <ul class="text-muted">
        <li><code>Low win ratio against lower-rated</code>: Consider refocusing and avoiding underestimation.</li>
        <li><code>Inconsistent with similarly rated</code>: Re-evaluate your strategies.</li>
        <li><code>High losses against higher-rated</code>: Study their tactics to enhance your gameplay.</li>
        </ul>
        """

        def game_results(queryset):
            win = queryset.filter(result=F("player_color")).count()
            draw = queryset.filter(result="draw").count()
            loss = queryset.count() - win - draw
            return [win, draw, loss]

        lower_games = games.filter(opponent__elo__lt=F("player__elo") - 10)
        similar_games = games.filter(
            opponent__elo__gte=F("player__elo") - 10,
            opponent__elo__lte=F("player__elo") + 10,
        )
        higher_games = games.filter(opponent__elo__gt=F("player__elo") + 10)

        return {
            "lower_ratio": game_results(lower_games),
            "similar_ratio": game_results(similar_games),
            "higher_ratio": game_results(higher_games),
        }

    def get_Xusername(self, games: QuerySet[Game]) -> str:
        if games[0].host == "lichess.org":
            return games[0].report.lichess_username
        if games[0].host == "chess.com":
            return games[0].report.chess_com_username

    def get_avg_time_per_move(self, games: QuerySet[Game]) -> list:
        """
        Your average time per move vs your opponent's average time per move.
        Statistic is calculated for each phase of the game. You can see
        when your opponent is spending more time than you and vice versa.
        </br>
        <b>
        If you see that:
        </b>
        <ul class="text-muted">
        <li>You are spending <code>more time in the opening</code> than your opponent,
        maybe you should learn more openings.</li>
        <li>You are spending <code>more time in the end game</code> than your opponent,
        maybe you should you should learn more end game theory.</li>
        <li>You are spending <code>more time in the middle game</code> than your opponent,
        maybe you should you should play more bullet games.</li>
        </ul>
        """
        avg_time = {
            "player": {"opening": 0, "middle_game": 0, "end_game": 0},
            "opponent": {"opening": 0, "middle_game": 0, "end_game": 0},
        }
        for game in games:
            for phase in ["opening", "middle_game", "end_game"]:
                try:
                    avg_time["player"][phase] += game.player.avg_move_time[phase]
                    avg_time["opponent"][phase] += game.opponent.avg_move_time[phase]
                except KeyError:
                    self.logger.error(
                        f"No {phase} in get_avg_time_per_move for game {game.id}"
                    )
                    break

        for phase in ["opening", "middle_game", "end_game"]:
            avg_time["player"][phase] /= games.count()
            avg_time["opponent"][phase] /= games.count()
        return avg_time

    def get_win_ratio_per_color(self, games: QuerySet[Game]) -> list:
        """
        Your win ratio when playing as white compared to when playing as black.
        By evaluating your performance based on your color, you can gain insights
        into potential biases or strengths in your gameplay.
        </br>
        <b>
        If you notice that:
        </b>
        <ul class="text-muted">
        <li>You have a <code>higher win ratio as white</code> than as black,
        consider studying opening strategies for black</li>
        <li>Your <code>win ratio as black exceeds that as white</code>,
        Review and expand your opening repertoire when playing as white.</li>
        <li>Your win ratios are <code>approximately equal for both colors</code>,
        it indicates a well-rounded performance</li>
        </ul>
        """
        white = self.__get_win_ratio(Color.WHITE, games)
        black = self.__get_win_ratio(Color.BLACK, games)
        data_dict = {"white": white, "black": black}
        return data_dict

    def __get_win_ratio(self, color, games: QuerySet[Game]) -> int:
        opponent_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        win = games.filter(
            report=self.report, player_color=color, result=F("player_color")
        ).count()
        lost = games.filter(
            report=self.report,
            player_color=color,
            result=opponent_color,
        ).count()
        draws = (
            games.filter(report=self.report, player_color=color).count() - win - lost
        )
        return [win, draws, lost]

    def get_win_ratio_per_opening_as_white(self, games: QuerySet[Game]) -> dict:
        """
        Some as above but for white.
        """
        return self.__get_win_ratio_per_opening_for_color(games, Color.WHITE)

    def get_win_ratio_per_opening_as_black(self, games: QuerySet[Game]) -> dict:
        """
        Your win ratio for each opening as black. <br/>
        You can see which openings are the most successful for you. <br/>
        <b>Insights:</b>
        <ul class="text-muted">
        <li><code>High score ratio only in one opening</code>: You might be playing too many games in that opening. Consider expanding your opening repertoire.
        Otherwise opponents will be able to prepare against you.</li>
        <li><code>Low ratio in some openings you like</code>: Study it harder. Play against computer or friends.</li>
        <li><code>High ratio in some openings you don't like</code>: Study how you could change your first moves to get to the opening you like.</li>
        """
        return self.__get_win_ratio_per_opening_for_color(games, Color.BLACK)

    def get_end_reasons(self, games: QuerySet[Game]) -> dict:
        """
        Reasons why the game ended. <br/>
        IMPORTANT: <b>Lichess Api does not provide this data.</b>
        </br>
        <b>
        If you notice that:
        </b>
        <ul class="text-muted">
        <li><code>You loose a lot of games on time</code>, consider playing longer time controls.</li>
        <li><code>You loose a lot of games on checkmate</code>, consider doing more tactics.</li>
        <li><code>You loose a lot of games on resignation</code>, consider playing till the end. It costs you nothing.</li>
        </ul>
        """
        # field name end_reason
        end_reasons = {}
        end_reasons["win"] = list(
            games.filter(report=self.report, result=F("player_color"))
            .exclude(end_reason="unknown")
            .values("end_reason")
            .annotate(count=Count("end_reason"))
        )
        end_reasons["loss"] = list(
            games.filter(report=self.report)
            .exclude(
                Q(result=F("player_color"))
                | Q(result=Result.DRAW)
                | Q(end_reason="unknown")
            )
            .values("end_reason")
            .annotate(count=Count("end_reason"))
        )
        return end_reasons

    def __get_win_ratio_per_opening_for_color(
        self, games: QuerySet[Game], color: int, max_oppenings=5, short=True
    ) -> tuple[dict]:
        default_field_name = "opening"
        field_name = "opening"
        if short:
            field_name = "opening_short"
        openings = (
            games.filter(player_color=color)
            .values(field_name)
            .annotate(count=Count(field_name))
        )
        openings = sorted(openings, key=lambda x: x["count"], reverse=True)
        openings = openings[:max_oppenings]

        for opening in openings:
            opening[default_field_name] = opening.pop(field_name)
        win = Color.WHITE if color == Color.WHITE else Color.BLACK
        loss = Color.BLACK if color == Color.WHITE else Color.WHITE
        for opening in openings:
            for res, result in (("win", win), ("loss", loss), ("draw", Result.DRAW)):
                opening[res] = games.filter(
                    player_color=color,
                    opening__contains=opening[default_field_name],
                    result=result,
                ).count()
        return openings

    def get_player_elo_over_time(
        self, games: QuerySet[Game]
    ) -> list:  # TODO REfactor this method it retrurns 3 times the same data !!!
        """
        You can see how your elo changed over time. <br/>
        For most active players Lichess rating is about 200 points higher than chess.com rating.
        <br/>
        <b>Note:</b> A deeper engine evaluation ensures more precise assessments.
        <br/>
        <b>Insights:</b>
        <ul class="text-muted">
        <li><code>Sharp increase in elo</code>: You are probably underrated. Keep playing and your elo will stabilize.</li>
        <li><code>Sharp decrease in elo</code>: You are probably overrated. Keep playing and your elo will stabilize.</li>
        <li><code>Stable elo</code>: You are probably rated correctly. Keep playing and your elo will stabilize.</li>

        """
        games = games.annotate(count=Count("host")).order_by("-date")
        data = []
        day = -1
        for game in games:
            if game.date.date() != day:
                day = game.date.date()
                data.append({"x": game.date, "y": game.player.elo, "host": game.host})
        return data

    def get_mistakes_per_phase(self, games: QuerySet[Game]):
        """
        Retrieve the average mistakes made during each phase of the game.
        - Categorized into: 'opening', 'middle_game', and 'end_game'.
        - The statistics are derived from engine evaluations.
        <br/>
        <b>Note:</b> A deeper engine evaluation ensures more precise assessments.
        <br/>
        <b>Insights:</b>
        <ul class="text-muted">
        <li><code>Frequent mistakes in the opening:</code> Consider revisiting and learning opening theories.</li>
        <li><code>mistakes in the middle game:</code> You might need to improve your tactical vision or positional understanding.</li>
        <li><code>Blunders in the end game:</code> Focus on endgame techniques and familiarize yourself with common endgame patterns.</li>
        </ul>
        """

        data = {}
        for phase_name in ["opening", "middle_game", "end_game"]:
            blunders, mistakes, inaccuracies = 0, 0, 0
            games_count = games.count()
            if games_count == 0:
                continue
            for game in games:
                inaccuracies += game.player.evaluation[phase_name]["inaccuracy"]
                mistakes += game.player.evaluation[phase_name]["mistake"]
                blunders += game.player.evaluation[phase_name]["blunder"]
            data[phase_name] = [
                inaccuracies / games_count,
                mistakes / games_count,
                blunders / games_count,
            ]
        return data
