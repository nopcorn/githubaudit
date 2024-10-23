import requests
import logging
import sys
import time


class GitHub:
    def __init__(self, token, target):
        self.config = {
            'headers': {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            },
            'api_url': 'https://api.github.com',
            'target': target
        }
        self.session = requests.Session()
        self.session.headers.update(self.config['headers'])
        self.max_retries = 3
        self.retry_delay = 5
        self.validate()
        self.get_logo()


    def _make_request(self, method, url, **kwargs):
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, **kwargs)
                
                if response.status_code == 429:  # rate limit exceeded
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    sleep_time = max(reset_time - time.time(), 0) + 1
                    logging.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds.")
                    time.sleep(sleep_time)
                    continue
                else:
                    return response

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    logging.error(f"Error making request to {url}: {str(e)}")
                    raise
                logging.warning(f"Request failed. Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        raise requests.exceptions.RequestException("Max retries exceeded")


    def validate(self):
        user_url = f"{self.config['api_url']}/user"
        response = self._make_request('GET', user_url)
        if response.status_code != 200:
            logging.error(f"Invalid GitHub token. HTTP Status Code: {response.status_code}")
            sys.exit(1)
        
        authenticated_user = response.json()['login']
        logging.info(f"Authenticated as: {authenticated_user}")

        # check scopes
        scopes = response.headers.get('X-OAuth-Scopes', '').split(', ')
        required_scopes = {'repo'}
        missing_scopes = required_scopes - set(scopes)
        if missing_scopes:
            logging.error(f"Token is missing required scopes: {', '.join(missing_scopes)}")
            logging.error(f"Current scopes: {', '.join(scopes)}")
            sys.exit(1)
        logging.info(f"Token has all required scopes: {', '.join(required_scopes)}")

        if '/' in self.config['target']:
            owner, repo = self.config['target'].split('/', 1)
        else:
            owner, repo = self.config['target'], None

        org_url = f"{self.config['api_url']}/orgs/{owner}"
        user_url = f"{self.config['api_url']}/users/{owner}"
        
        org_response = self._make_request('GET', org_url)
        user_response = self._make_request('GET', user_url)
        
        if org_response.status_code == 200:
            target_type = 'organization'
            target_slug = f'orgs/{owner}'
        elif user_response.status_code == 200:
            target_type = 'user'
            target_slug = f'users/{owner}'
        else:
            logging.error(f"Unable to access the specified target. HTTP Status Codes: Org {org_response.status_code}, User {user_response.status_code}")
            sys.exit(1)

        logging.info(f"Successfully validated access to {target_type}: {owner}")

        if repo:
            repo_url = f"{self.config['api_url']}/repos/{owner}/{repo}"
            repo_response = self._make_request('GET', repo_url)
            if repo_response.status_code != 200:
                logging.error(f"Unable to access the specified repository. HTTP Status Code: {repo_response.status_code}")
                sys.exit(1)
            logging.info(f"Successfully validated access to repository: {repo}")

        self.config['owner'] = owner
        self.config['repo'] = repo
        self.config['target_type'] = target_type
        self.config['target_slug'] = target_slug


    def get_metadata(self):
        return {
            'target': self.config['target'],
            'logo_url': self.config['logo_url']
        }


    def get_logo(self):
        url = f"{self.config['api_url']}/{self.config['target_slug']}"
        response = self._make_request('GET', url)
        if response.status_code == 200:
            data = response.json()
            self.config['logo_url'] = data.get('avatar_url')
        else:
            self.config['logo_url'] = 'https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png'


    def get_repos(self):
        if self.config['repo']:
            url = f"{self.config['api_url']}/repos/{self.config['owner']}/{self.config['repo']}"
            response = self._make_request('GET', url)
            response.raise_for_status()
            return [response.json()]
        else:
            repos = []
            page = 1
            while True:
                url = f"{self.config['api_url']}/user/repos?per_page=100&page={page}"
                response = self._make_request('GET', url)
                response.raise_for_status()
                page_repos = response.json()
                
                page_repos = [repo for repo in page_repos if not repo['archived'] and repo['owner']['login'] == self.config['owner']]
                repos.extend(page_repos)
                
                if 'next' not in response.links:
                    break
                page += 1
            return repos


    def get_topics(self, repo_name):
        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/topics"
        response = self._make_request('GET', url)
        response.raise_for_status()
        return response.json()['names']


    def get_branch_protection(self, repo_name, branch):
        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/branches/{branch}"
        response = self._make_request('GET', url)
        return response.json().get('protected', False)


    def get_environments(self, repo_name):
        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/environments"
        response = self._make_request('GET', url)
        if response.status_code == 200:
            return response.json()['environments']
        return []


    def get_secrets(self, repo_name, environments):
        secrets = {}

        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/actions/secrets"
        response = self._make_request('GET', url)
        if response.status_code == 200:
            if response.json().get('total_count') > 0:
                secrets['_repo'] = [s['name'] for s in response.json().get('secrets') if 'name' in s]
        else:
            secrets['_repo'] = f"HTTP CODE {response.status_code}"
        
        for env in environments:
            env_name = env['name']
            url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/environments/{env_name}/secrets"
            response = self._make_request('GET', url)
            if response.status_code == 200:
                if response.json().get('total_count') > 0:
                    secrets[env_name] = [secret['name'] for secret in response.json()['secrets']]
            else:
                secrets[env['name']] = f"http_error {response.status_code}"
        
        return secrets


    def get_codeowners(self, repo_name):
        codeowners_files = [
            {'label': 'root', 'path': 'CODEOWNERS'},
            {'label': 'docs', 'path': 'docs/CODEOWNERS'},
            {'label': '.github', 'path': '.github/CODEOWNERS'}
        ]
        
        codeowners_data = {'files': [], 'has_errors': False}

        for file in codeowners_files:
            url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/contents/{file['path']}"
            response = self._make_request('GET', url)
            
            if response.status_code == 200:
                codeowners_data['files'].append(file['label'])
                content_url = response.json()['download_url']
                content_response = self._make_request('GET', content_url)
                content = content_response.text
                

        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/codeowners/errors"
        response = self._make_request('GET', url)
        if response.status_code == 200:
            if len(response.json()['errors']) > 0:
                codeowners_data['has_errors'] = True
        
        return codeowners_data
    

    def get_rulesets(self, repo_name):
        rulesets = []

        url = f"{self.config['api_url']}/repos/{self.config['owner']}/{repo_name}/rulesets"
        response = self._make_request('GET', url)
        if response.status_code == 200:
            rules = response.json()
            for rule in rules:
                rulesets.append(rule.get('name'))

        return rulesets