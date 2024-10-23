import argparse
from .audit import run_audit
from .utils import setup_logging

def parse_arguments():
    parser = argparse.ArgumentParser(description='GitHub Organization/User/Repository Audit Script')
    parser.add_argument('-a', '--auth', required=True, help='GitHub API token')
    parser.add_argument('-t', '--target', required=True, help='Target in format: org, user, org/repo, or user/repo')
    parser.add_argument('-o', '--output', choices=['html', 'json'], default='html', help='Output format (default: html)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    return parser.parse_args()

def main():
    args = parse_arguments()
    setup_logging(args.verbose)
    run_audit(args)

if __name__ == '__main__':
    main()