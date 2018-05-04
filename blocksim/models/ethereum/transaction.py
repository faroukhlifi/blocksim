from blocksim.models.transaction import Transaction
from blocksim.utils import keccak_256, encode_hex
from blocksim.models.ethereum.config import default_config


class ETHTransaction(Transaction):
    """ Defines a simple transaction model for the Ethereum.

    :param to: destination address
    :param sender: sender address
    :param value: amount to send to destination
    :param signature: sender signature
    :param int nonce: sequence number, issued by the originating EOA, used to prevent message replay
    :param gasprice: price of gas (in wei) the originator is willing to pay
    :param startgas: maximum amount of gas the originator is willing to pay, also known as gaslimit

    """

    def __init__(self,
                 to,
                 sender,
                 value,
                 signature,
                 nonce: int,
                 gasprice,
                 startgas=default_config['TX_BASE_GAS_COST']):
        # In Ethereum the fee is calculated as following:
        fee = gasprice * startgas
        super().__init__(to, sender, value, signature, fee)
        self.nonce = nonce
        self.gasprice = gasprice
        self.startgas = startgas

    @property
    def hash(self):
        """The transaction hash calculated using Keccak 256"""
        return encode_hex(keccak_256(str(self).encode('utf-8')))

    def __lt__(self, other):
        return isinstance(other, self.__class__) and self.gasprice < other.gasprice

    def __le__(self, other):
        return isinstance(other, self.__class__) and self.gasprice <= other.gasprice

    def __gt__(self, other):
        return isinstance(other, self.__class__) and self.gasprice > other.gasprice

    def __ge__(self, other):
        return isinstance(other, self.__class__) and self.gasprice >= other.gasprice
