# -*- coding: utf-8 -*-
import os
import json

from .managers import SharedManager, DedicatedManager

plans = [
    {'name': 'shared', 'description': 'It\'s a shared instance of PostgreSQL'},
    {'name': 'dedicated', 'description': 'Your own PostgreSQL instance'}
]

class PlanDoNotExists(Exception):
    def __init__(self, name):
        self.args = ["Plan %s does not exist." % name]

def list_active():
    plans_environ = os.environ.get("POSTGRES_API_PLANS", "[]")
    active_plans_name = json.loads(plans_environ)
    active_plans = []

    for plan in plans:
        if plan["name"] in active_plans_name:
            active_plans.append(plan)

    return active_plans

def get_manager_by_plan(plan):
    """Get the manager for the given plan

    This helps us to provide multiple ways to handle different plans.

    """
    if plan == 'shared':
        return SharedManager()
    elif plan == 'dedicated':
        return DedicatedManager()
    else:
        raise PlanDoNotExists(name=plan)


def get_manager_by_instance(instance):
    return get_manager_by_plan(instance.plan)
