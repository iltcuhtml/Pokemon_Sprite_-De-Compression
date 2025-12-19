def printColor(color):
    if color in [0x00, 0x01, 0x10, 0x11]:
        if color == 0x00:
            color = "107"

        elif color == 0x01:
            color = "47"

        elif color == 0x10:
            color = "100"

        else:
            color = "40"

    else:
        raise ValueError("Invalid color code. Must be one of 00, 01, 10, or 11.")
    
    print("\033[" + color + "m" + "  " + "\033[0m", end='')

class BitStream:
    bin_str = ""
    pointer = 0

    def __init__(self, bin_str):
        self.bin_str = bin_str

    def consume(self, length):
        bits = self.bin_str[self.pointer:self.pointer + length]

        self.pointer += length
        
        return bits

class Sprite(BitStream):
    sprite_width = 0
    sprite_height = 0

    sprite_size = 0

    # 0 = Buffer B, 1 = Buffer C
    buffer_type = 0

    # 0 = RLE, 1 = Data
    packet_type = 0

    # "0" = Mode 1, "10" = Mode 2, "11" = Mode 3
    decoding_method = "0"

    offset = 0

    Buffer_A = ""
    Buffer_B = ""
    Buffer_C = ""

    def __init__(self, bin_str):
        super().__init__(bin_str)

        self.sprite_width = int(self.consume(4), 2)
        self.sprite_height = int(self.consume(4), 2)

        self.sprite_size = self.sprite_width * self.sprite_height

        self.buffer_type = int(self.consume(1), 2)
        self.packet_type = int(self.consume(1), 2)

        self.offset = (7 * int(4 - self.sprite_width / 2) + (7 - self.sprite_height)) * 64

    def decompress(self):
        while ((self.buffer_type == 0 and len(self.Buffer_B) < self.sprite_size * 64) or 
               (self.buffer_type == 1 and len(self.Buffer_C) < self.sprite_size * 64)):
            
            if self.packet_type == 0:
                self.decodeRLEPacket()

            else:
                self.decodeDataPacket()

            self.packet_type ^= 1

        self.buffer_type ^= 1

    def decodeRLEPacket(self):
        buffer = self.consume(1)

        while buffer[-1] != "0":
            buffer += self.consume(1)

        buffer = int(buffer, 2) + int(self.consume(len(buffer)), 2) + 1

        if self.buffer_type == 0:
            self.Buffer_B += "00" * buffer

        else:
            self.Buffer_C += "00" * buffer

    def decodeDataPacket(self):
        buffer = self.consume(2)

        while buffer[-2:] != "00":
            buffer += self.consume(2)

        if self.buffer_type == 0:
            self.Buffer_B += buffer[:-2]

        else:
            self.Buffer_C += buffer[:-2]

    def getEncodingMethod(self):
        self.decoding_method = self.consume(1)

        if self.decoding_method == "1":
            self.decoding_method += self.consume(1)

        self.packet_type = int(self.consume(1), 2)

    def decode(self):
        bit = 0

        if self.decoding_method != "10":
            for i in range(self.sprite_size * 64):
                if self.buffer_type == 0:
                    bit ^= self.Buffer_C[i]

                    self.Buffer_C[i] = bit

                else:
                    bit ^= self.Buffer_B[i]

                    self.Buffer_B[i] = bit

        bit = 0

        for i in range(self.sprite_size * 64):
            if self.buffer_type == 0:
                bit ^= self.Buffer_B[i]

                self.Buffer_B[i] = bit

            else:
                bit ^= self.Buffer_C[i]

                self.Buffer_C[i] = bit

        if self.decoding_method != "0":
            for i in range(self.sprite_size * 64):
                if self.buffer_type == 0:
                    self.Buffer_C[i] = self.buffer_B[i] ^ self.Buffer_C[i]

                else:
                    self.Buffer_B[i] = self.buffer_C[i] ^ self.Buffer_B[i]

        self.Buffer_A = "0" * self.offset

        # TODO: Buffer A rendering

    def render(self):
        pass

def main():
    file_adr = input("Enter the compressed binary file address (*.bin): ")
    file = open(file_adr, "rb")

    bin_str = ''.join(f'{byte:08b}' for byte in bytes.fromhex(file.read().hex()))
    sprite = Sprite(bin_str)

    sprite.decompress()
    sprite.getEncodingMethod()
    sprite.decompress()
    sprite.decode()

    file.close()

if __name__ == "__main__":
    main()