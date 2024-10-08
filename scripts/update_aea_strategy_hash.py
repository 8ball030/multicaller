"""
Simple script to update the hash of the strategy in the AEA config file.

Usage:

python scripts/update_aea_strategy_hash.py <path_to_aea_config_file|aea_config.yaml> <strategy_hash>
Example:
"""


import click
import re

def update_aea_strategy_hash(aea_config_path: str, strategy_hash: str) -> None:
    """
    Update the strategy hash in the AEA config file.
    """

    replace_with = 'file_hash_to_id: ${list:[[' + f'"{strategy_hash.strip()}"'+ ',["sma_strategy"]]]}'

    with open(aea_config_path, 'r') as file:
        filedata = file.read()


    # We search uintil ",

    regex = r"file_hash_to_id: \$\{list:\[\[\"[a-zA-Z0-9]*\",\[\"sma_strategy\"\]\]\]\}"

    newdata = re.sub(regex, replace_with, filedata)

    with open(aea_config_path, 'w') as file:
        file.write(newdata)


    
    

@click.command()
@click.argument('aea_config_path', type=click.Path(exists=True))
@click.argument('strategy_hash', type=str)
def main(aea_config_path: str, strategy_hash: str) -> None:
    """
    Update the strategy hash in the AEA config file.
    """
    update_aea_strategy_hash(aea_config_path, strategy_hash)
    print('Strategy hash updated successfully.')

if __name__ == '__main__':
    main()

