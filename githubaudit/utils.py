import json
import logging

def setup_logging(verbose):
    logging.basicConfig(level=logging.INFO if verbose else logging.WARN,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    if not verbose:
        logging.getLogger().disabled = True

def dict_to_pretty_string(d):
    return json.dumps(d, indent=2)