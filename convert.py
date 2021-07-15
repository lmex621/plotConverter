import blspy
import io
from blspy import AugSchemeMPL, G1Element, PrivateKey
from typing import Any, BinaryIO
from typing import List, Optional
from typing import List, Optional, Tuple
import os
import math
import glob

new_puzzle_key = 'xch1gcugp6ucqks2hzfeqfkz74tsx3r6ece9lh42hxyj742nqjwm79rqs23qxr'
new_farmer_key = '93e9f654ff3515aaa7d9a350d581acb8c454914b5422ac5486217dcacb3fcbd9a009eecb5d0ff91e30b43baa755b975e'



def make_sized_bytes(size: int):
    """
    Create a streamable type that subclasses "bytes" but requires instances
    to be a certain, fixed size.
    """
    name = "bytes%d" % size

    def __new__(cls, v):
        v = bytes(v)
        if not isinstance(v, bytes) or len(v) != size:
            raise ValueError("bad %s initializer %s" % (name, v))
        return bytes.__new__(cls, v)  # type: ignore

    @classmethod  # type: ignore
    def parse(cls, f: BinaryIO) -> Any:
        b = f.read(size)
        assert len(b) == size
        return cls(b)

    def stream(self, f):
        f.write(self)

    @classmethod  # type: ignore
    def from_bytes(cls: Any, blob: bytes) -> Any:
        # pylint: disable=no-member
        f = io.BytesIO(blob)
        result = cls.parse(f)
        assert f.read() == b""
        return result

    def __bytes__(self: Any) -> bytes:
        f = io.BytesIO()
        self.stream(f)
        return bytes(f.getvalue())

    def __str__(self):
        return self.hex()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, str(self))

    namespace = dict(
        __new__=__new__,
        parse=parse,
        stream=stream,
        from_bytes=from_bytes,
        __bytes__=__bytes__,
        __str__=__str__,
        __repr__=__repr__,
    )

    return type(name, (bytes,), namespace)



bytes32 = make_sized_bytes(32)

def std_hash(b) -> bytes32:
    """
    The standard hash used in many places.
    """
    return bytes32(blspy.Util.hash256(bytes(b)))

def calculate_plot_id_ph(
    pool_contract_puzzle_hash: bytes32,
    plot_public_key: G1Element,
) -> bytes32:
    return std_hash(bytes(pool_contract_puzzle_hash) + bytes(plot_public_key))

def stream_plot_info_ph(
    pool_contract_puzzle_hash: bytes32,
    farmer_public_key: G1Element,
    local_master_sk: PrivateKey,
):
    # There are two ways to stream plot info: with a pool public key, or with a pool contract puzzle hash.
    # This one streams the pool contract puzzle hash, into bytes
    data = pool_contract_puzzle_hash + bytes(farmer_public_key) + bytes(local_master_sk)
    assert len(data) == (32 + 48 + 32)
    return data

def generate_taproot_sk(local_pk: G1Element, farmer_pk: G1Element) -> PrivateKey:
    taproot_message: bytes = bytes(local_pk + farmer_pk) + bytes(local_pk) + bytes(farmer_pk)
    taproot_hash: bytes32 = std_hash(taproot_message)
    return AugSchemeMPL.key_gen(taproot_hash)

def generate_plot_public_key(local_pk: G1Element, farmer_pk: G1Element, include_taproot: bool = False) -> G1Element:
    if include_taproot:
        taproot_sk: PrivateKey = generate_taproot_sk(local_pk, farmer_pk)
        return local_pk + farmer_pk + taproot_sk.get_g1()
    else:
        return local_pk + farmer_pk

def _derive_path(sk: PrivateKey, path: List[int]) -> PrivateKey:
    for index in path:
        sk = AugSchemeMPL.derive_child_sk(sk, index)
    return sk

def master_sk_to_local_sk(master: PrivateKey) -> PrivateKey:
    return _derive_path(master, [12381, 8444, 3, 0])

def bech32_polymod(values: List[int]) -> int:
    """Internal function that computes the Bech32 checksum."""
    generator = [0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3]
    chk = 1
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk

def bech32_hrp_expand(hrp: str) -> List[int]:
    """Expand the HRP into values for checksum computation."""
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]

M = 0x2BC830A3
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

def bech32_verify_checksum(hrp: str, data: List[int]) -> bool:
    return bech32_polymod(bech32_hrp_expand(hrp) + data) == M

def bech32_decode(bech: str) -> Tuple[Optional[str], Optional[List[int]]]:
    """Validate a Bech32 string, and determine HRP and data."""
    if (any(ord(x) < 33 or ord(x) > 126 for x in bech)) or (bech.lower() != bech and bech.upper() != bech):
        return (None, None)
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        return (None, None)
    if not all(x in CHARSET for x in bech[pos + 1 :]):
        return (None, None)
    hrp = bech[:pos]
    data = [CHARSET.find(x) for x in bech[pos + 1 :]]
    if not bech32_verify_checksum(hrp, data):
        return (None, None)
    return hrp, data[:-6]


def convertbits(data: List[int], frombits: int, tobits: int, pad: bool = True) -> List[int]:
    """General power-of-2 base conversion."""
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            raise ValueError("Invalid Value")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise ValueError("Invalid bits")
    return ret

def decode_puzzle_hash(address: str) -> bytes32:
    hrpgot, data = bech32_decode(address)
    if data is None:
        raise ValueError("Invalid Address")
    decoded = convertbits(data, 5, 8, False)
    decoded_bytes = bytes(decoded)
    return decoded_bytes




def readPlot(path):
    ogplot = True
    f = open(path,'rb')
    headerText :bytes = f.read(19)
    plotID :bytes = f.read(32)
    k :bytes = f.read(1)
    format_len :bytes = f.read(2)
    format_len_int = int.from_bytes(format_len,byteorder='big')
    format_byte :bytes = f.read(format_len_int)
    memo_len :bytes = f.read(2)
    memo_len_int = int.from_bytes(memo_len,byteorder='big')
    if memo_len_int == 128:
        ppk :bytes = f.read(48)
        farmer :bytes = f.read(48)
        sk :bytes = f.read(32)
    elif memo_len_int == 112:
        ppk :bytes = f.read(32)
        farmer :bytes = f.read(48)
        sk :bytes = f.read(32)
        ogplot = False
    
    f.close()

    return [headerText,plotID,k,format_len,format_byte,memo_len,ppk,farmer,sk,ogplot]


def createIdMemo(puzzle :str,farmer :str, skHeader :bytes):
    pool_contract_puzzle_hash: Optional[bytes32] =  decode_puzzle_hash(new_puzzle_key)
    farmer_public_key: G1Element =  G1Element.from_bytes(bytes.fromhex(new_farmer_key))


    sk = AugSchemeMPL.key_gen(b'4057f39822077663f4c97ce2ceacbdab8d559e230317c13a888008322040ef3b')

    sk = blspy.PrivateKey.from_bytes(skHeader)

    include_taproot: bool = pool_contract_puzzle_hash is not None
    plot_public_key = generate_plot_public_key(
        master_sk_to_local_sk(sk).get_g1(), farmer_public_key, include_taproot
    )


    plot_id = calculate_plot_id_ph(pool_contract_puzzle_hash, plot_public_key)
    plot_memo = stream_plot_info_ph(pool_contract_puzzle_hash, farmer_public_key, sk)
    return [plot_id,plot_memo]

def createHeader(plot_id :bytes,k :bytes,format_len:bytes,format_id :bytes,memo_len :bytes,memo :bytes):
    header :bytes
    header = b'Proof of Space Plot'
    header = header + plot_id
    header = header + k
    header = header + format_len
    header = header + format_id
    header = header + memo_len
    header = header + memo

    return header

def createPortable(oldpath,header :bytes,newpath):
    f = open(oldpath,'br')
    old :bytes = f.read(300)
    #f.close()
    old = old[188:]
    new = header + old
    o = open(newpath,'bw')
    o.write(new)
    o.close()

    size = os.path.getsize(oldpath)
    times = str(int(math.ceil(size/200000)))
    print('total progress: '+times+' times ')
    for i in range(int(math.ceil(size/200000))):
        if i % 1000 == 0:
            print(str(i)+'/'+times)
        old = f.read(200000)
        o = open(newpath,'ba')
        o.write(old)


    o.close()
    f.close()
    
    return



def main():

    dirPath = "create"
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
    plotList = glob.glob('*.plot')

    for i in range(len(plotList)):
        oldpath = plotList[i]
        print(oldpath)
        headerOld = readPlot(oldpath) #[headerText,plotID,k,format_len,format_byte,memo_len,ppk,farmer,sk,ogplot(bool)]
        IdMemo = createIdMemo(new_puzzle_key,new_farmer_key,headerOld[8])


        header :bytes = createHeader(IdMemo[0],headerOld[2],headerOld[3],headerOld[4],b'\x00\x70',IdMemo[1])

        idName = IdMemo[0].hex()
        newpath = 'create\\plot-k32-'+idName+'.plot'
        
        print("convert plot "+str(i+1)+"/"+str(len(plotList)))
        print("------------start convert------------")
        if headerOld[9] == True:
            createPortable(oldpath,header,newpath)
            os.remove(oldpath)
        else:
            print("skip "+oldpath)

        print("conplete to convert!")
        print("portable plot is in create folder")
    
    


if __name__ == '__main__':
    main()