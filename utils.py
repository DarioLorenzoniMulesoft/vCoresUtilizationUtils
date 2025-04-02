import requests
import json
from rich.console import Console
from rich.table import Table
import inquirer
import getpass
from alive_progress import alive_bar

US_BASE_URL = "https://anypoint.mulesoft.com"
EU_BASE_URL = "https://eu1.anypoint.mulesoft.com"

def get_bearer_token(base_url, client_id, client_secret):
  url = f"{base_url}/accounts/api/v2/oauth2/token"
  payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret
  }
  headers = {
    "Content-Type": "application/json"
  }
  response = requests.post(url, json=payload, headers=headers)
  response.raise_for_status()
  return response.json()["access_token"]

def get_organization_id(base_url, access_token):
  url = f"{base_url}/accounts/api/me"
  headers = {
  "Authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  return response.json()["user"]["organization"]["id"]

def get_sub_organizations(base_url, access_token, org_id):
  url = f"{base_url}/accounts/api/organizations/{org_id}/hierarchy"
  headers = {
  "Authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  return {response.json()["name"] : response.json()["id"]} | {(so["name"]): so["id"] for so in response.json()["subOrganizations"]}

def get_environments(base_url, access_token, org_id):
  url = f"{base_url}/accounts/api/organizations/{org_id}/environments"
  headers = {
  "Authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  return {(env["name"]): env["id"] for env in response.json()["data"]}

def get_deployments(base_url, access_token, org_id, env_id):
  url = f"{base_url}/amc/application-manager/api/v2/organizations/{org_id}/environments/{env_id}/deployments/"
  headers = {
  "Authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  return response.json()

def get_resource_allocation(base_url, access_token, org_id, env_id, deployment_id):
  url = f"{base_url}/amc/application-manager/api/v2/organizations/{org_id}/environments/{env_id}/deployments/{deployment_id}"
  headers = {
  "Authorization": f"Bearer {access_token}"
  }
  response = requests.get(url, headers=headers)
  response.raise_for_status()
  with open('data.json', 'w') as f:
    json.dump(response.json(), f)
  return response.json()

def calculate_vcore_usage(base_url, access_token, org_id, env_id):
  deployments = get_deployments(base_url, access_token, org_id, env_id)
  filtered_deployments = [item for item in deployments['items'] if item['application']['status'] == 'RUNNING']
  d = []
  total_vcore_usage = 0
  with alive_bar(len(filtered_deployments), title='Calculating vCore Usage') as bar:
    for deployment in filtered_deployments:
      deployment_id = deployment['id']
      resource_allocation = get_resource_allocation(base_url, access_token, org_id, env_id, deployment_id)
      vcore = resource_allocation['application']['vCores']
      replicas = resource_allocation['target']['replicas']
      d += [{'application': deployment['name'], 'replicas': resource_allocation['target']['replicas'], 'vcore': resource_allocation['application']['vCores']}]
      total_vcore_usage += vcore * replicas
      bar()
  return round(total_vcore_usage, 2), d

questions = [
  inquirer.List('cp_location',
    message="Which is the target control plane?",
    choices=['EU', 'US'],
    ),
  ]
answers = inquirer.prompt(questions)

if answers.get('cp_location', 'EU') == 'EU':
  base_url = EU_BASE_URL
else:
  base_url = US_BASE_URL
  
client_id = getpass.getpass('Client Id:')
client_secret = getpass.getpass('Client Secret:')

access_token = get_bearer_token(base_url, client_id, client_secret)
organization_id = get_organization_id(base_url, access_token)
sub_organizations = get_sub_organizations(base_url, access_token, organization_id)

questions = [
  inquirer.List('selected_org',
    message="Which is the target org/sub-org?",
    choices=sub_organizations.keys(),
    ),
  ]
answers = inquirer.prompt(questions)
selected_org = sub_organizations.get(answers.get('selected_org'))

environments = get_environments(base_url, access_token, selected_org)

questions = [
  inquirer.Checkbox('selected_envs',
                    message="Which are the traget environments?",
                    choices=environments.keys(),
                    ),
]
answers = inquirer.prompt(questions)
selected_envs = answers.get('selected_envs', [])

questions = [
  inquirer.List('detailed_view',
                    message="Would you like to have a detailed view of the data?",
                    choices=[True, False],
                    ),
]
answers = inquirer.prompt(questions)
detailed_view = answers.get('detailed_view')

console = Console()
table = Table(show_header=True, header_style="bold magenta")

if detailed_view:
  table.add_column("Environment Name")
  table.add_column("Application Name")
  table.add_column("Replicas")
  table.add_column("vCore per Replica")
else:
  table.add_column("Environment Name", justify="right")
  table.add_column("vCore Usage", justify="right")
  
total_vcore_usage = 0
for e in selected_envs:
  env_id = environments.get(e)
  total_vcore_usage_per_env, deployments = calculate_vcore_usage(base_url, access_token, selected_org, env_id)
  total_vcore_usage += total_vcore_usage_per_env
  if detailed_view:
    for d in deployments:
      table.add_row(f"{e}", f"{d.get('application')}", f"{d.get('replicas')}", f"{d.get('vcore')}")
    table.add_section()
    table.add_row(f"{e} Total", "", "", f"{total_vcore_usage_per_env}")
    table.add_section()
  else:
    table.add_row(f"{e}", f"{total_vcore_usage_per_env}")

if detailed_view:
  table.add_section()
  table.add_row(f"Total", "", "", f"{total_vcore_usage}")
else:
  table.add_section()
  table.add_row(f"Total", f"{total_vcore_usage}")
  
console.print(table)
