from typing import List, Dict, Any
from functools import cmp_to_key

# Assuming these are your database and exception classes
# from eff.eff_lib.base import DB, EffException
# from eff.eff_lib.tools import Map, Scalars
# from eff.eff_lib.sql import SqlUpdate


class DraftResult:
    """
    Base class for draft actions
    """
    
   
    def execute(self, division_id: int) -> List[Dict[str, Any]]:
        """
        Execute the draft result generation
        
        Returns:
            List of member dictionaries
        """
        
        # Execute query and fetch all rows into a list
        query = DB.db().query(self.select_teams_sql(), {'divisionID': division_id})
        team_rows = []
        while (row := DB.db().fetch(query)) is not False:
            team_rows.append(row)
        
        # Process all team rows
        members = self._add_team_members(team_rows)
        
        # Sort members using compare_members as key function
        members.sort(key=cmp_to_key(self._compare_members))
        return members
    
    def _add_team_members(self, teams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add team members to the members list
        
        Args:
            teams: List of team dictionaries
        """
        members: List[Dict[str, Any]] = []
        num_teams = len(teams)
        
        for team in teams:
            # Parse team members keys
            team_members_str = team.get('teamMembers', '')
            keys = team_members_str[:-1].split('.') if team_members_str else []
            
            # Remove unnecessary keys
            team.pop('teamMembers', None)
            team.pop('draftMembers', None)
            
            # Query for team members
            if len(keys) > 0:
                query = DB.db().query(self._select_team_members_sql(keys))
                
                while (row := DB.db().fetch(query)) is not False:
                    for i, key in enumerate(keys):
                        if key == row['realTeamMemberKey']:
                            member = {**team, **row}
                            member['draftingRound'] = i + 1
                            
                            if i % 2 == 0:
                                member['draftingMemberOrder'] = (i * num_teams) + member['draftOrder']
                            else:
                                member['draftingMemberOrder'] = ((i + 1) * num_teams) - member['draftOrder'] + 1
                            
                            members.append(member)
                            break
        return members
    
    @staticmethod
    def _compare_members(a: Dict[str, Any], b: Dict[str, Any]) -> int:
        """
        Compare two members by their drafting order
        
        Args:
            a: First member
            b: Second member
            
        Returns:
            Comparison result (-1, 0, 1)
        """
        return (a['draftingMemberOrder'] > b['draftingMemberOrder']) - (a['draftingMemberOrder'] < b['draftingMemberOrder'])
    
    def select_teams_sql(self) -> str:
        """
        Generate SQL for selecting teams
        
        Returns:
            SQL string
        """
        return """
SELECT `teamID`,
       `baseRealCompetitionID`,
       `leagueID`,
       `divisionID`,
       `commissionerID`,
       `userID`,
       `seasonNum`,
       `draftOrder`,
       `randomOrder`,
       `teamName`,
       `isCommissioner`,
       `cntEPLTeam`,
       `cntPlayer`,
       `cntGoalkeeper`,
       `cntDefender`,
       `cntMidfielder`,
       `cntStriker`,
       `teamMembers`,
       `draftMembers`
    FROM `Teams`
    WHERE `divisionID` = :divisionID
    ORDER BY `draftOrder` ASC
"""
    
    def _select_team_members_sql(self, keys: List[str]) -> str:
        """
        Generate SQL for selecting team members
        
        Args:
            keys: List of member keys
            
        Returns:
            SQL string
        """
        quoted_keys = "','".join(keys)
        condition = f"`realTeamMemberKey` IN ('{quoted_keys}')"
        
        return f"""
SELECT `realTeamMemberKey`,
       `realTeamID`,
       `realTeamUID`,
       `realTeamName`,
       `realTeamShortName`,
       `realPlayerID`,
       `realPlayerUID`,
       `firstName`,
       `lastName`,
       `knownName`,
       `name`,
       `draftPosition`,
       `draftPositionOrder`
   FROM `RealTeamMembers`
   WHERE {condition}
"""