import random
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.constants import (
    CompetitionTypeConstants,
    MatchCreationConstants,
    MatchStatusConstants,
    DraftConstants,
)
from app.utils.match_day_map_keys import lea_map_days_map_key


class MatchFactory(ABC):
    def __init__(self, db: Session, divisions: list[dict], user_id: int, now: datetime):
        self._db: Session = db
        self._divisions: list[dict] = divisions
        self._mmd: list[dict] | None = None
        self._pairs: list[list[tuple[int]]] | None = None
        self._teams: list[dict] = []
        self._user_id: int = user_id
        self._now = now

    def build(self) -> bool:
        return (
            self._valid_state()
            and self._load_teams()
            and self._load_mmd()
            and self._create_pairs()
            and self._create_matches()
            and self._save()
        )

    @property
    def divisions(self) -> list[dict]:
        return self._divisions

    @property
    @abstractmethod
    def competition_type(self) -> int: ...

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def now(self) -> datetime:
        return self._now

    @property
    def leagueID(self) -> int:
        return self._divisions[0]["leagueID"]

    @property
    def divisionID(self) -> int | None:
        return self._divisions[0]["divisionID"]

    @property
    def season(self) -> int:
        return self._divisions[0]["season"]

    @property
    def season_num(self) -> int:
        return self._divisions[0]["seasonNum"]

    @property
    def base_real_competition_id(self) -> int:
        return self._divisions[0]["baseRealCompetitionID"]

    @property
    def first_real_competition_match_day(self) -> int:
        return self._divisions[0]["firstRealCompetitionMatchDay"]

    @property
    def num_teams(self) -> int:
        return len(self._teams)

    @property
    def rounds(self) -> int | None:
        if self._mmd is not None and len(self._mmd) > 0:
            return self._mmd[0]["rounds"]
        return None

    def _load_mmd(self) -> bool:
        stmt = text("""
            SELECT `totalMatchDays`,
                   `rounds`,
                   `firstRealCompetitionMatchDaySort`,
                   `matchDay`,
                   `realCompetitionID`,
                   `realCompetitionMatchDay`,
                   `realCompetitionMatchDaySort`
              FROM `MatchDaysMap`
             WHERE `baseRealCompetitionID` = :baseRealCompetitionID
               AND `competitionType` = :competitionType
               AND `firstRealCompetitionMatchDay` = :firstRealCompetitionMatchDay
               AND `minNumTeams` <= :numTeams
               AND `maxNumTeams` >= :numTeams
        """)
        rows = (
            self._db.execute(
                stmt,
                {
                    "baseRealCompetitionID": self.base_real_competition_id,
                    "competitionType": self.competition_type,
                    "firstRealCompetitionMatchDay": self.first_real_competition_match_day,
                    "numTeams": self.num_teams,
                },
            )
            .mappings()
            .all()
        )
        if rows:
            self._mmd = [dict(row) for row in rows]
            return True
        self._mmd = None
        return False

    @abstractmethod
    def _create_pairs(self) -> bool: ...

    def _add_rounds(self, pairs: list[list[tuple[int]]]) -> list[list[tuple[int]]]:
        swap = False
        new_pairs = []
        for r in range(self.rounds):
            for i in range(len(pairs)):
                matches = []
                for match in pairs[i]:
                    if swap:
                        matches.append((match[1], match[0], match[2], match[3], r + 1))
                    else:
                        matches.append((match[0], match[1], match[2], match[3], r + 1))
                new_pairs.append(matches)
            swap = not swap
        return new_pairs

    @abstractmethod
    def _valid_state(self) -> bool: ...

    def _load_teams(self) -> bool:
        is_league = self.competition_type == CompetitionTypeConstants.LEAGUE_KNOCK_OUT
        id_val = self.leagueID if is_league else self.divisionID
        rows = (
            self._db.execute(
                text(self._sql_teams()),
                {"competitionType": self.competition_type, "id": id_val},
            )
            .mappings()
            .all()
        )
        self._teams = [dict(row) for row in rows]
        num_teams = 0
        for division in self._divisions:
            num_teams += division["numTeams"]
        return len(self._teams) == num_teams

    @abstractmethod
    def _save(self) -> bool: ...

    def _create_matches(self) -> bool:
        match_num = 0
        for i in range(len(self._pairs)):
            for j in range(len(self._pairs[i])):
                match_num += 1
                team_num_1, team_num_2, group, next_group, round = self._pairs[i][j]
                team_1 = {} if team_num_1 is None else self._teams[team_num_1]
                team_2 = {} if team_num_2 is None else self._teams[team_num_2]
                m_values = self._match_values(
                    i + 1, match_num, group, next_group, round
                )
                match_id = self._insert_match(m_values)
                mt1_values = self._match_team_values(match_id, team_1, 1)
                mt2_values = self._match_team_values(match_id, team_2, 2)
                self._insert_match_team(mt1_values)
                self._insert_match_team(mt2_values)
        return True

    def _match_values(
        self, mDay: int, mNum: int, group: int, next_group: int | None, round
    ) -> dict[str, Any]:
        mmd = self._mmd[mDay - 1]
        return {
            "matchStatus": MatchStatusConstants.NOT_STARTED,
            "leagueID": self.leagueID,
            "divisionID": self.divisionID,
            "season": self.season,
            "seasonNum": self.season_num,
            "realCompetitionID": mmd["realCompetitionID"],
            "realCompetitionMatchDay": mmd["realCompetitionMatchDay"],
            "realCompetitionMatchDaySort": mmd["realCompetitionMatchDaySort"],
            "competitionType": self.competition_type,
            "competitionMatchDay": mDay,
            "competitionLastMatchDay": len(self._pairs),
            "competitionMatchNumber": mNum,
            "competitionMatchGroup": group,
            "competitionMatchNextGroup": next_group,
            "competitionMatchRound": round,
            "competitionMatchLastRound": self.rounds,
            "matchGroupWinnerTeamID": None,
            "lastCompetitionMatchDay": len(self._pairs),
            "createdBy": self.user_id,
            "createdIn": self.now,
            "updatedBy": None,
            "updatedIn": None,
        }

    def _match_team_values(
        self, match_id: int, team_1: dict, mtNum: int
    ) -> dict[str, Any]:
        return {
            "matchID": match_id,
            "matchTeamNum": mtNum,
            "userID": team_1.get("userID"),
            "teamID": team_1.get("teamID", None),
            "teamName": team_1.get("teamName", None),
            "teamScore": None,
            "teamPoints": None,
            "teamSeeding": team_1.get("seeding", None),
            "matchDayMapKey": team_1.get("matchDayMapKey", None),
            "lineup": None,
            "cntEPLTeam": None,
            "cntGoalkeeper": None,
            "cntDefender": None,
            "cntMidfielder": None,
            "cntStriker": None,
            "cntSubstitute": None,
            "cntInactive": None,
            "place": None,
            "won": None,
            "draw": None,
            "lost": None,
            "scoreFor": None,
            "scoreAgainst": None,
            "points": None,
            "wonHome": None,
            "drawHome": None,
            "lostHome": None,
            "scoreForHome": None,
            "scoreAgainstHome": None,
            "pointsHome": None,
            "wonAway": None,
            "drawAway": None,
            "lostAway": None,
            "scoreForAway": None,
            "scoreAgainstAway": None,
            "pointsAway": None,
            "createdBy": self.user_id,
            "createdIn": self.now,
            "updatedBy": None,
            "updatedIn": None,
        }

    def _insert_match(self, values: dict) -> int | None:
        stmt = text("""
            INSERT INTO `Matches` (
                `matchStatus`, `leagueID`, `divisionID`, `season`, `seasonNum`,
                `realCompetitionID`, `realCompetitionMatchDay`, `realCompetitionMatchDaySort`,
                `competitionType`, `competitionMatchDay`, `competitionLastMatchDay`,
                `competitionMatchNumber`, `competitionMatchGroup`, `competitionMatchNextGroup`,
                `competitionMatchRound`, `competitionMatchLastRound`,
                `matchGroupWinnerTeamID`, `lastCompetitionMatchDay`,
                `createdBy`, `createdIn`, `updatedBy`, `updatedIn`
            ) VALUES (
                :matchStatus, :leagueID, :divisionID, :season, :seasonNum,
                :realCompetitionID, :realCompetitionMatchDay, :realCompetitionMatchDaySort,
                :competitionType, :competitionMatchDay, :competitionLastMatchDay,
                :competitionMatchNumber, :competitionMatchGroup, :competitionMatchNextGroup,
                :competitionMatchRound, :competitionMatchLastRound,
                :matchGroupWinnerTeamID, :lastCompetitionMatchDay,
                :createdBy, :createdIn, :updatedBy, :updatedIn
            )
        """)
        result = self._db.execute(stmt, values)
        return result.lastrowid

    def _insert_match_team(self, values: dict) -> None:
        stmt = text("""
            INSERT INTO `MatchTeams` (
                `matchID`, `matchTeamNum`, `userID`, `teamID`, `teamName`,
                `teamScore`, `teamPoints`, `teamSeeding`, `matchDayMapKey`,
                `lineup`, `cntEPLTeam`, `cntGoalkeeper`, `cntDefender`,
                `cntMidfielder`, `cntStriker`, `cntSubstitute`, `cntInactive`,
                `place`, `won`, `draw`, `lost`, `scoreFor`, `scoreAgainst`, `points`,
                `wonHome`, `drawHome`, `lostHome`, `scoreForHome`, `scoreAgainstHome`, `pointsHome`,
                `wonAway`, `drawAway`, `lostAway`, `scoreForAway`, `scoreAgainstAway`, `pointsAway`,
                `createdBy`, `createdIn`, `updatedBy`, `updatedIn`
            ) VALUES (
                :matchID, :matchTeamNum, :userID, :teamID, :teamName,
                :teamScore, :teamPoints, :teamSeeding, :matchDayMapKey,
                :lineup, :cntEPLTeam, :cntGoalkeeper, :cntDefender,
                :cntMidfielder, :cntStriker, :cntSubstitute, :cntInactive,
                :place, :won, :draw, :lost, :scoreFor, :scoreAgainst, :points,
                :wonHome, :drawHome, :lostHome, :scoreForHome, :scoreAgainstHome, :pointsHome,
                :wonAway, :drawAway, :lostAway, :scoreForAway, :scoreAgainstAway, :pointsAway,
                :createdBy, :createdIn, :updatedBy, :updatedIn
            )
        """)
        self._db.execute(stmt, values)

    def _sql_teams(self) -> str:
        if self.competition_type != CompetitionTypeConstants.LEAGUE_KNOCK_OUT:
            id_name = "divisionID"
        else:
            id_name = "leagueID"
        return f"""
SELECT `teamID`,
       `divisionID`,
       `userID`,
       `teamName`,
       CASE :competitionType
          WHEN 1 THEN `seedingC1`
          WHEN 2 THEN `seedingC2`
          WHEN 3 THEN `seedingC3`
          ELSE NULL
       END AS `seeding`
   FROM `Teams`
   WHERE `{id_name}` = :id
   ORDER BY `seeding`
         """


class DivisionRRFactory(MatchFactory):
    def __init__(self, db: Session, division: dict, user_id: int, now: datetime):
        super().__init__(db, [division], user_id, now)

    @property
    def competition_type(self) -> int:
        return CompetitionTypeConstants.DIVISION_ROUND_ROBIN

    def _valid_state(self) -> bool:
        return (
            self._divisions[0]["draftStatus"] == DraftConstants.DRAFT_STATUS_DRAFTED
            and self._divisions[0]["divisionMatches"] == MatchCreationConstants.READY
        )

    def _save(self) -> bool:
        self._db.execute(
            text("""
                UPDATE `Divisions`
                   SET `divisionMatches` = :divisionMatches,
                       `updatedBy` = :updatedBy,
                       `updatedIn` = :updatedIn
                 WHERE `divisionID` = :divisionID
            """),
            {
                "divisionMatches": MatchCreationConstants.CREATING,
                "updatedBy": self._user_id,
                "updatedIn": self._now,
                "divisionID": self.divisionID,
            },
        )
        self._db.commit()
        return True

    def _create_pairs(self) -> bool:
        """
        Generate a complete round-robin schedule for n teams (0 to n-1).
        Each team plays every other team exactly once.

        Args:
            n: Number of teams (must be even)

        Returns:
            List of match days, where each match day is a list of (team1, team2) tuples
            Total rounds: n-1
            Matches per round: n/2
        """

        # Initialize teams list
        teams = list(range(self.num_teams))

        # Fix one team (let's fix team 0) and rotate the rest
        pairs = []

        group = 0
        for _ in range(self.num_teams - 1):
            matches = []

            # Pair first half with second half
            for i in range(self.num_teams // 2):
                team1 = teams[i]
                team2 = teams[self.num_teams - 1 - i]
                matches.append((team1, team2))

            random.shuffle(matches)
            for idx, match in enumerate(matches):
                group += 1
                matches[idx] = (match[0], match[1], group, None, 1)
            pairs.append(matches)

            # Rotate teams for next round (keep team 0 fixed)
            # Move last element to position 1, shift everything else right
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        self._pairs = self._add_rounds(pairs)
        return isinstance(self._pairs, list) and len(self._pairs) == len(self._mmd)


class DivisionKOFactory(MatchFactory):
    def __init__(self, db: Session, division: dict, user_id: int, now: datetime):
        super().__init__(db, [division], user_id, now)

    @property
    def competition_type(self) -> int:
        return CompetitionTypeConstants.DIVISION_KNOCK_OUT

    def _valid_state(self) -> bool:
        return (
            self._divisions[0]["draftStatus"] == DraftConstants.DRAFT_STATUS_DRAFTED
            and self._divisions[0]["divisionMatches"] == MatchCreationConstants.CREATING
        )

    def _create_pairs(self) -> bool:
        def get_base() -> list[tuple[int]]:
            """Gets the base matches that can contain self.num_teams

            Returns:
                list[tuple[int]]: the list of matches
            """
            # build an initial balanced list of teams
            base: list[int] = [1]
            while self.num_teams > len(base):
                base = base + [0] * len(base)  # array_pad equivalent
                for j in range(len(base) // 2 - 1, -1, -1):
                    base[2 * j] = base[j]
                    base[(2 * j) + 1] = 1 + len(base) - base[j]
            # build the matches
            new_base = []
            for i in range(0, len(base), 2):
                # eliminate the teams that are > num_teams
                t_0 = base[i] - 1 if base[i] <= self.num_teams else None
                t_1 = base[i + 1] - 1 if base[i + 1] <= self.num_teams else None
                new_base.append((t_0, t_1))
            return new_base

        def init_template() -> list[list[int]]:
            """_summary_

            Returns:
                _type_: _description_
            """
            base = get_base()
            template: list[list[int]] = []
            group = 1
            while len(base) > 1:
                new_base = []
                t = len(template)
                template.append([])
                for i in range(0, len(base), 2):
                    # process 2 matches to generate the next match
                    m = []
                    for j in range(i, i + 2):
                        t_0 = base[j][0]
                        t_1 = base[j][1]
                        if t_0 is not None or t_1 is not None:
                            if t_0 is None:
                                m.append(t_1)
                            elif t_1 is None:
                                m.append(t_0)
                            else:
                                # use the min to keep track of what's going on
                                m.append(min(t_0, t_1))
                                template[t].append([t_0, t_1, group, None])
                                group += 1
                    new_base.append(m)
                base = new_base
            # add the last match
            template.append([[base[0][0], base[0][1], group, None]])
            return template

        def add_next_groups(template: list[list[int]]) -> list[list[int]]:
            """_summary_

            Args:
                template (list[list[int]]): _description_

            Returns:
                list[list[int]]: _description_
            """
            for i in range(len(template) - 1):
                for j in range(len(template[i])):
                    t = min(template[i][j][0], template[i][j][1])
                    for k in range(len(template[i + 1])):
                        if t == template[i + 1][k][0] or t == template[i + 1][k][1]:
                            template[i][j][3] = template[i + 1][k][2]
                            break
            return template

        template = add_next_groups(init_template())
        # We only keep the first mention of each team
        teams = set()
        self._pairs = []
        for i, t in enumerate(template):
            matches = []
            for m in t:
                # get the team numbers or none if the teams had already been used
                t_0 = m[0] if m[0] not in teams else None
                t_1 = m[1] if m[1] not in teams else None
                # add the match tuple
                matches.append((t_0, t_1, m[2], m[3], 1))
                # save the teams
                if t_0 is not None:
                    teams.add(t_0)
                if t_1 is not None:
                    teams.add(t_1)
            if i == len(template) - 1:
                # only one round for the final game
                self._pairs.append(matches)
            else:
                # add the rounds
                for mm in self._add_rounds([matches]):
                    self._pairs.append(mm)
        return isinstance(self._pairs, list) and len(self._pairs) == len(self._mmd)

    def _save(self) -> bool:
        self._db.execute(
            text("""
                UPDATE `Divisions`
                   SET `divisionMatches` = :divisionMatches,
                       `updatedBy` = :updatedBy,
                       `updatedIn` = :updatedIn
                 WHERE `divisionID` = :divisionID
            """),
            {
                "divisionMatches": MatchCreationConstants.CREATED,
                "updatedBy": self._user_id,
                "updatedIn": self._now,
                "divisionID": self.divisionID,
            },
        )
        self._db.commit()
        return True


class LeagueKOFactory(DivisionKOFactory):
    def __init__(self, db: Session, divisions: list[dict], user_id: int, now: datetime):
        MatchFactory.__init__(self, db, divisions, user_id, now)
        self._season: int | None = None
        self._season_num: int | None = None

    @property
    def competition_type(self) -> int:
        return CompetitionTypeConstants.LEAGUE_KNOCK_OUT

    def _valid_state(self) -> bool:
        for i, division in enumerate(self._divisions):
            if division["draftStatus"] != DraftConstants.DRAFT_STATUS_DRAFTED:
                return False
            if division["divisionMatches"] != MatchCreationConstants.CREATED:
                return False
            if division["leagueMatches"] != MatchCreationConstants.READY:
                return False
            matchDayMapKey = lea_map_days_map_key(
                self._db,
                leaCnt=sum(d["numTeams"] for d in self._divisions),
                key=division["matchDayMapKey"],
                dt=self._now,
            )
            if matchDayMapKey is None:
                return False
            self._divisions[i]["matchDayMapKey"] = matchDayMapKey
        return True

    def _load_teams(self) -> bool:
        if super()._load_teams():
            if sum(d["numTeams"] for d in self._divisions) != self.num_teams:
                return False
            keys = {d["divisionID"]: d["matchDayMapKey"] for d in self._divisions}
            for i, team in enumerate(self._teams):
                if team["divisionID"] not in keys:
                    return False
                self._teams[i]["matchDayMapKey"] = keys[team["divisionID"]]
            return True
        return False

    @property
    def divisionID(self) -> int | None:
        return None

    @property
    def season(self) -> int:
        if self._season is None:
            self._season = max(d["season"] for d in self._divisions)
        return self._season

    @property
    def season_num(self) -> int:
        if self._season_num is None:
            self._season_num = max(d["seasonNum"] for d in self._divisions)
        return self._season_num

    def _save(self) -> bool:
        for division in self._divisions:
            self._save_division(division)
        self._save_teams()
        self._save_match_teams()
        self._db.commit()
        return self._save_remaining()

    def _save_division(self, division: dict) -> None:
        self._db.execute(
            text("""
                UPDATE `Divisions`
                SET `leagueMatches` = :leagueMatches,
                    `matchDayMapKey` = :matchDayMapKey,
                    `updatedBy` = :updatedBy,
                    `updatedIn` = :updatedIn
                WHERE `divisionID` = :divisionID
            """),
            {
                "leagueMatches": MatchCreationConstants.CREATED,
                "matchDayMapKey": division["matchDayMapKey"],
                "updatedBy": self._user_id,
                "updatedIn": self._now,
                "divisionID": division["divisionID"],
            },
        )

    def _save_teams(self) -> None:
        self._db.execute(
            text("""
                UPDATE `Teams` `t`
                LEFT OUTER JOIN `Divisions` `d` ON `d`.`divisionID` = `t`.`divisionID`
                SET `t`.`matchDayMapKey` = `d`.`matchDayMapKey`,
                    `t`.`updatedBy` = :updatedBy,
                    `t`.`updatedIn` = :updatedIn
                WHERE `t`.`leagueID` = :leagueID
            """),
            {
                "updatedBy": self._user_id,
                "updatedIn": self._now,
                "leagueID": self.leagueID,
            },
        )

    def _save_match_teams(self) -> None:
        self._db.execute(
            text("""
                UPDATE `MatchTeams` `mt`
                INNER JOIN `Teams` `t` ON `t`.`teamID` = `mt`.`teamID`
                SET `mt`.`matchDayMapKey` = `t`.`matchDayMapKey`,
                    `mt`.`updatedBy` = :updatedBy,
                    `mt`.`updatedIn` = :updatedIn
                WHERE `t`.`leagueID` = :leagueID
            """),
            {
                "updatedBy": self._user_id,
                "updatedIn": self._now,
                "leagueID": self.leagueID,
            },
        )
