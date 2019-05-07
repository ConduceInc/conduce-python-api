from __future__ import print_function
from __future__ import absolute_import
import json
from . import api


def get_access_values(permissions):
    return 'read' in permissions, 'write' in permissions, 'share' in permissions


def get_team_id(team_name, teams):
    if 'members' not in teams:
        raise RuntimeError('No teams in list')
    for team in teams['members']:
        if team['team']['name'] == team_name:
            return team['team']['id']


def get_group_id(group_name, groups):
    for group in groups['groups']:
        if group['name'] == group_name:
            return group['id']


def get_user_id(email, users):
    if 'members' not in users:
        raise RuntimeError('No users in list')
    for user in users['members']:
        if user['user']['email'].lower() == email.lower():
            return user['user']['id']


def initialize_permissions(resource_id, team_id, permissions, **kwargs):
    if resource_id is None:
        raise RuntimeError('Resource ID must be provided to set permissions')

    if team_id is None:
        print('No team specified for {}, permissions will not be updated'.format(resource_id))
        return

    api.set_owner(team_id, resource_id, **kwargs)

    if permissions is None:
        print('Using default permissions for {}'.format(resource_id))
        return

    if 'public' in permissions:
        api.set_public_permissions(resource_id, *get_access_values(permissions['public']), **kwargs)
    if 'teams' in permissions:
        for team, permissions in permissions['teams'].items():
            api.set_team_permissions(resource_id, *get_access_values(permissions), **kwargs)
    if 'groups' in permissions:
        groups = json.loads(api.list_groups(team_id, **kwargs).content)
        for group, permissions in permissions['groups'].items():
            api.set_group_permissions(get_group_id(group, groups), resource_id, *get_access_values(permissions), **kwargs)
    if 'users' in permissions:
        users = api.list_team_members(team_id, **kwargs)
        for email, permissions in permissions['users'].items():
            api.set_user_permissions(get_user_id(email, users), resource_id, *get_access_values(permissions), **kwargs)


def user_in_group(user_id, members):
    for member in members:
        if member['user']['id'] == user_id:
            return True

    return False


def build_groups(groups, team_id, **kwargs):
    team_members = json.loads(api.list_team_members(team_id, **kwargs).content)
    current_groups = json.loads(api.list_groups(team_id, **kwargs).content)
    for name, users in groups.items():
        group_id = get_group_id(name, current_groups)
        if group_id is None:
            response = api.create_group(team_id, name, **kwargs)
            # NOTE: groop is a typo
            group_id = json.loads(response.content)['groop']['id']
        group_members = json.loads(api.list_group_members(team_id, group_id, **kwargs).content)['members']
        for user in users['users']:
            if api.account_exists(user['email'], **kwargs):
                user_id = get_user_id(user['email'], team_members)
                if user_id is None:
                    print('Adding {} to team'.format(user['email']))
                    response = api.add_user_to_team(team_id, user['email'], **kwargs)
                    user_id = json.loads(response.content)['invite']['invitee']['id']
                    # Update team members list since the user was added to the team
                    team_members = json.loads(api.list_team_members(team_id, **kwargs).content)
                if user_id is not None and not user_in_group(user_id, group_members):
                    print('Adding user {} to group {}'.format(user['email'], name))
                    api.add_user_to_group(team_id, group_id, user_id, **kwargs)
            else:
                if kwargs['create_accounts']:
                    print('Creating account for {}'.format(user['email']))
                    response = api.create_account(user['name'], user['email'], **kwargs)
                    user_id = json.loads(response.content)['id']
                    api.add_user_to_team(team_id, user['email'], **kwargs)
                    # Update team members list since the user was added to the team
                    team_members = json.loads(api.list_team_members(team_id, **kwargs).content)
                    api.add_user_to_group(team_id, group_id, user_id, **kwargs)
                else:
                    print('{} cannot be added to team/group.  Account does not exist.'.format(user['email']))


def build_team(config, **kwargs):
    if 'acl' in config:
        acl = config['acl']
        if 'teams' in acl:
            teams = json.loads(api.list_teams(**kwargs).content)
            for team in acl['teams']:
                team_id = get_team_id(team['name'], teams)
                if team_id is None:
                    response = api.create_team(team['name'], **kwargs)
                    team_id = json.loads(response.content)['team']['id']
                if 'groups' in team:
                    build_groups(team['groups'], team_id, **kwargs)
                # HACK there should probably only be one team per orchestration
                # This prevents an orchestration configuration from creating multiple teams
                return team_id


def build_teams(config, **kwargs):
    if 'acl' in config:
        acl = config['acl']
        if 'teams' in acl:
            teams = json.loads(api.list_teams(**kwargs).content)
            for team in acl['teams']:
                team_id = get_team_id(team['name'], teams)
                if team_id is None:
                    response = api.create_team(team['name'], **kwargs)
                    team_id = json.loads(response.content)['team']['id']
                if 'groups' in team:
                    build_groups(team['groups'], team_id, **kwargs)
