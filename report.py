"""
Cli tool to generate a report of of the trading history of a given account.
"""
from pathlib import Path
from aea.aea import Envelope
import rich_click as click
from packages.eightballer.connections.dcxt.dcxt.balancer import LEDGER_TO_NATIVE_SYMBOL, LEDGER_TO_TOKEN_LIST, SupportedLedgers
from packages.eightballer.connections.dcxt.interfaces.interface_base import get_dialogues
from packages.eightballer.connections.dcxt.tests.test_dcxt_connection import BaseDcxtConnectionTest



from packages.eightballer.contracts.erc_20.contract import Erc20Token
from packages.eightballer.contracts.erc_20.tests.test_contract import TestContractCommon
from packages.eightballer.protocols.balances.dialogues import BalancesDialogue, BaseBalancesDialogues
from packages.eightballer.protocols.balances.message import BalancesMessage



PACKAGE_DIR = Path(__file__).parent.parent

DEFAULT_ADDRESS = "http://eth.chains.wtf:8545"

DAI_ADDRESS = "0x6b175474e89094c44da98b954eedeac495271d0f"
OLAS_ADDRESS = "0x0001a500a6b18995b03f44bb040a5ffc28e45cb0"




from rich.console import Console
from rich.table import Table
from rich import print
import pandas as pd


RPC_MAPPING = {
    SupportedLedgers.ETHEREUM: "http://eth.chains.wtf:8545",
    SupportedLedgers.BASE: "https://rpc.ankr.com/base",
    SupportedLedgers.OPTIMISM: "https://rpc.ankr.com/optimism",
    SupportedLedgers.GNOSIS: "https://rpc.ankr.com/gnosis",
    SupportedLedgers.POLYGON_POS: "https://rpc.ankr.com/polygon",
    SupportedLedgers.ARBITRUM: "https://rpc.ankr.com/arbitrum",
}

@click.command()
@click.argument("account", type=click.STRING)
@click.option("--ledger", type=click.Choice(
    [f.value for f in SupportedLedgers] + ["all"]
    ), default="all")
@click.option("--portfolio-requires", type=click.Path(), default=None)
@click.option("--output", type=click.Path(), default=None)
def check_balances(account: str, ledger: str, output: str, portfolio_requires: str):
    """
    Check the balances of the account.
    Use the --ledger option to specify the ledger.

    Example:
    check_balances 0x1234 --ledger ethereum
    """
    print(f"Checking balances for account {account} on ledger `{ledger}`.")
    print()


    contract = TestContractCommon()

    if ledger == "all":
        ledgers = [f.value for f in SupportedLedgers]
    else:
        ledgers = [ledger]


    console = Console(
        record=True if output else False,
    )

    ledger_data = {}
    for ledger in ledgers:
        contract.setup(address=RPC_MAPPING[SupportedLedgers(ledger)])

        token_list = LEDGER_TO_TOKEN_LIST[SupportedLedgers(ledger)]
        
        account = contract.ledger_api.api.to_checksum_address(account)
        tokens = [Erc20Token(**contract.contract.get_token(contract.ledger_api, token_data)
                             ) for token_data in token_list]
    
        for token in tokens:
            token.balance = contract.contract.balance_of(contract.ledger_api, token.address, account)['int']

        table = Table(title=f"Balances account `{account}` on ledger {ledger}", min_width=80)
        table.add_column("Token")
        table.add_column("Balance")
        table.add_column("Address")
        data = []
        for token in tokens:
            row = [
                token.symbol,
                token.to_human(token.balance),
                token.address
            ]
            table.add_row(*[str(cell) for cell in row])
            data.append(row + [token])
        
        ledger_data[ledger] = data

        # We also add in the native balance and symbol;
        native_balance = contract.ledger_api.get_balance(account)
        if native_balance:
            native_balance /= 10**18
        table.add_row(LEDGER_TO_NATIVE_SYMBOL[SupportedLedgers(ledger)], f"{native_balance}")


        console.print(table, justify="left", markup=True, highlight=True)
        print() 
    

    all_data = pd.DataFrame()
    for ledger, data in ledger_data.items():
        df = pd.DataFrame(data, columns=["Token", "Balance", "Address", "Token Object"])
        df['ledger'] = ledger
        all_data = pd.concat([all_data, df])

    all_data = all_data.sort_values(by=["ledger", "Token"])
    # We can now pivot the table
    balances_by_ledger = all_data.pivot(index="Token", columns="ledger", values="Balance").transpose()

    console.print(balances_by_ledger)

    totals = all_data[['Token', 'Balance']].groupby("Token").sum()

    console.print(totals)





    if output:
        console.save_html(output)

    
    print("Done.")















@click.command()
@click.argument("account", type=str)
def check_trades():
    """Check the trades of the account."""
    pass

# We create a click group to group the commands
@click.group()
def report():
    """Cli tool to generate a report of of the trading history of a given account."""
    pass

# We add the commands to the group
report.add_command(check_balances)
report.add_command(check_trades)

if __name__ == "__main__":
    report()  # pylint: disable=no-value-for-parameter


