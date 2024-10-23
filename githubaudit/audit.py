from .github import GitHub
from .output import generate_html, generate_json
from .utils import dict_to_pretty_string
import logging


def sort_issues_by_severity(issues):
    severity_order = {'high': 0, 'medium': 1, 'low': 2}
    return sorted(issues, key=lambda x: severity_order[x['level']])


def generate_issues(repo_data):
    issues = []

    # if branch protection is true but no codeowners
    if repo_data['branch_protection']['protected'] and len(repo_data['codeowners']['files']) == 0:
        issues.append({
            'level': 'high',
            'message': 'Branch protection is enabled but no CODEOWNERS files present'
        })

    # if codeowners but no branch protection
    if not repo_data['branch_protection']['protected'] and len(repo_data['codeowners']['files']) > 0:
        issues.append({
            'level': 'high',
            'message': 'CODEOWNERS files present but no branch protection configured'
        })

    # if codeowners has errors in it
    if repo_data['codeowners']['has_errors']:
        issues.append({
            'level': 'high',
            'message': 'Errors in CODEOWNERS file(s)'
        })

    # repository secrets present and unprotected
    if len(repo_data['secrets'].keys()) > 0:
        for key, value in repo_data['secrets'].items():
            if key == '_repo':
                issues.append({
                    'level': 'medium',
                    'message': 'Repository-wide secrets can be accessed by anyone with "write" permissions on repo'
                })
            else:
                for env in repo_data.get('environments'):
                    if env['name'] == key and not env['protection']:
                        issues.append({
                            'level': 'high',
                            'message': f'Secret present in "{env['name']}" environment without any environment protection'
                        })

    # unprotected environment, may provide additional access
    if len(repo_data.get('environments')) > 0:
        for env in repo_data.get('environments'):
            if not env['protection']:
                issues.append({
                    'level': 'low',
                    'message': f'Unprotected "{env['name']}" environment could lead to further privilege escalation (OIDC login, etc)'
                })

    return sort_issues_by_severity(issues)


def get_repo_data(github):
    repos = github.get_repos()
    repo_data = []
    
    for repo in repos:
        repo_name = repo['name']
        repo_url = repo['html_url']
        logging.info(f"Processing {repo_name}...")

        topics = github.get_topics(repo_name)
        
        branch_protection_data = {
            'default_branch': repo['default_branch'],
            'protected': github.get_branch_protection(repo_name, repo['default_branch'])
        }

        environments = github.get_environments(repo_name)
        env_data = []
        
        for env in environments:
            env_name = env['name']
            env_protection = len(env['protection_rules']) > 0

            env_data.append({
                'name': env_name,
                'protection': env_protection,
                'can_admins_bypass': env['can_admins_bypass']
            })
        
        secrets = github.get_secrets(repo_name, environments)
        codeowners = github.get_codeowners(repo_name)
        rulesets = github.get_rulesets(repo_name)

        tmp_repo_data = {
            'name': repo_name,
            'url': repo_url,
            'private': repo['private'],
            'topics': topics,
            'branch_protection': branch_protection_data,
            'environments': env_data,
            'secrets': secrets,
            'secrets_str': dict_to_pretty_string(secrets),
            'codeowners': codeowners,
            'rulesets': rulesets
        }

        tmp_repo_data['issues'] = generate_issues(tmp_repo_data)
        repo_data.append(tmp_repo_data)
    
    return repo_data


def run_audit(args):
    github = GitHub(args.auth, args.target)
    
    data = get_repo_data(github)
    
    if args.output == 'html':
        metadata = github.get_metadata()
        generate_html(metadata, data)
    else: 
        generate_json(data)