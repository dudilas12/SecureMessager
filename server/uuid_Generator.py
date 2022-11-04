import uuid


def uuidGen():
    hex_data = uuid.uuid1().hex

    ascii_string = ''

    byte_array = bytearray.fromhex(hex_data)
    return byte_array




