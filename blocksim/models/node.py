from collections import namedtuple

from blocksim.models.network import Connection, Network
from blocksim.models.chain import Chain
from blocksim.models.ethereum.block import Block, BlockHeader

Envelope = namedtuple('Envelope', 'msg, timestamp, destination, origin')

MAX_KNOWN_TXS = 30000 # Maximum transactions hashes to keep in the known list (prevent DOS)
MAX_KNOWN_BLOCKS = 1024 # Maximum block hashes to keep in the known list (prevent DOS)

class Node:
    """This class represents the node.

    Each node has their own `chain`, and when a node is initiated its started with a clean chain.

    A node needs to be initiated with known `neighbors` to run the simulation. For now there is
    not any mechanism to discover neighbors.

    To properly stimulate a real world scenario, the node model needs to know the geographic
    `location` and his `transmission_speed`.

    In order to a node to be identified in the network simulation, is needed to have an `address`
    """
    def __init__(self, env, network: Network, transmission_speed, location: str, address: str):
        self.env = env
        self.transmission_speed = transmission_speed
        self.location = location
        self.address = address
        self.neighbors = {}
        # Create genesis block and init the chain
        genesis = Block(BlockHeader())
        self.chain = Chain(genesis)
        # The node will join to the network
        network.add_node(self)

    def add_neighbors(self, *nodes):
        """Add nodes as neighbors"""
        for node in nodes:
            connection = Connection(self.env, self, node)
            self.neighbors[node.address] = {
                'connection': connection,
                'head': node.chain.head,
                'location': node.location,
                'address': node.address,
                'knownTxs': {''},
                'knownBlocks': {''}
            }

    def _update_neighbors(self, new_neighbor: dict):
        address = new_neighbor.get('address')
        self.neighbors[address] = new_neighbor

    def _get_neighbor(self, neighbor_address: str):
        neighbor = self.neighbors.get(neighbor_address)
        if neighbor is None:
            raise RuntimeError('Neighbor {} not reachable by the {}'.format(neighbor_address, self.address))
        return neighbor

    def _mark_block(self, block_hash: str, neighbor_address: str):
        """Marks a block as known for the neighbor, ensuring that it will never be
        propagated to this particular neighbor."""
        neighbor = self._get_neighbor(neighbor_address)
        known_blocks = neighbor.get('knownBlocks')
        while len(known_blocks) >= MAX_KNOWN_BLOCKS:
            known_blocks.pop()
        known_blocks.add(block_hash)
        neighbor['knownBlocks'] = known_blocks
        self._update_neighbors(neighbor)

    def _mark_transaction(self, tx_hash: str, neighbor_address: str):
        """Marks a transaction as known for the neighbor, ensuring that it will never be
        propagated to this particular neighbor."""
        neighbor = self._get_neighbor(neighbor_address)
        known_txs = neighbor.get('knownTxs')
        while len(known_txs) >= MAX_KNOWN_TXS:
            known_txs.pop()
        known_txs.add(tx_hash)
        neighbor['knownTxs'] = known_txs
        self._update_neighbors(neighbor)

    def listening(self, download_rate):
        # TODO: When sending add an download rate in Mbps
        for neighbor in self.neighbors.items():
            connection: Connection = neighbor['connection']
            if connection is None:
                raise RuntimeError('There is not a direct connection with the neighbor ({})'
                .format(neighbor))
            print('At {}: Node {} is listening for inbound connections from the {}'
            .format(self.env.now, self.address, connection.destination_node.address))
            while True:
                # Get the message from connection
                envelope = yield connection.get()
                print('At {}: Node with address {} receive the message: {} at {} from {}'.format(
                    self.env.now,
                    self.address,
                    envelope.msg,
                    envelope.timestamp,
                    envelope.origin.address
                ))
                yield self.env.timeout(download_rate)

    def send(self, destination_address: str, upload_rate, msg):
        """Sends a message to a specific `destination_address`"""
        # TODO: Add a Store here to queue the messages that need to be sent
        neighbor = self._get_neighbor(destination_address)
        connection = neighbor.get('connection')
        if connection is None:
            raise RuntimeError('There is not a direct connection with the neighbor ({})'
            .format(neighbor))

        # TODO: Calculate a delay/timeout do simulate the TCP handshake
        yield self.env.timeout(3)
        # TODO: When sending add an upload rate
        yield self.env.timeout(upload_rate)
        envelope = Envelope(msg, self.env.now, connection.destination_node, connection.origin_node)
        connection.put(envelope)
