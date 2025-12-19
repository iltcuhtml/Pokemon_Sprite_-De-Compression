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
    primary_buffer = 0
    initial_packet = 0

    def __init__(self, bin_str):
        super().__init__(bin_str)

        self.sprite_width = int(self.consume(4), 2)
        self.sprite_height = int(self.consume(4), 2)
        self.primary_buffer = int(self.consume(1), 2)
        self.initial_packet = int(self.consume(1), 2)
        
        if self.initial_packet == 0:
            self.decompressTypeA()
        
        else:
            self.decompressTypeB()
        
        self.renderSprite()

    def decompressTypeA(self):
        pass

    def decompressTypeB(self):
        pass

    def renderSprite(self):
        pass

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
    

def main():
    file_adr = input("Enter the compressed binary file address (*.bin): ")
    file = open(file_adr, "rb")

    bin_str = ''.join(f'{byte:08b}' for byte in bytes.fromhex(file.read().hex()))
    sprite = Sprite(bin_str)

    print(sprite.sprite_width, sprite.sprite_height)

    file.close()

if __name__ == "__main__":
    main()